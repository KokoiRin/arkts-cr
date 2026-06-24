"""Command line entry points for cr.

The CLI stays thin: it handles argument parsing and terminal formatting, while
Git access and source outline parsing live in small focused modules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import git
from .browser import run_browser
from .hunks import render_diff_hunks
from .outline import (
    CODE_EXTENSIONS,
    modified_symbols,
    parse_file,
    parse_outline,
    render_outline,
    render_outline_body,
)
from .prompt import render_prompt_handoff
from .purpose import describe_file
from .review_data import build_review_data
from .risk import risk_hints
from .summary import render_review_summary
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri
from .tree import format_change_summary, render_change_tree
from .tree import shorten_path


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["browse"]
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except git.GitError as exc:
        print(f"cr: git error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"cr: file not found: {exc.filename}", file=sys.stderr)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cr",
        description="Lightweight terminal code review helper.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    browse = subparsers.add_parser("browse", help="open an interactive review browser")
    _add_filter_args(browse)
    browse.add_argument(
        "--context",
        type=_non_negative_int,
        default=2,
        metavar="N",
        help="number of context lines around diff hunks",
    )
    browse.add_argument(
        "--sort",
        choices=("git", "risk", "churn", "path"),
        default="git",
        help="order review files by Git order, risk, churn, or path",
    )
    browse.add_argument(
        "--open-cmd",
        metavar="CMD",
        help=(
            "command used by browse 'o'; supports {file}, {line}, and {fileline}"
        ),
    )
    browse.set_defaults(func=cmd_browse)

    diff = subparsers.add_parser("diff", help="show current Git diff summary")
    _add_filter_args(diff)
    diff.set_defaults(func=cmd_diff)

    outline = subparsers.add_parser("outline", help="show a rough file outline")
    outline.add_argument("file")
    outline.set_defaults(func=cmd_outline)

    review = subparsers.add_parser("review", help="show diff summary with code outlines")
    _add_filter_args(review)
    review.add_argument(
        "--summary",
        action="store_true",
        help="only show summary and changed file tree",
    )
    review.add_argument(
        "--no-hunks",
        action="store_true",
        help="hide per-file diff hunks while keeping purpose, symbols, and outline",
    )
    output = review.add_mutually_exclusive_group()
    output.add_argument(
        "--json",
        action="store_true",
        help="emit structured JSON instead of terminal text",
    )
    output.add_argument(
        "--prompt",
        action="store_true",
        help="emit compact Markdown for AI or chat review handoff",
    )
    review.add_argument(
        "--context",
        type=_non_negative_int,
        default=2,
        metavar="N",
        help="number of context lines around diff hunks",
    )
    review.add_argument(
        "--sort",
        choices=("git", "risk", "churn", "path"),
        default="git",
        help="order review files by Git order, risk, churn, or path",
    )
    review.add_argument(
        "--pick",
        type=_positive_int,
        metavar="N",
        help="show only the Nth file after filtering and sorting",
    )
    review.add_argument(
        "--seen",
        action="append",
        default=[],
        metavar="PATH",
        help="mark a changed path as already reviewed; repeat or use commas",
    )
    review.add_argument(
        "--remaining",
        action="store_true",
        help="hide files listed with --seen",
    )
    review.set_defaults(func=cmd_review)
    return parser


def cmd_diff(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    changes = _selected_changes(args)
    if not changes:
        print(_empty_message(args))
        return 0

    stat_paths = [change.path for change in changes] if args.code else args.paths
    stat = git.diff_stat(
        stat_paths,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    if stat:
        print(style.bold("Git diff stat:"))
        print(stat)
        print()

    _print_other_side_note(args)
    print(style.bold("Changed file tree:"))
    first_lines = _first_changed_lines(changes, args)
    link_targets = _link_targets(changes, first_lines, args)
    risks = _change_risks(changes)
    annotations = _change_annotations(
        changes,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    tree_annotations = _tree_annotations(annotations, first_lines, risks)
    for line in render_change_tree(
        changes,
        tree_annotations,
        style=style,
        link_targets=link_targets,
    ).splitlines():
        print(f"  {line}")
    return 0


def cmd_outline(args: argparse.Namespace) -> int:
    path = Path(args.file)
    symbols = parse_file(path)
    print(f"purpose: {describe_file(path, symbols)}")
    print(render_outline(path, symbols))
    return 0


def cmd_browse(args: argparse.Namespace) -> int:
    return run_browser(args)


def cmd_review(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    changes = _sort_changes(_selected_changes(args), args.sort)
    seen_paths = _seen_paths(args)
    if args.remaining:
        changes = [change for change in changes if change.path not in seen_paths]
    if args.pick is not None:
        total = len(changes)
        if total == 0:
            print("cr: no changed files to pick", file=sys.stderr)
            return 2
        if args.pick > total:
            print(f"cr: --pick must be between 1 and {total}", file=sys.stderr)
            return 2
        changes = [changes[args.pick - 1]]
    if not changes:
        if args.json:
            print(
                json.dumps(
                    {
                        "summary": {"files": 0, "added": 0, "deleted": 0},
                        "other_changes": _other_change_counts(args),
                        "files": [],
                    }
                )
            )
            return 0
        print(_empty_message(args))
        return 0

    include_hunks = not args.summary and not args.no_hunks
    other_changes = _other_change_counts(args)
    if args.prompt:
        print(
            render_prompt_handoff(
                build_review_data(
                    changes,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    include_hunks=include_hunks,
                    other_changes=other_changes,
                    context=args.context,
                    seen_paths=seen_paths,
                )
            )
        )
        return 0
    if args.json:
        print(
            json.dumps(
                build_review_data(
                    changes,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    include_hunks=include_hunks,
                    other_changes=other_changes,
                    context=args.context,
                    seen_paths=seen_paths,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(style.bold("Review changes:"))
    _print_other_side_note(args, other_changes)
    first_lines = _first_changed_lines(changes, args)
    anchors = _change_anchors(first_lines)
    link_targets = _link_targets(changes, first_lines, args)
    risks = _change_risks(changes)
    annotations = _change_annotations(
        changes,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    for line in render_review_summary(
        changes,
        annotations,
        anchors,
        link_targets,
        risks,
        seen_paths=seen_paths,
        style=style,
    ):
        print(line)
    print()
    print(style.bold("Changed file tree:"))
    tree_annotations = _tree_annotations(annotations, first_lines, risks)
    for line in render_change_tree(
        changes,
        tree_annotations,
        style=style,
        link_targets=link_targets,
    ).splitlines():
        print(f"  {line}")
    if args.summary:
        return 0

    for index, change in enumerate(changes):
        print()
        print(_format_file_header(change, anchors, style, link_targets))
        _print_risk_hints(risks.get(change.path, []), style)
        if change.status == "deleted":
            if not args.no_hunks:
                _print_change_hunks(
                    change,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    context=args.context,
                    style=style,
                )
        elif _is_code_file(change.path):
            try:
                symbols = _parse_change_symbols(change, args)
            except FileNotFoundError:
                print("  (file deleted or unavailable)")
                continue

            print(f"  purpose: {describe_file(change.path, symbols)}")
            if not args.no_hunks:
                _print_change_hunks(
                    change,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    context=args.context,
                    style=style,
                )
            names = set(
                _modified_names(
                    change.path,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                )
            )
            print(f"  modified: {', '.join(names)}")
            print(f"  {style.bold('outline:')}")
            for line in render_outline_body(symbols, names - {"unknown"}):
                print(f"  {line}")
        else:
            if not args.no_hunks:
                _print_change_hunks(
                    change,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    context=args.context,
                    style=style,
                )
    return 0


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("context must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("context must be >= 0")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pick must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("pick must be >= 1")
    return parsed


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument(
        "--staged",
        action="store_true",
        help="review staged/index changes instead of unstaged working tree changes",
    )
    scope.add_argument(
        "--all",
        action="store_true",
        dest="all_changes",
        help="review combined staged and unstaged tracked changes",
    )
    scope.add_argument(
        "--base",
        metavar="REF",
        help="review changes between REF and the current working tree or HEAD",
    )
    scope.add_argument(
        "--range",
        dest="ref_range",
        metavar="OLD..NEW",
        help="review changes between two refs without changing checkout",
    )
    parser.add_argument(
        "--code",
        action="store_true",
        help="only show ArkTS / ETS / TypeScript files",
    )
    parser.add_argument(
        "--untracked",
        action="store_true",
        help="include untracked files; can be slow in very large working trees",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="colorize terminal output",
    )
    parser.add_argument(
        "--links",
        choices=("auto", "always", "never"),
        default="auto",
        help="emit clickable terminal hyperlinks for changed files",
    )
    parser.add_argument(
        "--link-scheme",
        choices=("file", "vscode"),
        default="file",
        help="link target scheme for clickable file paths",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="optional Git pathspecs, such as src/pages or README.md",
    )


def _selected_changes(args: argparse.Namespace) -> list[git.FileChange]:
    changes = git.changed_files(
        args.paths,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
        include_untracked=args.untracked,
    )
    return _filter_changes(changes, code_only=args.code)


def _other_change_counts(args: argparse.Namespace) -> dict[str, int]:
    if args.all_changes:
        return {"staged": 0, "unstaged": 0}
    if args.base or args.ref_range:
        return {"staged": 0, "unstaged": 0}
    staged_changes = _filter_changes(
        git.changed_files(args.paths, staged=True),
        code_only=args.code,
    )
    unstaged_changes = _filter_changes(
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


def _first_changed_lines(
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


def _link_targets(
    changes: list[git.FileChange],
    first_lines: dict[str, int],
    args: argparse.Namespace,
) -> dict[str, str]:
    return {
        change.path: _link_target(change.path, first_lines.get(change.path), args)
        for change in changes
    }


def _link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)


def _change_anchors(first_lines: dict[str, int]) -> dict[str, str]:
    return {path: f"{shorten_path(path)}:{line}" for path, line in first_lines.items()}


def _change_risks(changes: list[git.FileChange]) -> dict[str, list[str]]:
    risks: dict[str, list[str]] = {}
    for change in changes:
        hints = risk_hints(change.path)
        if hints:
            risks[change.path] = hints
    return risks


def _tree_annotations(
    annotations: dict[str, str],
    first_lines: dict[str, int],
    risks: dict[str, list[str]],
) -> dict[str, str]:
    paths = set(annotations) | set(first_lines) | set(risks)
    tree_annotations: dict[str, str] = {}
    for path in paths:
        parts: list[str] = []
        if annotations.get(path):
            parts.append(annotations[path])
        if path in first_lines:
            parts.append(f"line {first_lines[path]}")
        if risks.get(path):
            parts.append(f"risk: {', '.join(risks[path])}")
        tree_annotations[path] = " ".join(parts)
    return tree_annotations


def _filter_changes(
    changes: list[git.FileChange],
    code_only: bool = False,
) -> list[git.FileChange]:
    if code_only:
        return [change for change in changes if _is_code_file(change.path)]
    return changes


def _seen_paths(args: argparse.Namespace) -> set[str]:
    paths: set[str] = set()
    for value in args.seen:
        for path in value.split(","):
            normalized = path.strip().replace("\\", "/")
            if normalized:
                paths.add(normalized)
    return paths


def _sort_changes(
    changes: list[git.FileChange],
    sort_mode: str,
) -> list[git.FileChange]:
    if sort_mode == "git":
        return changes
    if sort_mode == "path":
        return sorted(changes, key=lambda change: change.path)
    if sort_mode == "churn":
        return sorted(changes, key=lambda change: (-_change_churn(change), change.path))
    if sort_mode == "risk":
        return sorted(
            changes,
            key=lambda change: (
                0 if risk_hints(change.path) else 1,
                -_change_churn(change),
                change.path,
            ),
        )
    return changes


def _change_churn(change: git.FileChange) -> int:
    return (change.added or 0) + (change.deleted or 0)


def _print_other_side_note(
    args: argparse.Namespace,
    other_changes: dict[str, int] | None = None,
) -> None:
    if args.all_changes:
        return
    if args.base or args.ref_range:
        return
    other_changes = other_changes or _other_change_counts(args)
    if args.staged and other_changes.get("unstaged", 0):
        print("Note: unstaged changes also exist; omit --staged to review them.")
        print()
    elif not args.staged and other_changes.get("staged", 0):
        print("Note: staged changes also exist; use --staged to review them.")
        print()


def _modified_names(
    path: str,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> list[str]:
    try:
        symbols = parse_outline(git.file_text(path, _range_right_ref(ref_range)))
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


def _print_change_hunks(
    change: git.FileChange,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    context: int = 2,
    style: TerminalStyle | None = None,
) -> None:
    _print_lines(
        _change_hunk_lines(
            change,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
            context=context,
            style=style,
        )
    )


def _change_hunk_lines(
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


def _print_risk_hints(risks: list[str], style: TerminalStyle | None = None) -> None:
    style = style or TerminalStyle(False)
    if risks:
        print(f"  {style.warning('risk: ' + ', '.join(risks))}")


def _change_annotations(
    changes: list[git.FileChange],
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> dict[str, str]:
    annotations: dict[str, str] = {}
    for change in changes:
        if change.status != "deleted" and _is_code_file(change.path):
            names = _modified_names(
                change.path,
                staged=staged,
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            )
            annotations[change.path] = f"modified: {', '.join(names)}"
    return annotations


def _empty_message(args: argparse.Namespace) -> str:
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


def _format_file_header(
    change: git.FileChange,
    anchors: dict[str, str],
    style: TerminalStyle | None = None,
    link_targets: dict[str, str] | None = None,
) -> str:
    style = style or TerminalStyle(False)
    link_targets = link_targets or {}
    anchor = anchors.get(change.path)
    suffix = f" @ {anchor}" if anchor else ""
    return (
        f"{style.path(shorten_path(change.path), link_targets.get(change.path))} "
        f"{style.bold(_format_counts(change))}"
        f"{style.dim(suffix)}"
    )


def _is_code_file(path: str) -> bool:
    return Path(path).suffix in CODE_EXTENSIONS


def _format_counts(change: git.FileChange) -> str:
    return format_change_summary(change)


def _parse_change_symbols(
    change: git.FileChange,
    args: argparse.Namespace,
):
    return parse_outline(git.file_text(change.path, _range_right_ref(args.ref_range)))


def _range_right_ref(ref_range: str | None) -> str | None:
    if ref_range is None:
        return None
    return git.range_right_ref(ref_range)
