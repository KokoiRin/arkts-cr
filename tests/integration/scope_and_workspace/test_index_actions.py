import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs import git
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


def _run(cwd, *args):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


class IndexActionTests(unittest.TestCase):
    def test_browser_command_executor_stages_selected_file_and_refreshes_scope(self):
        # Behavior: 当用户在scope home中选择index、actions、stages、refreshes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        state.file_line_cache["old"] = ["stale"]
        BrowserNavigation.open_file_detail(state)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.stage_path", return_value=None) as stage:
            with patch(
                "cr.ui.browser._load_browse_changes",
                return_value=[FileChange("src/New.ts", 1, 0)],
            ):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        stage.assert_called_once_with("src/Old.ts")
        self.assertEqual(state.changes, [FileChange("src/New.ts", 1, 0)])
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Staged src/Old.ts", output.getvalue())

    def test_browser_command_executor_stage_failure_does_not_refresh_scope(self):
        # Behavior: 当用户在scope home遇到失败反馈时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.git.stage_path",
            side_effect=git.GitError("cannot stage file"),
        ):
            with patch("cr.ui.browser._load_browse_changes") as load:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        load.assert_not_called()
        self.assertIn("Stage failed: cannot stage file", output.getvalue())

    def test_browser_command_executor_unstages_selected_file_and_refreshes_scope(self):
        # Behavior: 当用户在scope home中选择index、actions、unstages、refreshes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Staged.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.unstage_path", return_value=None) as unstage:
            with patch("cr.ui.browser._load_browse_changes", return_value=[]):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_called_once_with("src/Staged.ts")
        self.assertEqual(state.changes, [])
        self.assertIn("Unstaged src/Staged.ts", output.getvalue())

    def test_browser_command_executor_stage_reports_empty_selection(self):
        # Behavior: 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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

        with patch("cr.ui.browser.git.stage_path") as stage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        stage.assert_not_called()
        self.assertIn("No changed file to stage.", output.getvalue())

    def test_browser_command_executor_unstage_reports_empty_selection(self):
        # Behavior: 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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

        with patch("cr.ui.browser.git.unstage_path") as unstage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_not_called()
        self.assertIn("No changed file to unstage.", output.getvalue())

    def test_git_stage_and_unstage_path_update_index(self):
        # Behavior: 当用户在file action中验证index、actions、git、stage时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            _run(repo, "git", "init")
            _run(repo, "git", "config", "user.email", "cr@example.invalid")
            _run(repo, "git", "config", "user.name", "cr")
            _run(repo, "git", "add", "Sample.ts")
            _run(repo, "git", "commit", "-m", "init")
            sample.write_text("new\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                git.stage_path("Sample.ts")
                staged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(staged.returncode, 0, staged.stderr)
                self.assertIn("Sample.ts", staged.stdout)
                git.unstage_path("Sample.ts")
                unstaged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
                self.assertNotIn("Sample.ts", unstaged.stdout)
            finally:
                os.chdir(previous_cwd)
