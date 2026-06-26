import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import commit_picker, page_content
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    _draw_browse_screen,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import CommitSummary, FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class CommitPickerTests(unittest.TestCase):
    def test_browse_screen_recent_commits_stays_scope_picker(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                )
            ],
            page="commits",
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: recent commits", text)
        self.assertNotIn("Scope: recent commits > Files", text)

    def test_commit_picker_rows_show_change_summary(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                    files=2,
                    added=10,
                    deleted=3,
                )
            ],
            page=BrowserPage.COMMIT_PICKER,
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("2 files, +10 -3", "\n".join(lines))
        self.assertIn("Example change", "\n".join(lines))

    def test_commit_picker_filter_matches_scope_summary_fields(self):
        commits = [
            CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-24",
                subject="Feature login",
                files=2,
                added=10,
                deleted=3,
            ),
            CommitSummary(
                commit="1111111122222222",
                parent="abcdef1234567890",
                authored_at="2026-06-25",
                subject="Docs only",
                files=1,
                added=1,
                deleted=0,
            ),
        ]

        self.assertEqual(commit_picker.filter_commits_by_query(commits, ""), commits)
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "ABCDEF"),
            [commits[0]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "2026-06-25"),
            [commits[1]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "login"),
            [commits[0]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "+10 -3"),
            [commits[0]],
        )

    def test_commit_picker_selected_commit_uses_filtered_results(self):
        commits = [
            CommitSummary(
                commit="1111111111111111",
                parent="0000000000000000",
                authored_at="2026-06-24",
                subject="Docs only",
            ),
            CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-25",
                subject="Feature login",
            ),
        ]

        self.assertIs(
            commit_picker.selected_commit(commits, selected=0, query="login"),
            commits[1],
        )
        self.assertIsNone(
            commit_picker.selected_commit(commits, selected=0, query="missing")
        )
        self.assertIsNone(commit_picker.selected_commit(commits, selected=9))

    def test_commit_picker_filter_shows_matches_and_count(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                    files=2,
                    added=10,
                    deleted=3,
                ),
                CommitSummary(
                    commit="1111111122222222",
                    parent="abcdef1234567890",
                    authored_at="2026-06-25",
                    subject="Docs only",
                    files=1,
                    added=1,
                    deleted=0,
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn('Filter: login (1/2 matches, c to clear)', text)
        self.assertIn("Feature login", text)
        self.assertNotIn("Docs only", text)

    def test_commit_picker_filter_empty_state(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="missing",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn("No recent commits match filter: missing (1 total).", text)
        self.assertIn("Press c to clear the filter.", text)

    def test_commit_picker_filter_commands_are_isolated_from_file_filter(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                )
            ],
            page=BrowserPage.COMMIT_PICKER,
            filter_text="src/",
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        set_result = executor.execute(parse_browser_command("/login"))
        clear_result = executor.execute(parse_browser_command("c"))

        self.assertTrue(set_result.handled)
        self.assertTrue(set_result.needs_redraw)
        self.assertTrue(clear_result.handled)
        self.assertEqual(state.page, BrowserPage.COMMIT_PICKER)
        self.assertEqual(state.filter_text, "src/")
        self.assertEqual(state.commit_filter_text, "")

    def test_commit_picker_number_selects_filtered_commit(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="1111111111111111",
                    parent="0000000000000000",
                    authored_at="2026-06-24",
                    subject="Docs only",
                ),
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-25",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/Login.ts", 1, 0)],
        ):
            result = executor.execute(parse_browser_command("1"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected_commit.subject, "Feature login")
        self.assertEqual(args.ref_range, "1234567890abcdef..abcdef1234567890")

    def test_commit_picker_filter_prompt_does_not_change_file_filter(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        frames: list[tuple[str, str, str]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, state.filter_text, state.commit_filter_text))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch(
                            "cr.ui.browser._load_recent_commits",
                            return_value=[
                                CommitSummary(
                                    commit="abcdef1234567890",
                                    parent="1234567890abcdef",
                                    authored_at="2026-06-25",
                                    subject="Feature login",
                                )
                            ],
                        ):
                            with patch("cr.ui.browser._show_commits_when_empty"):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=["g", "filter_prompt", "q"],
                                    ):
                                        with patch(
                                            "cr.ui.browser._read_filter_query",
                                            return_value="login",
                                        ):
                                            with patch(
                                                "cr.ui.browser._draw_browse_screen",
                                                side_effect=capture_draw,
                                            ):
                                                from cr.ui.browser import run_browser

                                                result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn((BrowserPage.COMMIT_PICKER, "", "login"), frames)

    def test_browse_screen_selected_commit_files_show_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range="abcdef1^..abcdef1",
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            selected_commit=CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-24",
                subject="Example change",
            ),
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        self.assertIn("Scope: commit abcdef12 > Files", output.getvalue())
