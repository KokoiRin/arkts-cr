import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui.browser import BrowserCommandExecutor, BrowserFrame, BrowserState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class FileActionBrowserCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_selected_path(self):
        # Behavior: 当用户在file action中复制action、copies、path时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy path"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy.assert_called_once_with("src/Sample.ts", "copy-tool")
        self.assertIn("Copied src/Sample.ts", output.getvalue())
    def test_browser_command_executor_copies_selected_anchor(self):
        # Behavior: 当用户在file action中复制action、copies、anchor时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
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

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        copy.assert_called_once_with("src/Sample.ts:12", None)
        self.assertIn("Copied src/Sample.ts:12", output.getvalue())
    def test_browser_command_executor_anchor_falls_back_to_path_without_line(self):
        # Behavior: 当用户在file action遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
        )
        state = BrowserState([FileChange("asset.bin", None, None)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch("cr.ui.browser.git.first_changed_line", return_value=None):
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(StringIO()):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        copy.assert_called_once_with("asset.bin", None)
    def test_browser_command_executor_opens_selected_file(self):
        # Behavior: 当用户在file action中打开action、opens时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
    def test_browser_command_executor_reveals_selected_file(self):
        # Behavior: 当用户在file action中选择action、reveals时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(reveal_cmd="reveal-tool --file {file}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
            with patch("cr.ui.browser.file_actions.reveal_path", return_value=None) as reveal:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        reveal.assert_called_once_with(repo_file, "reveal-tool --file {file}")
        self.assertIn("Revealed src/Sample.ts", output.getvalue())
    def test_browser_command_executor_shows_file_action_diagnostics(self):
        # Behavior: 当用户在file action中展示action、shows、action、diagnostics时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            open_cmd="code -g {fileline}",
            copy_cmd="copy-tool {text}",
            reveal_cmd="reveal-tool {file}",
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

        with patch("cr.ui.browser.git.repo_root", return_value=Path("/tmp/repo")):
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("file actions"))

        text = output.getvalue()
        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        self.assertIn("File actions:", text)
        self.assertIn("open: cli code -g", text)
        self.assertIn("copy: cli copy-tool", text)
        self.assertIn("reveal: cli reveal-tool", text)
    def test_browser_file_actions_report_when_no_changed_file_is_available(self):
        # Behavior: 当用户在file action中验证action、actions、report、no时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with patch("cr.ui.browser.file_actions.reveal_path") as reveal:
                with redirect_stdout(output):
                    copy_result = executor.execute(parse_browser_command("copy path"))
                    reveal_result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(copy_result.handled)
        self.assertTrue(reveal_result.handled)
        copy.assert_not_called()
        reveal.assert_not_called()
        self.assertIn("No changed file to copy.", output.getvalue())
        self.assertIn("No changed file to reveal.", output.getvalue())
    def test_browse_parser_accepts_file_action_command_configuration(self):
        # Behavior: 当系统处理file action的配置时，系统应解析出正确结果 [Requirement: TODO]
        from cr.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "browse",
                "--copy-cmd",
                "copy-tool",
                "--reveal-cmd",
                "reveal-tool --file {file}",
            ]
        )

        self.assertEqual(args.copy_cmd, "copy-tool")
        self.assertEqual(args.reveal_cmd, "reveal-tool --file {file}")

if __name__ == "__main__":
    unittest.main()
