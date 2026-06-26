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


class SourceFileSymbolCopyCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_source_enum_symbol(self):
        # Behavior: 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            source = repo / "src" / "Status.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "export const enum FeedStatus {",
                        "  Loading = 'loading',",
                        "  Ready = 'ready',",
                        "}",
                        "function after() {",
                        "  return FeedStatus.Ready",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            change = FileChange("src/Status.ets", 1, 0)
            copied: list[str] = []
            state = browser_module.BrowserState(
                [change],
                page=browser_module.BrowserPage.SOURCE_FILE,
                source_file_path="src/Status.ets",
                source_file_line=2,
                selected=0,
            )
            executor = browser_module.BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    side_effect=lambda text, _cmd: copied.append(text),
                ):
                    result = executor.execute(parse_browser_command("copy source symbol"))

        self.assertTrue(result.handled)
        self.assertIn("Copied source symbol src/Status.ets:1-4.", state.status_message)
        self.assertEqual(len(copied), 1)
        self.assertIn("Symbol: enum FeedStatus", copied[0])
        self.assertIn("  Loading = 'loading',", copied[0])
        self.assertNotIn("function after", copied[0])
    def test_browser_command_executor_copies_source_file_symbol_directly(self):
        # Behavior: 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
                source_selection_start=7,
                source_selection_end=8,
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
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertNotIn("other() {", copied)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 8))
        self.assertIn("Copied source symbol src/Foo.ets:2-5.", state.status_message)
    def test_browser_command_executor_copies_source_field_arrow_symbol(self):
        # Behavior: 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  private onTap = () => {",
                        "    this.handleTap()",
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
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: struct Foo > method onTap", copied)
        self.assertIn("private onTap = () => {", copied)
        self.assertIn("this.handleTap()", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)
    def test_browser_command_executor_copies_source_accessor_symbol(self):
        # Behavior: 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  get title(): string {",
                        "    return this.model.title",
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
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method title", copied)
        self.assertIn("get title(): string", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)
    def test_browser_command_executor_copies_source_generic_method_symbol(self):
        # Behavior: 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  private createModel<T extends BaseModel>(value: T): T {",
                        "    return value",
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
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method createModel", copied)
        self.assertIn("private createModel<T extends BaseModel>", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

if __name__ == "__main__":
    unittest.main()
