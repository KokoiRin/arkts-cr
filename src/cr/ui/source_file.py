"""Read-only source file view model for the interactive browser.

This module owns repo-local source-file reads and windowing for TUI previews.
It does not render terminal pages, edit files, parse syntax, open editors, or
persist source-view state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFileRow:
    line_number: int
    text: str
    is_target: bool = False


@dataclass(frozen=True)
class SourceFileView:
    path: str
    target_line: int
    scroll: int
    rows: list[SourceFileRow]
    total_lines: int
    error: str | None = None


def load_source_file_view(
    repo: Path,
    path: str,
    *,
    target_line: int,
    scroll: int,
    capacity: int,
) -> SourceFileView:
    relative = Path(path)
    repo = repo.resolve()
    resolved = (repo / relative).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return _error_view(path, target_line, "Source file is outside repository.")
    try:
        text = resolved.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _error_view(path, target_line, "Source file not found.")
    except UnicodeDecodeError:
        return _error_view(path, target_line, "Source file is not UTF-8 text.")
    except OSError as exc:
        return _error_view(path, target_line, f"Source file unreadable: {exc}")
    lines = text.splitlines()
    if not lines:
        lines = [""]
    target_line = max(1, min(target_line, len(lines)))
    capacity = max(1, capacity)
    start = _initial_scroll(scroll, target_line, len(lines), capacity)
    end = min(len(lines), start + capacity)
    rows = [
        SourceFileRow(
            line_number=index + 1,
            text=lines[index],
            is_target=index + 1 == target_line,
        )
        for index in range(start, end)
    ]
    return SourceFileView(
        path=relative.as_posix(),
        target_line=target_line,
        scroll=start,
        rows=rows,
        total_lines=len(lines),
    )


def _initial_scroll(scroll: int, target_line: int, total: int, capacity: int) -> int:
    if total <= capacity:
        return 0
    if scroll >= 0:
        return max(0, min(scroll, total - capacity))
    centered = target_line - 1 - capacity // 2
    return max(0, min(centered, total - capacity))


def _error_view(path: str, target_line: int, error: str) -> SourceFileView:
    return SourceFileView(
        path=Path(path).as_posix(),
        target_line=max(1, target_line),
        scroll=0,
        rows=[],
        total_lines=0,
        error=error,
    )
