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


class FileDetailNavigationCommandTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
