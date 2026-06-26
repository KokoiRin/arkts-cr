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


class TaskOutputPageContentTests(unittest.TestCase):

    def test_task_output_screen_renders_current_task(self):
        # Behavior: 当用户在Task Panel / Task Output中查看「Task Output screen 渲染 当前 task」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
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
        # Behavior: 当用户在Task Panel / Task Output中查看「Task Output screen 渲染 选中 问题」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
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
        # Behavior: 当用户在Task Panel / Task Output中查看「Task Output screen 渲染 空态 状态」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        state = BrowserState([])

        lines = page_content.task_output_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=6,
        )
        text = "\n".join(lines)

        self.assertIn("No current task output.", text)
        self.assertIn("Run build, test, or lint", text)

if __name__ == "__main__":
    unittest.main()
