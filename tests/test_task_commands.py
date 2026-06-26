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


class TaskCommandTests(unittest.TestCase):
    def test_browser_command_executor_shows_task_diagnostics_without_starting_task(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.task_runtime.task_diagnostic_lines",
                    return_value=["Task commands:", "build: missing"],
                ) as diagnostics:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("tasks"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        diagnostics.assert_called_once_with(repo, args)
        self.assertIn("Task commands:", output.getvalue())
        self.assertIn("build: missing", output.getvalue())

    def test_browser_command_executor_shows_task_schema_help_without_starting_task(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.task_runtime.task_schema_help_lines",
            return_value=["Task preset file: .cr/tasks.json"],
        ) as help_lines:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("tasks help"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        help_lines.assert_called_once_with()
        self.assertIn("Task preset file: .cr/tasks.json", output.getvalue())

    def test_browser_frame_module_owns_task_panel_presentation_implementation(self):
        browser_source = Path(browser_module.__file__).read_text(encoding="utf-8")
        frame_source = Path(frame_module.__file__).read_text(encoding="utf-8")

        self.assertIn("class BrowserFrame", frame_source)
        self.assertIn("class ScreenLayout", frame_source)
        self.assertIn("def task_panel_lines", frame_source)
        self.assertIn("def draw_task_panel_only", frame_source)
        self.assertIn("frame_module.task_panel_lines", browser_source)
        self.assertIn("frame_module.draw_task_panel_only", browser_source)
        self.assertNotIn("shlex.quote", browser_source)
        self.assertNotIn("def task_panel_lines", browser_source)
        self.assertNotIn("def draw_task_panel_only", browser_source)

    def test_background_task_runtime_uses_task_state_names(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertTrue(hasattr(browser_module, "TaskState"))
        self.assertFalse(hasattr(browser_module, "BuildState"))
        self.assertIn('task: "TaskState | None"', source)
        self.assertNotIn('build: "BuildState | None"', source)
        self.assertIn("def _poll_task", source)
        self.assertNotIn("def _poll_build", source)
        self.assertIn("def _task_panel_lines", source)
        self.assertNotIn("def _build_panel_lines", source)

    def test_build_command_detects_douyin_harmony_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")

            self.assertEqual(
                _build_command(repo),
                ["./remote", "buildEntry", "--app", "douyin"],
            )
            self.assertEqual(
                _build_command(repo, "./custom build"),
                ["./custom", "build"],
            )

    def test_task_command_resolves_configured_test_and_lint_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd="./build.sh",
                test_cmd="npm test -- --watch=false",
                lint_cmd="npm run lint",
            )

            self.assertEqual(_task_command(repo, args, "build"), ["./build.sh"])
            self.assertEqual(
                _task_command(repo, args, "test"),
                ["npm", "test", "--", "--watch=false"],
            )
            self.assertEqual(
                _task_command(repo, args, "lint"),
                ["npm", "run", "lint"],
            )

    def test_task_command_does_not_guess_test_or_lint_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            self.assertIsNone(_task_command(repo, args, "test"))
            self.assertIsNone(_task_command(repo, args, "lint"))

    def test_task_panel_collects_background_output(self):
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

    def test_lint_task_without_command_shows_configuration_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=None,
                lint_cmd=None,
            )
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                from cr.ui.browser import _start_task

                _start_task(state, args, "lint")

            self.assertIsNotNone(state.task)
            self.assertEqual(state.task.kind, "lint")
            self.assertEqual(_task_status(state.task), "failed to start")
            self.assertIn(
                "No lint command configured. Set --lint-cmd or CR_LINT_CMD.",
                state.task.lines,
            )

    def test_task_panel_renders_recent_task_history(self):
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
        state = BrowserState([])

        _stop_task(state)
        _record_completed_task(state)

        self.assertEqual(state.task_history, [])

    def test_browse_screen_task_panel_includes_task_history(self):
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

    def test_build_start_records_process_group_id(self):
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

    def test_build_rerun_starts_new_process_after_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            output = repo / "build.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('build.out')\n"
                "path.write_text(path.read_text() + 'run\\n' if path.exists() else 'run\\n')\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)
                self.assertEqual(state.task.returncode, 0)

                _rerun_task(state, args)
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertEqual(state.task.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "run\nrun\n")

    def test_rerun_repeats_recent_test_task_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "test_task.py"
            output = repo / "test.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('test.out')\n"
                "path.write_text(path.read_text() + 'test\\n' if path.exists() else 'test\\n')\n",
                encoding="utf-8",
            )
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=f"{sys.executable} {script}",
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
                self.assertEqual(state.task.kind, "test")
                self.assertEqual(state.task.returncode, 0)

                _rerun_task(state, args)
                self.assertEqual(state.task.kind, "test")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertEqual(state.task.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "test\ntest\n")

    def test_build_rerun_keeps_previous_task_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            output = repo / "build.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('build.out')\n"
                "count = int(path.read_text()) if path.exists() else 0\n"
                "path.write_text(str(count + 1))\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)
                _record_completed_task(state)

                self.assertEqual(len(state.task_history), 1)

                _rerun_task(state, args)

            self.assertEqual(len(state.task_history), 1)
            self.assertEqual(state.task_history[0].status, "succeeded")
            self.assertIsNotNone(state.task)
            self.assertIsNone(state.task.returncode)
            if state.task.running:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            if state.task.process.stdout is not None:
                state.task.process.stdout.close()

    def test_build_rerun_while_running_does_not_start_second_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                first_process = state.task.process

                _rerun_task(state, args)

            self.assertIs(state.task.process, first_process)
            self.assertIn("Build is already running. Stop it before rerun.", state.task.lines)
            _stop_task(state)
            for _ in range(100):
                _poll_task(state.task)
                if state.task.returncode is not None:
                    break
                time.sleep(0.01)

    def test_build_stop_without_running_build_shows_feedback(self):
        state = BrowserState([])

        _stop_task(state)

        self.assertIsNotNone(state.task)
        self.assertEqual(_task_status(state.task), "idle")
        self.assertIn("No build is running.", state.task.lines)

    def test_task_panel_partial_refresh_does_not_clear_screen(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["compile line"])
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                _draw_task_panel_only(build, TerminalStyle(False))

        text = output.getvalue()
        self.assertNotIn("\033[2J", text)
        self.assertIn("\0337", text)
        self.assertIn("\033[7;1H", text)
        self.assertIn("\0338", text)
        self.assertIn("compile line", text)

        output = StringIO()
        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                _draw_task_panel_only(build, TerminalStyle(False))

        self.assertEqual(output.getvalue(), "")
        process.wait(timeout=1)

    def test_full_browser_redraw_primes_task_panel_frame_cache(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        frame = BrowserFrame()
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False), frame)

                    output = StringIO()
                    with redirect_stdout(output):
                        refreshed = _draw_task_panel_only(
                            state.task,
                            TerminalStyle(False),
                            frame,
                        )

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        process.wait(timeout=1)

    def test_task_panel_partial_refresh_refuses_stale_frame_layout(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=False,
        )
        build.last_rendered_panel = ["old panel"]
        build.lines.append("new line")
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 30)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_task_panel_partial_refresh_refuses_dirty_frame(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=True,
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_browser_status_message_marks_frame_dirty_before_task_refresh(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=False,
        )
        state = BrowserState([], task=build)
        output = StringIO()

        _show_browser_message(state, "Opened src/Sample.ts:3", raw_keys=True, frame=frame)

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertEqual(state.status_message, "Opened src/Sample.ts:3")
        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_browser_test_command_starts_background_test_task(self):
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
            build_cmd=None,
            test_cmd="echo test",
            lint_cmd=None,
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["test", "q"],
                                ):
                                    with patch("cr.ui.browser._draw_browse_screen"):
                                        with patch("cr.ui.browser._start_task") as start_task:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(start_task.call_args.args[2], "test")


if __name__ == "__main__":
    unittest.main()
