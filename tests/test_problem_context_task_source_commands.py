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


class TaskAndSourceProblemContextCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_task_problem_context_with_diff(self):
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
    def test_browser_command_executor_copies_source_page_problem_context(self):
        from cr.ui.browser import parse_browser_command

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
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
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
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
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
        self.assertNotIn("## Problem", copied)
        self.assertIn("  4  line 4", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 3", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_copies_source_page_problem_context_with_current_problem(self):
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
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
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
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
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
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_copies_selected_source_problem_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
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
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
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
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_copies_selected_source_problem_context_with_current_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:5:1 warning W1: warn call"],
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
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
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
        self.assertIn("## Problem", copied)
        self.assertIn("Severity: warning", copied)
        self.assertIn("Code: W1", copied)
        self.assertIn("warn call", copied)
        self.assertIn("## Task Output", copied)
        self.assertIn("> 1  src/Foo.ets:5:1 warning W1: warn call", copied)
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_saves_selected_source_problem_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_selection_start=3,
                source_selection_end=6,
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
                    parse_browser_command("save problem context tmp/source-selected.md")
                )

            saved = repo / "tmp" / "source-selected.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:3-6", text)
        self.assertIn("> 5  line 5", text)
        self.assertNotIn("line 2", text)
        self.assertNotIn("line 7", text)
        self.assertIn("Saved problem context to tmp/source-selected.md", state.status_message)
    def test_browser_command_executor_does_not_use_stale_source_problem_for_context(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            other = repo / "src" / "Other.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 10)),
                encoding="utf-8",
            )
            other.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1), FileChange("src/Other.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:2:1 error TS9: other bad"],
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
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
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
        self.assertIn("## Source", copied)
        self.assertIn("## Diff", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertNotIn("src/Other.ets", copied)
        self.assertNotIn("other bad", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)
    def test_browser_command_executor_copies_problem_context_without_diff(self):
        from cr.ui.browser import parse_browser_command

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
        self.assertIn("# Problem Context: src/Foo.ets:2", copied)
        self.assertIn("No diff in current review scope.", copied)
        self.assertIn("Copied problem context src/Foo.ets:2", state.status_message)
    def test_browser_command_executor_reports_empty_problem_context_copy(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy problem context"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No problem context to copy.", state.status_message)
    def test_browser_command_executor_reports_missing_problem_context_source(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Missing.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(
                        parse_browser_command("copy problem context")
                    )

        self.assertTrue(result.handled)
        copy_text.assert_not_called()
        self.assertIn("Source file not found.", state.status_message)
    def test_browser_command_executor_saves_task_problem_context(self):
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
    def test_browser_command_executor_saves_source_page_problem_context_default_path(self):
        from cr.ui.browser import parse_browser_command

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
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save problem context"))

            saved = repo / ".cr" / "handoff" / "problem-context.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Problem Context: src/Foo.ets:2", text)
        self.assertIn("> 2  two", text)
        self.assertIn("No diff in current review scope.", text)
        self.assertIn(
            "Saved problem context to .cr/handoff/problem-context.md.",
            state.status_message,
        )
    def test_browser_command_executor_reports_empty_problem_context_save(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.handoff_module.save_problem_context_text") as save_text:
            result = executor.execute(parse_browser_command("save problem context"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        save_text.assert_not_called()
        self.assertIn("No problem context to save.", state.status_message)
    def test_browser_command_executor_reports_problem_context_save_failure(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=4,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            failure = handoff_module.HandoffSaveResult(
                repo / "blocked" / "problem.md",
                "blocked/problem.md",
                "Could not save problem context to blocked/problem.md: denied",
            )
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.handoff_module.save_problem_context_text",
                    return_value=failure,
                ):
                    result = executor.execute(
                        parse_browser_command("save problem context blocked/problem.md")
                    )

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Foo.ets")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 4)
        self.assertIn(
            "Could not save problem context to blocked/problem.md: denied",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
