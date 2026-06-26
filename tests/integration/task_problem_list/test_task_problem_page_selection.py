import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import task_problems
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
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

class TaskProblemPageSelectionTests(unittest.TestCase):

    def test_browser_command_executor_moves_task_problem_selection(self):
        # Behavior: 当用户在Task Problems中选择「BrowserCommandExecutor 移动 Task Problems 选择」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                        "src/Three.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                down = executor.execute(parse_browser_command("down", raw_keys=True))
                selected_after_down = state.problem_selected
                end = executor.execute(parse_browser_command("end", raw_keys=True))
                selected_after_end = state.problem_selected
                home = executor.execute(parse_browser_command("home", raw_keys=True))

        self.assertTrue(down.needs_redraw)
        self.assertTrue(end.needs_redraw)
        self.assertTrue(home.needs_redraw)
        self.assertEqual(selected_after_down, 1)
        self.assertEqual(selected_after_end, 2)
        self.assertEqual(state.problem_selected, 0)
    def test_browser_command_executor_jumps_to_next_task_problem_file(self):
        # Behavior: 当用户在Task Problems中导航「BrowserCommandExecutor 跳转 to next Task Problems 文件」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/One.ets:2:1 warning",
                        "src/Two.ets:3:1 error",
                        "src/Three.ets:4:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("next problem file"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 2)
    def test_browser_command_executor_jumps_to_previous_task_problem_file(self):
        # Behavior: 当用户在Task Problems中导航「BrowserCommandExecutor 跳转 to previous Task Problems 文件」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=4,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                        "src/Two.ets:3:1 warning",
                        "src/Three.ets:4:1 error",
                        "src/Three.ets:5:1 warning",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("prev problem file"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.problem_selected, 1)
    def test_browser_command_executor_jumps_between_visible_task_problem_files(self):
        # Behavior: 当用户在Task Problems中导航「BrowserCommandExecutor 跳转 between 可见 Task Problems 文件」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_filter="error",
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/Two.ets:2:1 warning W2: skipped",
                        "src/Three.ets:3:1 error E3: bad three",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("next problem file"))

        self.assertTrue(result.handled)
        self.assertEqual(state.problem_selected, 1)
    def test_browser_command_executor_keeps_task_problem_selection_at_file_edges(self):
        # Behavior: 当用户在Task Problems中选择「BrowserCommandExecutor keeps Task Problems 选择 at 文件 edges」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_result = executor.execute(parse_browser_command("next problem file"))
                next_message = state.status_message
                selected_after_next = state.problem_selected
                state.problem_selected = 0
                prev_result = executor.execute(parse_browser_command("prev problem file"))
                previous_message = state.status_message

        self.assertTrue(next_result.handled)
        self.assertTrue(prev_result.handled)
        self.assertEqual(selected_after_next, 1)
        self.assertIn("已经在最后一个问题文件。", next_message)
        self.assertEqual(state.problem_selected, 0)
        self.assertIn("已经在第一个问题文件。", previous_message)

if __name__ == "__main__":
    unittest.main()
