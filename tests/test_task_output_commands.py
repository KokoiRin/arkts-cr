import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import input as browser_input
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
    _draw_browse_screen,
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


class TaskOutputCommandTests(unittest.TestCase):
    def test_browser_command_executor_finds_text_in_task_output(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["compile ok", "\033[31mERROR target\033[0m", "done"],
                returncode=1,
            ),
            file_find_text="file-query",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._max_task_output_scroll", return_value=10):
            result = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(state.task_scroll, 1)
        self.assertEqual(state.task_find_text, "target")
        self.assertEqual(state.file_find_text, "file-query")
        self.assertIn('Found "target" at line 2.', state.status_message)

    def test_browser_command_executor_repeats_task_output_find_matches(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["target first", "context", "target second"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._max_task_output_scroll", return_value=10):
            find = executor.execute(parse_browser_command("find target", raw_keys=True))
            next_match = executor.execute(
                parse_browser_command("next match", raw_keys=True)
            )
            scroll_after_next = state.task_scroll
            previous_match = executor.execute(
                parse_browser_command("prev match", raw_keys=True)
            )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(scroll_after_next, 2)
        self.assertEqual(state.task_scroll, 0)
        self.assertEqual(state.task_find_text, "target")
        self.assertIn('Found "target" at line 1.', state.status_message)

    def test_browser_command_executor_reports_task_output_find_empty_states(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_OUTPUT)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        no_task = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(no_task.handled)
        self.assertTrue(no_task.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertIn("No task output to find.", state.status_message)

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state.task = TaskState(["./build.sh"], process, lines=["compile ok"])
        empty = executor.execute(parse_browser_command("find", raw_keys=True))
        missing = executor.execute(parse_browser_command("find owner", raw_keys=True))
        repeat = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertTrue(repeat.needs_redraw)
        self.assertEqual(state.task_find_text, "owner")
        self.assertIn('No matches for "owner".', state.status_message)

    def test_browser_command_executor_copies_task_output(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            task=TaskState(
                ["npm", "test"],
                process,
                kind="test",
                lines=["failed test"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Test output", copied_text)
        self.assertIn("failed test", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output.", output.getvalue())

    def test_browser_command_executor_copy_task_reports_empty_state(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("No task output to copy.", output.getvalue())

    def test_browser_command_executor_copies_task_output_tail(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 7)],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task tail 2"))

        self.assertTrue(result.handled)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Build output tail", copied_text)
        self.assertNotIn("line 4", copied_text)
        self.assertIn("line 5", copied_text)
        self.assertIn("line 6", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output tail.", output.getvalue())

    def test_browser_command_executor_copy_task_tail_reports_empty_state(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task tail"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("No task output tail to copy.", output.getvalue())

    def test_browser_command_executor_copies_task_output_match(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task_scroll=4,
            task_find_text="target",
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 4)]
                + ["before target", "target failure", "after target"]
                + [f"line {index}" for index in range(7, 10)],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task match"))

        self.assertTrue(result.handled)
        copied_text = copy.call_args.args[0]
        self.assertIn("# Build output match", copied_text)
        self.assertIn("Query: target", copied_text)
        self.assertIn("  4  before target", copied_text)
        self.assertIn("> 5  target failure", copied_text)
        self.assertIn("  6  after target", copied_text)
        self.assertNotIn("line 9", copied_text)
        self.assertEqual(copy.call_args.args[1], "copy-tool")
        self.assertIn("Copied task output match.", output.getvalue())

    def test_browser_command_executor_copy_task_match_requires_find(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["target failure"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy task match"))

        self.assertTrue(result.handled)
        copy.assert_not_called()
        self.assertIn("Run find TEXT first.", output.getvalue())

    def test_browser_command_executor_saves_task_output(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=["compile line"],
                returncode=0,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task tmp/task.md"))

            target = repo / "tmp" / "task.md"
            self.assertTrue(result.handled)
            self.assertIn("# Build output", target.read_text(encoding="utf-8"))
            self.assertIn("Saved task output to tmp/task.md", output.getvalue())

    def test_browser_command_executor_saves_task_output_tail(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=[f"line {index}" for index in range(1, 45)],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task tail"))

            target = repo / ".cr" / "handoff" / "task-output-tail.md"
            saved_text = target.read_text(encoding="utf-8")
            self.assertTrue(result.handled)
            self.assertIn("# Build output tail", saved_text)
            self.assertNotIn("\nline 4\n", saved_text)
            self.assertIn("line 44", saved_text)
            self.assertIn(
                "Saved task output tail to .cr/handoff/task-output-tail.md",
                output.getvalue(),
            )

    def test_browser_command_executor_saves_task_output_match_default_path(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task_scroll=1,
            task_find_text="target",
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=["compile started", "target failure", "compile stopped"],
                returncode=1,
            ),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task match"))

            target = repo / ".cr" / "handoff" / "task-output-match.md"
            saved_text = target.read_text(encoding="utf-8")
            self.assertTrue(result.handled)
            self.assertIn("# Build output match", saved_text)
            self.assertIn("> 2  target failure", saved_text)
            self.assertIn(
                "Saved task output match to .cr/handoff/task-output-match.md",
                output.getvalue(),
            )

    def test_browser_command_executor_save_task_tail_reports_empty_state(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task tail"))

            self.assertTrue(result.handled)
            self.assertFalse((repo / ".cr").exists())
            self.assertIn("No task output tail to save.", output.getvalue())

    def test_browser_command_executor_save_task_reports_empty_state(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("save task"))

            self.assertTrue(result.handled)
            self.assertFalse((repo / ".cr").exists())
            self.assertIn("No task output to save.", output.getvalue())

    def test_browser_command_executor_opens_task_output_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=12,
            task_scroll=9,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("task output"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(state.task_scroll, 0)

        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 12)

    def test_browser_command_executor_moves_task_output_problem_selection(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (source_dir / name).write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "plain line",
                        "src/Two.ets:2:1 error",
                        "plain line",
                        "src/Three.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(False),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_result = executor.execute(parse_browser_command("next problem"))
                selected_after_next = state.problem_selected
                scroll_after_next = state.task_scroll
                prev_result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertEqual(selected_after_next, 1)
        self.assertGreaterEqual(scroll_after_next, 1)
        self.assertTrue(prev_result.handled)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)

    def test_browser_command_executor_views_selected_task_output_problem_source(self):
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
                        "src/One.ets:2:1 error",
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
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.problem_selected, 1)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)

    def test_browser_command_executor_reports_task_output_view_without_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(["./build.sh"], process, lines=["plain failure"]),
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertIn("No task problem to view.", state.status_message)

    def test_browser_command_executor_scrolls_task_output_page(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                lines=[f"line {index}" for index in range(30)],
                returncode=0,
            ),
            page=BrowserPage.TASK_OUTPUT,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(False),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            page_down = executor.execute(parse_browser_command("pagedown"))
            self.assertTrue(page_down.needs_redraw)
            self.assertGreater(state.task_scroll, 0)

            executor.execute(parse_browser_command("home"))
            self.assertEqual(state.task_scroll, 0)

            executor.execute(parse_browser_command("end"))
            self.assertGreater(state.task_scroll, 0)

    def test_browse_screen_renders_task_output_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.TASK_OUTPUT,
            task=TaskState(
                ["./build.sh"],
                process,
                kind="build",
                lines=["compile line"],
                returncode=0,
            ),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Task Output", text)
        self.assertIn("Task output", text)
        self.assertIn("compile line", text)
        self.assertIn("cr:task> ", text)

    def test_task_output_page_tick_redraws_main_content_not_panel_only(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        processes: list[subprocess.Popen[bytes]] = []

        def start_running_task(state, _args, _kind):
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            state.task = TaskState(["sleep"], process, lines=["first line"])

        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                with patch("cr.ui.browser.git.repo_root", return_value=repo):
                    with patch(
                        "cr.ui.browser._should_restore_browser_workspace_state",
                        return_value=False,
                    ):
                        with patch(
                            "cr.ui.browser._load_browse_changes",
                            return_value=[FileChange("src/Sample.ts", 1, 1)],
                        ):
                            with patch("cr.ui.browser._show_commits_when_empty"):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "build",
                                            "task output",
                                            browser_input.TICK,
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._start_task",
                                            side_effect=start_running_task,
                                        ):
                                            with patch(
                                                "cr.ui.browser._draw_browse_screen"
                                            ) as draw:
                                                with patch(
                                                    "cr.ui.browser._draw_task_panel_only"
                                                ) as panel_only:
                                                    from cr.ui.browser import run_browser

                                                    result = run_browser(args)
        finally:
            for process in processes:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)

        self.assertEqual(result, 0)
        self.assertGreaterEqual(draw.call_count, 4)
        panel_only.assert_not_called()


if __name__ == "__main__":
    unittest.main()
