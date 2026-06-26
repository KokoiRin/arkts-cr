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


class SourceFileFindSymbolNavigationTests(unittest.TestCase):
    def test_browser_command_executor_finds_text_in_source_file_page(self):
        # Behavior: 当用户在source file中查找源码文件、导航时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nBeta target\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                file_find_text="file-query",
                task_find_text="task-query",
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("find TARGET", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertEqual(state.source_find_text, "TARGET")
        self.assertEqual(state.file_find_text, "file-query")
        self.assertEqual(state.task_find_text, "task-query")
        self.assertIn('Found "TARGET" at line 2.', state.status_message)
    def test_browser_command_executor_repeats_source_file_find_matches(self):
        # Behavior: 当用户在source file中验证源码文件、导航时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "target one\nmiddle\ntarget two\n",
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                find = executor.execute(parse_browser_command("find target", raw_keys=True))
                next_match = executor.execute(
                    parse_browser_command("next match", raw_keys=True)
                )
                line_after_next = state.source_file_line
                previous_match = executor.execute(
                    parse_browser_command("prev match", raw_keys=True)
                )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(line_after_next, 3)
        self.assertEqual(state.source_file_line, 1)
        self.assertEqual(state.source_find_text, "target")
        self.assertIn('Found "target" at line 1.', state.status_message)
    def test_browser_command_executor_jumps_source_file_symbols(self):
        # Behavior: 当用户在source file中跳转源码文件、导航时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
                        "    Text('first')",
                        "  }",
                        "  private onTap = () => {",
                        "    this.handleTap()",
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
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_symbol = executor.execute(parse_browser_command("next symbol"))
                line_after_next = state.source_file_line
                scroll_after_next = state.source_file_scroll
                prev_symbol = executor.execute(parse_browser_command("prev symbol"))

        self.assertTrue(next_symbol.handled)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(line_after_next, 5)
        self.assertEqual(scroll_after_next, -1)
        self.assertTrue(prev_symbol.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertIn("已跳到源码符号 struct Foo > method build src/Foo.ets:2.", state.status_message)
    def test_browser_command_executor_reports_source_symbol_jump_empty_states(self):
        # Behavior: 当用户在source file遇到空状态、源码文件、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                no_symbols = executor.execute(parse_browser_command("next symbol"))
                no_symbol_message = state.status_message
                state.source_file_path = "src/Missing.ets"
                missing = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(no_symbols.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(no_symbol_message, "没有可跳转的源码符号。")
        self.assertIn("Source file not found.", state.status_message)
    def test_browser_command_executor_reports_source_symbol_jump_boundaries(self):
        # Behavior: 当用户在source file遇到源码文件、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
                        "    Text('first')",
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
                source_file_line=1,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                previous_symbol = executor.execute(parse_browser_command("prev symbol"))
                previous_message = state.status_message
                state.source_file_line = 4
                next_symbol = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(previous_symbol.needs_redraw)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(previous_message, "已经在第一个源码符号。")
        self.assertEqual(state.source_file_line, 4)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(state.status_message, "已经在最后一个源码符号。")
    def test_browser_command_executor_reports_source_file_find_empty_states(self):
        # Behavior: 当用户在source file遇到空状态、源码文件、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                empty = executor.execute(parse_browser_command("find", raw_keys=True))
                missing = executor.execute(parse_browser_command("find owner", raw_keys=True))
                repeat = executor.execute(parse_browser_command("next match", raw_keys=True))
                state.source_file_path = "src/Missing.ets"
                unreadable = executor.execute(
                    parse_browser_command("find alpha", raw_keys=True)
                )

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertTrue(repeat.needs_redraw)
        self.assertTrue(unreadable.needs_redraw)
        self.assertEqual(state.source_find_text, "owner")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertIn("Source file not found.", state.status_message)

if __name__ == "__main__":
    unittest.main()
