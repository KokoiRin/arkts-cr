"""Structured review data assembly.

This module gathers the same facts used by terminal rendering into plain
dictionaries so alternate output formats can stay consistent with human output.
"""

from __future__ import annotations

from . import git
from .hunks import render_diff_hunks
from .outline import CODE_EXTENSIONS, modified_symbols, parse_outline
from .purpose import describe_file
from .risk import risk_hints
from .tree import format_change_summary


def build_review_data(
    changes: list[git.FileChange],
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    include_hunks: bool = True,
    other_changes: dict[str, int] | None = None,
    context: int = 2,
    seen_paths: set[str] | None = None,
) -> dict[str, object]:
    seen_paths = seen_paths or set()
    files = [
        _file_data(
            change,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
            include_hunks=include_hunks,
            context=context,
            seen=change.path in seen_paths,
        )
        for change in changes
    ]
    return {
        "summary": {
            "files": len(changes),
            "added": _sum_known(change.added for change in changes),
            "deleted": _sum_known(change.deleted for change in changes),
        },
        "other_changes": other_changes or {"staged": 0, "unstaged": 0},
        "files": files,
    }


def _file_data(
    change: git.FileChange,
    staged: bool,
    all_changes: bool,
    base: str | None,
    ref_range: str | None,
    include_hunks: bool,
    context: int,
    seen: bool,
) -> dict[str, object]:
    first_changed_line = git.first_changed_line(
        change.path,
        staged=staged,
        all_changes=all_changes,
        base=base,
        ref_range=ref_range,
    )
    data: dict[str, object] = {
        "path": change.path,
        "old_path": change.old_path,
        "status": change.status,
        "added": change.added,
        "deleted": change.deleted,
        "first_changed_line": first_changed_line,
        "anchor": (
            f"{change.path}:{first_changed_line}" if first_changed_line else None
        ),
        "risk_hints": risk_hints(change.path),
        "summary": format_change_summary(change),
        "seen": seen,
        "is_code": _is_code_file(change.path),
        "purpose": None,
        "modified_symbols": [],
        "hunks": (
            _hunks(change, staged, all_changes, base, ref_range, context)
            if include_hunks
            else []
        ),
    }

    if change.status != "deleted" and _is_code_file(change.path):
        try:
            symbols = parse_outline(
                git.file_text(change.path, _range_right_ref(ref_range))
            )
        except FileNotFoundError:
            data["modified_symbols"] = ["unknown"]
            return data
        data["purpose"] = describe_file(change.path, symbols)
        data["modified_symbols"] = modified_symbols(
            symbols,
            git.changed_new_lines(
                change.path,
                staged=staged,
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
        )
    return data


def _hunks(
    change: git.FileChange,
    staged: bool,
    all_changes: bool,
    base: str | None,
    ref_range: str | None,
    context: int,
) -> list[str]:
    return render_diff_hunks(
        git.file_diff(
            change.path,
            context=context,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
        )
    )


def _sum_known(values: object) -> int:
    return sum(value for value in values if value is not None)


def _is_code_file(path: str) -> bool:
    return any(path.endswith(extension) for extension in CODE_EXTENSIONS)


def _range_right_ref(ref_range: str | None) -> str | None:
    if ref_range is None:
        return None
    return git.range_right_ref(ref_range)
