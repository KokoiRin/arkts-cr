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


class FileDetailHunkCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_current_hunk_in_file_detail(self):
        # Behavior: 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到失败反馈、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到失败反馈、文件详情时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
