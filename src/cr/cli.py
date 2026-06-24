"""Command line entry points for cr.

The CLI owns argument parsing and command dispatch. Domain behavior lives in
the vcs, source, review, and ui packages so the command surface stays thin.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .review.changes import (
    change_annotations,
    change_risks,
    empty_message,
    first_changed_lines,
    link_targets,
    print_other_side_note,
    selected_changes,
    tree_annotations,
)
from .review.tree import render_change_tree
from .review.workflow import run_review
from .source.outline import (
    parse_file,
    render_outline,
)
from .source.purpose import describe_file
from .ui.browser import run_browser
from .ui.terminal import make_style
from .vcs import git


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        argv = ["browse"]
    elif argv[0].startswith("-"):
        argv = ["browse", *argv]
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
    browse.add_argument(
        "--copy-cmd",
        metavar="CMD",
        help=(
            "command used by browse 'copy path' and 'copy anchor'; receives "
            "text on stdin and supports {text}"
        ),
    )
    browse.add_argument(
        "--reveal-cmd",
        metavar="CMD",
        help=(
            "command used by browse 'reveal'; supports {file} and {dir}"
        ),
    )
    browse.add_argument(
        "--build-cmd",
        metavar="CMD",
        help=(
            "command used by browse 'build'; defaults to CR_BUILD_CMD or a "
            "known repo build"
        ),
    )
    browse.add_argument(
        "--test-cmd",
        metavar="CMD",
        help="command used by browse 'test'; defaults to CR_TEST_CMD",
    )
    browse.add_argument(
        "--lint-cmd",
        metavar="CMD",
        help="command used by browse 'lint'; defaults to CR_LINT_CMD",
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
    changes = selected_changes(args)
    if not changes:
        print(empty_message(args))
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

    print_other_side_note(args)
    print(style.bold("Changed file tree:"))
    first_lines = first_changed_lines(changes, args)
    targets = link_targets(changes, first_lines, args)
    risks = change_risks(changes)
    annotations = change_annotations(
        changes,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    annotations_for_tree = tree_annotations(annotations, first_lines, risks)
    for line in render_change_tree(
        changes,
        annotations_for_tree,
        style=style,
        link_targets=targets,
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
    return run_review(args)


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
