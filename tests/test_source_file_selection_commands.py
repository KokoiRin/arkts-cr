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


class SourceFileSelectionCommandTests(unittest.TestCase):
    def test_browser_command_executor_sets_and_clears_source_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_selection = executor.execute(parse_browser_command("source select 8 3"))
        selection_after_set = (
            state.source_selection_start,
            state.source_selection_end,
        )
        invalid_selection = executor.execute(parse_browser_command("source select nope 3"))
        selection_after_invalid = (
            state.source_selection_start,
            state.source_selection_end,
        )
        clear_selection = executor.execute(parse_browser_command("source clear selection"))

        self.assertTrue(set_selection.handled)
        self.assertTrue(set_selection.needs_redraw)
        self.assertTrue(invalid_selection.handled)
        self.assertTrue(clear_selection.handled)
        self.assertEqual(selection_after_set, (3, 8))
        self.assertEqual(selection_after_invalid, (3, 8))
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertIn("Source selection cleared.", state.status_message)
    def test_browser_command_executor_selects_source_range_from_mark_to_current_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        mark_result = executor.execute(parse_browser_command("source mark"))
        state.source_file_line = 9
        select_result = executor.execute(parse_browser_command("source select to"))
        state.source_file_line = 3
        reverse_result = executor.execute(parse_browser_command("source select to"))
        clear_mark_result = executor.execute(parse_browser_command("source clear mark"))

        self.assertTrue(mark_result.needs_redraw)
        self.assertTrue(select_result.needs_redraw)
        self.assertTrue(reverse_result.needs_redraw)
        self.assertTrue(clear_mark_result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (3, 5))
        self.assertEqual(state.source_mark_line, 0)
        self.assertIn("Source mark cleared.", state.status_message)
    def test_browser_command_executor_reports_source_select_to_without_mark(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select to"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn("Set a source mark before selecting to it.", state.status_message)
    def test_browser_command_executor_selects_current_source_symbol(self):
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
                        "    const title = 'hi'",
                        "    Text(title)",
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
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (2, 5))
        self.assertIn(
            "Selected source symbol struct Foo > method build src/Foo.ets:2-5.",
            state.status_message,
        )
    def test_browser_command_executor_reports_source_symbol_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn(
            "Open a source file before selecting source symbol.",
            state.status_message,
        )
    def test_browser_command_executor_reports_source_symbol_selection_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                source_selection_start=7,
                source_selection_end=9,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 9))
        self.assertIn("No source symbol at current line.", state.status_message)
    def test_browser_command_executor_reports_source_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select 1 3"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_selection_start, 0)
        self.assertIn("Open a source file before selecting source.", state.status_message)
    def test_browser_command_executor_copies_selected_source_symbol_range(self):
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
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
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
                    select_result = executor.execute(
                        parse_browser_command("source select symbol")
                    )
                    copy_result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(select_result.handled)
        self.assertTrue(copy_result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("const title = 'hi'", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied selected source src/Foo.ets:2-5.", state.status_message)

if __name__ == "__main__":
    unittest.main()
