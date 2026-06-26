import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import command_catalog
from cr.ui.browser import (
    BrowserState,
    _browse_command_palette_screen_lines,
    _command_palette_entries,
    _draw_browse_screen,
    _filtered_command_palette_entries,
    _move_selection,
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


class CommandPaletteRenderingTests(unittest.TestCase):
    def test_command_palette_selection_is_independent_from_file_selection(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            selected=1,
            page="commands",
        )

        _move_selection(state, 1)

        self.assertEqual(state.selected, 1)
        self.assertEqual(state.command_selected, 1)
    def test_command_palette_screen_marks_selected_command(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page="commands",
            command_selected=1,
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("命令面板", text)
        self.assertIn("Enter：执行选中命令", text)
        self.assertIn("> ", text)
    def test_command_palette_screen_shows_filter_and_empty_results(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page="commands",
            command_filter_text="zz-missing",
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        total = len(_command_palette_entries())
        self.assertIn(f"过滤：zz-missing （0/{total} 个匹配）", text)
        self.assertIn("没有匹配命令。", text)
        self.assertNotIn("运行仓库配置的编译命令", text)
    def test_command_palette_screen_shows_filter_match_count(self):
        state = BrowserState([], page="commands", command_filter_text="build")
        lines = _browse_command_palette_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=20,
        )
        text = "\n".join(lines)
        total = len(_command_palette_entries())
        matches = len(_filtered_command_palette_entries(state))

        self.assertIn(f"过滤：build （{matches}/{total} 个匹配）", text)
        self.assertGreater(matches, 0)

if __name__ == "__main__":
    unittest.main()
