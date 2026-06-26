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

class TaskProblemListSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_file_detail_current_file_task_problems(self):
        # Behavior: 当用户在Task Problems中保存「BrowserCommandExecutor 保存 File Detail 当前文件 task 问题」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("sample", encoding="utf-8")
            (source_dir / "Two.ets").write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/Two.ets:3:1 error E3: bad two",
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
                result = executor.execute(
                    parse_browser_command("save file problems tmp/one-problems.md")
                )

            saved = repo / "tmp" / "one-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertIn("1. src/One.ets:1:1 [ERROR E1]", text)
        self.assertNotIn("src/Two.ets", text)
        self.assertIn(
            "Saved 1 task problems for src/One.ets to tmp/one-problems.md.",
            state.status_message,
        )
    def test_browser_command_executor_saves_task_problems_default_path(self):
        # Behavior: 当用户在Task Problems中保存「BrowserCommandExecutor 保存 task 问题 默认 路径」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error TS1: first bad",
                        "src/Two.ets:1:1 warning TS2: second bad",
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
                result = executor.execute(parse_browser_command("save problems"))

            saved = repo / ".cr" / "handoff" / "task-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertIn("1. src/One.ets:1:1 [ERROR TS1]", text)
        self.assertIn("2. src/Two.ets:1:1 [WARNING TS2]", text)
        self.assertIn(
            "Saved 2 task problems to .cr/handoff/task-problems.md.",
            state.status_message,
        )
    def test_browser_command_executor_saves_file_task_problems_requested_path(self):
        # Behavior: 当用户在Task Problems中保存「BrowserCommandExecutor 保存 文件 task 问题 requested 路径」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error TS1: first bad",
                        "src/Two.ets:1:1 error TS2: second bad",
                        "src/Two.ets:1:1 warning TS3: third bad",
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
                result = executor.execute(
                    parse_browser_command("save file problems tmp/two-problems.md")
                )

            saved = repo / "tmp" / "two-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertNotIn("src/One.ets", text)
        self.assertIn("1. src/Two.ets:1:1 [ERROR TS2]", text)
        self.assertIn("2. src/Two.ets:1:1 [WARNING TS3]", text)
        self.assertIn(
            "Saved 2 task problems for src/Two.ets to tmp/two-problems.md.",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
