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


class TaskStopLifecycleTests(unittest.TestCase):
    def test_build_start_records_process_group_id(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「build start records process group id」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")

            self.assertIsNotNone(state.task)
            try:
                self.assertEqual(
                    state.task.process_group_id,
                    state.task.process.pid,
                )
            finally:
                if state.task.running:
                    state.task.process.terminate()
                    state.task.process.wait(timeout=1)
                if state.task.process.stdout is not None:
                    state.task.process.stdout.close()
    def test_build_stop_terminates_child_processes(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「build stop terminates child processes」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            child_pid_file = repo / "child.pid"
            script.write_text(
                "from pathlib import Path\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                "Path('child.pid').write_text(str(child.pid))\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])
            child_pid: int | None = None

            def pid_is_running(pid: int) -> bool:
                try:
                    os.kill(pid, 0)
                except OSError:
                    return False
                return True

            try:
                with patch("cr.ui.browser.git.repo_root", return_value=repo):
                    _start_task(state, args, "build")
                    self.assertIsNotNone(state.task)
                    for _ in range(100):
                        if child_pid_file.exists():
                            child_pid = int(child_pid_file.read_text(encoding="utf-8"))
                            break
                        time.sleep(0.01)
                    self.assertIsNotNone(child_pid)
                    self.assertTrue(pid_is_running(child_pid))

                    _stop_task(state)
                    for _ in range(100):
                        _poll_task(state.task)
                        if state.task.returncode is not None and not pid_is_running(child_pid):
                            break
                        time.sleep(0.01)

                self.assertFalse(pid_is_running(child_pid))
            finally:
                if child_pid is not None and pid_is_running(child_pid):
                    os.kill(child_pid, signal.SIGKILL)
                if state.task is not None and state.task.running:
                    state.task.process.terminate()
                    state.task.process.wait(timeout=1)
    def test_build_stop_falls_back_when_process_group_stop_fails(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「build stop 回退 返回 when process group stop fails」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                with patch(
                    "cr.ui.tasks.os.killpg",
                    side_effect=OSError("pg gone"),
                ):
                    _stop_task(state)
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            try:
                self.assertIsNotNone(state.task.returncode)
                self.assertEqual(_task_status(state.task), "stopped")
                self.assertTrue(
                    any(
                        "Build process group stop failed: pg gone" in line
                        for line in state.task.lines
                    )
                )
            finally:
                if state.task is not None and state.task.running:
                    state.task.process.kill()
    def test_poll_escalates_stopped_build_to_process_group_kill(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「poll escalates stopped build to process group kill」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

            def kill(self):
                raise AssertionError("process.kill should not be used with a process group")

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_called_once_with(1234, signal.SIGKILL)
        self.assertTrue(build.stop_escalated)
        self.assertIn("Build did not stop; force killing process group.", build.lines)
    def test_poll_does_not_escalate_stopped_build_within_grace_period(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「poll 不会 escalate stopped build within grace period」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

            def kill(self):
                raise AssertionError("process.kill should not run inside grace period")

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=9.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_not_called()
        self.assertFalse(build.stop_escalated)
        self.assertEqual(build.lines, [])
    def test_poll_escalates_stopped_build_only_once(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「poll escalates stopped build 只读 once」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)
                _poll_task(build)

        killpg.assert_called_once_with(1234, signal.SIGKILL)
        self.assertEqual(
            build.lines.count("Build did not stop; force killing process group."),
            1,
        )
    def test_poll_escalates_stopped_build_without_process_group_to_process_kill(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「poll escalates stopped build 不包含 process group to process kill」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        class RunningProcess:
            stdout = None

            def __init__(self):
                self.kill_count = 0

            def poll(self):
                return None

            def kill(self):
                self.kill_count += 1

        process = RunningProcess()
        build = TaskState(
            ["fake-build"],
            process,
            process_group_id=None,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_not_called()
        self.assertEqual(process.kill_count, 1)
        self.assertTrue(build.stop_escalated)
        self.assertIn("Build did not stop; force killing build process.", build.lines)
    def test_build_stop_records_stop_request_time(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「build stop records stop request time」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                before_stop = time.monotonic()
                _stop_task(state)
                after_stop = time.monotonic()

            try:
                self.assertGreaterEqual(state.task.stop_requested_at, before_stop)
                self.assertLessEqual(state.task.stop_requested_at, after_stop)
                self.assertFalse(state.task.stop_escalated)
            finally:
                if state.task is not None and state.task.running:
                    state.task.process.kill()
                    state.task.process.wait(timeout=1)
                if state.task.process.stdout is not None:
                    state.task.process.stdout.close()
    def test_build_stop_marks_stopped_not_failed(self):
        # Behavior: 当用户在Task Panel / Task Output中标记「build stop 标记 stopped 不 失败」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                self.assertTrue(state.task.running)

                _stop_task(state)
                self.assertTrue(state.task.stop_requested)
                self.assertEqual(_task_status(state.task), "stopping")
                self.assertIn("Stopping build...", state.task.lines)

                for _ in range(100):
                    _poll_task(state.task)
                    if state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task.returncode)
            self.assertEqual(_task_status(state.task), "stopped")
            self.assertIn("Build stopped.", state.task.lines)
    def test_build_stop_without_running_build_shows_feedback(self):
        # Behavior: 当用户在Task Panel / Task Output中查看「build stop 不包含 running build 显示 feedback」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        state = BrowserState([])

        _stop_task(state)

        self.assertIsNotNone(state.task)
        self.assertEqual(_task_status(state.task), "idle")
        self.assertIn("No build is running.", state.task.lines)

if __name__ == "__main__":
    unittest.main()
