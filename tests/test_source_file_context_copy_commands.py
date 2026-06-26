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


class SourceFileContextCopyCommandsTest(unittest.TestCase):

    def test_browser_command_executor_copies_source_file_page_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=20,
            source_file_scroll=7,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with("src/Foo.ets:20", "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 20)
        self.assertEqual(state.source_file_scroll, 7)
        self.assertIn("Copied source line src/Foo.ets:20", state.status_message)
    def test_browser_command_executor_copies_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:5", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  8  line 8", copied)
        self.assertNotIn("line 1", copied)
        copy_text.assert_called_once_with(copied, "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 5)
        self.assertEqual(state.source_file_scroll, 2)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)
    def test_browser_command_executor_copies_source_file_context_with_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('hello')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("> 3  ", copied)
        self.assertIn("Copied source context src/Foo.ets:3", state.status_message)
    def test_browser_command_executor_copies_configured_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("  4  line 4", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 3", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)
    def test_browser_command_executor_copies_selected_source_range(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied selected source src/Foo.ets:3-6", state.status_message)

if __name__ == "__main__":
    unittest.main()
