import os
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from cr.ui import frame
from cr.ui.browser import BrowserState, _draw_browse_screen, _screen_layout
from cr.ui.tasks import TaskRecord, TaskState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class BrowserFrameTests(unittest.TestCase):
    def test_task_panel_lines_include_current_task_and_recent_history(self):
        # Behavior: 当用户在navigation中验证frame、panel、lines、include时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在产品行为遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在产品行为中刷新frame、partial、panel、refresh时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当系统处理产品行为的frame、terminal、line、fitting时，系统应统计出正确结果 [Requirement: TODO]
        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((8, 12)),
        ):
            self.assertEqual(frame.fit_terminal_line("abcdefghi"), "abcdefg")
            self.assertEqual(
                frame.fit_terminal_line("\033[31mabcdefghi\033[0m"),
                "\033[31mabcdefghi\033[0m",
            )

    def test_screen_layout_reserves_prompt_and_task_panel_regions(self):
        # Behavior: 当用户在产品行为中验证frame、layout、reserves、prompt时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["compile line"])

        plain = _screen_layout(None, rows=12)
        with_task = _screen_layout(build, rows=12)

        self.assertEqual(plain.prompt_row, 12)
        self.assertEqual(plain.content_height, 11)
        self.assertEqual(plain.task_height, 0)
        self.assertIsNone(plain.task_start_row)
        self.assertEqual(with_task.prompt_row, 12)
        self.assertEqual(with_task.task_start_row, 7)
        self.assertEqual(with_task.task_height, 5)
        self.assertEqual(with_task.content_height, 6)
        process.wait(timeout=1)

    def test_browse_screen_redraws_in_place(self):
        # Behavior: 当用户在产品行为中验证frame、browse、redraws、place时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertTrue(text.startswith("\033[2J\033[H"))
        self.assertIn("Scope: worktree > Files", text)
        self.assertIn("> 1", text)
        self.assertIn("└─ src", text)
        self.assertIn("└─ Sample.ts", text)
        self.assertIn("操作：Enter 打开", text)

    def test_browse_screen_action_bar_coexists_with_task_panel(self):
        # Behavior: 当用户在产品行为中验证frame、browse、action、bar时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((80, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("操作：Enter 打开", text)
        self.assertIn("compile line", text)
        self.assertIn("Build running", text)

    def test_browse_screen_places_task_panel_above_prompt(self):
        # Behavior: 当用户在产品行为中验证frame、browse、places、panel时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        self.assertIn("compile line", text)
        self.assertIn("\033[12;1H\033[2Kcr:list> ", text)
        process.wait(timeout=1)

    def test_browse_screen_pads_short_content_before_task_panel(self):
        # Behavior: 当用户在产品行为中验证frame、browse、pads、short时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 30)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        before_panel = text.split("Build running", 1)[0]
        process.wait(timeout=1)
        self.assertEqual(before_panel.count("\n"), 23)

    def test_browse_screen_shows_command_list_with_task_panel(self):
        # Behavior: 当用户在产品行为中展示frame、browse、shows、list时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
            page="commands",
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 40)),
        ):
            with redirect_stdout(output):
                _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        process.wait(timeout=1)
        self.assertIn("命令面板", text)
        self.assertIn("Enter：执行选中命令", text)
        self.assertIn("审查范围", text)
        self.assertIn("compile line", text)
        self.assertIn("\033[40;1H\033[2Kcr:commands> ", text)

if __name__ == "__main__":
    unittest.main()
