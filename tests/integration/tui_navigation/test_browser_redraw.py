import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import input as browser_input
from cr.ui.browser import TaskState
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class BrowserRedrawTests(unittest.TestCase):

    def test_command_prompt_cancel_forces_full_browser_redraw(self):
        # Behavior: 当用户在产品行为中验证redraw、prompt、cancel、forces时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
                                    side_effect=["command_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_command_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)

    def test_filter_prompt_cancel_forces_full_browser_redraw(self):
        # Behavior: 当用户在产品行为中过滤redraw、filter、prompt、cancel时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
                                    side_effect=["filter_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_filter_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)

    def test_task_problems_page_tick_redraws_main_content_not_panel_only(self):
        # Behavior: 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
                                            "problems",
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
