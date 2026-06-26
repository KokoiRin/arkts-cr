import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
    _draw_browse_screen,
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


class FileDetailCommandTests(unittest.TestCase):
    def test_browser_command_executor_marks_done_and_opens_next_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=8,
            review_notes={"src/First.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("seen next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertEqual(state.review_notes["src/First.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_jumps_to_next_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1 +1 @@",
            "  +first",
            "  context",
            "  @@ -20 +21 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(
                    parse_browser_command("next hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 1)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to hunk 1/2.", state.status_message)

    def test_browser_command_executor_jumps_to_previous_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=5,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +1 @@",
            "  +first",
            "  context",
            "  @@ -20 +21 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(parse_browser_command("[", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.file_scroll, 3)
        self.assertIn("Moved to hunk 2/2.", state.status_message)

    def test_browser_command_executor_jumps_between_changed_rows_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1,5 +1,5 @@",
            "     1    1 | context",
            "       \033[32m2 | +added\033[0m",
            "    3      | -deleted",
            "     4    3 | context",
            "          4 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            next_result = executor.execute(
                parse_browser_command("next change", raw_keys=True)
            )
            previous_result = executor.execute(
                parse_browser_command("prev change", raw_keys=True)
            )

        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertTrue(previous_result.handled)
        self.assertTrue(previous_result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 5)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to change 3/3.", state.status_message)

    def test_browser_command_executor_reports_changed_row_navigation_outside_file_detail(self):
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

        result = executor.execute(parse_browser_command("next change", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to jump changes.", state.status_message)

    def test_browser_command_executor_reports_changed_row_navigation_without_changed_rows(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +1 @@",
            "     1    1 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("next change", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No changed rows in current file.", state.status_message)

    def test_browser_command_executor_opens_current_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=3,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  context",
            "  @@ -20,2 +31,3 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/repo/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(
                        parse_browser_command("open hunk", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            31,
            "editor {fileline}",
        )
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Opened hunk src/Sample.ts:31", state.status_message)

    def test_browser_command_executor_reports_open_hunk_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd=None)
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.open_path") as open_path:
            result = executor.execute(parse_browser_command("open hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to open hunk.", state.status_message)

    def test_browser_command_executor_opens_current_line_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/repo/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(
                        parse_browser_command("open line", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            32,
            "editor {fileline}",
        )
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Opened line src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_copies_current_line_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy line", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with("src/Sample.ts:32", "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied line src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_line_action_outside_file_detail(self):
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

        result = executor.execute(parse_browser_command("open line", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to open line.", state.status_message)

    def test_browser_command_executor_reports_line_action_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy line", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_views_current_file_detail_source_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 32)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)

    def test_browser_command_executor_views_current_file_detail_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "  other() {",
                        "    return 'nope'",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command("view source symbol", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 4)
        self.assertEqual(state.source_selection_start, 2)
        self.assertEqual(state.source_selection_end, 6)
        self.assertIn(
            "Selected source symbol class Sample > method render src/Sample.ts:2-6.",
            state.status_message,
        )

    def test_browser_command_executor_reports_view_source_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_reports_view_source_symbol_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command("view source symbol", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_views_source_symbol_line_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text("const value = 1\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -1,1 +1,1 @@",
                "          1 | +const value = 1",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command("view source symbol", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 1)
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_view_source_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to view source.", state.status_message)

    def test_browser_command_executor_copies_file_detail_source_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text",
                        return_value=None,
                    ) as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy source", raw_keys=True)
                        )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Sample.ts:4", copied)
        self.assertIn("Symbol: class Sample > method render", copied)
        self.assertIn("> 4      const title = 'new'", copied)
        self.assertNotIn("class Sample {", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Copied source context src/Sample.ts:4.", state.status_message)

    def test_browser_command_executor_reports_file_detail_copy_source_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy source", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_does_not_use_selected_problem_for_file_detail_context(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            other = repo / "src" / "Other.ts"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            other.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0), FileChange("src/Other.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ts:2:1 error TS9: other bad"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/2  src/Sample.ts",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.build_review_data",
                        return_value={"files": [{"path": "src/Sample.ts"}]},
                    ):
                        with patch(
                            "cr.ui.browser.render_file_diff_snippet",
                            return_value="# File Diff: src/Sample.ts",
                        ):
                            with patch(
                                "cr.ui.browser.file_actions.copy_text",
                                return_value=None,
                            ) as copy_text:
                                result = executor.execute(
                                    parse_browser_command(
                                        "copy problem context",
                                        raw_keys=True,
                                    )
                                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("# Problem Context: src/Sample.ts:4", copied)
        self.assertIn("## Source", copied)
        self.assertIn("## Diff", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertNotIn("src/Other.ts", copied)
        self.assertNotIn("other bad", copied)
        self.assertIn("# File Diff: src/Sample.ts", copied)

    def test_browser_command_executor_copies_file_detail_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "  other() {",
                        "    return 'nope'",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text",
                        return_value=None,
                    ) as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy source symbol", raw_keys=True)
                        )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Sample.ts:2-6", copied)
        self.assertIn("Symbol: class Sample > method render", copied)
        self.assertIn("const title = 'new'", copied)
        self.assertNotIn("other() {", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("Copied source symbol src/Sample.ts:2-6.", state.status_message)

    def test_browser_command_executor_reports_file_detail_copy_symbol_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy source symbol", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_copies_current_change_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy change", raw_keys=True)
                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("# Changed Row: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:32", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied change for src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_copy_change_without_changed_row(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy change", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No current changed row in File Detail.", state.status_message)

    def test_browser_command_executor_reports_copy_change_outside_file_detail(self):
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

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(
                parse_browser_command("copy change", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to copy change.", state.status_message)

    def test_browser_command_executor_notes_current_change_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "file note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command(
                    "note change check lifecycle",
                    raw_keys=True,
                )
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIsNotNone(state.task)
        self.assertEqual(
            state.review_notes,
            {"src/Sample.ts": "file note | line 32: check lifecycle"},
        )
        self.assertIn("Noted change src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_change_note_without_changed_row(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
            review_notes={"src/Sample.ts": "file note"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command("note change check lifecycle", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.review_notes, {"src/Sample.ts": "file note"})
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No current changed row in File Detail.", state.status_message)

    def test_browser_command_executor_reports_change_note_outside_file_detail(self):
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

        result = executor.execute(
            parse_browser_command("note change check lifecycle", raw_keys=True)
        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.review_notes, {})
        self.assertIn("Open a file detail to note change.", state.status_message)

    def test_browser_command_executor_copies_current_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=3,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  context",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("# Hunk Diff: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:31", copied)
        self.assertIn("- hunk: 2/2", copied)
        self.assertIn("```text", copied)
        self.assertIn("@@ -20,2 +31,3 @@", copied)
        self.assertIn("  20   31 | context", copied)
        self.assertIn("        32 | +second", copied)
        self.assertNotIn("+first", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied hunk 2/2 for src/Sample.ts:31", state.status_message)

    def test_browser_command_executor_reports_copy_hunk_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to copy hunk.", state.status_message)

    def test_browser_command_executor_reports_copy_hunk_without_hunks(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._cached_file_lines", return_value=["File 1/1"]):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No diff hunks in current file.", state.status_message)

    def test_browser_command_executor_surfaces_copy_hunk_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1", "  @@ -1 +9 @@", "        9 | +new"],
        ):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value="Copy failed (cli copy-tool): missing copy",
            ):
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Copy failed (cli copy-tool): missing copy", state.status_message)

    def test_browser_command_executor_reports_open_hunk_without_hunks(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd=None)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._cached_file_lines", return_value=["File 1/1"]):
            with patch("cr.ui.browser.file_actions.open_path") as open_path:
                result = executor.execute(
                    parse_browser_command("open hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_not_called()
        self.assertIn("No diff hunks in current file.", state.status_message)

    def test_browser_command_executor_surfaces_open_hunk_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1", "  @@ -1 +9 @@"],
        ):
            with patch(
                "cr.ui.browser.git.repo_path",
                return_value=Path("/repo/src/Sample.ts"),
            ):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value="Open failed (cli editor): missing editor",
                ):
                    result = executor.execute(
                        parse_browser_command("open hunk", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Open failed (cli editor): missing editor", state.status_message)

    def test_browser_command_executor_reports_hunk_navigation_outside_file_detail(self):
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

        result = executor.execute(parse_browser_command("next hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to jump hunks.", state.status_message)

    def test_browser_command_executor_steps_file_detail_problem_to_visible_diff_line(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Other.ets:1:1 error",
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
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
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)

    def test_browser_command_executor_steps_file_detail_previous_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
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
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)

    def test_browser_command_executor_steps_file_detail_problem_without_visible_diff_line(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:3:1 error"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,1 +1,2 @@",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn(
            "已选择当前文件问题 1/1 src/Foo.ets:3，但当前 diff 不显示该行。",
            state.status_message,
        )

    def test_browser_command_executor_reports_file_detail_without_file_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:1:1 error"],
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
                result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("当前文件没有任务问题。", state.status_message)

    def test_refresh_preserves_file_detail_when_selected_file_survives(self):
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
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 1),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            file_scroll=20,
        )
        state.file_line_cache["stale"] = ["old"]
        state.page_back_stack.append(
            browser_module.BrowserPageSnapshot(
                BrowserPage.CHANGED_FILES,
                0,
                0,
                0,
                0,
                0,
                0,
                "",
                None,
                0,
            )
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[
                FileChange("src/Second.ts", 3, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                with patch("cr.ui.browser._max_file_scroll", return_value=8):
                    result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.changes[0].path, "src/Second.ts")
        self.assertEqual(state.file_scroll, 8)
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_returns_to_changed_files_when_file_detail_disappears(self):
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
        state = BrowserState(
            [FileChange("src/Old.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=12,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/New.ts", 1, 0)],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])
        self.assertIn("Current file no longer visible after refresh.", state.status_message)

    def test_browse_screen_file_detail_shows_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
            context=2,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.change_hunk_lines",
                    return_value=["changes:", "  3 + added"],
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Files > src/Sample.ts", text)
        self.assertIn("操作：]/[ 跳转 hunk", text)


if __name__ == "__main__":
    unittest.main()
