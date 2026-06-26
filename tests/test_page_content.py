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

    def test_browse_tree_highlights_guides_and_uses_plain_white_file_names(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/pages/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/pages/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(True, True))

        text = output.getvalue()
        self.assertIn("\033[36m└─ src/pages\033[0m", text)
        self.assertIn("\033[36m   └─ \033[0m", text)
        self.assertIn("\033[37mSample.ts", text)
        self.assertNotIn("\033[36mSample.ts", text)
        self.assertNotIn("\033]8;;", text)

    def test_page_content_owns_prompt_labels_and_scroll_window(self):
        self.assertEqual(page_content.browse_prompt(BrowserPage.SCOPE_HOME), "cr:scopes> ")
        self.assertEqual(page_content.browse_prompt(BrowserPage.FILE_DETAIL), "cr:file> ")
        self.assertEqual(page_content.ensure_window(0, 8, 20, 5), 4)
        self.assertEqual(page_content.ensure_window(4, 2, 20, 5), 2)

    def test_page_content_builds_compacted_changed_file_tree(self):
        changes = [
            FileChange("src/pages/home/HomeView.ets", 1, 0),
            FileChange("src/pages/home/HomeModel.ets", 2, 1),
        ]

        rows = page_content.browse_tree_rows(changes)

        self.assertEqual(rows[0].label, "└─ src/pages/home")
        self.assertEqual(rows[1].label, "   ├─ HomeModel.ets")
        self.assertEqual(rows[2].label, "   └─ HomeView.ets")

    def test_page_content_changed_file_rows_show_source_badges(self):
        change = FileChange("src/Sample.ts", 1, 1, source="mixed")

        lines = page_content.browse_list_lines(
            [change],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            seen_paths=set(),
            review_notes={"src/Sample.ts": "check lifecycle"},
        )

        row = "\n".join(lines)
        self.assertIn("mixed", row)
        self.assertIn("[ ]", row)
        self.assertIn("modified", row)
        self.assertIn("note", row)

    def test_page_content_changed_file_header_shows_source_summary(self):
        lines = page_content.browse_list_lines(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 2, 1, source="unstaged"),
                FileChange("src/Mixed.ts", 3, 2, source="mixed"),
            ],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1, unstaged 1, mixed 1", "\n".join(lines))

    def test_page_content_source_summary_omits_zero_and_empty_sources(self):
        staged_lines = page_content.browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
        )
        comparison_lines = page_content.browse_list_lines(
            [FileChange("src/CommitOnly.ts", 1, 0)],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1", "\n".join(staged_lines))
        self.assertNotIn("unstaged 0", "\n".join(staged_lines))
        self.assertNotIn("Sources:", "\n".join(comparison_lines))

    def test_page_content_changed_file_header_shows_source_filter(self):
        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        lines = page_content.browse_list_screen_lines(
            state,
            argparse_namespace(),
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("Source: staged", "\n".join(lines))

    def test_browse_list_lines_wrapper_passes_source_filter(self):
        lines = _browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            source_filter="staged",
        )

        self.assertIn("Source: staged", "\n".join(lines))

    def test_browse_filter_matches_paths_and_clamps_selection(self):
        changes = [
            FileChange("src/pages/Home.ets", 1, 1),
            FileChange("src/components/Button.ts", 2, 0),
            FileChange("README.md", 1, 0),
        ]
        self.assertEqual(
            [change.path for change in filter_changes_by_query(changes, "BUTTON")],
            ["src/components/Button.ts"],
        )

        state = BrowserState(changes, selected=2)
        state.set_filter("src/")
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/pages/Home.ets", "src/components/Button.ts"],
        )
        self.assertEqual(state.selected, 0)

        state.selected = 99
        state.clamp_selection()
        self.assertEqual(state.selected, 1)

        state.set_filter("missing")
        self.assertEqual(state.visible_changes, [])
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.mode, "list")

    def test_browse_screen_renders_task_problems_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 1)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    kind="build",
                    lines=["src/Foo.ets:12:3 error: bad call"],
                    returncode=1,
                ),
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
        self.assertIn("Scope: worktree > Task Problems", text)
        self.assertIn("Task problems", text)
        self.assertIn("src/Foo.ets:12:3", text)
        self.assertIn("bad call", text)
        self.assertIn("cr:problems> ", text)

    def test_browse_screen_only_measures_visible_list_rows(self):
        changes = [FileChange(f"src/File{index}.ts", 1, 0) for index in range(30)]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(changes)
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=1) as first_line:
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/File0.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertLess(first_line.call_count, len(changes))
        self.assertIn("showing rows", text)
        self.assertIn("File0.ts", text)
        self.assertNotIn("File29.ts", text)

    def test_browse_file_screen_scrolls_long_content(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        full_lines = ["File 1/1  src/Sample.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            top = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )
            state.file_scroll = 10
            lower = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        self.assertEqual(top[:2], ["File 1/1  src/Sample.ts", "line 1"])
        self.assertIn("showing 1-4/20", top[-1])
        self.assertIn("line 11", lower)
        self.assertIn("showing 11-14/20", lower[-1])

    def test_browse_file_screen_shows_review_queue_dock(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 2, 0, source="staged"),
            FileChange("src/Second.ts", 5, 1, source="unstaged"),
            FileChange("src/Third.ts", 1, 3, source="unstaged"),
        ]
        state = BrowserState(
            changes,
            page=BrowserPage.FILE_DETAIL,
            selected=1,
            seen_paths={"src/First.ts"},
            review_notes={"src/Second.ts": "check edge"},
        )
        full_lines = ["File 2/3  src/Second.ts"] + [
            f"line {index}" for index in range(1, 9)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                3,
                args,
                TerminalStyle(False),
                max_lines=14,
            )

        text = "\n".join(lines)
        self.assertIn("Changed files 2/3", text)
        self.assertIn("Progress: 1/3 seen", text)
        self.assertIn("  1 [x] src/First.ts", text)
        self.assertIn("> 2 [ ] src/Second.ts", text)
        self.assertIn("note", text)
        self.assertIn("unstaged", text)
        self.assertIn("+5 -1", text)

    def test_browse_file_screen_omits_review_queue_dock_when_short(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 1, 0),
            FileChange("src/Second.ts", 1, 0),
        ]
        state = BrowserState(changes, page=BrowserPage.FILE_DETAIL, selected=1)
        full_lines = ["File 2/2  src/Second.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                2,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        text = "\n".join(lines)
        self.assertNotIn("Changed files", text)
        self.assertIn("showing 1-4/20", lines[-1])

    def test_browse_file_lines_show_seen_or_todo_status(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        todo_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=False,
                        )
                        seen_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=True,
                        )

        self.assertIn("todo", todo_lines[0])
        self.assertIn("seen", seen_lines[0])

    def test_browse_lines_show_review_notes(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)
        review_notes = {"src/Sample.ts": "check lifecycle edge case"}

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        list_lines = _browse_list_lines(
                            [change],
                            args,
                            TerminalStyle(False),
                            selected=0,
                            review_notes=review_notes,
                        )
                        screen_lines = _browse_list_screen_lines(
                            BrowserState([change], review_notes=review_notes),
                            args,
                            TerminalStyle(False),
                            max_lines=8,
                        )
                        detail_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            review_note=review_notes["src/Sample.ts"],
                        )

        self.assertIn("note", "\n".join(list_lines))
        self.assertIn("note", "\n".join(screen_lines))
        self.assertIn("note: check lifecycle edge case", "\n".join(detail_lines))

if __name__ == "__main__":
    unittest.main()
