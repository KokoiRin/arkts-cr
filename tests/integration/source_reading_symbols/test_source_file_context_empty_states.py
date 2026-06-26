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


class SourceFileContextEmptyStatesTest(unittest.TestCase):

    def test_browser_command_executor_reports_source_context_without_source_page(self):
        # Behavior: 当用户在Source File中处理异常「BrowserCommandExecutor 提示 源码 上下文 不包含 源码 page」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.CHANGED_FILES,
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source context 8"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_context_lines, 3)
        self.assertIn("Open a source file before setting source context.", state.status_message)
    def test_browser_command_executor_reports_empty_source_context_copy(self):
        # Behavior: 当用户在Source File中复制「BrowserCommandExecutor 提示 空态 源码 上下文 复制」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file to copy.", state.status_message)
    def test_browser_command_executor_reports_missing_source_context_copy(self):
        # Behavior: 当用户在Source File中复制「BrowserCommandExecutor 提示 缺失 源码 上下文 复制」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Missing.ets",
                source_file_line=5,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("Source file not found.", state.status_message)
    def test_browser_command_executor_reports_empty_source_file_line_copy(self):
        # Behavior: 当用户在Source File中复制「BrowserCommandExecutor 提示 空态 Source File 行 复制」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file line to copy.", state.status_message)

if __name__ == "__main__":
    unittest.main()
