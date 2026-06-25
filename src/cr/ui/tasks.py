"""Task runtime for the interactive browser.

This module owns Task Panel runtime behavior: command resolution, process
lifecycle, output capture, stopping, rerun, and completion history. It does not
render terminal panels, manage browser pages, read keys, or own workspace state.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
import signal
import shlex
from pathlib import Path
import subprocess
import time
from typing import Protocol


BUILD_STOP_KILL_GRACE_SECONDS = 2.0


TASK_LABELS = {
    "build": "Build",
    "test": "Test",
    "lint": "Lint",
}
TASK_PRESET_KINDS = {"build", "test", "lint"}


@dataclass(frozen=True)
class TaskRecord:
    kind: str
    status: str
    command: list[str]
    returncode: int | None = None


@dataclass(frozen=True)
class TaskCommandSource:
    kind: str
    source: str
    command: list[str] | None = None


@dataclass(frozen=True)
class TaskPresetResult:
    presets: dict[str, str]
    error: str | None = None


@dataclass
class TaskState:
    command: list[str]
    process: subprocess.Popen[bytes]
    kind: str = "build"
    lines: list[str] = field(default_factory=list)
    last_rendered_panel: list[str] = field(default_factory=list)
    partial: str = ""
    returncode: int | None = None
    start_error: str | None = None
    process_group_id: int | None = None
    stop_requested: bool = False
    stop_requested_at: float | None = None
    stop_escalated: bool = False
    history_recorded: bool = False

    @property
    def running(self) -> bool:
        return self.returncode is None and self.start_error is None


class TaskRuntimeState(Protocol):
    task: TaskState | None
    task_history: list[TaskRecord]


def task_label(kind: str) -> str:
    return TASK_LABELS.get(kind, kind.replace("-", " ").title())


def task_name(kind: str) -> str:
    return kind.replace("-", " ")


def missing_task_command_message(kind: str) -> str:
    if kind == "build":
        return (
            "No build command configured. Set --build-cmd or CR_BUILD_CMD; "
            "DouyinHarmony defaults to './remote buildEntry --app douyin'."
        )
    if kind == "test":
        return "No test command configured. Set --test-cmd or CR_TEST_CMD."
    if kind == "lint":
        return "No lint command configured. Set --lint-cmd or CR_LINT_CMD."
    return f"No {task_name(kind)} command configured."


def build_command(repo: Path, configured: str | None = None) -> list[str] | None:
    args = argparse.Namespace(build_cmd=configured, test_cmd=None, lint_cmd=None)
    return _task_command_source(repo, args, "build").command


def task_command(
    repo: Path,
    args: argparse.Namespace,
    kind: str,
) -> list[str] | None:
    return _task_command_source(repo, args, kind).command


def task_presets(repo: Path) -> dict[str, str]:
    return load_task_presets(repo).presets


def load_task_presets(repo: Path) -> TaskPresetResult:
    path = repo / ".cr" / "tasks.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return TaskPresetResult({})
    except json.JSONDecodeError:
        return TaskPresetResult({}, "invalid .cr/tasks.json: invalid JSON")
    except OSError as exc:
        return TaskPresetResult({}, f"invalid .cr/tasks.json: {exc}")
    if not isinstance(data, dict):
        return TaskPresetResult({}, "invalid .cr/tasks.json: expected object")
    presets: dict[str, str] = {}
    for kind in TASK_PRESET_KINDS:
        value = data.get(kind)
        if isinstance(value, str) and value.strip():
            presets[kind] = value
    return TaskPresetResult(presets)


def task_diagnostic_lines(repo: Path, args: argparse.Namespace) -> list[str]:
    preset_result = load_task_presets(repo)
    lines = ["Task commands:"]
    if preset_result.error:
        lines.append(f"preset: {preset_result.error}")
        lines.append("hint: run : tasks help for .cr/tasks.json format")
    for kind in ("build", "test", "lint"):
        source = _task_command_source(repo, args, kind, preset_result)
        if source.command is None:
            lines.append(f"{kind}: missing")
        else:
            lines.append(f"{kind}: {source.source} {_format_command(source.command)}")
    return lines


def task_schema_help_lines() -> list[str]:
    return [
        "Task preset file: .cr/tasks.json",
        "Supported keys: build, test, lint",
        "Each value must be a shell-like command string.",
        (
            "Priority: CLI args > environment variables > .cr/tasks.json > "
            "DouyinHarmony build default > missing"
        ),
        "Example:",
        "{",
        '  "build": "./remote buildEntry --app douyin",',
        '  "test": "npm test",',
        '  "lint": "npm run lint"',
        "}",
    ]


def _task_command_source(
    repo: Path,
    args: argparse.Namespace,
    kind: str,
    preset_result: TaskPresetResult | None = None,
) -> TaskCommandSource:
    preset_result = preset_result or load_task_presets(repo)
    if kind == "build":
        cli = getattr(args, "build_cmd", None)
        if cli:
            return TaskCommandSource(kind, "cli", shlex.split(cli))
        env = os.environ.get("CR_BUILD_CMD")
        if env:
            return TaskCommandSource(kind, "env", shlex.split(env))
        preset = preset_result.presets.get("build")
        if preset:
            return TaskCommandSource(kind, "preset", shlex.split(preset))
        if repo.name == "DouyinHarmony" and (repo / "remote").exists():
            return TaskCommandSource(
                kind,
                "default",
                ["./remote", "buildEntry", "--app", "douyin"],
            )
        return TaskCommandSource(kind, "missing")
    if kind == "test":
        return _template_task_command_source(
            kind,
            getattr(args, "test_cmd", None),
            "CR_TEST_CMD",
            preset_result.presets.get("test"),
        )
    if kind == "lint":
        return _template_task_command_source(
            kind,
            getattr(args, "lint_cmd", None),
            "CR_LINT_CMD",
            preset_result.presets.get("lint"),
        )
    return TaskCommandSource(kind, "missing")


def _template_task_command_source(
    kind: str,
    cli: str | None,
    env_name: str,
    preset: str | None,
) -> TaskCommandSource:
    if cli:
        return TaskCommandSource(kind, "cli", shlex.split(cli))
    env = os.environ.get(env_name)
    if env:
        return TaskCommandSource(kind, "env", shlex.split(env))
    if preset:
        return TaskCommandSource(kind, "preset", shlex.split(preset))
    return TaskCommandSource(kind, "missing")


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def task_status(task: TaskState) -> str:
    if task.start_error is not None:
        return "failed to start"
    if task.returncode is None and task.stop_requested:
        return "stopping"
    if task.returncode is None:
        return "running"
    if not task.command:
        return "idle"
    if task.stop_requested:
        return "stopped"
    if task.returncode == 0:
        return "succeeded"
    return f"failed ({task.returncode})"


def task_output_handoff_text(task: TaskState) -> str:
    command = _format_command(task.command) if task.command else "(no command)"
    output = "\n".join(task.lines).strip()
    if not output:
        output = "(no output captured)"
    return "\n".join(
        [
            f"# {task_label(task.kind)} output",
            "",
            f"Status: {task_status(task)}",
            f"Command: {command}",
            "",
            "```text",
            output,
            "```",
        ]
    )


def record_completed_task(state: TaskRuntimeState) -> None:
    task = state.task
    if (
        task is None
        or not task.command
        or task.returncode is None
        or task.history_recorded
    ):
        return
    state.task_history.append(
        TaskRecord(
            kind=task.kind,
            status=task_status(task),
            command=task.command,
            returncode=task.returncode,
        )
    )
    state.task_history = state.task_history[-5:]
    task.history_recorded = True


def start_task(
    state: TaskRuntimeState,
    args: argparse.Namespace,
    kind: str,
    *,
    repo: Path,
) -> None:
    command = task_command(repo, args, kind)
    if command is None:
        state.task = failed_task_state(
            [],
            missing_task_command_message(kind),
            kind,
        )
        return
    if state.task is not None and state.task.running:
        state.task.lines.append(f"{task_label(state.task.kind)} is already running.")
        return
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as exc:
        label = task_label(kind)
        state.task = failed_task_state(
            command,
            f"{label} failed to start: {exc}",
            kind,
        )
        return
    if process.stdout is not None:
        os.set_blocking(process.stdout.fileno(), False)
    state.task = TaskState(
        command=command,
        process=process,
        kind=kind,
        lines=[f"started in {repo}"],
        process_group_id=process.pid,
    )


def stop_task(state: TaskRuntimeState) -> None:
    if state.task is None:
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait()
        state.task = TaskState(
            command=[],
            process=process,
            kind="build",
            lines=["No build is running."],
            returncode=0,
        )
        return
    if not state.task.running:
        state.task.lines.append(f"No {task_name(state.task.kind)} is running.")
        return
    state.task.stop_requested = True
    state.task.lines.append(f"Stopping {task_name(state.task.kind)}...")
    state.task.stop_requested_at = time.monotonic()
    if state.task.process_group_id is not None and hasattr(os, "killpg"):
        try:
            os.killpg(state.task.process_group_id, signal.SIGTERM)
            return
        except OSError as exc:
            state.task.lines.append(
                f"{task_label(state.task.kind)} process group stop failed: {exc}"
            )
    try:
        state.task.process.terminate()
    except OSError as exc:
        state.task.lines.append(f"{task_label(state.task.kind)} stop failed: {exc}")


def rerun_task(
    state: TaskRuntimeState,
    args: argparse.Namespace,
    *,
    repo: Path,
) -> None:
    if state.task is not None and state.task.running:
        state.task.lines.append(
            f"{task_label(state.task.kind)} is already running. Stop it before rerun."
        )
        return
    kind = state.task.kind if state.task is not None else "build"
    start_task(state, args, kind, repo=repo)


def run_task_foreground(
    args: argparse.Namespace,
    kind: str,
    *,
    repo: Path,
) -> None:
    command = task_command(repo, args, kind)
    if command is None:
        print(missing_task_command_message(kind))
        return
    label = task_label(kind)
    print(f"{label}: {' '.join(shlex.quote(part) for part in command)}")
    try:
        result = subprocess.run(command, cwd=repo, check=False)
    except OSError as exc:
        print(f"{label} failed to start: {exc}")
        return
    if result.returncode == 0:
        print(f"{label} succeeded.")
    else:
        print(f"{label} failed with exit code {result.returncode}.")


def failed_task_state(
    command: list[str],
    message: str,
    kind: str = "build",
) -> TaskState:
    process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
    process.wait()
    return TaskState(
        command=command,
        process=process,
        kind=kind,
        lines=[message],
        returncode=1,
        start_error=message,
    )


def poll_task(task: TaskState | None) -> None:
    if task is None or task.start_error is not None:
        return
    if task.returncode is not None:
        return
    drain_task_output(task)
    returncode = task.process.poll()
    if returncode is not None and task.returncode is None:
        drain_task_output(task)
        if task.partial:
            task.lines.append(task.partial)
            task.partial = ""
        task.returncode = returncode
        if task.stop_requested:
            message = f"{task_label(task.kind)} stopped."
        else:
            label = task_label(task.kind)
            message = (
                f"{label} succeeded."
                if returncode == 0
                else f"{label} failed with exit code {returncode}."
            )
        task.lines.append(message)
        if task.process.stdout is not None:
            task.process.stdout.close()
    else:
        maybe_escalate_task_stop(task)


def maybe_escalate_task_stop(task: TaskState) -> None:
    if (
        not task.stop_requested
        or task.stop_requested_at is None
        or task.stop_escalated
    ):
        return
    if time.monotonic() - task.stop_requested_at < BUILD_STOP_KILL_GRACE_SECONDS:
        return
    task.stop_escalated = True
    if task.process_group_id is not None and hasattr(os, "killpg"):
        task.lines.append(
            f"{task_label(task.kind)} did not stop; force killing process group."
        )
        try:
            os.killpg(task.process_group_id, signal.SIGKILL)
            return
        except OSError as exc:
            task.lines.append(
                f"{task_label(task.kind)} process group force kill failed: {exc}"
            )
    task.lines.append(
        f"{task_label(task.kind)} did not stop; force killing {task_name(task.kind)} process."
    )
    try:
        task.process.kill()
    except OSError as exc:
        task.lines.append(f"{task_label(task.kind)} force kill failed: {exc}")


def drain_task_output(task: TaskState) -> None:
    if task.process.stdout is None:
        return
    fd = task.process.stdout.fileno()
    while True:
        try:
            chunk = os.read(fd, 4096)
        except BlockingIOError:
            break
        except OSError as exc:
            task.lines.append(f"output read failed: {exc}")
            break
        if not chunk:
            break
        text = chunk.decode(errors="replace")
        combined = task.partial + text
        parts = combined.splitlines(keepends=True)
        task.partial = ""
        for part in parts:
            if part.endswith("\n") or part.endswith("\r"):
                task.lines.append(part.rstrip("\r\n"))
            else:
                task.partial = part
        if len(task.lines) > 200:
            task.lines = task.lines[-200:]
