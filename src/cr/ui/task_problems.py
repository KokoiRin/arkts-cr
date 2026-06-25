"""Task output problem extraction for the interactive browser.

This module owns lightweight file-location extraction from already captured
task output. It does not manage task processes, render browser pages, open
editors, or persist diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from . import text_search


ANCHOR_RE = re.compile(
    r"(?P<path>(?:[A-Za-z]:)?/?[^\s:]+?\.[A-Za-z0-9_+.-]+):"
    r"(?P<line>[1-9]\d*)"
    r"(?::(?P<column>[1-9]\d*))?"
)


@dataclass(frozen=True)
class TaskProblem:
    path: str
    line: int
    column: int | None
    summary: str
    output_line: int


def extract_task_problems(repo: Path, lines: list[str]) -> list[TaskProblem]:
    repo = repo.resolve()
    problems: list[TaskProblem] = []
    for output_index, raw_line in enumerate(lines, start=1):
        line = text_search.plain_text(raw_line)
        for match in ANCHOR_RE.finditer(line):
            normalized = _normalize_problem_path(repo, match.group("path"))
            if normalized is None:
                continue
            problems.append(
                TaskProblem(
                    path=normalized,
                    line=int(match.group("line")),
                    column=_optional_int(match.group("column")),
                    summary=line.strip(),
                    output_line=output_index,
                )
            )
    return problems


def _normalize_problem_path(repo: Path, raw_path: str) -> str | None:
    if "://" in raw_path:
        return None
    path = Path(raw_path)
    if path.is_absolute():
        try:
            resolved = path.resolve()
            relative = resolved.relative_to(repo)
        except (OSError, ValueError):
            return None
    else:
        relative = path
        resolved = (repo / relative).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return relative.as_posix()


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)
