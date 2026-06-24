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
    display = display_save_path(path, repo)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        return HandoffSaveResult(
            path,
            display,
            f"Could not save prompt to {display}: {exc}",
        )
    return HandoffSaveResult(path, display)


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


def display_save_path(path: Path, repo: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return str(path)
