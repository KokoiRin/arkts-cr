import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import page_content
from cr.ui import source_file
from cr.ui import task_problems
from cr.ui.browser import (
    BrowserState,
    _browse_file_lines,
    _browse_file_screen_lines,
    _browse_list_lines,
    _browse_list_screen_lines,
    _draw_browse_screen,
    filter_changes_by_query,
)
from cr.ui.navigation import BrowserPage
from cr.ui.tasks import TaskState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class PageHelpAndActionBarTests(unittest.TestCase):

    def test_help_screen_explains_current_page_actions_in_chinese(self):
        state = BrowserState([], page=BrowserPage.HELP, help_topic_page=BrowserPage.TASK_PROBLEMS)

        lines = page_content.page_help_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=40,
        )
        text = "\n".join(lines)

        self.assertIn("Task Problems 帮助", text)
        self.assertIn("这个页面能做什么", text)
        self.assertIn("按文件分组", text)
        self.assertIn("problems group file", text)
        self.assertIn("view problem diff", text)
        self.assertIn("save problem", text)
        self.assertIn("copy problem diff", text)
        self.assertIn("save problem diff", text)
        self.assertIn("save problems", text)
        self.assertIn("save file problems", text)
        self.assertIn("copy problem context", text)
        self.assertIn("save problem context", text)

        state.help_topic_page = BrowserPage.TASK_OUTPUT
        task_output_text = "\n".join(
            page_content.page_help_screen_lines(
                state,
                TerminalStyle(False),
                max_lines=40,
            )
        )
        self.assertIn("Task Output 帮助", task_output_text)
        self.assertIn("view problem", task_output_text)
        self.assertIn("view problem diff", task_output_text)
        self.assertIn("save problem", task_output_text)
        self.assertIn("copy problem diff", task_output_text)
        self.assertIn("save problem diff", task_output_text)
        self.assertIn("copy problem context", task_output_text)
        self.assertIn("save problem context", task_output_text)
        self.assertIn("copy task tail", task_output_text)
        self.assertIn("copy task match", task_output_text)
        self.assertIn("save task match", task_output_text)
        self.assertIn("save task tail", task_output_text)

        state.help_topic_page = BrowserPage.FILE_DETAIL
        file_detail_text = "\n".join(
            page_content.page_help_screen_lines(
                state,
                TerminalStyle(False),
                max_lines=40,
            )
        )
        self.assertIn("File Detail 帮助", file_detail_text)
        self.assertIn("view source", file_detail_text)
        self.assertIn("view source symbol", file_detail_text)
        self.assertIn("copy source", file_detail_text)
        self.assertIn("copy source symbol", file_detail_text)
        self.assertIn("save source", file_detail_text)
        self.assertIn("save source symbol", file_detail_text)
        self.assertIn("copy problem context", file_detail_text)
        self.assertIn("save problem context", file_detail_text)
        self.assertIn("copy file problems", file_detail_text)
        self.assertIn("save file problems", file_detail_text)
        self.assertIn("next problem", file_detail_text)
        self.assertIn("prev problem", file_detail_text)
    def test_help_screen_lists_source_file_commands(self):
        state = BrowserState([], page=BrowserPage.HELP, help_topic_page=BrowserPage.SOURCE_FILE)

        text = "\n".join(
            page_content.page_help_screen_lines(
                state,
                TerminalStyle(False),
                max_lines=40,
            )
        )

        self.assertIn("Source File 帮助", text)
        self.assertIn("next problem", text)
        self.assertIn("prev problem", text)
        self.assertIn("source select START END", text)
        self.assertIn("source select symbol", text)
        self.assertIn("source mark", text)
        self.assertIn("source select to", text)
        self.assertIn("copy source symbol", text)
        self.assertIn("copy source", text)
        self.assertIn("save source symbol", text)
        self.assertIn("save source", text)
        self.assertIn("view diff", text)
        self.assertIn("copy problem", text)
        self.assertIn("save problem", text)
        self.assertIn("copy problem diff", text)
        self.assertIn("save problem diff", text)
        self.assertIn("选择源码行范围", text)
    def test_contextual_action_bar_matches_current_page(self):
        style = TerminalStyle(False)

        changed_files = page_content.contextual_action_bar(
            BrowserPage.CHANGED_FILES,
            style,
        )
        file_detail = page_content.contextual_action_bar(
            BrowserPage.FILE_DETAIL,
            style,
        )
        scope_home = page_content.contextual_action_bar(
            BrowserPage.SCOPE_HOME,
            style,
        )
        commit_picker = page_content.contextual_action_bar(
            BrowserPage.COMMIT_PICKER,
            style,
        )
        command_palette = page_content.contextual_action_bar(
            BrowserPage.COMMAND_PALETTE,
            style,
        )

        self.assertIn("操作：", changed_files)
        self.assertIn("Enter 打开", changed_files)
        self.assertIn("done next 完成并下一个", changed_files)
        self.assertIn("build", changed_files)
        self.assertIn("copy task 复制任务", changed_files)
        self.assertIn("help 帮助", changed_files)
        self.assertIn("]/[ 跳转 hunk", file_detail)
        self.assertIn("find 查找", file_detail)
        self.assertIn("view source 看源码", file_detail)
        self.assertIn("copy source 复制源码", file_detail)
        self.assertIn("copy symbol 复制函数", file_detail)
        self.assertIn("copy context 复制上下文", file_detail)
        self.assertIn("copy line 复制行", file_detail)
        self.assertIn("Enter 选择", scope_home)
        self.assertIn(":base", scope_home)
        self.assertIn("/ 过滤提交", commit_picker)
        self.assertIn("Enter 执行", command_palette)
        task_output = page_content.contextual_action_bar(
            BrowserPage.TASK_OUTPUT,
            style,
        )
        self.assertIn("copy task tail 复制尾部", task_output)
        self.assertIn("copy task match 复制匹配", task_output)
        self.assertIn("copy task 复制任务", task_output)
        self.assertIn("save task 保存任务", task_output)
        self.assertIn("next/prev problem 切换问题", task_output)
        self.assertIn("view problem 查看选中问题", task_output)
        self.assertIn("view problem diff 查看 diff", task_output)
        self.assertIn("copy problem diff 复制 diff", task_output)
        self.assertIn("save problem 保存问题", task_output)
        self.assertIn("save problem diff 保存 diff", task_output)
        self.assertIn("copy context 复制选中问题", task_output)
        self.assertIn("save context 保存选中问题", task_output)
        self.assertIn("find 查找", task_output)
        self.assertIn("next match 下个匹配", task_output)
        self.assertIn("stop", task_output)
        self.assertIn("b 返回", task_output)
        task_problems_bar = page_content.contextual_action_bar(
            BrowserPage.TASK_PROBLEMS,
            style,
        )
        self.assertIn("Enter 打开", task_problems_bar)
        self.assertIn("errors 错误", task_problems_bar)
        self.assertIn("warnings 警告", task_problems_bar)
        self.assertIn("all 全部", task_problems_bar)
        self.assertIn("find 查找", task_problems_bar)
        self.assertIn("sort severity 按严重度", task_problems_bar)
        self.assertIn("group file 按文件分组", task_problems_bar)
        self.assertIn("next file 下个文件", task_problems_bar)
        self.assertIn("prev file 上个文件", task_problems_bar)
        self.assertIn("task output 任务输出", task_problems_bar)
        self.assertIn("copy problem 复制问题", task_problems_bar)
        self.assertIn("save problem 保存问题", task_problems_bar)
        self.assertIn("copy problem diff 复制 diff", task_problems_bar)
        self.assertIn("save problem diff 保存 diff", task_problems_bar)
        self.assertIn("copy problems 复制列表", task_problems_bar)
        self.assertIn("copy file problems 当前文件", task_problems_bar)
        self.assertIn("copy context 复制上下文", task_problems_bar)
        self.assertIn("save context 保存上下文", task_problems_bar)
        self.assertIn("view problem 查看源码", task_problems_bar)
        self.assertIn("view problem diff 查看 diff", task_problems_bar)
        self.assertIn("b 返回", task_problems_bar)
        source_file_bar = page_content.contextual_action_bar(
            BrowserPage.SOURCE_FILE,
            style,
        )
        self.assertIn("↑/↓ 滚动", source_file_bar)
        self.assertIn("find 查找", source_file_bar)
        self.assertIn("next match 下个匹配", source_file_bar)
        self.assertIn("next/prev problem 切问题", source_file_bar)
        self.assertIn("next/prev symbol 跳符号", source_file_bar)
        self.assertIn("open 打开", source_file_bar)
        self.assertIn("copy line 复制行", source_file_bar)
        self.assertIn("copy source 复制源码", source_file_bar)
        self.assertIn("copy problem 复制问题", source_file_bar)
        self.assertIn("save problem 保存问题", source_file_bar)
        self.assertIn("copy problem diff 复制 diff", source_file_bar)
        self.assertIn("save problem diff 保存 diff", source_file_bar)
        self.assertIn("view diff 查看 diff", source_file_bar)
        self.assertIn("copy context 复制上下文", source_file_bar)
        self.assertIn("save context 保存上下文", source_file_bar)
        self.assertIn("source context 上下文行数", source_file_bar)
        self.assertIn("select range 选择范围", source_file_bar)
        self.assertIn("select symbol 选择函数", source_file_bar)
        self.assertIn("b 返回", source_file_bar)
        help_bar = page_content.contextual_action_bar(
            BrowserPage.HELP,
            style,
        )
        self.assertIn("b 返回", help_bar)
        self.assertIn("commands 命令面板", help_bar)
        self.assertNotEqual(changed_files, file_detail)
    def test_contextual_action_bar_uses_line_fitting(self):
        fitted = page_content.contextual_action_bar(
            BrowserPage.CHANGED_FILES,
            TerminalStyle(False),
            lambda line: line[:20],
        )

        self.assertEqual(fitted, "操作：Enter 打开  |  / 过滤")

if __name__ == "__main__":
    unittest.main()
