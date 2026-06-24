"""Screen-layer helpers for the interactive browser.

This module owns Browser Frame layout, Task Panel presentation, terminal line
fitting, and Task Panel-only refresh output. It does not own review workspace
state, product page content, command parsing, task process lifecycle, or Git
review facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import shlex
import shutil
import sys

from . import tasks as task_runtime
from .tasks import TaskRecord, TaskState
from .terminal import TerminalStyle


@dataclass(frozen=True)
class ScreenLayout:
    content_height: int
    task_height: int
    prompt_row: int
    task_start_row: int | None

    @property
    def max_render_lines(self) -> int:
        return max(0, self.prompt_row - 1)


@dataclass
class BrowserFrame:
    layout: ScreenLayout | None = None
    complete: bool = False
    task_panel: list[str] = field(default_factory=list)
    dirty: bool = True


def screen_height() -> int:
    return max(8, shutil.get_terminal_size((100, 30)).lines)


def task_panel_height(task: TaskState | None, available_lines: int) -> int:
    if task is None:
        return 0
    return max(3, min(10, max(5, available_lines // 4), max(3, available_lines - 6)))


def screen_layout(task: TaskState | None, rows: int | None = None) -> ScreenLayout:
    terminal_rows = screen_height() if rows is None else max(8, rows)
    max_render_lines = max(1, terminal_rows - 1)
    task_height = task_panel_height(task, max_render_lines)
    content_height = max(1, max_render_lines - task_height)
    task_start_row = content_height + 1 if task_height else None
    return ScreenLayout(
        content_height=content_height,
        task_height=task_height,
        prompt_row=terminal_rows,
        task_start_row=task_start_row,
    )


def task_panel_lines(
    task: TaskState | None,
    style: TerminalStyle,
    max_lines: int,
    history: list[TaskRecord] | None = None,
) -> list[str]:
    if task is None or max_lines <= 0:
        return []
    width = shutil.get_terminal_size((100, 30)).columns
    status = task_runtime.task_status(task)
    command = " ".join(shlex.quote(part) for part in task.command)
    lines = [
        style.dim("─" * min(width, 100)),
        f"{style.bold(task_runtime.task_label(task.kind))} {status}  {style.dim(command)}",
    ]
    if history:
        lines.append(task_history_line(history[-3:]))
    capacity = max(0, max_lines - len(lines))
    body = task.lines[-capacity:] if capacity else []
    if capacity and not body:
        body = [style.dim("(waiting for output)")]
    return [*lines, *body][-max_lines:]


def task_history_line(history: list[TaskRecord]) -> str:
    summaries = []
    for record in history:
        command = " ".join(shlex.quote(part) for part in record.command)
        summaries.append(f"{record.kind} {record.status} {command}".strip())
    return "Recent: " + " | ".join(summaries)


def draw_task_panel_only(
    task: TaskState | None,
    style: TerminalStyle,
    frame: BrowserFrame | None = None,
    history: list[TaskRecord] | None = None,
) -> bool:
    if task is None:
        return False
    layout = screen_layout(task)
    height = layout.task_height
    if frame is not None:
        if frame.dirty or not frame.complete or frame.layout != layout:
            frame.dirty = True
            return False
    lines = task_panel_lines(task, style, height, history)
    previous_panel = frame.task_panel if frame is not None else task.last_rendered_panel
    if lines == previous_panel:
        return False
    task.last_rendered_panel = lines
    if frame is not None:
        frame.task_panel = lines
    start_row = layout.task_start_row or 1
    output: list[str] = ["\0337", f"\033[{start_row};1H"]
    for index in range(height):
        output.append("\033[2K")
        if index < len(lines):
            output.append(fit_terminal_line(lines[index]))
        if index != height - 1:
            output.append("\n")
    output.append("\0338")
    sys.stdout.write("".join(output))
    sys.stdout.flush()
    return True


def fit_terminal_line(line: str) -> str:
    if "\033[" in line:
        return line
    width = shutil.get_terminal_size((100, 30)).columns
    return line[: max(0, width - 1)]
