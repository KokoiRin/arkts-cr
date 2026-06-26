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


class TaskRerunTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
