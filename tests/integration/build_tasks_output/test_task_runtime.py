import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui import tasks
from cr.ui.tasks import TaskState


ROOT = Path(__file__).resolve().parents[3]


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class TaskRuntimeTests(unittest.TestCase):
    def test_task_output_handoff_includes_kind_status_command_and_output(self):
        # Behavior: 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        task = TaskState(
            ["npm", "test"],
            process,
            kind="test",
            lines=["first line", "second line"],
            returncode=1,
        )

        text = tasks.task_output_handoff_text(task)

        self.assertIn("# Test output", text)
        self.assertIn("Status: failed (1)", text)
        self.assertIn("Command: npm test", text)
        self.assertIn("```text\nfirst line\nsecond line\n```", text)

    def test_running_task_output_handoff_reports_no_output(self):
        # Behavior: 当用户在task output遇到任务输出时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        self.addCleanup(process.wait, timeout=1)
        task = TaskState(["./build.sh"], process, kind="build")

        text = tasks.task_output_handoff_text(task)

        self.assertIn("# Build output", text)
        self.assertIn("Status: running", text)
        self.assertIn("Command: ./build.sh", text)
        self.assertIn("(no output captured)", text)

    def test_task_output_tail_handoff_keeps_only_recent_lines(self):
        # Behavior: 当用户在task output中保持任务输出时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        task = TaskState(
            ["./build.sh"],
            process,
            kind="build",
            lines=[f"line {index}" for index in range(1, 7)],
            returncode=1,
        )

        text = tasks.task_output_tail_handoff_text(task, max_lines=3)

        self.assertIn("# Build output tail", text)
        self.assertIn("Status: failed (1)", text)
        self.assertIn("Command: ./build.sh", text)
        self.assertIn("Last 3 of 6 output lines", text)
        self.assertNotIn("line 3", text)
        self.assertIn("```text\nline 4\nline 5\nline 6\n```", text)

    def test_task_commands_use_cli_env_presets_then_defaults(self):
        # Behavior: 当用户在task output中验证runtime、use、cli、env时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")
            (repo / ".cr").mkdir()
            (repo / ".cr" / "tasks.json").write_text(
                json.dumps(
                    {
                        "build": "./preset-build",
                        "test": "preset-test",
                        "lint": "preset-lint",
                    }
                ),
                encoding="utf-8",
            )

            cli_args = argparse_namespace(
                build_cmd="./cli-build",
                test_cmd=None,
                lint_cmd=None,
            )
            env_args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            with patch.dict(os.environ, {"CR_TEST_CMD": "env-test"}, clear=False):
                self.assertEqual(tasks.task_command(repo, cli_args, "build"), ["./cli-build"])
                self.assertEqual(tasks.task_command(repo, env_args, "test"), ["env-test"])
                self.assertEqual(tasks.task_command(repo, env_args, "lint"), ["preset-lint"])
                self.assertEqual(tasks.task_command(repo, env_args, "build"), ["./preset-build"])

    def test_task_commands_can_be_defined_by_project_presets(self):
        # Behavior: 当用户在task output中验证runtime、can、be、defined时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".cr").mkdir()
            (repo / ".cr" / "tasks.json").write_text(
                json.dumps(
                    {
                        "build": "./scripts/build.sh --fast",
                        "test": "npm test",
                        "lint": "npm run lint",
                    }
                ),
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            self.assertEqual(
                tasks.task_command(repo, args, "build"),
                ["./scripts/build.sh", "--fast"],
            )
            self.assertEqual(tasks.task_command(repo, args, "test"), ["npm", "test"])
            self.assertEqual(tasks.task_command(repo, args, "lint"), ["npm", "run", "lint"])

    def test_task_command_preserves_douyin_build_default_without_preset(self):
        # Behavior: 当用户在task output遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            self.assertEqual(
                tasks.build_command(repo),
                ["./remote", "buildEntry", "--app", "douyin"],
            )
            self.assertEqual(
                tasks.task_command(repo, args, "build"),
                ["./remote", "buildEntry", "--app", "douyin"],
            )

    def test_task_commands_use_explicit_cli_test_and_lint_commands(self):
        # Behavior: 当用户在task output中验证runtime、use、cli、lint时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd=None,
                test_cmd="npm test",
                lint_cmd="npm run lint",
            )

            self.assertEqual(tasks.task_command(repo, args, "test"), ["npm", "test"])
            self.assertEqual(tasks.task_command(repo, args, "lint"), ["npm", "run", "lint"])

    def test_invalid_project_task_presets_are_ignored(self):
        # Behavior: 当用户在task output中验证runtime、invalid、project、presets时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            config_dir = repo / ".cr"
            config_dir.mkdir()
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            (config_dir / "tasks.json").write_text("{", encoding="utf-8")
            self.assertEqual(tasks.task_presets(repo), {})
            self.assertIsNone(tasks.task_command(repo, args, "test"))

            (config_dir / "tasks.json").write_text("[\"npm test\"]", encoding="utf-8")
            self.assertEqual(tasks.task_presets(repo), {})
            self.assertIsNone(tasks.task_command(repo, args, "test"))

            (config_dir / "tasks.json").write_text(
                json.dumps({"test": ["npm", "test"], "lint": "npm run lint"}),
                encoding="utf-8",
            )
            self.assertEqual(tasks.task_presets(repo), {"lint": "npm run lint"})
            self.assertIsNone(tasks.task_command(repo, args, "test"))
            self.assertEqual(tasks.task_command(repo, args, "lint"), ["npm", "run", "lint"])

    def test_task_diagnostics_report_sources_errors_and_missing_commands(self):
        # Behavior: 当用户在task output遇到缺失状态时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            config_dir = repo / ".cr"
            config_dir.mkdir()
            (config_dir / "tasks.json").write_text("{", encoding="utf-8")
            args = argparse_namespace(
                build_cmd="./cli-build",
                test_cmd=None,
                lint_cmd=None,
            )

            with patch.dict(os.environ, {"CR_TEST_CMD": "env-test"}, clear=True):
                lines = tasks.task_diagnostic_lines(repo, args)

        text = "\n".join(lines)
        self.assertIn("preset: invalid .cr/tasks.json", text)
        self.assertIn("build: cli ./cli-build", text)
        self.assertIn("test: env env-test", text)
        self.assertIn("lint: missing", text)
        self.assertIn("hint: run : tasks help", text)

    def test_task_diagnostics_report_presets_and_douyin_default(self):
        # Behavior: 当用户在task output中验证runtime、diagnostics、report、presets时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")
            (repo / ".cr").mkdir()
            (repo / ".cr" / "tasks.json").write_text(
                json.dumps({"test": "npm test", "lint": "npm run lint"}),
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            with patch.dict(os.environ, {}, clear=True):
                lines = tasks.task_diagnostic_lines(repo, args)

        text = "\n".join(lines)
        self.assertIn("build: default ./remote buildEntry --app douyin", text)
        self.assertIn("test: preset npm test", text)
        self.assertIn("lint: preset npm run lint", text)

    def test_task_schema_help_describes_project_tasks_json(self):
        # Behavior: 当用户在task output中验证runtime、schema、help、describes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        text = "\n".join(tasks.task_schema_help_lines())

        self.assertIn(".cr/tasks.json", text)
        self.assertIn("build", text)
        self.assertIn("test", text)
        self.assertIn("lint", text)
        self.assertIn("command string", text)
        self.assertIn("CLI args > environment variables > .cr/tasks.json", text)
        self.assertIn('"build": "./remote buildEntry --app douyin"', text)

    def test_started_task_collects_output_and_records_history(self):
        # Behavior: 当用户在task output中验证runtime、started、collects、output时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd=f"{sys.executable} -c \"print('runtime line')\""
            )
            state = argparse_namespace(task=None, task_history=[])

            tasks.start_task(state, args, "build", repo=repo)
            for _ in range(100):
                tasks.poll_task(state.task)
                if state.task and state.task.returncode is not None:
                    break
                time.sleep(0.01)
            tasks.record_completed_task(state)

        self.assertIsNotNone(state.task)
        self.assertEqual(state.task.returncode, 0)
        self.assertIn("runtime line", state.task.lines)
        self.assertEqual(len(state.task_history), 1)
        self.assertEqual(state.task_history[0].status, "succeeded")

    def test_start_task_uses_project_task_preset(self):
        # Behavior: 当用户在task output中验证runtime、start、uses、project时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".cr").mkdir()
            (repo / ".cr" / "tasks.json").write_text(
                json.dumps({"test": f"{sys.executable} -c \"print('preset test')\""}),
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)
            state = argparse_namespace(task=None, task_history=[])

            tasks.start_task(state, args, "test", repo=repo)
            for _ in range(100):
                tasks.poll_task(state.task)
                if state.task and state.task.returncode is not None:
                    break
                time.sleep(0.01)

        self.assertIsNotNone(state.task)
        self.assertEqual(state.task.kind, "test")
        self.assertEqual(state.task.returncode, 0)
        self.assertIn("preset test", state.task.lines)

    def test_task_runtime_owns_process_lifecycle_implementation(self):
        # Behavior: 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        tasks_source = (ROOT / "src/cr/ui/tasks.py").read_text(encoding="utf-8")
        browser_source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("def start_task(", tasks_source)
        self.assertIn("def poll_task(", tasks_source)
        self.assertIn("start_new_session=True", tasks_source)
        self.assertIn("os.killpg", tasks_source)
        self.assertIn("os.read(fd, 4096)", tasks_source)
        self.assertNotIn("start_new_session=True", browser_source)
        self.assertNotIn("os.killpg", browser_source)
        self.assertNotIn("os.read(fd, 4096)", browser_source)


if __name__ == "__main__":
    unittest.main()
