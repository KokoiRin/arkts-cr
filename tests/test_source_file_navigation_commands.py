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


class SourceFileNavigationCommandTests(unittest.TestCase):
    def test_browser_command_executor_views_source_file_diff(self):
        # Behavior: 当用户在source file中验证源码文件、导航时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 2/2  src/Two.ets",
                "  @@ -1,2 +1,3 @@",
                "     1    1 | one",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Opened source diff src/Two.ets:2.", state.status_message)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
    def test_browser_command_executor_reports_source_file_diff_without_changed_file(self):
        # Behavior: 当用户在source file遇到缺少前置条件、源码文件、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.selected, 0)
        self.assertIn(
            "No diff for source src/Two.ets:2 in current review scope.",
            state.status_message,
        )
    def test_browser_command_executor_scrolls_and_opens_source_file_page(self):
        # Behavior: 当用户在source file中打开源码文件、导航时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 40)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=20,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                down = executor.execute(parse_browser_command("down", raw_keys=True))
                scroll_after_down = state.source_file_scroll
                end = executor.execute(parse_browser_command("end", raw_keys=True))
                scroll_after_end = state.source_file_scroll
                home = executor.execute(parse_browser_command("home", raw_keys=True))
                scroll_after_home = state.source_file_scroll
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    opened = executor.execute(parse_browser_command("open"))

        self.assertTrue(down.needs_redraw)
        self.assertTrue(end.needs_redraw)
        self.assertTrue(home.needs_redraw)
        self.assertGreater(scroll_after_down, 0)
        self.assertGreater(scroll_after_end, scroll_after_down)
        self.assertEqual(scroll_after_home, 0)
        self.assertTrue(opened.needs_redraw)
        open_path.assert_called_once_with(source, 20, "editor {fileline}")
        self.assertIn("Opened source src/Foo.ets:20", state.status_message)

if __name__ == "__main__":
    unittest.main()
