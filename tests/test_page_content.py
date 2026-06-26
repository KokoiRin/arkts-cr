import subprocess
import unittest

from cr.ui import page_content
from cr.ui import source_file
from cr.ui import task_problems
from cr.ui.browser import BrowserState
from cr.ui.navigation import BrowserPage
from cr.ui.tasks import TaskState
from cr.ui.terminal import TerminalStyle


class PageContentTests(unittest.TestCase):
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

    def test_task_output_screen_renders_current_task(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["npm", "test"],
                process,
                kind="test",
                lines=["start tests", "failed test"],
                returncode=1,
            ),
        )

        lines = page_content.task_output_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn("Task output", text)
        self.assertIn("Status: failed (1)", text)
        self.assertIn("Command: npm test", text)
        self.assertIn("start tests", text)
        self.assertIn("failed test", text)

    def test_task_output_screen_renders_selected_problem(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(["npm", "test"], process, lines=["one", "two"]),
            problem_selected=1,
        )
        problems = [
            task_problems.TaskProblem(
                path="src/One.ets",
                line=1,
                column=1,
                summary="src/One.ets:1:1 error",
                output_line=1,
            ),
            task_problems.TaskProblem(
                path="src/Two.ets",
                line=2,
                column=4,
                summary="src/Two.ets:2:4 error",
                output_line=2,
            ),
        ]

        lines = page_content.task_output_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=10,
            problems=problems,
        )
        text = "\n".join(lines)

        self.assertIn("Problem: 2/2 src/Two.ets:2:4", text)

    def test_task_output_screen_renders_empty_state(self):
        state = BrowserState([])

        lines = page_content.task_output_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("No current task output.", text)
        self.assertIn("Run build, test, or lint", text)

    def test_task_problems_screen_renders_problem_facts(self):
        problems = [
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=12,
                column=3,
                summary="src/Foo.ets:12:3 error: bad call",
                output_line=1,
                severity="error",
                code="TS2322",
                message="bad call",
            ),
            task_problems.TaskProblem(
                path="src/Bar.ets",
                line=8,
                column=None,
                summary="src/Bar.ets:8 warning",
                output_line=2,
                severity="warning",
            ),
        ]
        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)

        lines = page_content.task_problems_screen_lines(
            state,
            problems,
            TerminalStyle(False),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn("Task problems", text)
        self.assertIn("1 error, 1 warning", text)
        self.assertIn("> 1", text)
        self.assertIn("src/Foo.ets:12:3", text)
        self.assertIn("ERROR TS2322", text)
        self.assertIn("bad call", text)
        self.assertIn("src/Bar.ets:8", text)

    def test_task_problems_screen_renders_sort_state(self):
        problems = [
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=12,
                column=None,
                summary="src/Foo.ets:12 error",
                output_line=1,
                severity="error",
            ),
        ]
        state = BrowserState(
            [],
            page=BrowserPage.TASK_PROBLEMS,
            problem_sort="severity",
        )

        lines = page_content.task_problems_screen_lines(
            state,
            problems,
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("sort: severity", text)

    def test_task_problems_screen_renders_query_state(self):
        problems = [
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=12,
                column=None,
                summary="src/Foo.ets:12 error",
                output_line=1,
                severity="error",
            ),
        ]
        state = BrowserState(
            [],
            page=BrowserPage.TASK_PROBLEMS,
            problem_query="Foo",
        )

        lines = page_content.task_problems_screen_lines(
            state,
            problems,
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("find: Foo", text)

    def test_task_problems_screen_renders_grouped_by_file(self):
        problems = [
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=12,
                column=None,
                summary="src/Foo.ets:12 error",
                output_line=1,
                severity="error",
            ),
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=20,
                column=None,
                summary="src/Foo.ets:20 warning",
                output_line=2,
                severity="warning",
            ),
            task_problems.TaskProblem(
                path="src/Bar.ets",
                line=3,
                column=None,
                summary="src/Bar.ets:3 error",
                output_line=3,
                severity="error",
            ),
        ]
        state = BrowserState(
            [],
            page=BrowserPage.TASK_PROBLEMS,
            problem_group="file",
            problem_selected=1,
        )

        lines = page_content.task_problems_screen_lines(
            state,
            problems,
            TerminalStyle(False),
            max_lines=12,
        )
        text = "\n".join(lines)

        self.assertIn("group: file", text)
        self.assertIn("src/Foo.ets (2)", text)
        self.assertIn("src/Bar.ets (1)", text)
        self.assertIn("  1  src/Foo.ets:12", text)
        self.assertIn("> 2  src/Foo.ets:20", text)
        self.assertIn("  3  src/Bar.ets:3", text)

    def test_task_problems_screen_renders_filtered_empty_state(self):
        state = BrowserState(
            [],
            page=BrowserPage.TASK_PROBLEMS,
            problem_filter="error",
            problem_sort="severity",
        )

        lines = page_content.task_problems_screen_lines(
            state,
            [],
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("Task problems: error", text)
        self.assertIn("sort: severity", text)
        self.assertIn("No error task problems found.", text)
        self.assertIn("problems all", text)

    def test_task_problems_screen_renders_query_empty_state(self):
        state = BrowserState(
            [],
            page=BrowserPage.TASK_PROBLEMS,
            problem_query="Foo",
        )

        lines = page_content.task_problems_screen_lines(
            state,
            [],
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("find: Foo", text)
        self.assertIn("No task problems match Foo.", text)
        self.assertIn("problems clear find", text)

    def test_task_problems_screen_renders_empty_state(self):
        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)

        lines = page_content.task_problems_screen_lines(
            state,
            [],
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("No task problems found.", text)
        self.assertIn("Run build, test, or lint", text)

    def test_source_file_screen_renders_source_rows_and_error(self):
        view = source_file.SourceFileView(
            path="src/Foo.ets",
            target_line=2,
            scroll=0,
            total_lines=3,
            rows=[
                source_file.SourceFileRow(1, "first", is_selected=True),
                source_file.SourceFileRow(2, "target", is_target=True, is_selected=True),
                source_file.SourceFileRow(3, "third", is_selected=True),
            ],
        )

        lines = page_content.source_file_screen_lines(
            view,
            TerminalStyle(False),
            max_lines=8,
            context_lines=8,
            selection_start=1,
            selection_end=3,
            mark_line=2,
            symbol_label="struct Foo > method build",
            problem_label="1/2 ERROR TS123 bad value",
        )
        text = "\n".join(lines)

        self.assertIn("Source src/Foo.ets", text)
        self.assertIn("context: 8", text)
        self.assertIn("selection: 1-3", text)
        self.assertIn("mark: 2", text)
        self.assertIn("symbol: struct Foo > method build", text)
        self.assertIn("problem: 1/2 ERROR TS123 bad value", text)
        self.assertIn("* 1  first", text)
        self.assertIn("> 2  target", text)
        self.assertIn("* 3  third", text)

        error = source_file.SourceFileView(
            path="src/Missing.ets",
            target_line=1,
            scroll=0,
            total_lines=0,
            rows=[],
            error="Source file not found.",
        )
        error_text = "\n".join(
            page_content.source_file_screen_lines(
                error,
                TerminalStyle(False),
                max_lines=5,
            )
        )

        self.assertIn("Source src/Missing.ets", error_text)
        self.assertIn("Source file not found.", error_text)


if __name__ == "__main__":
    unittest.main()
