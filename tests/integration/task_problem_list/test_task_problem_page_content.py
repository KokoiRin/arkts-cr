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


class TaskProblemPageContentTests(unittest.TestCase):

    def test_task_problems_screen_renders_problem_facts(self):
        # Behavior: 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
    def test_browse_screen_renders_task_problems_page(self):
        # Behavior: 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
