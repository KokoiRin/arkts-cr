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


class FileDetailChangeCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_current_change_in_file_detail(self):
        # Behavior: 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
