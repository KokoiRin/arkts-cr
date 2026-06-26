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

class TaskProblemSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_selected_task_problem_default_path(self):
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
                problem_scroll=1,
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
                result = executor.execute(parse_browser_command("save problem"))

            saved = repo / ".cr" / "handoff" / "task-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.problem_scroll, 1)
        self.assertIn("src/Two.ets:1:1", text)
        self.assertIn("Severity: warning", text)
        self.assertIn("Code: TS2", text)
        self.assertIn("second bad", text)
        self.assertIn(
            "Saved task problem to .cr/handoff/task-problem.md.",
            state.status_message,
        )
    def test_browser_command_executor_saves_source_file_current_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
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
                    parse_browser_command("save problem tmp/source-problem.md")
                )

            saved = repo / "tmp" / "source-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Foo.ets:2:1", text)
        self.assertIn("Severity: error", text)
        self.assertIn("Code: TS123", text)
        self.assertIn("bad value", text)
        self.assertIn(
            "Saved source problem to tmp/source-problem.md.",
            state.status_message,
        )
    def test_browser_command_executor_does_not_save_stale_source_file_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
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
                    parse_browser_command("save problem tmp/source-problem.md")
                )

            saved = repo / "tmp" / "source-problem.md"

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertFalse(saved.exists())
        self.assertIn("No current source problem to save.", state.status_message)
    def test_browser_command_executor_saves_file_detail_current_row_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:4:1 warning W1: warn one",
                        "src/Two.ets:2:1 error E2: bad two",
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
            lines = [
                "File 1/1  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command(
                            "save problem tmp/file-detail-problem.md",
                            raw_keys=True,
                        )
                    )

            saved = repo / "tmp" / "file-detail-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/One.ets:4:1", text)
        self.assertIn("Severity: warning", text)
        self.assertIn("Code: W1", text)
        self.assertIn("warn one", text)
        self.assertNotIn("src/Two.ets", text)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn(
            "Saved file problem src/One.ets:4 to tmp/file-detail-problem.md.",
            state.status_message,
        )
    def test_browser_command_executor_saves_file_detail_current_file_task_problems(self):
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
