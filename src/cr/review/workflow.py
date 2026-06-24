"""Command workflow for `cr review`.

The CLI delegates here after parsing arguments. This module owns review
selection, seen/pick handling, alternate output formats, and terminal detail
rendering as one deep module interface.
"""

from __future__ import annotations

import argparse
import json
import sys

from .changes import (
    change_anchors,
    change_annotations,
    change_risks,
    empty_message,
    first_changed_lines,
    format_file_header,
    is_code_file,
    link_targets,
    other_change_counts,
    print_change_hunks,
    print_other_side_note,
    print_risk_hints,
    render_modified_outline_lines,
    seen_paths,
    selected_changes,
    sort_changes,
    tree_annotations,
)
from .data import build_review_data
from .prompt import render_prompt_handoff
from .summary import render_review_summary
from .tree import render_change_tree
from ..ui.terminal import make_style


def run_review(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    changes = sort_changes(selected_changes(args), args.sort)
    reviewed_paths = seen_paths(args)
    if args.remaining:
        changes = [change for change in changes if change.path not in reviewed_paths]
    if args.pick is not None:
        picked = _pick_change(changes, args.pick)
        if picked is None:
            return 2
        changes = [picked]
    if not changes:
        if args.json:
            print(
                json.dumps(
                    {
                        "summary": {"files": 0, "added": 0, "deleted": 0},
                        "other_changes": other_change_counts(args),
                        "files": [],
                    }
                )
            )
            return 0
        print(empty_message(args))
        return 0

    include_hunks = not args.summary and not args.no_hunks
    other_changes = other_change_counts(args)
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
                    seen_paths=reviewed_paths,
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
                    seen_paths=reviewed_paths,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(style.bold("Review changes:"))
    print_other_side_note(args, other_changes)
    first_lines = first_changed_lines(changes, args)
    anchors = change_anchors(first_lines)
    targets = link_targets(changes, first_lines, args)
    risks = change_risks(changes)
    annotations = change_annotations(
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
        targets,
        risks,
        seen_paths=reviewed_paths,
        style=style,
    ):
        print(line)
    print()
    print(style.bold("Changed file tree:"))
    annotations_for_tree = tree_annotations(annotations, first_lines, risks)
    for line in render_change_tree(
        changes,
        annotations_for_tree,
        style=style,
        link_targets=targets,
    ).splitlines():
        print(f"  {line}")
    if args.summary:
        return 0

    _print_file_details(changes, anchors, risks, targets, args, style)
    return 0


def _pick_change(changes, pick: int):
    total = len(changes)
    if total == 0:
        print("cr: no changed files to pick", file=sys.stderr)
        return None
    if pick > total:
        print(f"cr: --pick must be between 1 and {total}", file=sys.stderr)
        return None
    return changes[pick - 1]


def _print_file_details(
    changes,
    anchors,
    risks,
    targets,
    args: argparse.Namespace,
    style,
) -> None:
    for change in changes:
        print()
        print(format_file_header(change, anchors, style, targets))
        print_risk_hints(risks.get(change.path, []), style)
        if change.status == "deleted":
            if not args.no_hunks:
                print_change_hunks(
                    change,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    context=args.context,
                    style=style,
                )
        elif is_code_file(change.path):
            try:
                lines = render_modified_outline_lines(change, args, style)
            except FileNotFoundError:
                print("  (file deleted or unavailable)")
                continue
            print(lines[0])
            if not args.no_hunks:
                print_change_hunks(
                    change,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                    context=args.context,
                    style=style,
                )
            for line in lines[1:]:
                print(line)
        elif not args.no_hunks:
            print_change_hunks(
                change,
                staged=args.staged,
                all_changes=args.all_changes,
                base=args.base,
                ref_range=args.ref_range,
                context=args.context,
                style=style,
            )

