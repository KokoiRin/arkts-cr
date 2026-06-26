import os
import json
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import cr.ui.browser as browser_module
from cr.ui import input as browser_input
from cr.ui import commit_picker
from cr.ui import page_content
from cr.ui import source_file
from cr.ui import task_problems
from cr.ui.browser import (
    TaskState,
    BrowserActionResult,
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    ReviewWorkspace,
    TaskRecord,
    _build_command,
    _task_panel_lines,
    _task_status,
    _browse_command_lines,
    _browse_command_palette_screen_lines,
    _command_palette_entries,
    _filtered_command_palette_entries,
    _browse_file_lines,
    _browse_file_screen_lines,
    _browse_list_lines,
    _browse_list_screen_lines,
    _browser_workspace_state_path,
    _save_browser_workspace_state,
    _load_browser_workspace_state,
    _draw_task_panel_only,
    _draw_browse_screen,
    _move_selection,
    _normalize_command_query,
    _poll_task,
    _record_completed_task,
    _read_browse_command,
    _restore_browser_workspace_state,
    _rerun_task,
    _screen_layout,
    _show_browser_message,
    _start_task,
    _stop_task,
    _switch_review_scope,
    _task_command,
    filter_changes_by_query,
    ReviewScope,
)
from cr.review.changes import format_counts
from cr.review.data import build_review_data
from cr.review.snippet import render_file_diff_snippet
from cr.ui import command_catalog
from cr.ui import frame as frame_module
from cr.ui.terminal import TerminalStyle
from cr.vcs import git
from cr.vcs.git import CommitSummary, FileChange


