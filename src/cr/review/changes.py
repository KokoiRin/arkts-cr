"""Shared review change selection and per-file facts.

This module owns the rules that turn a CLI review scope into changed files,
anchors, annotations, hunk lines, and status messages. Command handlers can use
these helpers without knowing the Git and source-outline details behind them.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .hunks import render_diff_hunks
from .risk import risk_hints
from .tree import format_change_summary, shorten_path
from ..source.outline import (
    CODE_EXTENSIONS,
    modified_symbols,
    parse_outline,
)
from ..source.purpose import describe_file
from ..source.outline import render_outline_body
from ..ui.terminal import TerminalStyle, file_uri, vscode_uri
from ..vcs import git


def selected_changes(args: argparse.Namespace) -> list[git.FileChange]:
    changes = git.changed_files(
        args.paths,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
        include_untracked=args.untracked,
    )
    return filter_changes(changes, code_only=args.code)


def other_change_counts(args: argparse.Namespace) -> dict[str, int]:
    if args.all_changes:
        return {"staged": 0, "unstaged": 0}
    if args.base or args.ref_range:
        return {"staged": 0, "unstaged": 0}
    staged_changes = filter_changes(
        git.changed_files(args.paths, staged=True),
        code_only=args.code,
    )
    unstaged_changes = filter_changes(
        git.changed_files(
            args.paths,
            staged=False,
            include_untracked=args.untracked,
        ),
        code_only=args.code,
    )
    if args.staged:
        return {"staged": 0, "unstaged": len(unstaged_changes)}
    return {"staged": len(staged_changes), "unstaged": 0}


def first_changed_lines(
    changes: list[git.FileChange],
    args: argparse.Namespace,
) -> dict[str, int]:
    lines: dict[str, int] = {}
    for change in changes:
        line = git.first_changed_line(
            change.path,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
        )
        if line is not None:
            lines[change.path] = line
    return lines


def link_targets(
    changes: list[git.FileChange],
    first_lines: dict[str, int],
    args: argparse.Namespace,
) -> dict[str, str]:
    return {
        change.path: link_target(change.path, first_lines.get(change.path), args)
        for change in changes
    }


def link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)


def change_anchors(first_lines: dict[str, int]) -> dict[str, str]:
    return {path: f"{shorten_path(path)}:{line}" for path, line in first_lines.items()}


def change_risks(changes: list[git.FileChange]) -> dict[str, list[str]]:
    risks: dict[str, list[str]] = {}
    for change in changes:
        hints = risk_hints(change.path)
        if hints:
            risks[change.path] = hints
    return risks


def tree_annotations(
    annotations: dict[str, str],
    first_lines: dict[str, int],
    risks: dict[str, list[str]],
) -> dict[str, str]:
    paths = set(annotations) | set(first_lines) | set(risks)
    result: dict[str, str] = {}
    for path in paths:
        parts: list[str] = []
        if annotations.get(path):
            parts.append(annotations[path])
        if path in first_lines:
            parts.append(f"line {first_lines[path]}")
        if risks.get(path):
            parts.append(f"risk: {', '.join(risks[path])}")
        result[path] = " ".join(parts)
    return result


def filter_changes(
    changes: list[git.FileChange],
    code_only: bool = False,
) -> list[git.FileChange]:
    if code_only:
        return [change for change in changes if is_code_file(change.path)]
    return changes


def seen_paths(args: argparse.Namespace) -> set[str]:
    paths: set[str] = set()
    for value in args.seen:
        for path in value.split(","):
            normalized = path.strip().replace("\\", "/")
            if normalized:
                paths.add(normalized)
    return paths


def sort_changes(
    changes: list[git.FileChange],
    sort_mode: str,
) -> list[git.FileChange]:
    if sort_mode == "git":
        return changes
    if sort_mode == "path":
        return sorted(changes, key=lambda change: change.path)
    if sort_mode == "churn":
        return sorted(changes, key=lambda change: (-change_churn(change), change.path))
    if sort_mode == "risk":
        return sorted(
            changes,
            key=lambda change: (
                0 if risk_hints(change.path) else 1,
                -change_churn(change),
                change.path,
            ),
        )
    return changes


def change_churn(change: git.FileChange) -> int:
    return (change.added or 0) + (change.deleted or 0)


def print_other_side_note(
    args: argparse.Namespace,
    other_changes: dict[str, int] | None = None,
) -> None:
    if args.all_changes:
        return
    if args.base or args.ref_range:
        return
    other_changes = other_changes or other_change_counts(args)
    if args.staged and other_changes.get("unstaged", 0):
        print("Note: unstaged changes also exist; omit --staged to review them.")
        print()
    elif not args.staged and other_changes.get("staged", 0):
        print("Note: staged changes also exist; use --staged to review them.")
        print()


def modified_names(
    path: str,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> list[str]:
    try:
        symbols = parse_outline(git.file_text(path, range_right_ref(ref_range)))
    except FileNotFoundError:
        return ["unknown"]
    return modified_symbols(
        symbols,
        git.changed_new_lines(
            path,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
        ),
    )


def print_change_hunks(
    change: git.FileChange,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    context: int = 2,
    style: TerminalStyle | None = None,
) -> None:
    for line in change_hunk_lines(
        change,
        staged=staged,
        all_changes=all_changes,
        base=base,
        ref_range=ref_range,
        context=context,
        style=style,
    ):
        print(line)


def change_hunk_lines(
    change: git.FileChange,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    context: int = 2,
    style: TerminalStyle | None = None,
) -> list[str]:
    style = style or TerminalStyle(False)
    lines = render_diff_hunks(
        git.file_diff(
            change.path,
            context=context,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
        ),
        style=style,
    )
    rendered = [f"  {style.bold('changes:')}"]
    if not lines:
        return [*rendered, "  (no text diff available)"]
    for line in lines:
        rendered.append(f"  {line}")
    return rendered


def print_risk_hints(risks: list[str], style: TerminalStyle | None = None) -> None:
    style = style or TerminalStyle(False)
    if risks:
        print(f"  {style.warning('risk: ' + ', '.join(risks))}")


def change_annotations(
    changes: list[git.FileChange],
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> dict[str, str]:
    annotations: dict[str, str] = {}
    for change in changes:
        if change.status != "deleted" and is_code_file(change.path):
            names = modified_names(
                change.path,
                staged=staged,
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            )
            annotations[change.path] = f"modified: {', '.join(names)}"
    return annotations


def empty_message(args: argparse.Namespace) -> str:
    if getattr(args, "remaining", False):
        return "No remaining changes."
    if args.ref_range:
        return f"No changes in {args.ref_range}."
    if args.base:
        return f"No changes from {args.base}."
    if args.all_changes:
        return "No local changes."
    if args.staged:
        return "No staged changes."
    return "No working tree changes."


def format_file_header(
    change: git.FileChange,
    anchors: dict[str, str],
    style: TerminalStyle | None = None,
    targets: dict[str, str] | None = None,
) -> str:
    style = style or TerminalStyle(False)
    targets = targets or {}
    anchor = anchors.get(change.path)
    suffix = f" @ {anchor}" if anchor else ""
    return (
        f"{style.path(shorten_path(change.path), targets.get(change.path))} "
        f"{style.bold(format_counts(change))}"
        f"{style.dim(suffix)}"
    )


def is_code_file(path: str) -> bool:
    return Path(path).suffix in CODE_EXTENSIONS


def format_counts(change: git.FileChange) -> str:
    return format_change_summary(change)


def parse_change_symbols(change: git.FileChange, args: argparse.Namespace):
    return parse_outline(git.file_text(change.path, range_right_ref(args.ref_range)))


def render_modified_outline_lines(
    change: git.FileChange,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> list[str]:
    symbols = parse_change_symbols(change, args)
    names = set(
        modified_names(
            change.path,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
        )
    )
    lines = [
        f"  purpose: {describe_file(change.path, symbols)}",
        f"  modified: {', '.join(names)}",
        f"  {style.bold('outline:')}",
    ]
    lines.extend(f"  {line}" for line in render_outline_body(symbols, names - {"unknown"}))
    return lines


def range_right_ref(ref_range: str | None) -> str | None:
    if ref_range is None:
        return None
    return git.range_right_ref(ref_range)

