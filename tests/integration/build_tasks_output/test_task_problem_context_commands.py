import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
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


class TaskProblemContextCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_task_problem_context_with_diff(self):
        # Behavior: 当用户在Task Panel / Task Output中复制「BrowserCommandExecutor 复制 Task Problems 上下文 with diff」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 10)),
                encoding="utf-8",
            )
            change = FileChange("src/Foo.ets", 2, 1)
            state = BrowserState(
                [change],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "compile started",
                        "src/Foo.ets:5:1 error TS2322: bad call",
                        "compile failed",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets\n\n```diff\n+line 5\n```",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem context")
                            )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Problem Context: src/Foo.ets:5", copied)
        self.assertIn("## Problem", copied)
        self.assertIn("Severity: error", copied)
        self.assertIn("Code: TS2322", copied)
        self.assertIn("bad call", copied)
        self.assertIn("## Source", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("## Task Output", copied)
        self.assertIn("  1  compile started", copied)
        self.assertIn("> 2  src/Foo.ets:5:1 error TS2322: bad call", copied)
        self.assertIn("  3  compile failed", copied)
        self.assertIn("## Diff", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
        self.assertNotIn("No diff in current review scope.", copied)
        build_data.assert_called_once()
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied problem context src/Foo.ets:5", state.status_message)
    def test_browser_command_executor_copies_selected_task_output_problem_context(self):
        # Behavior: 当用户在Task Panel / Task Output中复制「BrowserCommandExecutor 复制 选中 Task Output Problem Context」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "compile started",
                        "src/One.ets:2:1 error TS1: first bad",
                        "compile continued",
                        "src/Two.ets:2:1 error TS2: second bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(
                        parse_browser_command("copy problem context")
                    )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Problem Context: src/Two.ets:2", copied)
        self.assertIn("second bad", copied)
        self.assertIn("## Task Output", copied)
        self.assertIn("  3  compile continued", copied)
        self.assertIn("> 4  src/Two.ets:2:1 error TS2: second bad", copied)
        self.assertIn("> 2  beta", copied)
        self.assertNotIn("first bad", copied)
        self.assertIn("Copied problem context src/Two.ets:2", state.status_message)
    def test_browser_command_executor_saves_selected_task_output_problem_context(self):
        # Behavior: 当用户在Task Panel / Task Output中保存「BrowserCommandExecutor 保存 选中 Task Output Problem Context」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:2:1 error TS1: first bad",
                        "src/Two.ets:2:1 error TS2: second bad",
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
                    parse_browser_command("save problem context tmp/task-first.md")
                )

            saved = repo / "tmp" / "task-first.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Problem Context: src/Two.ets:2", text)
        self.assertIn("second bad", text)
        self.assertIn("## Task Output", text)
        self.assertIn("> 2  src/Two.ets:2:1 error TS2: second bad", text)
        self.assertIn("Saved problem context to tmp/task-first.md", state.status_message)
    def test_browser_command_executor_saves_task_problem_context(self):
        # Behavior: 当用户在Task Panel / Task Output中保存「BrowserCommandExecutor 保存 Task Problems 上下文」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 10)),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:5:1 error TS2322: bad call"],
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
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
                    ):
                        result = executor.execute(
                            parse_browser_command("save problem context tmp/problem.md")
                        )

            saved = repo / "tmp" / "problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("# Problem Context: src/Foo.ets:5", text)
        self.assertIn("Severity: error", text)
        self.assertIn("> 5  line 5", text)
        self.assertIn("# File Diff: src/Foo.ets", text)
        self.assertIn("Saved problem context to tmp/problem.md.", state.status_message)

if __name__ == "__main__":
    unittest.main()
