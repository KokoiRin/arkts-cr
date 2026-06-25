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
    is_selected: bool = False


@dataclass(frozen=True)
class SourceFileView:
    path: str
    target_line: int
    scroll: int
    rows: list[SourceFileRow]
    total_lines: int
    error: str | None = None


@dataclass(frozen=True)
class SourceFileContent:
    path: str
    lines: list[str]
    error: str | None = None


def load_source_file_content(repo: Path, path: str) -> SourceFileContent:
    relative = Path(path)
    repo = repo.resolve()
    resolved = (repo / relative).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return _error_content(path, "Source file is outside repository.")
    try:
        text = resolved.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _error_content(path, "Source file not found.")
    except UnicodeDecodeError:
        return _error_content(path, "Source file is not UTF-8 text.")
    except OSError as exc:
        return _error_content(path, f"Source file unreadable: {exc}")
    lines = text.splitlines()
    if not lines:
        lines = [""]
    return SourceFileContent(relative.as_posix(), lines)


def load_source_file_view(
    repo: Path,
    path: str,
    *,
    target_line: int,
    scroll: int,
    capacity: int,
    selection_start: int = 0,
    selection_end: int = 0,
) -> SourceFileView:
    content = load_source_file_content(repo, path)
    if content.error:
        return _error_view(content.path, target_line, content.error)
    lines = content.lines
    target_line = max(1, min(target_line, len(lines)))
    selection = _normalize_range(selection_start, selection_end, len(lines))
    capacity = max(1, capacity)
    start = _initial_scroll(scroll, target_line, len(lines), capacity)
    end = min(len(lines), start + capacity)
    rows = [
        SourceFileRow(
            line_number=index + 1,
            text=lines[index],
            is_target=index + 1 == target_line,
            is_selected=(
                selection is not None
                and selection[0] <= index + 1 <= selection[1]
            ),
        )
        for index in range(start, end)
    ]
    return SourceFileView(
        path=content.path,
        target_line=target_line,
        scroll=start,
        rows=rows,
        total_lines=len(lines),
    )


def source_context_markdown(
    content: SourceFileContent,
    *,
    target_line: int,
    context_lines: int = 3,
    symbol_label: str = "",
) -> str:
    if content.error:
        return content.error
    lines = content.lines or [""]
    target_line = max(1, min(target_line, len(lines)))
    context_lines = max(0, context_lines)
    start = max(1, target_line - context_lines)
    end = min(len(lines), target_line + context_lines)
    width = len(str(end))
    body = []
    for line_number in range(start, end + 1):
        marker = ">" if line_number == target_line else " "
        body.append(f"{marker} {str(line_number).rjust(width)}  {lines[line_number - 1]}")
    header = [f"{content.path}:{target_line}"]
    if symbol_label.strip():
        header.append(f"Symbol: {symbol_label.strip()}")
    return "\n".join(
        [
            *header,
            "",
            "```text",
            *body,
            "```",
        ]
    )


def source_range_markdown(
    content: SourceFileContent,
    *,
    start_line: int,
    end_line: int,
    target_line: int = 0,
    symbol_label: str = "",
) -> str:
    if content.error:
        return content.error
    lines = content.lines or [""]
    selection = _normalize_range(start_line, end_line, len(lines))
    if selection is None:
        return "No source range selected."
    start, end = selection
    target_line = max(0, min(target_line, len(lines)))
    width = len(str(end))
    body = []
    for line_number in range(start, end + 1):
        marker = ">" if line_number == target_line else " "
        body.append(f"{marker} {str(line_number).rjust(width)}  {lines[line_number - 1]}")
    header = [f"{content.path}:{start}-{end}"]
    if symbol_label.strip():
        header.append(f"Symbol: {symbol_label.strip()}")
    return "\n".join(
        [
            *header,
            "",
            "```text",
            *body,
            "```",
        ]
    )


def _error_content(path: str, error: str) -> SourceFileContent:
    return SourceFileContent(Path(path).as_posix(), [], error)


def _initial_scroll(scroll: int, target_line: int, total: int, capacity: int) -> int:
    if total <= capacity:
        return 0
    if scroll >= 0:
        return max(0, min(scroll, total - capacity))
    centered = target_line - 1 - capacity // 2
    return max(0, min(centered, total - capacity))


def _normalize_range(start_line: int, end_line: int, total: int) -> tuple[int, int] | None:
    if start_line <= 0 or end_line <= 0 or total <= 0:
        return None
    start, end = sorted((start_line, end_line))
    start = max(1, min(start, total))
    end = max(1, min(end, total))
    return start, end


def _error_view(path: str, target_line: int, error: str) -> SourceFileView:
    return SourceFileView(
        path=Path(path).as_posix(),
        target_line=max(1, target_line),
        scroll=0,
        rows=[],
        total_lines=0,
        error=error,
    )
