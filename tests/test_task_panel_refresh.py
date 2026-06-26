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


class TaskPanelRefreshTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
