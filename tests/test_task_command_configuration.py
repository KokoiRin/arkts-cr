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


class TaskCommandConfigurationTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
