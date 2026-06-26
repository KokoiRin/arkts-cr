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


class SourceFileContextCommandTests(unittest.TestCase):
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
    def test_browser_command_executor_saves_selected_source_context_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save source"))

            saved = repo / ".cr" / "handoff" / "source.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:3-6", text)
        self.assertIn("> 5  line 5", text)
        self.assertNotIn("line 2", text)
        self.assertNotIn("line 7", text)
        self.assertIn("Saved selected source to .cr/handoff/source.md.", state.status_message)
    def test_browser_command_executor_sets_source_context_lines(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_context = executor.execute(parse_browser_command("source context 8"))
        clamped_context = executor.execute(parse_browser_command("source context 999"))
        invalid_context = executor.execute(parse_browser_command("source context nope"))

        self.assertTrue(set_context.handled)
        self.assertTrue(set_context.needs_redraw)
        self.assertTrue(clamped_context.handled)
        self.assertTrue(invalid_context.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_context_lines, 50)
        self.assertIn("Source context must be a non-negative integer.", state.status_message)
    def test_browser_command_executor_reports_source_context_without_source_page(self):
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
    def test_browser_command_executor_reports_empty_source_context_copy(self):
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
