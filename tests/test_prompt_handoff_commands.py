import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.review.prompt import render_prompt_handoff
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class PromptHandoffCommandTests(unittest.TestCase):
    def test_prompt_handoff_renders_review_notes_in_summary_and_detail(self):
        prompt = render_prompt_handoff(
            {
                "summary": {"files": 1, "added": 2, "deleted": 1},
                "other_changes": {"staged": 0, "unstaged": 0},
                "files": [
                    {
                        "path": "src/Sample.ts",
                        "summary": "+2 -1",
                        "status": "modified",
                        "anchor": "src/Sample.ts:3",
                        "risk_hints": [],
                        "seen": False,
                        "purpose": None,
                        "modified_symbols": [],
                        "review_note": "check lifecycle edge case",
                        "hunks": ["@@ -1 +1 @@", "-old", "+new"],
                    }
                ],
            }
        )

        self.assertEqual(prompt.count("review note: check lifecycle edge case"), 2)
        self.assertIn("   - review note: check lifecycle edge case", prompt)
        self.assertIn("- review note: check lifecycle edge case", prompt)

    def test_browser_command_executor_copies_visible_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool {text}",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=3,
            paths=[],
            code=False,
            untracked=True,
        )
        src_change = FileChange("src/Sample.ts", 2, 1)
        docs_change = FileChange("docs/Guide.md", 1, 0)
        state = BrowserState(
            [src_change, docs_change],
            selected=0,
            page=BrowserPage.FILE_DETAIL,
            filter_text="src",
            seen_paths={"src/Sample.ts"},
            review_notes={
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Sample.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Sample.ts",
            ) as render_prompt:
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 0},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.filter_text, "src")
        self.assertEqual(
            state.review_notes,
            {
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        self.assertIsNone(state.task)
        build_data.assert_called_once_with(
            [src_change],
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 0},
            context=3,
            seen_paths={"src/Sample.ts"},
            review_notes={"src/Sample.ts": "check lifecycle"},
        )
        render_prompt.assert_called_once()
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Sample.ts",
            "copy-tool {text}",
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())

    def test_browser_command_executor_saves_visible_scope_prompt_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=3,
                paths=[],
                code=False,
                untracked=True,
            )
            src_change = FileChange("src/Sample.ts", 2, 1)
            docs_change = FileChange("docs/Guide.md", 1, 0)
            state = BrowserState(
                [src_change, docs_change],
                selected=0,
                page=BrowserPage.FILE_DETAIL,
                filter_text="src",
                seen_paths={"src/Sample.ts"},
                review_notes={
                    "src/Sample.ts": "check lifecycle",
                    "docs/Guide.md": "outside filtered handoff",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Sample.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Sample.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                                with redirect_stdout(output):
                                    result = executor.execute(
                                        parse_browser_command("save prompt")
                                    )

            target = repo / ".cr" / "handoff" / "review-prompt.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Code Review Handoff\n\nsrc/Sample.ts")
            self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
            self.assertEqual(state.selected, 0)
            self.assertEqual(state.filter_text, "src")
            self.assertIsNone(state.task)
            build_data.assert_called_once_with(
                [src_change],
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 0},
                context=3,
                seen_paths={"src/Sample.ts"},
                review_notes={"src/Sample.ts": "check lifecycle"},
            )
            copy.assert_not_called()
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
                output.getvalue(),
            )

    def test_browser_command_executor_copies_selected_file_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=False,
        )
        first_change = FileChange("src/First.ts", 2, 0)
        second_change = FileChange("src/Second.ts", 1, 1)
        state = BrowserState(
            [first_change, second_change],
            selected=1,
            page=BrowserPage.CHANGED_FILES,
            review_notes={
                "src/First.ts": "not selected",
                "src/Second.ts": "selected note",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Second.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Second.ts",
            ):
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 3},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt file")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        build_data.assert_called_once_with(
            [second_change],
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 3},
            context=2,
            seen_paths=set(),
            review_notes={"src/Second.ts": "selected note"},
        )
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Second.ts",
            None,
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())

    def test_browser_command_executor_saves_selected_file_prompt_explicit_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=False,
            )
            first_change = FileChange("src/First.ts", 2, 0)
            second_change = FileChange("src/Second.ts", 1, 1)
            state = BrowserState(
                [first_change, second_change],
                selected=1,
                page=BrowserPage.CHANGED_FILES,
                review_notes={
                    "src/First.ts": "not selected",
                    "src/Second.ts": "selected note",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Second.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 3},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command(
                                        "save prompt file tmp/second.md"
                                    )
                                )

            target = repo / "tmp" / "second.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
            self.assertEqual(state.selected, 1)
            build_data.assert_called_once_with(
                [second_change],
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 3},
                context=2,
                seen_paths=set(),
                review_notes={"src/Second.ts": "selected note"},
            )
            self.assertIn(
                "Saved prompt for 1 file to tmp/second.md",
                output.getvalue(),
            )

    def test_browser_command_executor_saves_selected_file_prompt_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState(
                [FileChange("src/First.ts", 2, 0), FileChange("src/Second.ts", 1, 1)],
                selected=1,
                review_notes={"src/Second.ts": "selected note"},
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Second.ts"}],
                    },
                ):
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command("save prompt file")
                                )

            target = repo / ".cr" / "handoff" / "review-prompt-file.md"
            self.assertTrue(result.handled)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt-file.md",
                output.getvalue(),
            )

    def test_browser_command_executor_does_not_copy_empty_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed files to copy prompt.", output.getvalue())

    def test_browser_command_executor_does_not_copy_missing_file_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt file"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed file to copy prompt.", output.getvalue())

    def test_browser_command_executor_does_not_save_empty_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.build_review_data") as build_data:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("save prompt"))

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            build_data.assert_not_called()
            self.assertFalse((repo / ".cr" / "handoff" / "review-prompt.md").exists())
            self.assertIn("No changed files to save prompt.", output.getvalue())

    def test_browser_command_executor_surfaces_prompt_save_failure(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            blocker = repo / "blocker"
            blocker.write_text("not a directory", encoding="utf-8")
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=True,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("save prompt blocker/review.md")
                            )

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertIn(
                "Could not save prompt to blocker/review.md",
                output.getvalue(),
            )

    def test_browser_command_executor_surfaces_prompt_copy_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool",
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
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
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value="Copy failed using CLI command: copy-tool",
                ):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Copy failed using CLI command: copy-tool", output.getvalue())

    def test_browser_command_executor_copies_prompt_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        frame = BrowserFrame()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch("cr.ui.browser.file_actions.copy_text", return_value=None):
                    result = executor.execute(
                        parse_browser_command("copy prompt", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn("Copied prompt for 1 file", state.status_message)

    def test_browser_command_executor_saves_prompt_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            frame = BrowserFrame()
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                frame,
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            result = executor.execute(
                                parse_browser_command("save prompt", raw_keys=True)
                            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn(
            "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
            state.status_message,
        )


if __name__ == "__main__":
    unittest.main()
