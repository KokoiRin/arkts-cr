import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui import frame as frame_module
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    TaskRecord,
    TaskState,
    _build_command,
    _draw_browse_screen,
    _draw_task_panel_only,
    _poll_task,
    _record_completed_task,
    _rerun_task,
    _screen_layout,
    _show_browser_message,
    _start_task,
    _stop_task,
    _task_command,
    _task_panel_lines,
    _task_status,
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


class TaskOutputHistoryTests(unittest.TestCase):
    def test_task_panel_collects_background_output(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = (
                f"{sys.executable} -c "
                "\"print('compile line 1'); print('compile line 2')\""
            )
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task)
            if state.task.returncode is None:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            self.assertEqual(state.task.returncode, 0)
            _poll_task(state.task)
            lines = _task_panel_lines(state.task, TerminalStyle(False), 5)
            text = "\n".join(lines)
            self.assertIn("Build succeeded.", text)
            self.assertIn("compile line 1", text)
            self.assertIn("compile line 2", text)
    def test_test_task_collects_background_output_and_history(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"print('test line')\""
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=command,
                lint_cmd=None,
            )
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                from cr.ui.browser import _start_task

                _start_task(state, args, "test")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task)
            if state.task.returncode is None:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            self.assertEqual(state.task.returncode, 0)
            _poll_task(state.task)
            _record_completed_task(state)
            lines = _task_panel_lines(state.task, TerminalStyle(False), 5)
            text = "\n".join(lines)
            self.assertIn("Test succeeded.", text)
            self.assertIn("test line", text)
            self.assertEqual(state.task_history[0].kind, "test")
    def test_task_panel_renders_recent_task_history(self):
        # Behavior: 当用户在task output中渲染任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        build = TaskState(
            ["./build.sh"],
            process,
            lines=["compile line"],
            returncode=0,
        )
        history = [
            TaskRecord(
                kind="build",
                status="failed (1)",
                command=["./build.sh"],
                returncode=1,
            )
        ]

        lines = _task_panel_lines(build, TerminalStyle(False), 6, history)
        text = "\n".join(lines)

        self.assertIn("Recent: build failed (1) ./build.sh", text)
        self.assertIn("compile line", text)
    def test_completed_build_records_task_history_once(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["Build succeeded."],
                returncode=0,
            ),
        )

        _record_completed_task(state)
        _record_completed_task(state)

        self.assertEqual(len(state.task_history), 1)
        self.assertEqual(state.task_history[0].kind, "build")
        self.assertEqual(state.task_history[0].status, "succeeded")
        self.assertEqual(state.task_history[0].returncode, 0)
    def test_stop_without_running_build_does_not_record_task_history(self):
        # Behavior: 当用户在task output遇到缺少前置条件、任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        state = BrowserState([])

        _stop_task(state)
        _record_completed_task(state)

        self.assertEqual(state.task_history, [])
    def test_browse_screen_task_panel_includes_task_history(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
            task=TaskState(["./build.sh"], process, lines=["compile line"]),
            task_history=[
                TaskRecord(
                    kind="build",
                    status="succeeded",
                    command=["./old-build.sh"],
                    returncode=0,
                )
            ],
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Recent: build succeeded ./old-build.sh", text)

if __name__ == "__main__":
    unittest.main()
