"""UI-side helpers for review handoff files.

This module owns default browser handoff file paths, repo-relative path
resolution, UTF-8 writes, parent directory creation, and write-error messages.
It does not render prompt Markdown, inspect browser state, or choose files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_PROMPT_PATH = Path(".cr") / "handoff" / "review-prompt.md"
DEFAULT_FILE_PROMPT_PATH = Path(".cr") / "handoff" / "review-prompt-file.md"
DEFAULT_DIFF_SNIPPET_PATH = Path(".cr") / "handoff" / "review-diff.md"
DEFAULT_TASK_OUTPUT_PATH = Path(".cr") / "handoff" / "task-output.md"
DEFAULT_TASK_OUTPUT_TAIL_PATH = Path(".cr") / "handoff" / "task-output-tail.md"
DEFAULT_TASK_OUTPUT_MATCH_PATH = Path(".cr") / "handoff" / "task-output-match.md"
DEFAULT_PROBLEM_CONTEXT_PATH = Path(".cr") / "handoff" / "problem-context.md"


@dataclass(frozen=True)
class HandoffSaveResult:
    path: Path
    display_path: str
    error: str | None = None


def save_prompt_text(
    text: str,
    repo: Path,
    requested_path: str = "",
    *,
    selected_only: bool,
) -> HandoffSaveResult:
    path = prompt_save_path(repo, requested_path, selected_only=selected_only)
    return _save_text(text, path, repo, label="prompt")


def save_diff_text(
    text: str,
    repo: Path,
    requested_path: str = "",
) -> HandoffSaveResult:
    path = diff_save_path(repo, requested_path)
    return _save_text(text, path, repo, label="diff")


def save_task_output_text(
    text: str,
    repo: Path,
    requested_path: str = "",
) -> HandoffSaveResult:
    path = task_output_save_path(repo, requested_path)
    return _save_text(text, path, repo, label="task output")


def save_task_output_tail_text(
    text: str,
    repo: Path,
    requested_path: str = "",
) -> HandoffSaveResult:
    path = task_output_tail_save_path(repo, requested_path)
    return _save_text(text, path, repo, label="task output tail")


def save_task_output_match_text(
    text: str,
    repo: Path,
    requested_path: str = "",
) -> HandoffSaveResult:
    path = task_output_match_save_path(repo, requested_path)
    return _save_text(text, path, repo, label="task output match")


def save_problem_context_text(
    text: str,
    repo: Path,
    requested_path: str = "",
) -> HandoffSaveResult:
    path = problem_context_save_path(repo, requested_path)
    return _save_text(text, path, repo, label="problem context")


def prompt_save_path(
    repo: Path,
    requested_path: str = "",
    *,
    selected_only: bool,
) -> Path:
    text_path = requested_path.strip()
    path = (
        Path(text_path)
        if text_path
        else default_prompt_path(selected_only=selected_only)
    )
    if path.is_absolute():
        return path
    return repo / path


def default_prompt_path(*, selected_only: bool) -> Path:
    return DEFAULT_FILE_PROMPT_PATH if selected_only else DEFAULT_PROMPT_PATH


def diff_save_path(repo: Path, requested_path: str = "") -> Path:
    text_path = requested_path.strip()
    path = Path(text_path) if text_path else DEFAULT_DIFF_SNIPPET_PATH
    if path.is_absolute():
        return path
    return repo / path


def task_output_save_path(repo: Path, requested_path: str = "") -> Path:
    text_path = requested_path.strip()
    path = Path(text_path) if text_path else DEFAULT_TASK_OUTPUT_PATH
    if path.is_absolute():
        return path
    return repo / path


def task_output_tail_save_path(repo: Path, requested_path: str = "") -> Path:
    text_path = requested_path.strip()
    path = Path(text_path) if text_path else DEFAULT_TASK_OUTPUT_TAIL_PATH
    if path.is_absolute():
        return path
    return repo / path


def task_output_match_save_path(repo: Path, requested_path: str = "") -> Path:
    text_path = requested_path.strip()
    path = Path(text_path) if text_path else DEFAULT_TASK_OUTPUT_MATCH_PATH
    if path.is_absolute():
        return path
    return repo / path


def problem_context_save_path(repo: Path, requested_path: str = "") -> Path:
    text_path = requested_path.strip()
    path = Path(text_path) if text_path else DEFAULT_PROBLEM_CONTEXT_PATH
    if path.is_absolute():
        return path
    return repo / path


def display_save_path(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)


def _save_text(text: str, path: Path, repo: Path, *, label: str) -> HandoffSaveResult:
    display = display_save_path(path, repo)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        return HandoffSaveResult(
            path,
            display,
            f"Could not save {label} to {display}: {exc}",
        )
    return HandoffSaveResult(path, display)
