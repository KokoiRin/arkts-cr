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


class SourceFileRenderingTests(unittest.TestCase):
    def test_browse_source_file_screen_lines_show_current_symbol(self):
        # Behavior: 当用户在Source File中查看「browse Source File screen 行 显示 当前 符号」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
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
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("symbol: struct Foo > method build", text)
        self.assertIn("> 3", text)
    def test_browse_source_file_screen_lines_show_matching_task_problem(self):
        # Behavior: 当用户在Source File中查看「browse Source File screen 行 显示 matching Task Problems」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("problem: 1/1 ERROR TS123", text)
        self.assertIn("bad value", text)
    def test_browse_source_file_screen_lines_hides_stale_task_problem(self):
        # Behavior: 当用户在Source File中查看「browse Source File screen 行 hides stale Task Problems」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertNotIn("problem:", text)
        self.assertNotIn("bad value", text)
    def test_browse_screen_renders_source_file_page(self):
        # Behavior: 当用户在Source File中查看「browse screen 渲染 Source File page」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_context_lines=8,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.frame.shutil.get_terminal_size",
                    return_value=os.terminal_size((120, 12)),
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Source > src/Foo.ets", text)
        self.assertIn("Source src/Foo.ets", text)
        self.assertIn("context: 8", text)
        self.assertIn("> 2  two", text)
        self.assertIn("cr:source> ", text)

if __name__ == "__main__":
    unittest.main()
