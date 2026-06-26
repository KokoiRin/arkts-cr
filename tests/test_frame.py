import os
import subprocess
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from cr.ui import frame
from cr.ui.tasks import TaskRecord, TaskState
from cr.ui.terminal import TerminalStyle


class BrowserFrameTests(unittest.TestCase):
    def test_task_panel_lines_include_current_task_and_recent_history(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        task = TaskState(["./build.sh"], process, lines=["compile line"], returncode=0)

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            layout = frame.screen_layout(task)
            lines = frame.task_panel_lines(
                task,
                TerminalStyle(False),
                layout.task_height,
                [
                    TaskRecord(
                        kind="build",
                        status="succeeded",
                        command=["./old-build.sh"],
                        returncode=0,
                    )
                ],
            )

        self.assertEqual(layout.prompt_row, 12)
        self.assertGreaterEqual(layout.task_height, 3)
        text = "\n".join(lines)
        self.assertIn("Build succeeded", text)
        self.assertIn("Recent: build succeeded ./old-build.sh", text)
        self.assertIn("compile line", text)

    def test_partial_task_panel_refresh_draws_without_full_clear_once(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        task = TaskState(["true"], process, lines=["compile line"])
        browser_frame = frame.BrowserFrame(
            layout=frame.screen_layout(task, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                refreshed = frame.draw_task_panel_only(
                    task,
                    TerminalStyle(False),
                    browser_frame,
                )
            second_output = StringIO()
            with redirect_stdout(second_output):
                second_refreshed = frame.draw_task_panel_only(
                    task,
                    TerminalStyle(False),
                    browser_frame,
                )

        text = output.getvalue()
        self.assertTrue(refreshed)
        self.assertNotIn("\033[2J", text)
        self.assertIn("\0337", text)
        self.assertIn("\033[7;1H", text)
        self.assertIn("\0338", text)
        self.assertIn("compile line", text)
        self.assertFalse(second_refreshed)
        self.assertEqual(second_output.getvalue(), "")
        process.wait(timeout=1)

    def test_partial_task_panel_refresh_refuses_dirty_frame(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        task = TaskState(["true"], process, lines=["compile line"])
        browser_frame = frame.BrowserFrame(
            layout=frame.screen_layout(task, rows=12),
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
                refreshed = frame.draw_task_panel_only(
                    task,
                    TerminalStyle(False),
                    browser_frame,
                )

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(browser_frame.dirty)
        process.wait(timeout=1)

    def test_terminal_line_fitting_counts_visible_width(self):
        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((8, 12)),
        ):
            self.assertEqual(frame.fit_terminal_line("abcdefghi"), "abcdefg")
            self.assertEqual(
                frame.fit_terminal_line("\033[31mabcdefghi\033[0m"),
                "\033[31mabcdefghi\033[0m",
            )


if __name__ == "__main__":
    unittest.main()
