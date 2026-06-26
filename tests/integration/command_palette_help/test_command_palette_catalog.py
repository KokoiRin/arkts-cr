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


class CommandPaletteCatalogTests(unittest.TestCase):
    def test_command_palette_lists_selected_file_index_actions(self):
        # Behavior: 当用户在Command Palette / Help中选择「Command Palette lists 选中文件 index 动作」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        commands = {entry.command for entry in command_catalog.command_palette_entries()}

        self.assertIn("stage", commands)
        self.assertIn("unstage", commands)
    def test_command_palette_lists_source_filter_actions(self):
        # Behavior: 当用户在Command Palette / Help中过滤「Command Palette lists 源码 过滤 动作」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        commands = {entry.command for entry in command_catalog.command_palette_entries()}

        self.assertIn("source staged", commands)
        self.assertIn("source unstaged", commands)
        self.assertIn("source mixed", commands)
        self.assertIn("source all", commands)
    def test_command_palette_entries_include_only_executable_commands(self):
        # Behavior: 当用户在Command Palette / Help中执行操作「Command Palette entries 包含 只读 executable 命令」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        entries = _command_palette_entries()
        commands = [entry.command for entry in entries]

        self.assertIn("build", commands)
        self.assertIn("test", commands)
        self.assertIn("lint", commands)
        self.assertIn("copy path", commands)
        self.assertIn("copy anchor", commands)
        self.assertIn("reveal", commands)
        self.assertIn("file actions", commands)
        self.assertIn("tasks", commands)
        self.assertIn("tasks help", commands)
        self.assertIn("notes", commands)
        self.assertIn("copy notes", commands)
        self.assertIn("save notes", commands)
        self.assertIn("copy prompt", commands)
        self.assertIn("copy prompt file", commands)
        self.assertIn("done next", commands)
        self.assertIn("copy diff", commands)
        self.assertIn("open hunk", commands)
        self.assertIn("open line", commands)
        self.assertIn("copy hunk", commands)
        self.assertIn("copy line", commands)
        self.assertIn("copy change", commands)
        self.assertIn("find TEXT", commands)
        self.assertIn("next match", commands)
        self.assertIn("prev match", commands)
        self.assertIn("next change", commands)
        self.assertIn("prev change", commands)
        self.assertIn("save diff", commands)
        self.assertIn("next hunk", commands)
        self.assertIn("prev hunk", commands)
        self.assertIn("save prompt", commands)
        self.assertIn("save prompt file", commands)
        self.assertIn("staged", commands)
        self.assertIn("forward", commands)
        self.assertIn("remaining", commands)
        self.assertNotIn("b", commands)
        self.assertNotIn("n", commands)
        self.assertNotIn("base REF", commands)
        self.assertNotIn("range OLD..NEW", commands)
        self.assertNotIn("note TEXT", commands)
        self.assertNotIn("note change TEXT", commands)
        self.assertNotIn("notes QUERY", commands)
        self.assertNotIn("copy notes QUERY", commands)
        self.assertNotIn("Enter / 1..N", commands)

if __name__ == "__main__":
    unittest.main()
