"""Task output problem extraction for the interactive browser.

This module owns lightweight file-location extraction, generic diagnostic facts,
and handoff text for already captured task output. It does not manage task
processes, render browser pages, open editors, copy to clipboards, or persist
diagnostics.
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
SEVERITY_RE = re.compile(
    r"\b(?P<severity>fatal error|error|warning|warn|info|note)\b",
    re.IGNORECASE,
)
CODE_RE = re.compile(
    r"^\s*(?:[: -]\s*)?"
    r"(?:\[(?P<bracket>[A-Za-z]+\d+[A-Za-z0-9_-]*)\]"
    r"|\((?P<paren>[A-Za-z]+\d+[A-Za-z0-9_-]*)\)"
    r"|(?P<plain>[A-Z]{1,12}\d+[A-Za-z0-9_-]*))"
)
SEVERITY_SORT_ORDER = {
    "error": 0,
    "warning": 1,
    "info": 2,
    "note": 3,
}


@dataclass(frozen=True)
class TaskProblem:
    path: str
    line: int
    column: int | None
    summary: str
    output_line: int
    severity: str | None = None
    code: str | None = None
    message: str = ""


def problem_location(problem: TaskProblem) -> str:
    column = f":{problem.column}" if problem.column is not None else ""
    return f"{problem.path}:{problem.line}{column}"


def problem_diagnostic_label(problem: TaskProblem) -> str:
    parts = []
    if problem.severity:
        parts.append(problem.severity.upper())
    if problem.code:
        parts.append(problem.code)
    return " ".join(parts)


def problem_handoff_text(problem: TaskProblem) -> str:
    lines = [problem_location(problem)]
    if problem.severity:
        lines.append(f"Severity: {problem.severity}")
    if problem.code:
        lines.append(f"Code: {problem.code}")
    if problem.message:
        lines.append(f"Message: {problem.message}")
    lines.append(problem.summary)
    return "\n".join(lines)


def problems_handoff_text(problems: list[TaskProblem]) -> str:
    lines = ["# Task problems", ""]
    for index, problem in enumerate(problems, start=1):
        label = problem_diagnostic_label(problem)
        label_text = f" [{label}]" if label else ""
        detail = f"Message: {problem.message}" if problem.message else problem.summary
        lines.extend(
            [
                f"{index}. {problem_location(problem)}{label_text}",
                f"   {detail}",
            ]
        )
    return "\n".join(lines)


def filter_task_problems(
    problems: list[TaskProblem],
    severity: str,
) -> list[TaskProblem]:
    normalized = severity.strip().lower()
    if not normalized:
        return list(problems)
    return [problem for problem in problems if problem.severity == normalized]


def filter_task_problems_by_query(
    problems: list[TaskProblem],
    query: str,
) -> list[TaskProblem]:
    normalized = query.strip().lower()
    if not normalized:
        return list(problems)
    return [
        problem
        for problem in problems
        if normalized in _problem_query_text(problem)
    ]


def sort_task_problems(
    problems: list[TaskProblem],
    sort_mode: str,
) -> list[TaskProblem]:
    if sort_mode.strip().lower() != "severity":
        return list(problems)
    return [
        problem
        for _, problem in sorted(
            enumerate(problems),
            key=lambda item: (
                SEVERITY_SORT_ORDER.get(item[1].severity or "", 4),
                item[0],
            ),
        )
    ]


def problem_severity_count_label(problems: list[TaskProblem]) -> str:
    if not problems:
        return ""
    counts = {
        "error": 0,
        "warning": 0,
        "info": 0,
        "note": 0,
        "unknown": 0,
    }
    for problem in problems:
        severity = problem.severity if problem.severity in counts else "unknown"
        counts[severity] += 1
    parts = [
        _format_count(counts["error"], "error"),
        _format_count(counts["warning"], "warning"),
        _format_count(counts["info"], "info"),
        _format_count(counts["note"], "note"),
        _format_count(counts["unknown"], "unknown"),
    ]
    return ", ".join(part for part in parts if part)


def _problem_query_text(problem: TaskProblem) -> str:
    return "\n".join(
        part
        for part in (
            problem.path,
            problem_location(problem),
            problem.summary,
            problem.severity or "",
            problem.code or "",
            problem.message,
        )
        if part
    ).lower()


def extract_task_problems(repo: Path, lines: list[str]) -> list[TaskProblem]:
    repo = repo.resolve()
    problems: list[TaskProblem] = []
    for output_index, raw_line in enumerate(lines, start=1):
        line = text_search.plain_text(raw_line)
        for match in ANCHOR_RE.finditer(line):
            normalized = _normalize_problem_path(repo, match.group("path"))
            if normalized is None:
                continue
            severity, code, message = _extract_diagnostic_facts(line, match.end())
            problems.append(
                TaskProblem(
                    path=normalized,
                    line=int(match.group("line")),
                    column=_optional_int(match.group("column")),
                    summary=line.strip(),
                    output_line=output_index,
                    severity=severity,
                    code=code,
                    message=message,
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


def _format_count(count: int, label: str) -> str:
    if count == 0:
        return ""
    if label == "unknown":
        return f"{count} unknown"
    suffix = "" if count == 1 else "s"
    return f"{count} {label}{suffix}"


def _extract_diagnostic_facts(line: str, anchor_end: int) -> tuple[str | None, str | None, str]:
    suffix = line[anchor_end:].strip()
    severity_match = SEVERITY_RE.search(suffix)
    code_start = severity_match.end() if severity_match else 0
    if severity_match is None:
        severity_match = SEVERITY_RE.search(line[:anchor_end])
        code_start = 0
    severity = _normalize_severity(severity_match.group("severity")) if severity_match else None
    if severity_match is None:
        return None, None, ""
    code, message_start = _extract_diagnostic_code(suffix, code_start)
    message = _clean_diagnostic_message(suffix[message_start:])
    return severity, code, message


def _normalize_severity(value: str) -> str:
    normalized = value.lower()
    if normalized in {"warn", "warning"}:
        return "warning"
    if normalized in {"fatal error", "fatal"}:
        return "error"
    return normalized


def _extract_diagnostic_code(text: str, start: int) -> tuple[str | None, int]:
    remainder = text[start:]
    code_match = CODE_RE.match(remainder)
    if code_match is None:
        return None, start
    code = next(
        value
        for value in (
            code_match.group("bracket"),
            code_match.group("paren"),
            code_match.group("plain"),
        )
        if value is not None
    )
    return code, start + code_match.end()


def _clean_diagnostic_message(value: str) -> str:
    return value.strip(" \t:-")
