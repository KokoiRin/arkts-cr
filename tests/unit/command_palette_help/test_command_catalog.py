import unittest

from cr.ui import command_catalog
from cr.ui.browser import _browse_command_lines, _normalize_command_query
from cr.ui.terminal import TerminalStyle


class CommandCatalogTests(unittest.TestCase):
    def test_command_help_groups_commands_by_workflow(self):
        # Behavior: 当用户在Command Palette / Help中执行操作「命令 帮助 groups 命令 by workflow」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        groups = command_catalog.command_catalog()
        lines = command_catalog.command_list_lines(TerminalStyle(False), max_lines=140)
        text = "\n".join(lines)

        self.assertEqual([group.title for group in groups][0], "导航")
        self.assertIn("命令", text)
        self.assertIn("审查范围", text)
        self.assertIn("显示当前页面帮助", text)
        self.assertIn("copy prompt file", text)
        self.assertIn("done next", text)
        self.assertIn("note change TEXT", text)
        self.assertIn("open hunk", text)
        self.assertIn("open line", text)
        self.assertIn("view source", text)
        self.assertIn("view source symbol", text)
        self.assertIn("copy hunk", text)
        self.assertIn("copy line", text)
        self.assertIn("copy source", text)
        self.assertIn("copy source symbol", text)
        self.assertIn("save source", text)
        self.assertIn("save source symbol", text)
        self.assertIn("copy problem context", text)
        self.assertIn("copy task tail", text)
        self.assertIn("copy task match", text)
        self.assertIn("save task match", text)
        self.assertIn("save task tail", text)
        self.assertIn("copy change", text)
        self.assertIn("save notes", text)
        self.assertIn("source context N", text)
        self.assertIn("source select START END", text)
        self.assertIn("source select symbol", text)
        self.assertIn("source mark", text)
        self.assertIn("source select to", text)
        self.assertIn("source clear selection", text)
        self.assertIn("find TEXT", text)
        self.assertIn("next match", text)
        self.assertIn("prev match", text)
        self.assertIn("next change", text)
        self.assertIn("prev change", text)
        self.assertIn("save diff", text)
        self.assertIn("next hunk", text)
        self.assertIn("prev hunk", text)
        self.assertIn("save prompt file", text)
        self.assertIn("copy task", text)
        self.assertIn("save task", text)
        self.assertIn("save problem", text)
        self.assertIn("copy/save problem diff", text)
        self.assertIn("save problems", text)
        self.assertIn("save file problems", text)
        self.assertIn("save problem context", text)
        self.assertIn("task output", text)
        self.assertIn("problems errors", text)
        self.assertIn("problems all", text)
        self.assertIn("problems find TEXT", text)
        self.assertIn("problems clear find", text)
        self.assertIn("problems sort severity", text)
        self.assertIn("problems sort output", text)
        self.assertIn("problems group file", text)
        self.assertIn("problems group none", text)

    def test_executable_palette_entries_include_actions_not_parameter_templates(self):
        # Behavior: 当用户在Command Palette / Help中执行操作「executable palette entries 包含 动作 不 parameter templates」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        commands = [entry.command for entry in command_catalog.command_palette_entries()]
        scope_filtered = [
            entry.command
            for entry in command_catalog.filtered_command_palette_entries("scope")
        ]
        file_filtered = [
            entry.command
            for entry in command_catalog.filtered_command_palette_entries("file")
        ]

        self.assertIn("copy prompt", commands)
        self.assertIn("copy prompt file", commands)
        self.assertIn("copy task", commands)
        self.assertIn("save task", commands)
        self.assertIn("task output", commands)
        self.assertIn("problems", commands)
        self.assertIn("save problem", commands)
        self.assertIn("save notes", commands)
        self.assertIn("copy problem diff", commands)
        self.assertIn("save problem diff", commands)
        self.assertIn("problems errors", commands)
        self.assertIn("problems warnings", commands)
        self.assertIn("problems all", commands)
        self.assertIn("problems find TEXT", commands)
        self.assertIn("problems clear find", commands)
        self.assertIn("problems sort severity", commands)
        self.assertIn("problems sort output", commands)
        self.assertIn("problems group file", commands)
        self.assertIn("problems group none", commands)
        self.assertIn("next problem", commands)
        self.assertIn("prev problem", commands)
        self.assertIn("next problem file", commands)
        self.assertIn("prev problem file", commands)
        self.assertIn("copy problem", commands)
        self.assertIn("copy problems", commands)
        self.assertIn("copy file problems", commands)
        self.assertIn("copy problem context", commands)
        self.assertIn("save problem context", commands)
        self.assertIn("view problem", commands)
        self.assertIn("view problem diff", commands)
        self.assertIn("done next", commands)
        self.assertIn("open hunk", commands)
        self.assertIn("open line", commands)
        self.assertIn("view source", commands)
        self.assertIn("view source symbol", commands)
        self.assertIn("view diff", commands)
        self.assertIn("copy hunk", commands)
        self.assertIn("copy line", commands)
        self.assertIn("copy source", commands)
        self.assertIn("copy source symbol", commands)
        self.assertIn("next symbol", commands)
        self.assertIn("prev symbol", commands)
        self.assertIn("source context 3", commands)
        self.assertIn("source select 1 3", commands)
        self.assertIn("source select symbol", commands)
        self.assertIn("source mark", commands)
        self.assertIn("source select to", commands)
        self.assertIn("source clear mark", commands)
        self.assertIn("source clear selection", commands)
        self.assertIn("copy change", commands)
        self.assertNotIn("note change TEXT", commands)
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
        self.assertNotIn("base REF", commands)
        self.assertNotIn("copy notes QUERY", commands)
        self.assertLess(scope_filtered.index("scopes"), scope_filtered.index("staged"))
        self.assertLess(file_filtered.index("file actions"), file_filtered.index("open"))

    def test_command_palette_screen_renders_filter_selection_and_scroll(self):
        # Behavior: 当用户在Command Palette / Help中查看「Command Palette screen 渲染 过滤 选择 and scroll」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        screen = command_catalog.command_palette_screen_lines(
            query="build",
            selected=0,
            scroll=0,
            style=TerminalStyle(False),
            max_lines=20,
        )
        text = "\n".join(screen.lines)

        self.assertEqual(screen.scroll, 0)
        self.assertIn("命令面板", text)
        self.assertIn("过滤：build", text)
        self.assertIn("> ", text)

    def test_command_query_empty_or_question_mark_opens_command_list(self):
        # Behavior: 当用户在Command Palette / Help中打开或定位「命令 查询 空态 or question 标记 打开 命令 list」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        self.assertEqual(_normalize_command_query(""), "commands")
        self.assertEqual(_normalize_command_query("?"), "commands")
        self.assertEqual(_normalize_command_query(" build "), "build")

    def test_command_list_lines_group_commands_by_purpose(self):
        # Behavior: 当用户在Command Palette / Help中查看「命令 list 行 group 命令 by purpose」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        lines = _browse_command_lines(TerminalStyle(False), max_lines=120)
        text = "\n".join(lines)

        self.assertIn("命令", text)
        self.assertIn("导航", text)
        self.assertIn("审查范围", text)
        self.assertIn("任务", text)
        self.assertIn("文件", text)
        self.assertIn("会话", text)
        self.assertIn("staged", text)
        self.assertIn("build", text)
        self.assertIn("done next", text)
        self.assertIn("note TEXT", text)
        self.assertIn("note change TEXT", text)
        self.assertIn("notes QUERY", text)
        self.assertIn("copy notes QUERY", text)
        self.assertIn("save notes", text)
        self.assertIn("copy prompt", text)
        self.assertIn("copy prompt file", text)
        self.assertIn("open hunk", text)
        self.assertIn("open line", text)
        self.assertIn("copy hunk", text)
        self.assertIn("copy line", text)
        self.assertIn("copy change", text)
        self.assertIn("find TEXT", text)
        self.assertIn("next match", text)
        self.assertIn("prev match", text)
        self.assertIn("next change", text)
        self.assertIn("prev change", text)
        self.assertIn("save diff", text)
        self.assertIn("next hunk", text)
        self.assertIn("prev hunk", text)
        self.assertIn("save prompt", text)
        self.assertIn("save prompt file", text)

if __name__ == "__main__":
    unittest.main()