ROOT = Path(__file__).resolve().parents[1]


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class CliTests(unittest.TestCase):


    def test_file_diff_snippet_renders_compact_selected_file_context(self):
        text = render_file_diff_snippet(
            {
                "path": "src/Sample.ets",
                "status": "modified",
                "summary": "+2 -1",
                "anchor": "src/Sample.ets:12",
                "risk_hints": ["high churn"],
                "seen": True,
                "review_note": "check lifecycle edge case",
                "purpose": "ArkTS page/component SamplePage",
                "modified_symbols": ["build"],
                "hunks": ["@@ -1 +1 @@", "-old", "+new"],
            }
        )

        self.assertIn("# File Diff: src/Sample.ets", text)
        self.assertIn("- change: +2 -1 (modified)", text)
        self.assertIn("- anchor: src/Sample.ets:12", text)
        self.assertIn("- state: seen", text)
        self.assertIn("- review note: check lifecycle edge case", text)
        self.assertIn("- purpose: ArkTS page/component SamplePage", text)
        self.assertIn("- focus: build", text)
        self.assertIn("```diff\n@@ -1 +1 @@\n-old\n+new\n```", text)
        self.assertNotIn("Please review these changes.", text)

    def test_build_review_data_attaches_matching_review_notes(self):
        change = FileChange("src/Sample.ts", 2, 1)

        with patch("cr.review.data.git.first_changed_line", return_value=3):
            with patch(
                "cr.review.data.git.file_diff",
                return_value="@@ -1 +1 @@\n-old\n+new\n",
            ):
                data = build_review_data(
                    [change],
                    review_notes={
                        "src/Sample.ts": "check lifecycle edge case",
                        "docs/Other.md": "not in copied prompt",
                    },
                )

        self.assertEqual(
            data["files"][0]["review_note"],
            "check lifecycle edge case",
        )
        self.assertNotIn("docs/Other.md", str(data))


    def test_browser_command_executor_reports_quit_intent(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("q"))

        self.assertEqual(result, BrowserActionResult(exit_code=0))

    def test_browser_command_executor_changes_page_and_requests_redraw(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("commands"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.COMMAND_PALETTE)

    def test_browser_command_executor_reports_unknown_command_feedback(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("wat"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Unknown command.", output.getvalue())

    def test_browser_command_executor_opens_selected_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            open_cmd="code -g {fileline}",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
                with patch("cr.ui.browser.file_actions.open_path", return_value=None) as open_path:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("open"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        open_path.assert_called_once_with(repo_file, 12, "code -g {fileline}")
        self.assertIn("Opened src/Sample.ts:12", output.getvalue())


    def test_browser_command_executor_applies_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source staged", raw_keys=True))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.source_filter, "staged")
        self.assertEqual(state.selected, 0)
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Staged.ts"],
        )

    def test_browser_command_executor_rejects_unknown_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 0, source="staged")])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("source generated"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")
        self.assertIn("Unknown source filter", output.getvalue())

    def test_browser_command_executor_clears_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0, source="staged")],
            source_filter="staged",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with redirect_stdout(StringIO()):
            result = executor.execute(parse_browser_command("source all"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")


    def test_browser_command_executor_copies_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ) as copy_diff:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy diff"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy_diff.assert_called_once_with(state, args)
        self.assertIn("Copied diff for src/Sample.ts", output.getvalue())

    def test_browser_command_executor_copies_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ):
            result = executor.execute(parse_browser_command("copy diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Copied diff for src/Sample.ts", state.status_message)

    def test_browser_command_executor_saves_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to tmp/current.md",
        ) as save_diff:
            with redirect_stdout(output):
                result = executor.execute(
                    parse_browser_command("save diff tmp/current.md")
                )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        save_diff.assert_called_once_with(state, args, "tmp/current.md")
        self.assertIn(
            "Saved diff for src/Sample.ts to tmp/current.md",
            output.getvalue(),
        )

    def test_browser_command_executor_saves_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to .cr/handoff/review-diff.md",
        ):
            result = executor.execute(parse_browser_command("save diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Saved diff for src/Sample.ts", state.status_message)

    def test_browser_command_executor_marks_done_and_moves_next_in_changed_files(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertIn("Moved to src/Second.ts", state.status_message)


    def test_browser_command_executor_done_next_does_not_skip_remaining_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
            remaining_only=True,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )
        self.assertEqual(state.selected, 0)
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_last_visible_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/Second.ts"})
        self.assertIn("No next file after src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_empty_visible_files(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, set())
        self.assertIn("No changed file to mark seen.", state.status_message)


    def test_browser_command_executor_reports_repeat_find_without_query(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Run find TEXT first.", state.status_message)

    def test_browser_command_executor_reports_repeat_find_without_matches(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        state.file_find_text = "owner"
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1  src/Sample.ts", "  context"],
        ):
            result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn('No matches for "owner".', state.status_message)


    def test_browser_command_executor_stages_selected_file_and_refreshes_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        state.file_line_cache["old"] = ["stale"]
        BrowserNavigation.open_file_detail(state)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.stage_path", return_value=None) as stage:
            with patch(
                "cr.ui.browser._load_browse_changes",
                return_value=[FileChange("src/New.ts", 1, 0)],
            ):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        stage.assert_called_once_with("src/Old.ts")
        self.assertEqual(state.changes, [FileChange("src/New.ts", 1, 0)])
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Staged src/Old.ts", output.getvalue())

    def test_browser_command_executor_stage_failure_does_not_refresh_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.git.stage_path",
            side_effect=git.GitError("cannot stage file"),
        ):
            with patch("cr.ui.browser._load_browse_changes") as load:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        load.assert_not_called()
        self.assertIn("Stage failed: cannot stage file", output.getvalue())

    def test_browser_command_executor_unstages_selected_file_and_refreshes_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Staged.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.unstage_path", return_value=None) as unstage:
            with patch("cr.ui.browser._load_browse_changes", return_value=[]):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_called_once_with("src/Staged.ts")
        self.assertEqual(state.changes, [])
        self.assertIn("Unstaged src/Staged.ts", output.getvalue())

    def test_browser_command_executor_stage_reports_empty_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.stage_path") as stage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        stage.assert_not_called()
        self.assertIn("No changed file to stage.", output.getvalue())

    def test_browser_command_executor_unstage_reports_empty_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.unstage_path") as unstage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_not_called()
        self.assertIn("No changed file to unstage.", output.getvalue())


    def test_browser_command_executor_steps_source_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:2:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                view_result = executor.execute(parse_browser_command("view problem"))
                next_result = executor.execute(parse_browser_command("next problem"))
                selected_after_next = state.problem_selected
                path_after_next = state.source_file_path
                line_after_next = state.source_file_line
                prev_result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(view_result.handled)
        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertEqual(selected_after_next, 1)
        self.assertEqual(path_after_next, "src/Two.ets")
        self.assertEqual(line_after_next, 2)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertTrue(prev_result.handled)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.source_file_path, "src/One.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)


    def test_browser_command_executor_does_not_use_stale_source_problem_for_context(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            other = repo / "src" / "Other.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 10)),
                encoding="utf-8",
            )
            other.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1), FileChange("src/Other.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:2:1 error TS9: other bad"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem context")
                            )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Problem Context: src/Foo.ets:5", copied)
        self.assertIn("## Source", copied)
        self.assertIn("## Diff", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertNotIn("src/Other.ets", copied)
        self.assertNotIn("other bad", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)


    def test_browser_command_executor_views_selected_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)


    def test_browser_command_executor_views_sorted_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=0,
                problem_sort="severity",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 warning W1: noisy",
                        "src/Two.ets:2:1 error E1: bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)


    def test_browser_command_executor_reports_no_task_problem_to_view(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertIn("No task problem to view.", state.status_message)

    def test_browser_command_executor_does_not_copy_empty_task_problems(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No task problem to copy.", state.status_message)

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No task problems to copy.", state.status_message)


    def test_browser_command_executor_runs_forward_navigation(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("forward"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)

    def test_browser_command_executor_opens_page_help(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE, source_file_path="src/Foo.ets")
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("help"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.SOURCE_FILE)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)

    def test_switch_review_scope_resets_page_history(self):
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
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )

        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_resets_page_history_for_reloaded_changes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])


    def test_browser_main_loop_delegates_action_execution(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")
        run_loop_source = source[source.index("def run_browser") : source.index("def _should_restore")]

        self.assertIn("BrowserCommandExecutor(", run_loop_source)
        self.assertIn(".execute(parsed_command)", run_loop_source)
        self.assertNotIn("BrowserCommandAction.RUN_BUILD", run_loop_source)
        self.assertNotIn("BrowserCommandAction.CHOOSE_NUMBER", run_loop_source)

    def test_review_workspace_loads_filters_and_switches_scope(self):
        loads: list[tuple[bool, bool, str | None, str | None, bool]] = []

        def loader(args):
            loads.append(
                (
                    args.staged,
                    args.all_changes,
                    args.base,
                    args.ref_range,
                    args.untracked,
                )
            )
            if args.staged:
                return [FileChange("src/Staged.ts", 3, 1)]
            return [
                FileChange("src/First.ts", 1, 0),
                FileChange("docs/Second.md", 2, 0),
            ]

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
            sort="git",
        )
        workspace = ReviewWorkspace.load(args, loader=loader)

        self.assertEqual(
            [change.path for change in workspace.changes],
            ["src/First.ts", "docs/Second.md"],
        )

        workspace.set_filter("src/")
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/First.ts"],
        )
        workspace.selected = 4
        workspace.list_scroll = 3
        workspace.previous_scope = ReviewScope(False, False, None, None, True)

        workspace.switch_scope(
            args,
            ReviewScope(True, False, None, None, False),
            loader=loader,
        )

        self.assertEqual(workspace.changes, [FileChange("src/Staged.ts", 3, 1)])
        self.assertEqual(workspace.filter_text, "")
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.list_scroll, 0)
        self.assertIsNone(workspace.previous_scope)
        self.assertEqual(loads[-1], (True, False, None, None, False))

    def test_review_workspace_reloads_changes_preserving_selected_path(self):
        args = argparse_namespace()
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 0),
            ],
            selected=1,
            filter_text="src/",
            list_scroll=5,
        )

        workspace.reload_changes(
            args,
            loader=lambda _args: [
                FileChange("src/Second.ts", 3, 1),
                FileChange("src/Third.ts", 1, 0),
            ],
            preserve_selected_path="src/Second.ts",
        )

        self.assertEqual(
            workspace.changes,
            [
                FileChange("src/Second.ts", 3, 1),
                FileChange("src/Third.ts", 1, 0),
            ],
        )
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.filter_text, "src/")
        self.assertEqual(workspace.list_scroll, 5)

    def test_review_workspace_is_used_by_main_browser_implementation(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("ReviewWorkspace", source)
        self.assertIn("load_workspace_changes", source)
        self.assertNotIn("selected_changes", source)
        self.assertNotIn("sort_changes", source)


    def test_review_workspace_selects_commit_scope_and_captures_previous_scope(self):
        loads: list[str | None] = []

        def loader(args):
            loads.append(args.ref_range)
            return [FileChange("src/Commit.ts", 4, 2)]

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
        )
        commit = CommitSummary(
            commit="abcdef1234567890",
            parent="1234567890abcdef",
            authored_at="2026-06-24",
            subject="Example",
        )
        workspace = ReviewWorkspace([FileChange("src/Old.ts", 1, 1)])
        workspace.filter_text = "Old"
        workspace.selected = 3
        workspace.list_scroll = 8

        workspace.select_commit(args, commit, loader=loader)

        self.assertEqual(
            workspace.previous_scope,
            ReviewScope(True, False, None, None, False),
        )
        self.assertIs(workspace.selected_commit, commit)
        self.assertEqual(args.ref_range, "1234567890abcdef..abcdef1234567890")
        self.assertFalse(args.staged)
        self.assertFalse(args.all_changes)
        self.assertFalse(args.untracked)
        self.assertEqual(workspace.changes, [FileChange("src/Commit.ts", 4, 2)])
        self.assertEqual(workspace.filter_text, "")
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.list_scroll, 0)
        self.assertEqual(loads[-1], "1234567890abcdef..abcdef1234567890")

    def test_review_workspace_serializes_and_restores_workspace_state_data(self):
        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
        )
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=0,
            filter_text="src/",
            seen_paths={"src/First.ts"},
            remaining_only=True,
            review_notes={"src/Second.ts": "check lifecycle edge case"},
        )

        data = workspace.state_data(args, mode=BrowserPage.FILE_DETAIL)

        self.assertEqual(data["scope"]["staged"], True)
        self.assertEqual(data["selected_path"], "src/Second.ts")
        self.assertEqual(data["selected_index"], 0)
        self.assertEqual(data["mode"], "file")
        self.assertEqual(data["seen_paths"], ["src/First.ts"])
        self.assertEqual(data["remaining_only"], True)
        self.assertEqual(
            data["review_notes"],
            {"src/Second.ts": "check lifecycle edge case"},
        )

        restored_args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
        )
        restored = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ]
        )
        mode = restored.restore_state(restored_args, data)

        self.assertTrue(restored_args.staged)
        self.assertFalse(restored_args.untracked)
        self.assertEqual(restored.filter_text, "src/")
        self.assertEqual(restored.selected, 0)
        self.assertEqual(restored.seen_paths, {"src/First.ts"})
        self.assertTrue(restored.remaining_only)
        self.assertEqual(
            restored.review_notes,
            {"src/Second.ts": "check lifecycle edge case"},
        )
        self.assertEqual(mode, "file")


    def test_format_counts_handles_binary_stats(self):
        self.assertEqual(format_counts(FileChange("asset.bin", None, None)), "+? -?")


    def test_browse_screen_renders_task_problems_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 1)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    kind="build",
                    lines=["src/Foo.ets:12:3 error: bad call"],
                    returncode=1,
                ),
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.frame.shutil.get_terminal_size",
                    return_value=os.terminal_size((120, 12)),
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Task Problems", text)
        self.assertIn("Task problems", text)
        self.assertIn("src/Foo.ets:12:3", text)
        self.assertIn("bad call", text)
        self.assertIn("cr:problems> ", text)


    def test_command_prompt_cancel_forces_full_browser_redraw(self):
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

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["command_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_command_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)

    def test_filter_prompt_cancel_forces_full_browser_redraw(self):
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

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["filter_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_filter_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)


    def test_task_problems_page_tick_redraws_main_content_not_panel_only(self):
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
        processes: list[subprocess.Popen[bytes]] = []

        def start_running_task(state, _args, _kind):
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            state.task = TaskState(["sleep"], process, lines=["first line"])

        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                with patch("cr.ui.browser.git.repo_root", return_value=repo):
                    with patch(
                        "cr.ui.browser._should_restore_browser_workspace_state",
                        return_value=False,
                    ):
                        with patch(
                            "cr.ui.browser._load_browse_changes",
                            return_value=[FileChange("src/Sample.ts", 1, 1)],
                        ):
                            with patch("cr.ui.browser._show_commits_when_empty"):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "build",
                                            "problems",
                                            browser_input.TICK,
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._start_task",
                                            side_effect=start_running_task,
                                        ):
                                            with patch(
                                                "cr.ui.browser._draw_browse_screen"
                                            ) as draw:
                                                with patch(
                                                    "cr.ui.browser._draw_task_panel_only"
                                                ) as panel_only:
                                                    from cr.ui.browser import run_browser

                                                    result = run_browser(args)
        finally:
            for process in processes:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)

        self.assertEqual(result, 0)
        self.assertGreaterEqual(draw.call_count, 4)
        panel_only.assert_not_called()

    def test_screen_layout_reserves_prompt_and_task_panel_regions(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["compile line"])

        plain = _screen_layout(None, rows=12)
        with_task = _screen_layout(build, rows=12)

        self.assertEqual(plain.prompt_row, 12)
        self.assertEqual(plain.content_height, 11)
        self.assertEqual(plain.task_height, 0)
        self.assertIsNone(plain.task_start_row)
        self.assertEqual(with_task.prompt_row, 12)
        self.assertEqual(with_task.task_start_row, 7)
        self.assertEqual(with_task.task_height, 5)
        self.assertEqual(with_task.content_height, 6)
        process.wait(timeout=1)

    def test_browse_screen_redraws_in_place(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertTrue(text.startswith("\033[2J\033[H"))
        self.assertIn("Scope: worktree > Files", text)
        self.assertIn("> 1", text)
        self.assertIn("└─ src", text)
        self.assertIn("└─ Sample.ts", text)
        self.assertIn("操作：Enter 打开", text)

    def test_browse_screen_action_bar_coexists_with_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((80, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("操作：Enter 打开", text)
        self.assertIn("compile line", text)
        self.assertIn("Build running", text)


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

    def test_browse_screen_scope_home_shows_review_scope_entries(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="scopes")
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: scope home", text)
        self.assertNotIn("Scope: scope home > Files", text)
        self.assertIn("Review scopes", text)
        self.assertIn("Worktree", text)
        self.assertIn("Staged", text)
        self.assertIn("All local changes", text)
        self.assertIn("Recent commits", text)
        self.assertIn("Base ref", text)
        self.assertIn(": base REF", text)
        self.assertIn("Explicit range", text)
        self.assertIn(": range OLD..NEW", text)

    def test_scope_home_screen_shows_live_scope_counts(self):
        state = BrowserState(
            [],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={
                "worktree": 2,
                "staged": 1,
                "all": 3,
                "commits": 4,
            },
        )

        lines = page_content.browse_scope_home_screen_lines(
            state,
            TerminalStyle(),
            max_lines=20,
        )
        text = "\n".join(lines)

        self.assertIn("Worktree (2 files)", text)
        self.assertIn("Staged (1 file)", text)
        self.assertIn("All local changes (3 files)", text)
        self.assertIn("Recent commits (4 commits)", text)
        self.assertNotIn("Base ref (", text)
        self.assertNotIn("Explicit range (", text)

    def test_scope_home_command_opens_scope_home(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.mode)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["scopes", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("scopes", frames)

    def test_scope_home_command_loads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 2, "staged": 1, "all": 3, "commits": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("scopes", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 2)
        load_counts.assert_called_once_with(args)

    def test_scope_home_refresh_reloads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={"worktree": 1},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("r", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 4)
        load_counts.assert_called_once_with(args)

    def test_scope_home_count_loader_counts_review_scope_candidates(self):
        args = argparse_namespace(paths=["src"], code=True, untracked=True)

        def changed_files(paths, staged=False, all_changes=False, include_untracked=False):
            self.assertEqual(paths, ["src"])
            if staged:
                self.assertFalse(include_untracked)
                return [FileChange("src/Staged.ts", 1, 0)]
            if all_changes:
                self.assertTrue(include_untracked)
                return [
                    FileChange("src/Staged.ts", 1, 0),
                    FileChange("src/Unstaged.ts", 1, 0),
                    FileChange("README.md", 1, 0),
                ]
            self.assertTrue(include_untracked)
            return [
                FileChange("src/Unstaged.ts", 1, 0),
                FileChange("README.md", 1, 0),
            ]

        with patch("cr.ui.browser.git.changed_files", side_effect=changed_files):
            with patch(
                "cr.ui.browser.git.recent_commits",
                return_value=[
                    CommitSummary(
                        commit="abcdef1234567890",
                        parent=None,
                        authored_at="2026-06-24",
                        subject="Example",
                    )
                ],
            ):
                counts = browser_module._load_scope_home_counts(args)

        self.assertEqual(
            counts,
            {"worktree": 1, "staged": 1, "all": 2, "commits": 1},
        )

    def test_scope_home_enter_switches_to_staged_scope(self):
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
        frames: list[tuple[str, bool, bool]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, args.staged, args.all_changes))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["scopes", "down", "enter", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", True, False), frames)

    def test_scope_home_enter_opens_recent_commits(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.mode)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch(
                                "cr.ui.browser._load_recent_commits",
                                return_value=[
                                    CommitSummary(
                                        commit="abcdef1234567890",
                                        parent="1234567890abcdef",
                                        authored_at="2026-06-24",
                                        subject="Example change",
                                    )
                                ],
                            ):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "scopes",
                                            "down",
                                            "down",
                                            "down",
                                            "enter",
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen",
                                            side_effect=capture_draw,
                                        ):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("commits", frames)

    def test_home_key_still_jumps_to_first_file_instead_of_opening_scope_home(self):
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
        frames: list[tuple[str, int]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, state.selected))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[
                            FileChange("src/First.ts", 1, 0),
                            FileChange("src/Second.ts", 1, 0),
                        ],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["down", "home", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", 1), frames)
        self.assertEqual(frames[-1], ("list", 0))

    def test_browse_screen_places_task_panel_above_prompt(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("compile line", text)
        self.assertIn("\033[12;1H\033[2Kcr:list> ", text)
        process.wait(timeout=1)

    def test_browse_context_line_shows_status_message(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            status_message="Opened src/Sample.ts:3",
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        self.assertIn(
            "Scope: worktree > Files  |  Opened src/Sample.ts:3",
            output.getvalue(),
        )

    def test_raw_key_open_feedback_stays_inside_browser_frame(self):
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
            open_cmd="echo {fileline}",
        )
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir()
            sample.write_text("sample\n", encoding="utf-8")
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["open", "q"],
                                ):
                                    with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                                        with patch(
                                            "cr.ui.browser.git.repo_path",
                                            return_value=sample,
                                        ):
                                            with patch("cr.ui.file_actions.subprocess.Popen"):
                                                with patch(
                                                    "cr.ui.browser._draw_browse_screen",
                                                    side_effect=capture_draw,
                                                ):
                                                    output = StringIO()
                                                    with redirect_stdout(output):
                                                        from cr.ui.browser import run_browser

                                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Opened", output.getvalue())
        self.assertIn("Opened src/Sample.ts:3", frames)

    def test_raw_key_invalid_selection_feedback_stays_inside_browser_frame(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["99", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        output = StringIO()
                                        with redirect_stdout(output):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Choose 1-1.", output.getvalue())
        self.assertIn("Choose 1-1.", frames)

    def test_raw_key_unknown_command_feedback_stays_inside_browser_frame(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["wat", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        output = StringIO()
                                        with redirect_stdout(output):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Unknown command.", output.getvalue())
        self.assertTrue(any(message.startswith("Unknown command.") for message in frames))

    def test_browse_screen_pads_short_content_before_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 30)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        before_panel = text.split("Build running", 1)[0]
        process.wait(timeout=1)
        self.assertEqual(before_panel.count("\n"), 23)

    def test_browse_screen_shows_command_list_with_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
            page="commands",
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 40)),
        ):
            with redirect_stdout(output):
                _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        process.wait(timeout=1)
        self.assertIn("命令面板", text)
        self.assertIn("Enter：执行选中命令", text)
        self.assertIn("审查范围", text)
        self.assertIn("compile line", text)
        self.assertIn("\033[40;1H\033[2Kcr:commands> ", text)

    def test_raw_key_command_read_does_not_print_newline(self):
        output = StringIO()

        with patch("cr.ui.browser._read_raw_key", return_value="down"):
            with redirect_stdout(output):
                command = _read_browse_command("cr:list> ", raw_keys=True)

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_raw_key_reader_does_not_print_newline(self):
        output = StringIO()

        with redirect_stdout(output):
            command = browser_input.read_browse_command(
                "cr:list> ",
                raw_keys=True,
                raw_key_reader=lambda timeout=None: "down",
            )

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_line_mode_returns_eof_and_interrupt_sentinels(self):
        eof_output = StringIO()
        interrupt_output = StringIO()

        with patch("builtins.input", side_effect=EOFError):
            with redirect_stdout(eof_output):
                eof_command = browser_input.read_browse_command("cr:list> ", raw_keys=False)
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(interrupt_output):
                interrupt_command = browser_input.read_browse_command(
                    "cr:list> ",
                    raw_keys=False,
                )

        self.assertEqual(eof_command, browser_input.EOF_COMMAND)
        self.assertEqual(interrupt_command, browser_input.INTERRUPT)
        self.assertEqual(eof_output.getvalue(), "\n")
        self.assertEqual(interrupt_output.getvalue(), "\n")

    def test_browser_input_idle_tick_uses_raw_idle_timeout(self):
        seen_timeouts = []

        command = browser_input.read_browse_command(
            "cr:list> ",
            raw_keys=True,
            tick_when_idle=True,
            raw_key_reader=lambda timeout=None: seen_timeouts.append(timeout)
            or browser_input.TICK,
        )

        self.assertEqual(command, browser_input.TICK)
        self.assertEqual(seen_timeouts, [browser_input.RAW_IDLE_TIMEOUT_SECONDS])

    def test_browse_tree_highlights_guides_and_uses_plain_white_file_names(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/pages/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/pages/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(True, True))

        text = output.getvalue()
        self.assertIn("\033[36m└─ src/pages\033[0m", text)
        self.assertIn("\033[36m   └─ \033[0m", text)
        self.assertIn("\033[37mSample.ts", text)
        self.assertNotIn("\033[36mSample.ts", text)
        self.assertNotIn("\033]8;;", text)

    def test_page_content_owns_prompt_labels_and_scroll_window(self):
        self.assertEqual(page_content.browse_prompt(BrowserPage.SCOPE_HOME), "cr:scopes> ")
        self.assertEqual(page_content.browse_prompt(BrowserPage.FILE_DETAIL), "cr:file> ")
        self.assertEqual(page_content.ensure_window(0, 8, 20, 5), 4)
        self.assertEqual(page_content.ensure_window(4, 2, 20, 5), 2)

    def test_page_content_builds_compacted_changed_file_tree(self):
        changes = [
            FileChange("src/pages/home/HomeView.ets", 1, 0),
            FileChange("src/pages/home/HomeModel.ets", 2, 1),
        ]

        rows = page_content.browse_tree_rows(changes)

        self.assertEqual(rows[0].label, "└─ src/pages/home")
        self.assertEqual(rows[1].label, "   ├─ HomeModel.ets")
        self.assertEqual(rows[2].label, "   └─ HomeView.ets")

    def test_page_content_changed_file_rows_show_source_badges(self):
        change = FileChange("src/Sample.ts", 1, 1, source="mixed")

        lines = page_content.browse_list_lines(
            [change],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            seen_paths=set(),
            review_notes={"src/Sample.ts": "check lifecycle"},
        )

        row = "\n".join(lines)
        self.assertIn("mixed", row)
        self.assertIn("[ ]", row)
        self.assertIn("modified", row)
        self.assertIn("note", row)

    def test_page_content_changed_file_header_shows_source_summary(self):
        lines = page_content.browse_list_lines(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 2, 1, source="unstaged"),
                FileChange("src/Mixed.ts", 3, 2, source="mixed"),
            ],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1, unstaged 1, mixed 1", "\n".join(lines))

    def test_page_content_source_summary_omits_zero_and_empty_sources(self):
        staged_lines = page_content.browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
        )
        comparison_lines = page_content.browse_list_lines(
            [FileChange("src/CommitOnly.ts", 1, 0)],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1", "\n".join(staged_lines))
        self.assertNotIn("unstaged 0", "\n".join(staged_lines))
        self.assertNotIn("Sources:", "\n".join(comparison_lines))

    def test_page_content_changed_file_header_shows_source_filter(self):
        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        lines = page_content.browse_list_screen_lines(
            state,
            argparse_namespace(),
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("Source: staged", "\n".join(lines))

    def test_browse_list_lines_wrapper_passes_source_filter(self):
        lines = _browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            source_filter="staged",
        )

        self.assertIn("Source: staged", "\n".join(lines))

    def test_browse_filter_matches_paths_and_clamps_selection(self):
        changes = [
            FileChange("src/pages/Home.ets", 1, 1),
            FileChange("src/components/Button.ts", 2, 0),
            FileChange("README.md", 1, 0),
        ]
        self.assertEqual(
            [change.path for change in filter_changes_by_query(changes, "BUTTON")],
            ["src/components/Button.ts"],
        )

        state = BrowserState(changes, selected=2)
        state.set_filter("src/")
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/pages/Home.ets", "src/components/Button.ts"],
        )
        self.assertEqual(state.selected, 0)

        state.selected = 99
        state.clamp_selection()
        self.assertEqual(state.selected, 1)

        state.set_filter("missing")
        self.assertEqual(state.visible_changes, [])
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.mode, "list")

    def test_browser_remaining_only_filters_seen_paths(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            seen_paths={"src/First.ts", "src/Third.ts"},
            remaining_only=True,
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )

    def test_review_workspace_source_filter_combines_with_path_and_remaining_filters(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 2, 1, source="unstaged"),
                FileChange("docs/Third.md", 1, 0, source="staged"),
            ],
            filter_text="src",
            source_filter="staged",
            seen_paths={"src/First.ts"},
            remaining_only=True,
        )

        self.assertEqual(workspace.visible_changes, [])
        workspace.remaining_only = False
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/First.ts"],
        )

    def test_review_workspace_marks_selected_file_seen(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        self.assertTrue(workspace.mark_selected_seen())
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

        self.assertTrue(workspace.unmark_selected_seen())
        self.assertEqual(workspace.seen_paths, set())

    def test_review_workspace_mark_seen_and_advance_uses_remaining_index(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            selected=0,
            remaining_only=True,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/First.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertTrue(result.had_next_before)
        self.assertEqual(workspace.seen_paths, {"src/First.ts"})
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )

    def test_review_workspace_mark_seen_and_advance_reports_last_file(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/Second.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertFalse(result.had_next_before)
        self.assertEqual(workspace.selected, 1)
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

    def test_browser_state_syncs_source_filter_with_workspace(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/First.ts"],
        )

        state.source_filter = "unstaged"
        state._sync_to_workspace()
        state._sync_from_workspace()

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )

    def test_review_workspace_persists_source_filter(self):
        args = argparse_namespace(
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            untracked=False,
        )
        workspace = ReviewWorkspace(
            [FileChange("src/First.ts", 1, 0, source="staged")],
            source_filter="staged",
        )

        data = workspace.state_data(args, mode=BrowserPage.CHANGED_FILES)
        restored = ReviewWorkspace([FileChange("src/First.ts", 1, 0, source="staged")])
        restored.restore_state(args, data)

        self.assertEqual(data["source_filter"], "staged")
        self.assertEqual(restored.source_filter, "staged")

    def test_review_workspace_scope_switch_clears_source_filter(self):
        args = argparse_namespace(
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        workspace = ReviewWorkspace(
            [FileChange("src/Old.ts", 1, 0, source="staged")],
            source_filter="staged",
        )

        workspace.switch_scope(
            args,
            ReviewScope(False, False, None, None, False),
            loader=lambda _args: [FileChange("src/New.ts", 1, 0, source="unstaged")],
        )

        self.assertEqual(workspace.source_filter, "")

    def test_switch_review_scope_resets_view_state_but_keeps_task_panel(self):
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
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, returncode=0)
        state = BrowserState(
            [FileChange("src/Old.ts", 1, 1)],
            task=build,
            selected=3,
            list_scroll=4,
            commit_scroll=2,
            file_scroll=9,
            page="file",
            filter_text="Old",
        )
        state.first_line_cache["src/Old.ts"] = 1
        state.file_line_cache["src/Old.ts"] = ["cached"]

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 2, 0)]):
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )

        self.assertTrue(args.staged)
        self.assertEqual(state.changes, [FileChange("src/New.ts", 2, 0)])
        self.assertIs(state.task, build)
        self.assertEqual(state.mode, "list")
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.list_scroll, 0)
        self.assertEqual(state.commit_scroll, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.filter_text, "")
        self.assertEqual(state.first_line_cache, {})
        self.assertEqual(state.file_line_cache, {})
        process.wait(timeout=1)

    def test_command_query_empty_or_question_mark_opens_command_list(self):
        self.assertEqual(_normalize_command_query(""), "commands")
        self.assertEqual(_normalize_command_query("?"), "commands")
        self.assertEqual(_normalize_command_query(" build "), "build")

    def test_command_list_lines_group_commands_by_purpose(self):
        lines = _browse_command_lines(TerminalStyle(False), max_lines=120)
        text = "\n".join(lines)

        self.assertIn("命令", text)
        self.assertIn("导航", text)
        self.assertIn("审查范围", text)
        self.assertIn("任务", text)
        self.assertIn("文件", text)
        self.assertIn("会话", text)
        self.assertIn("staged", text)
        self.assertIn("build", text)
        self.assertIn("done next", text)
        self.assertIn("note TEXT", text)
        self.assertIn("note change TEXT", text)
        self.assertIn("notes QUERY", text)
        self.assertIn("copy notes QUERY", text)
        self.assertIn("save notes", text)
        self.assertIn("copy prompt", text)
        self.assertIn("copy prompt file", text)
        self.assertIn("open hunk", text)
        self.assertIn("open line", text)
        self.assertIn("copy hunk", text)
        self.assertIn("copy line", text)
        self.assertIn("copy change", text)
        self.assertIn("find TEXT", text)
        self.assertIn("next match", text)
        self.assertIn("prev match", text)
        self.assertIn("next change", text)
        self.assertIn("prev change", text)
        self.assertIn("save diff", text)
        self.assertIn("next hunk", text)
        self.assertIn("prev hunk", text)
        self.assertIn("save prompt", text)
        self.assertIn("save prompt file", text)


    def test_browse_screen_only_measures_visible_list_rows(self):
        changes = [FileChange(f"src/File{index}.ts", 1, 0) for index in range(30)]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(changes)
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=1) as first_line:
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/File0.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertLess(first_line.call_count, len(changes))
        self.assertIn("showing rows", text)
        self.assertIn("File0.ts", text)
        self.assertNotIn("File29.ts", text)

    def test_browse_file_screen_scrolls_long_content(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        full_lines = ["File 1/1  src/Sample.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            top = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )
            state.file_scroll = 10
            lower = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        self.assertEqual(top[:2], ["File 1/1  src/Sample.ts", "line 1"])
        self.assertIn("showing 1-4/20", top[-1])
        self.assertIn("line 11", lower)
        self.assertIn("showing 11-14/20", lower[-1])

    def test_browse_file_screen_shows_review_queue_dock(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 2, 0, source="staged"),
            FileChange("src/Second.ts", 5, 1, source="unstaged"),
            FileChange("src/Third.ts", 1, 3, source="unstaged"),
        ]
        state = BrowserState(
            changes,
            page=BrowserPage.FILE_DETAIL,
            selected=1,
            seen_paths={"src/First.ts"},
            review_notes={"src/Second.ts": "check edge"},
        )
        full_lines = ["File 2/3  src/Second.ts"] + [
            f"line {index}" for index in range(1, 9)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                3,
                args,
                TerminalStyle(False),
                max_lines=14,
            )

        text = "\n".join(lines)
        self.assertIn("Changed files 2/3", text)
        self.assertIn("Progress: 1/3 seen", text)
        self.assertIn("  1 [x] src/First.ts", text)
        self.assertIn("> 2 [ ] src/Second.ts", text)
        self.assertIn("note", text)
        self.assertIn("unstaged", text)
        self.assertIn("+5 -1", text)

    def test_browse_file_screen_omits_review_queue_dock_when_short(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 1, 0),
            FileChange("src/Second.ts", 1, 0),
        ]
        state = BrowserState(changes, page=BrowserPage.FILE_DETAIL, selected=1)
        full_lines = ["File 2/2  src/Second.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                2,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        text = "\n".join(lines)
        self.assertNotIn("Changed files", text)
        self.assertIn("showing 1-4/20", lines[-1])

    def test_browse_file_lines_show_seen_or_todo_status(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        todo_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=False,
                        )
                        seen_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=True,
                        )

        self.assertIn("todo", todo_lines[0])
        self.assertIn("seen", seen_lines[0])

    def test_browse_lines_show_review_notes(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)
        review_notes = {"src/Sample.ts": "check lifecycle edge case"}

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        list_lines = _browse_list_lines(
                            [change],
                            args,
                            TerminalStyle(False),
                            selected=0,
                            review_notes=review_notes,
                        )
                        screen_lines = _browse_list_screen_lines(
                            BrowserState([change], review_notes=review_notes),
                            args,
                            TerminalStyle(False),
                            max_lines=8,
                        )
                        detail_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            review_note=review_notes["src/Sample.ts"],
                        )

        self.assertIn("note", "\n".join(list_lines))
        self.assertIn("note", "\n".join(screen_lines))
        self.assertIn("note: check lifecycle edge case", "\n".join(detail_lines))


    def test_browser_workspace_state_saves_under_git_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                selected=0,
                page="file",
                filter_text="Second",
            )
            args = argparse_namespace(
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)

            path = _browser_workspace_state_path(repo)
            self.assertEqual(path, repo / ".git" / "cr" / "browse-state.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertEqual(data["scope"]["staged"], True)
            self.assertEqual(data["scope"]["all_changes"], False)
            self.assertEqual(data["filter_text"], "Second")
            self.assertEqual(data["selected_path"], "src/Second.ts")
            self.assertEqual(data["selected_index"], 0)
            self.assertEqual(data["mode"], "file")
            self.assertNotIn("task_history", data)

    def test_browser_workspace_state_does_not_persist_task_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [FileChange("src/First.ts", 1, 0)],
                task_history=[
                    TaskRecord(
                        kind="build",
                        status="succeeded",
                        command=["./build.sh"],
                        returncode=0,
                    )
                ],
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)

            data = json.loads(
                _browser_workspace_state_path(repo).read_text(encoding="utf-8")
            )
            self.assertNotIn("task_history", data)

    def test_browser_workspace_state_saves_and_restores_progress_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                seen_paths={"src/First.ts"},
                remaining_only=True,
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)
            workspace_state = _load_browser_workspace_state(repo)
            restored = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )
            _restore_browser_workspace_state(restored, args, workspace_state)

            self.assertEqual(restored.seen_paths, {"src/First.ts"})
            self.assertTrue(restored.remaining_only)
            self.assertEqual(
                [change.path for change in restored.visible_changes],
                ["src/Second.ts"],
            )

    def test_browser_workspace_state_saves_and_restores_review_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                review_notes={"src/Second.ts": "check lifecycle edge case"},
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)
            workspace_state = _load_browser_workspace_state(repo)
            restored = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )
            _restore_browser_workspace_state(restored, args, workspace_state)

            self.assertEqual(
                restored.review_notes,
                {"src/Second.ts": "check lifecycle edge case"},
            )

    def test_browser_workspace_state_restores_scope_filter_and_selected_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_path = _browser_workspace_state_path(repo)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": True,
                            "all_changes": False,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "Second",
                        "selected_path": "src/Second.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )

            workspace_state = _load_browser_workspace_state(repo)
            self.assertIsNotNone(workspace_state)
            _restore_browser_workspace_state(state, args, workspace_state)

            self.assertTrue(args.staged)
            self.assertFalse(args.all_changes)
            self.assertEqual(state.filter_text, "Second")
            self.assertEqual(state.selected, 0)
            self.assertEqual(state.visible_changes[0].path, "src/Second.ts")
            self.assertEqual(state.mode, "file")

    def test_browser_workspace_state_falls_back_to_index_when_path_is_missing(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            paths=[],
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ]
        )
        workspace_state = {
            "version": 1,
            "scope": {
                "staged": False,
                "all_changes": False,
                "base": None,
                "ref_range": None,
                "untracked": False,
            },
            "filter_text": "",
            "selected_path": "src/Missing.ts",
            "selected_index": 9,
            "mode": "file",
        }

        _restore_browser_workspace_state(state, args, workspace_state)

        self.assertEqual(state.selected, 1)
        self.assertEqual(state.visible_changes[state.selected].path, "src/Second.ts")
        self.assertEqual(state.mode, "file")

    def test_cli_diff_outline_and_review_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            diff = self._cr(repo, "diff")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Changed file tree:", diff.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            outline = self._cr(repo, "outline", "Sample.ets")
            self.assertEqual(outline.returncode, 0, outline.stderr)
            self.assertIn("purpose: ArkTS page/component SamplePage", outline.stdout)
            self.assertIn("struct SamplePage", outline.stdout)
            self.assertIn("method build", outline.stdout)

            review = self._cr(repo, "review")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("Summary:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("focus", review.stdout)
            self.assertIn("Changed file tree:", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("modified: build", review.stdout)
            self.assertIn("method build *", review.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-    Text('hello')", review.stdout)
            self.assertIn("+    Text('hello world')", review.stdout)

            summary = self._cr(repo, "review", "--summary")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("Summary:", summary.stdout)
            self.assertIn("Changed file tree:", summary.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", summary.stdout)
            self.assertNotIn("\n  changes:", summary.stdout)
            self.assertNotIn("purpose:", summary.stdout)
            self.assertNotIn("outline:", summary.stdout)

            no_hunks = self._cr(repo, "review", "--no-hunks")
            self.assertEqual(no_hunks.returncode, 0, no_hunks.stderr)
            self.assertIn("Summary:", no_hunks.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", no_hunks.stdout)
            self.assertIn("modified: build", no_hunks.stdout)
            self.assertIn("outline:", no_hunks.stdout)
            self.assertNotIn("\n  changes:", no_hunks.stdout)
            self.assertNotIn("-    Text('hello')", no_hunks.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 1)
            self.assertEqual(data["summary"]["added"], 1)
            self.assertEqual(data["summary"]["deleted"], 1)
            self.assertEqual(data["files"][0]["path"], "Sample.ets")
            self.assertEqual(data["files"][0]["status"], "modified")
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertIn("ArkTS page/component SamplePage", data["files"][0]["purpose"])
            self.assertTrue(any("+    Text('hello world')" in line for line in data["files"][0]["hunks"]))
            self.assertNotIn("Review changes:", json_review.stdout)

            json_summary = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_summary.returncode, 0, json_summary.stderr)
            summary_data = json.loads(json_summary.stdout)
            self.assertEqual(summary_data["files"][0]["hunks"], [])

    def test_cli_defaults_to_interactive_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "pages" / "Sample.ets"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('old')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            session = self._cr_input(repo, "q\n")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Enter", session.stdout)
            self.assertIn("j/k", session.stdout)
            self.assertIn("Sample.ets", session.stdout)
            self.assertIn("cr:list>", session.stdout)

    def test_cli_defaults_to_browser_when_options_are_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "--context", "0", "--sort", "path")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Sample.ts", session.stdout)

    def test_cli_interactive_browser_opens_file_and_navigates(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\nn\nb\nr\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("File 1/2", session.stdout)
            self.assertIn("File 2/2", session.stdout)
            self.assertIn("-export const first = 'old'", session.stdout)
            self.assertIn("+export const first = 'new'", session.stdout)
            self.assertIn("Changed files", session.stdout)

    def test_cli_browser_shows_recent_commits_when_no_worktree_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'from commit'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change sample")

            sample.write_text("export const sample = 'staged only'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")

            session = self._cr_input(
                repo,
                "1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("change sample", session.stdout)
            self.assertIn("1 file, +1 -1", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'from commit'", session.stdout)

    def test_cli_browser_can_switch_from_worktree_to_recent_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\nw\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("Scope: recent commits", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("committed sample", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)
            self.assertIn("-export const sample = 'committed'", session.stdout)
            self.assertIn("+export const sample = 'working tree'", session.stdout)

    def test_cli_browser_filters_recent_commits_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'docs'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "docs update")

            sample.write_text("export const sample = 'login'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "login flow")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n/login\n1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: login (1/", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("login flow", session.stdout)
            self.assertIn("+export const sample = 'login'", session.stdout)

    def test_cli_browser_can_open_scope_home_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(repo, "scopes\nq\n", "browse")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: scope home", session.stdout)
            self.assertIn("Review scopes", session.stdout)
            self.assertIn("Worktree", session.stdout)
            self.assertIn("Staged", session.stdout)
            self.assertIn("cr:scopes>", session.stdout)

    def test_cli_browser_back_from_commit_file_returns_to_commit_file_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            alpha = repo / "src" / "Alpha.ts"
            beta = repo / "src" / "Beta.ts"
            alpha.parent.mkdir(parents=True)
            alpha.write_text("export const alpha = 'old'\n", encoding="utf-8")
            beta.write_text("export const beta = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            alpha.write_text("export const alpha = 'committed'\n", encoding="utf-8")
            beta.write_text("export const beta = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change both files")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\n2\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("+export const alpha = 'committed'", session.stdout)
            self.assertIn("+export const beta = 'committed'", session.stdout)

    def test_cli_browser_can_switch_review_scopes_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'staged'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "staged\n1\nb\nall\n1\nb\nworktree\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertIn("Scope: all local changes", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: worktree", session.stdout)
            self.assertIn("-export const sample = 'staged'", session.stdout)

    def test_cli_browser_can_switch_to_base_and_range_scopes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "base HEAD~1\n1\nb\nrange HEAD~1..HEAD\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: base HEAD~1", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: range HEAD~1..HEAD", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)

    def test_cli_browser_command_list_is_discoverable_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "commands\nb\ncmds\nb\nhelp commands\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertGreaterEqual(session.stdout.count("命令"), 3)
            self.assertIn("审查范围", session.stdout)
            self.assertIn("任务", session.stdout)
            self.assertIn("cr:commands>", session.stdout)
            self.assertIn("Changed files", session.stdout)

    def test_cli_interactive_browser_filters_files_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "filter First\nc\n/Second\nr\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: First (1/2 matches, c to clear)", session.stdout)
            self.assertIn("Filter: Second (1/2 matches, c to clear)", session.stdout)
            self.assertIn("File 1/1", session.stdout)
            self.assertIn("Second.ts", session.stdout)
            self.assertIn("-export const second = 'old'", session.stdout)
            self.assertIn("+export const second = 'new'", session.stdout)

    def test_cli_browser_restores_saved_workspace_filter_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            first_session = self._cr_input(
                repo,
                "filter Second\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(first_session.returncode, 0, first_session.stderr)
            self.assertTrue((repo / ".git" / "cr" / "browse-state.json").exists())

            second_session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(second_session.returncode, 0, second_session.stderr)
            self.assertIn("File 1/1", second_session.stdout)
            self.assertIn("Second.ts", second_session.stdout)
            self.assertNotIn("First.ts", second_session.stdout)

    def test_cli_browser_explicit_scope_ignores_saved_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'staged'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": True,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "",
                        "selected_path": "src/Sample.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "1\nq\n",
                "browse",
                "--staged",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertNotIn("+export const sample = 'worktree'", session.stdout)

    def test_cli_browser_ignores_malformed_saved_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            sample.write_text("export const sample = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not json", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "browse", "--context", "0")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)

    def test_cli_browser_pathspec_ignores_saved_workspace_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": False,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "Second",
                        "selected_path": "src/Second.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--context",
                "0",
                "src/First.ts",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertNotIn("Second.ts", session.stdout)
            self.assertNotIn("Filter: Second", session.stdout)

    def test_cli_browser_can_mark_seen_and_show_remaining_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen", session.stdout)
            self.assertIn("remaining only", session.stdout)
            self.assertIn("[x]", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("[ ]", session.stdout)
            self.assertIn("Second.ts", session.stdout)

    def test_cli_browser_can_unmark_seen_and_return_to_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nallfiles\ntodo\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen remaining only", session.stdout)
            self.assertIn("Progress: 0/2 seen", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("Second.ts", session.stdout)

    def test_cli_interactive_browser_can_open_current_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\no\nq\n",
                "browse",
                "--context",
                "0",
                "--open-cmd",
                "true",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Opened src/Sample.ts:1", session.stdout)

    def test_cli_interactive_browser_can_run_build_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            build_script = repo / "build.sh"
            build_script.write_text(
                "#!/bin/sh\npwd > build.out\n",
                encoding="utf-8",
            )
            os.chmod(build_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            subdir = repo / "src"
            session = self._cr_input(
                subdir,
                "build\nq\n",
                "browse",
                "--build-cmd",
                "./build.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Build: ./build.sh", session.stdout)
            self.assertIn("Build succeeded.", session.stdout)
            self.assertEqual(
                Path((repo / "build.out").read_text(encoding="utf-8").strip()).resolve(),
                repo.resolve(),
            )

    def test_cli_interactive_browser_can_run_test_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            test_script = repo / "test.sh"
            test_script.write_text(
                "#!/bin/sh\necho test ran > test.out\n",
                encoding="utf-8",
            )
            os.chmod(test_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            session = self._cr_input(
                repo,
                "test\nq\n",
                "browse",
                "--test-cmd",
                "./test.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Test: ./test.sh", session.stdout)
            self.assertIn("Test succeeded.", session.stdout)
            self.assertEqual(
                (repo / "test.out").read_text(encoding="utf-8").strip(),
                "test ran",
            )

    def test_cli_can_emit_clickable_file_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const value = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const value = 'new'\n", encoding="utf-8")

            default_review = self._cr(repo, "review", "--summary")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033]8;;", default_review.stdout)

            linked_review = self._cr(
                repo,
                "review",
                "--summary",
                "--links",
                "always",
            )
            self.assertEqual(linked_review.returncode, 0, linked_review.stderr)
            self.assertIn("\033]8;;file://", linked_review.stdout)
            self.assertIn("#L1", linked_review.stdout)
            self.assertIn("\033]8;;\033\\", linked_review.stdout)

            vscode_browse = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--links",
                "always",
                "--link-scheme",
                "vscode",
            )
            self.assertEqual(vscode_browse.returncode, 0, vscode_browse.stderr)
            self.assertNotIn("\033]8;;", vscode_browse.stdout)
            self.assertIn("Sample.ts", vscode_browse.stdout)

    def test_cli_review_accepts_configurable_hunk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )

            no_context = self._cr(repo, "review", "--json", "--context", "0")
            self.assertEqual(no_context.returncode, 0, no_context.stderr)
            no_context_hunks = "\n".join(json.loads(no_context.stdout)["files"][0]["hunks"])
            self.assertIn("-    Text('hello')", no_context_hunks)
            self.assertIn("+    Text('hello world')", no_context_hunks)
            self.assertNotIn("  build() {", no_context_hunks)

            wider_context = self._cr(repo, "review", "--json", "--context", "3")
            self.assertEqual(wider_context.returncode, 0, wider_context.stderr)
            wider_hunks = "\n".join(json.loads(wider_context.stdout)["files"][0]["hunks"])
            self.assertIn("  build() {", wider_hunks)

            bad_context = self._cr(repo, "review", "--context", "-1")
            self.assertEqual(bad_context.returncode, 2)
            self.assertIn("context must be >= 0", bad_context.stderr)

    def test_cli_compacts_deep_paths_and_can_color_diff_hunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "a" / "b" / "c" / "d" / "e" / "f" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "export function sample(): string {\n  return 'old'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "export function sample(): string {\n  return 'new'\n}\n",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--color", "always")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn(".../d/e/f", review.stdout)
            self.assertIn(".../d/e/f/Sample.ts", review.stdout)
            self.assertNotIn("a/b/c/d/e/f/Sample.ts", review.stdout)
            self.assertIn("\033[32m", review.stdout)
            self.assertIn("\033[31m", review.stdout)

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033[", default_review.stdout)

    def test_cli_review_compares_against_named_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from head')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "head")

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertIn("No working tree changes.", default_review.stdout)

            review = self._cr(repo, "review", "--base", "HEAD~1", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("Sample.ets:3", review.stdout)

            diff = self._cr(repo, "diff", "--base", "HEAD~1", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            json_review = self._cr(repo, "review", "--base", "HEAD~1", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 1, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

    def test_cli_review_compares_explicit_ref_range_without_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")
            self._run(repo, "git", "branch", "-M", "main")
            self._run(repo, "git", "branch", "feature")
            self._run(repo, "git", "checkout", "feature")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from feature')
  }

  helper() {
    return 'feature only'
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "feature")
            self._run(repo, "git", "checkout", "main")

            review = self._cr(repo, "review", "--range", "main..feature", "--no-hunks")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +5 -1", review.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", review.stdout)
            self.assertIn(
                "purpose: ArkTS page/component SamplePage with methods build, helper",
                review.stdout,
            )
            self.assertIn("method helper", review.stdout)

            diff = self._cr(repo, "diff", "--range", "main..feature", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", diff.stdout)

            json_review = self._cr(repo, "review", "--range", "main..feature", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build", "helper"])
            self.assertIn("build, helper", data["files"][0]["purpose"])

    def test_cli_review_shows_first_changed_line_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("anchor", review.stdout)
            self.assertIn("Sample.ets:7", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build line 7", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["first_changed_line"], 7)
            self.assertEqual(data["files"][0]["anchor"], "Sample.ets:7")

    def test_cli_includes_untracked_files_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tracked = repo / "README.md"
            new_page = repo / "src" / "pages" / "NewPage.ets"
            tracked.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            new_page.parent.mkdir(parents=True)
            new_page.write_text(
                "struct NewPage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            default_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(default_diff.returncode, 0, default_diff.stderr)
            self.assertIn("No working tree changes.", default_diff.stdout)
            self.assertNotIn("NewPage.ets", default_diff.stdout)

            diff = self._cr(repo, "diff", "--untracked", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("NewPage.ets +5 -0 untracked", diff.stdout)
            self.assertIn("modified: build", diff.stdout)
            self.assertNotIn("No working tree changes.", diff.stdout)

            review = self._cr(repo, "review", "--untracked", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/NewPage.ets", review.stdout)
            self.assertIn("+5 -0 untracked", review.stdout)
            self.assertIn("src/pages/NewPage.ets:1", review.stdout)
            self.assertIn("+struct NewPage", review.stdout)
            self.assertIn("purpose: ArkTS page/component NewPage", review.stdout)
            self.assertIn("method build *", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 0})
            self.assertEqual(data["files"][0]["status"], "untracked")
            self.assertEqual(data["files"][0]["first_changed_line"], 1)
            self.assertEqual(data["files"][0]["anchor"], "src/pages/NewPage.ets:1")
            self.assertTrue(any("+struct NewPage" in line for line in data["files"][0]["hunks"]))

            staged = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertIn("No staged changes.", staged.stdout)
            self.assertNotIn("NewPage.ets", staged.stdout)

            all_changes = self._cr(repo, "review", "--all", "--untracked", "--code")
            self.assertEqual(all_changes.returncode, 0, all_changes.stderr)
            self.assertIn("src/pages/NewPage.ets", all_changes.stdout)

    def test_git_stage_and_unstage_path_update_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "init")
            sample.write_text("new\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                git.stage_path("Sample.ts")
                staged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(staged.returncode, 0, staged.stderr)
                self.assertIn("Sample.ts", staged.stdout)
                git.unstage_path("Sample.ts")
                unstaged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
                self.assertNotIn("Sample.ts", unstaged.stdout)
            finally:
                os.chdir(previous_cwd)

    def test_git_all_changes_marks_mixed_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("one\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("two\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            sample.write_text("three\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(all_changes=True)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].path, "Sample.ts")
        self.assertEqual(changes[0].source, "mixed")

    def test_git_local_scopes_mark_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged_file = repo / "staged.ts"
            unstaged_file = repo / "unstaged.ts"
            staged_file.write_text("old staged\n", encoding="utf-8")
            unstaged_file.write_text("old unstaged\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            staged_file.write_text("new staged\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged_file.write_text("new unstaged\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                staged_changes = git.changed_files(staged=True)
                unstaged_changes = git.changed_files()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(
            {change.path: change.source for change in staged_changes},
            {"staged.ts": "staged"},
        )
        self.assertEqual(
            {change.path: change.source for change in unstaged_changes},
            {"unstaged.ts": "unstaged"},
        )

    def test_git_recent_commits_include_change_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "first.ts"
            second = repo / "second.ts"
            first.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("new\n", encoding="utf-8")
            second.write_text("one\ntwo\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change summary")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                commits = git.recent_commits(limit=1)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].subject, "change summary")
        self.assertEqual(commits[0].files, 2)
        self.assertEqual(commits[0].added, 3)
        self.assertEqual(commits[0].deleted, 1)

    def test_git_comparison_scopes_do_not_mark_local_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "base")
            sample.write_text("new\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "head")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(base="HEAD~1")
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].source, "")

    def test_cli_omits_untracked_binary_and_large_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            binary = repo / "asset.bin"
            large = repo / "large.txt"
            readme.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            binary.write_bytes(b"\x00\xff\x00\xff")
            large.write_text("x" * 210_000, encoding="utf-8")

            review = self._cr(repo, "review", "--untracked")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("asset.bin +? -0 untracked", review.stdout)
            self.assertIn("large.txt +? -0 untracked", review.stdout)
            self.assertIn("asset.bin: binary or non-UTF-8 file; content omitted", review.stdout)
            self.assertIn("large.txt: file is too large for inline diff", review.stdout)
            self.assertNotIn("+" + ("x" * 200), review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            files = {item["path"]: item for item in data["files"]}
            self.assertIsNone(files["asset.bin"]["added"])
            self.assertIsNone(files["large.txt"]["added"])
            self.assertIn("content omitted", "\n".join(files["asset.bin"]["hunks"]))
            self.assertIn("too large for inline diff", "\n".join(files["large.txt"]["hunks"]))

    def test_cli_flags_lockfile_config_and_generated_risks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            lockfile = repo / "package-lock.json"
            config = repo / "tsconfig.json"
            generated = repo / "src" / "generated" / "client.ts"
            generated.parent.mkdir(parents=True)
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v1'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {"strict": true}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v2'\n}\n", encoding="utf-8")

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("risk", review.stdout)
            self.assertIn("package-lock.json", review.stdout)
            self.assertIn("lockfile", review.stdout)
            self.assertIn("tsconfig.json", review.stdout)
            self.assertIn("config", review.stdout)
            self.assertIn("src/generated/client.ts", review.stdout)
            self.assertIn("generated", review.stdout)
            self.assertIn("risk: lockfile", review.stdout)
            self.assertIn("risk: config", review.stdout)
            self.assertIn("risk: generated", review.stdout)

            full_review = self._cr(repo, "review", "package-lock.json")
            self.assertEqual(full_review.returncode, 0, full_review.stderr)
            self.assertIn("  risk: lockfile", full_review.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            risks = {item["path"]: item["risk_hints"] for item in data["files"]}
            self.assertEqual(risks["package-lock.json"], ["lockfile"])
            self.assertEqual(risks["tsconfig.json"], ["config"])
            self.assertEqual(risks["src/generated/client.ts"], ["generated"])

    def test_cli_review_sorts_large_reviews_by_risk_or_churn(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            risk_sorted = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(risk_sorted.returncode, 0, risk_sorted.stderr)
            self.assertLess(
                risk_sorted.stdout.index("package-lock.json"),
                risk_sorted.stdout.index("README.md"),
            )

            churn_sorted = self._cr(repo, "review", "--summary", "--sort", "churn")
            self.assertEqual(churn_sorted.returncode, 0, churn_sorted.stderr)
            self.assertLess(
                churn_sorted.stdout.index("src/app.ts"),
                churn_sorted.stdout.index("package-lock.json"),
            )

            json_review = self._cr(repo, "review", "--json", "--summary", "--sort", "risk")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["path"], "package-lock.json")

    def test_cli_review_picks_one_file_by_summary_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("idx", summary.stdout)
            self.assertLess(
                summary.stdout.index("1  package-lock.json"),
                summary.stdout.index("2  src/app.ts"),
            )

            picked = self._cr(repo, "review", "--sort", "risk", "--pick", "2")
            self.assertEqual(picked.returncode, 0, picked.stderr)
            self.assertIn("1 files", picked.stdout)
            self.assertIn("src/app.ts", picked.stdout)
            self.assertIn("+  const value = 'v2'", picked.stdout)
            self.assertNotIn("package-lock.json", picked.stdout)
            self.assertNotIn("README.md", picked.stdout)

            bad_pick = self._cr(repo, "review", "--pick", "9")
            self.assertEqual(bad_pick.returncode, 2)
            self.assertIn("--pick must be between 1 and 3", bad_pick.stderr)

    def test_cli_review_tracks_seen_files_and_filters_remaining(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v2'\n}\n",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--seen", "README.md")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("seen", summary.stdout)
            self.assertIn("README.md", summary.stdout)
            self.assertIn("yes", summary.stdout)
            self.assertIn("src/app.ts", summary.stdout)
            self.assertIn("no", summary.stdout)

            remaining = self._cr(
                repo,
                "review",
                "--summary",
                "--seen",
                "README.md",
                "--remaining",
            )
            self.assertEqual(remaining.returncode, 0, remaining.stderr)
            self.assertIn("src/app.ts", remaining.stdout)
            self.assertNotIn("README.md", remaining.stdout)

            no_remaining = self._cr(
                repo,
                "review",
                "--seen",
                "README.md,src/app.ts",
                "--remaining",
            )
            self.assertEqual(no_remaining.returncode, 0, no_remaining.stderr)
            self.assertIn("No remaining changes.", no_remaining.stdout)

            json_review = self._cr(repo, "review", "--json", "--seen", "README.md")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            seen_by_path = {item["path"]: item["seen"] for item in data["files"]}
            self.assertTrue(seen_by_path["README.md"])
            self.assertFalse(seen_by_path["src/app.ts"])

            prompt = self._cr(repo, "review", "--prompt", "--seen", "README.md")
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("state: seen", prompt.stdout)

    def test_cli_review_emits_prompt_ready_markdown_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            lockfile = repo / "package-lock.json"
            page.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello prompt')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")

            prompt = self._cr(
                repo,
                "review",
                "--prompt",
                "--sort",
                "risk",
                "--context",
                "0",
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("# Code Review Handoff", prompt.stdout)
            self.assertIn("Please review these changes.", prompt.stdout)
            self.assertIn("## Summary", prompt.stdout)
            self.assertIn("- Files: 2", prompt.stdout)
            self.assertIn("## Files", prompt.stdout)
            self.assertLess(
                prompt.stdout.index("package-lock.json"),
                prompt.stdout.index("src/pages/Sample.ets"),
            )
            self.assertIn("risk: lockfile", prompt.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", prompt.stdout)
            self.assertIn("focus: build", prompt.stdout)
            self.assertIn("```diff", prompt.stdout)
            self.assertIn("+    Text('hello prompt')", prompt.stdout)
            self.assertNotIn("Review changes:", prompt.stdout)
            self.assertNotIn('"summary"', prompt.stdout)

    def test_cli_filters_to_code_files_and_path_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            helper = repo / "src" / "utils" / "helper.ts"
            readme = repo / "README.md"
            page.parent.mkdir(parents=True)
            helper.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello page')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'b'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello docs\n", encoding="utf-8")

            review = self._cr(repo, "review", "--code", "src/pages")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/Sample.ets +1 -1", review.stdout)
            self.assertNotIn("src/utils/helper.ts", review.stdout)
            self.assertNotIn("README.md", review.stdout)

            diff = self._cr(repo, "diff", "--code", "src/pages")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("src/pages", diff.stdout)
            self.assertNotIn("src/utils", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

            code_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(code_diff.returncode, 0, code_diff.stderr)
            self.assertIn("src/pages/Sample.ets", code_diff.stdout)
            self.assertIn("src/utils/helper.ts", code_diff.stdout)
            self.assertNotIn("README.md", code_diff.stdout)

    def test_code_filter_does_not_show_doc_only_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("No working tree changes.", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

    def test_cli_marks_deleted_code_files_without_fake_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "src" / "utils" / "helper.ts"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("helper.ts +0 -3 deleted", diff.stdout)
            self.assertNotIn("modified: unknown", diff.stdout)

            review = self._cr(repo, "review", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/utils/helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_can_review_staged_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello staged')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")

            unstaged = self._cr(repo, "diff")
            self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
            self.assertIn("No working tree changes.", unstaged.stdout)

            staged_diff = self._cr(repo, "diff", "--staged")
            self.assertEqual(staged_diff.returncode, 0, staged_diff.stderr)
            self.assertIn("Sample.ets +1 -1 modified: build", staged_diff.stdout)

            staged_review = self._cr(repo, "review", "--staged")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn("Sample.ets +1 -1", staged_review.stdout)
            self.assertIn("+    Text('hello staged')", staged_review.stdout)
            self.assertIn("modified: build", staged_review.stdout)

    def test_cli_can_review_staged_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "helper.ts"
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "helper.ts")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()
            self._run(repo, "git", "add", "helper.ts")

            review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_notes_when_the_other_git_side_has_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'b'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'b'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Note: staged changes also exist; use --staged to review them.", diff.stdout)
            self.assertIn("unstaged.ts", diff.stdout)
            self.assertNotIn("  └─ staged.ts +1 -1", diff.stdout)

            staged_review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn(
                "Note: unstaged changes also exist; omit --staged to review them.",
                staged_review.stdout,
            )
            self.assertIn("staged.ts", staged_review.stdout)
            self.assertNotIn("  └─ unstaged.ts +1 -1", staged_review.stdout)

            json_review = self._cr(repo, "review", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["other_changes"], {"staged": 1, "unstaged": 0})

    def test_cli_can_review_all_staged_and_unstaged_changes_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'staged'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'unstaged'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--all", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", diff.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", diff.stdout)
            self.assertNotIn("also exist", diff.stdout)

            review = self._cr(repo, "review", "--all", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", review.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", review.stdout)
            self.assertIn("+  return 'staged'", review.stdout)
            self.assertIn("+  return 'unstaged'", review.stdout)
            self.assertNotIn("also exist", review.stdout)

            json_review = self._cr(repo, "review", "--all", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 2)
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

            bad_scope = self._cr(repo, "review", "--all", "--staged")
            self.assertEqual(bad_scope.returncode, 2)
            self.assertIn("not allowed with argument", bad_scope.stderr)

    def _cr(self, cwd, *args):
        return self._cr_input(cwd, None, *args)

    def _cr_input(self, cwd, input_text, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "cr", *args],
            cwd=cwd,
            text=True,
            input=input_text,
            capture_output=True,
            env=env,
            check=False,
        )

    def _run(self, cwd, *args):
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
