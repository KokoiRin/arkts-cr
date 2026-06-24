"""Interactive review browser for cr.

This module owns the browse session state, terminal rendering, key command
mapping, path filtering, and editor handoff. The CLI parser only delegates to
``run_browser`` so interactive behavior stays local as it grows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import termios
import tty

from ..review.changes import (
    change_hunk_lines,
    empty_message,
    is_code_file,
    modified_names,
    parse_change_symbols,
    selected_changes,
    sort_changes,
)
from ..review.risk import risk_hints
from ..review.tree import (
    DEFAULT_PATH_CONTEXT_DIRS,
    format_change_summary,
    shorten_path,
    style_change_summary,
)
from ..source.purpose import describe_file
from ..vcs import git
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri


@dataclass
class BrowserState:
    changes: list[git.FileChange]
    commits: list[git.CommitSummary] = field(default_factory=list)
    first_line_cache: dict[str, int | None] = field(default_factory=dict)
    file_line_cache: dict[str, list[str]] = field(default_factory=dict)
    selected: int = 0
    list_scroll: int = 0
    commit_scroll: int = 0
    file_scroll: int = 0
    mode: str = "list"
    filter_text: str = ""

    @property
    def visible_changes(self) -> list[git.FileChange]:
        return filter_changes_by_query(self.changes, self.filter_text)

    def clamp_selection(self) -> None:
        total = len(self.commits) if self.mode == "commits" else len(self.visible_changes)
        if total == 0:
            self.selected = 0
            if self.mode == "file":
                self.mode = "list"
            return
        self.selected = max(0, min(self.selected, total - 1))

    def clear_render_cache(self) -> None:
        self.first_line_cache.clear()
        self.file_line_cache.clear()
        self.file_scroll = 0

    def set_filter(self, query: str) -> None:
        self.filter_text = query.strip()
        self.mode = "list"
        self.selected = 0
        self.list_scroll = 0
        self.file_scroll = 0
        self.clamp_selection()

    def clear_filter(self) -> None:
        self.set_filter("")


@dataclass
class BrowseTreeRow:
    label: str
    change: git.FileChange | None = None
    change_index: int | None = None


@dataclass
class _BrowseTreeNode:
    name: str
    children: dict[str, "_BrowseTreeNode"] = field(default_factory=dict)
    change: git.FileChange | None = None
    change_index: int | None = None


def run_browser(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    state = BrowserState(changes=_load_browse_changes(args))
    _show_commits_when_empty(state, args)
    raw_keys = _use_raw_keys()

    if not raw_keys:
        _print_lines(_browse_help_lines(style))
    while True:
        state.clamp_selection()
        visible = state.visible_changes
        if raw_keys:
            _draw_browse_screen(state, args, style)
        prompt = _browse_prompt(state.mode)
        if not raw_keys:
            if state.mode == "commits":
                _print_lines(_browse_commit_lines(state.commits, style, selected=None))
            elif state.mode == "list":
                _print_lines(
                    _browse_list_lines(
                        visible,
                        args,
                        style,
                        selected=None,
                        total_changes=len(state.changes),
                        filter_text=state.filter_text,
                    )
                )
            elif visible:
                state.clamp_selection()
                _print_lines(
                    _browse_file_lines(
                        visible[state.selected],
                        state.selected,
                        len(visible),
                        args,
                        style,
                    )
                )
            else:
                _print_lines(
                    _empty_browse_lines(
                        args,
                        state.filter_text,
                        total_changes=len(state.changes),
                    )
                )
                state.mode = "list"

        command_result = _read_browse_command(prompt, raw_keys)
        if command_result == "__eof__":
            return 0
        if command_result == "__interrupt__":
            return 130
        command = command_result

        if command == "filter_prompt":
            query = _read_filter_query()
            if query != "__interrupt__":
                state.set_filter(query)
            continue
        if command.startswith("/") and not raw_keys:
            state.set_filter(command[1:])
            continue
        if command.startswith("filter "):
            state.set_filter(command.removeprefix("filter "))
            continue
        if command in {"c", "clear"}:
            state.clear_filter()
            continue
        if command in {"q", "quit", "exit"}:
            return 0
        if command in {"g", "commits", "log"}:
            state.commits = _load_recent_commits()
            state.mode = "commits"
            state.selected = 0
            state.commit_scroll = 0
            state.clamp_selection()
            continue
        if command in {"h", "?", "help"}:
            if raw_keys:
                state.mode = "list"
            else:
                _print_lines(_browse_help_lines(style))
            continue
        if command in {"o", "open"}:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                _open_change(visible[state.selected], args)
            else:
                print("No changed file to open.")
            continue
        if command in {"r", "refresh"}:
            if state.mode == "commits":
                state.commits = _load_recent_commits()
                state.commit_scroll = 0
            else:
                state.changes = _load_browse_changes(args)
                state.clear_render_cache()
                state.mode = "list"
                state.list_scroll = 0
                _show_commits_when_empty(state, args)
            state.clamp_selection()
            continue
        if command in {"s", "summary", "list", "ls", "b", "back"}:
            state.mode = "list"
            state.file_scroll = 0
            continue
        if command in {"down", "j"}:
            if state.mode == "file":
                _scroll_file(state, 1, args, style)
            else:
                _move_selection(state, 1)
            continue
        if command in {"up", "k"}:
            if state.mode == "file":
                _scroll_file(state, -1, args, style)
            else:
                _move_selection(state, -1)
            continue
        if command in {"pagedown", "space", "d"}:
            if state.mode == "file":
                _scroll_file(state, _page_step(), args, style)
            else:
                _move_selection(state, _page_step())
            continue
        if command in {"pageup", "u"}:
            if state.mode == "file":
                _scroll_file(state, -_page_step(), args, style)
            else:
                _move_selection(state, -_page_step())
            continue
        if command in {"home", "0"}:
            if state.mode == "file":
                state.file_scroll = 0
            else:
                state.selected = 0
            continue
        if command in {"end", "$"}:
            if state.mode == "file":
                state.file_scroll = _max_file_scroll(state, args, style)
            else:
                total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
                if total:
                    state.selected = total - 1
            continue
        if command in {"enter", "right", "l"}:
            if state.mode == "commits":
                _select_commit(state, args)
            elif state.visible_changes:
                state.mode = "file"
                state.file_scroll = 0
            continue
        if command in {"left", "h"}:
            state.mode = "list"
            state.file_scroll = 0
            continue
        if command in {"n", "next"}:
            visible = state.visible_changes
            if visible:
                state.selected = min(state.selected + 1, len(visible) - 1)
                state.mode = "file"
                state.file_scroll = 0
            continue
        if command in {"p", "prev", "previous"}:
            if state.visible_changes:
                state.selected = max(state.selected - 1, 0)
                state.mode = "file"
                state.file_scroll = 0
            continue
        if command.isdigit():
            choice = int(command)
            if state.mode == "commits":
                if 1 <= choice <= len(state.commits):
                    state.selected = choice - 1
                    _select_commit(state, args)
                else:
                    print(f"Choose 1-{len(state.commits)}.")
                continue
            visible = state.visible_changes
            if 1 <= choice <= len(visible):
                state.selected = choice - 1
                state.mode = "file"
            else:
                print(f"Choose 1-{len(visible)}.")
            continue
        if command:
            print(
                "Unknown command. Use arrows, Enter, /, c, a number, "
                "o, n, p, b, g, r, h, or q."
            )


def filter_changes_by_query(
    changes: list[git.FileChange],
    query: str,
) -> list[git.FileChange]:
    normalized = query.strip().casefold()
    if not normalized:
        return changes
    return [change for change in changes if normalized in change.path.casefold()]


def _load_browse_changes(args: argparse.Namespace) -> list[git.FileChange]:
    return sort_changes(selected_changes(args), args.sort)


def _load_recent_commits() -> list[git.CommitSummary]:
    try:
        return git.recent_commits()
    except git.GitError:
        return []


def _show_commits_when_empty(state: BrowserState, args: argparse.Namespace) -> None:
    if state.changes or args.base or args.ref_range:
        return
    state.commits = _load_recent_commits()
    if state.commits:
        state.mode = "commits"
        state.selected = 0


def _select_commit(state: BrowserState, args: argparse.Namespace) -> None:
    if not state.commits:
        print("No recent commits.")
        return
    state.clamp_selection()
    commit = state.commits[state.selected]
    args.ref_range = git.commit_ref_range(commit)
    args.base = None
    args.staged = False
    args.all_changes = False
    args.untracked = False
    state.filter_text = ""
    state.changes = _load_browse_changes(args)
    state.clear_render_cache()
    state.mode = "list"
    state.selected = 0
    state.list_scroll = 0
    state.clamp_selection()


def _move_selection(state: BrowserState, delta: int) -> None:
    total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
    if not total:
        return
    state.selected = max(0, min(state.selected + delta, total - 1))


def _scroll_file(
    state: BrowserState,
    delta: int,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    max_scroll = _max_file_scroll(state, args, style)
    state.file_scroll = max(0, min(state.file_scroll + delta, max_scroll))


def _max_file_scroll(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> int:
    visible = state.visible_changes
    if not visible:
        return 0
    state.clamp_selection()
    lines = _cached_file_lines(
        state,
        visible[state.selected],
        state.selected,
        len(visible),
        args,
        style,
    )
    body_count = max(0, len(lines) - 1)
    return max(0, body_count - _file_body_capacity())


def _page_step() -> int:
    return max(5, _screen_height() - 8)


def _screen_height() -> int:
    return max(8, shutil.get_terminal_size((100, 30)).lines)


def _file_body_capacity() -> int:
    return max(1, _screen_height() - 3)


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    state.clamp_selection()
    visible = state.visible_changes
    max_lines = _screen_height() - 1
    if state.mode == "commits":
        lines = [
            *_browse_help_lines(style),
            *_browse_commit_screen_lines(
                state,
                style,
                max(1, max_lines - len(_browse_help_lines(style))),
            ),
        ]
    elif state.mode == "list":
        lines = [
            *_browse_help_lines(style),
            *_browse_list_screen_lines(
                state,
                args,
                style,
                max(1, max_lines - len(_browse_help_lines(style))),
            ),
        ]
    elif visible:
        lines = _browse_file_screen_lines(
            state,
            visible[state.selected],
            state.selected,
            len(visible),
            args,
            style,
            max_lines,
        )
    else:
        lines = _empty_browse_lines(
            args,
            state.filter_text,
            total_changes=len(state.changes),
        )
    print("\033[2J\033[H", end="")
    _print_lines(lines[:max_lines])


def _browse_prompt(mode: str) -> str:
    if mode == "file":
        return "cr:file> "
    if mode == "commits":
        return "cr:commits> "
    return "cr:list> "


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("Interactive review"),
        "  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list",
        "  /: filter files     c: clear filter      o: open in editor",
        "  PgUp/PgDn or u/d: page    Home/End: jump",
        "  n/p: next/previous        g: recent commits    r: refresh    q: quit",
        "",
    ]


def _browse_list_lines(
    changes: list[git.FileChange],
    args: argparse.Namespace,
    style: TerminalStyle,
    selected: int | None = None,
    total_changes: int | None = None,
    filter_text: str = "",
) -> list[str]:
    total_changes = len(changes) if total_changes is None else total_changes
    if not changes:
        return _empty_browse_lines(args, filter_text, total_changes=total_changes)
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    lines = [
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    ]
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(changes)}/{total_changes} matches, c to clear)"
        )
    rows = _browse_tree_rows(changes)
    label_width = max(len(row.label) for row in rows)
    index_width = len(str(len(changes)))
    for row in rows:
        lines.append(
            _format_browse_tree_row(
                row,
                selected,
                index_width,
                label_width,
                style,
            )
        )
    lines.append("")
    return lines


def _browse_list_screen_lines(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    changes = state.visible_changes
    if not changes:
        return _empty_browse_lines(
            args,
            state.filter_text,
            total_changes=len(state.changes),
        )[:max_lines]
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    lines = [
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    ]
    if state.filter_text:
        lines.append(
            f"Filter: {state.filter_text} "
            f"({len(changes)}/{len(state.changes)} matches, c to clear)"
        )
    if len(changes) > 1:
        lines.append("Enter: open file   PgUp/PgDn: page   Home/End: jump")
    rows = _browse_tree_rows(changes)
    selected_row = _selected_tree_row(rows, state.selected)
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = _ensure_window(state.list_scroll, selected_row, len(rows), row_capacity)
    state.list_scroll = start
    end = min(len(rows), start + row_capacity)
    visible_rows = rows[start:end]
    index_width = len(str(len(changes)))
    label_width = max(len(row.label) for row in visible_rows)
    for row in visible_rows:
        lines.append(
            _format_browse_tree_row(
                row,
                state.selected,
                index_width,
                label_width,
                style,
            )
        )
    if len(rows) > row_capacity:
        lines.append(style.dim(f"showing rows {start + 1}-{end}/{len(rows)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def _browse_tree_rows(changes: list[git.FileChange]) -> list[BrowseTreeRow]:
    common_dir = _browser_common_changed_dir(changes)
    root = _BrowseTreeNode("")
    for index, change in enumerate(changes):
        _insert_browse_tree(root, change, index, common_dir)

    root_label = _browser_compact_root_label(common_dir)
    child_prefix = "   " if root_label else ""
    rows = _render_browse_tree_children(root, child_prefix)
    if root_label and rows:
        return [BrowseTreeRow(f"└─ {root_label}"), *rows]
    return rows


def _insert_browse_tree(
    root: _BrowseTreeNode,
    change: git.FileChange,
    change_index: int,
    common_dir: list[str],
) -> None:
    node = root
    parts = [part for part in change.path.split("/") if part]
    if common_dir and parts[: len(common_dir)] == common_dir:
        parts = parts[len(common_dir) :]
    for part in parts:
        node = node.children.setdefault(part, _BrowseTreeNode(part))
    node.change = change
    node.change_index = change_index


def _render_browse_tree_children(
    node: _BrowseTreeNode,
    prefix: str,
) -> list[BrowseTreeRow]:
    rows: list[BrowseTreeRow] = []
    items = sorted(node.children.values(), key=lambda child: child.name)
    for index, child in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└─" if is_last else "├─"
        rows.append(
            BrowseTreeRow(
                f"{prefix}{branch} {child.name}",
                child.change,
                child.change_index,
            )
        )
        child_prefix = prefix + ("   " if is_last else "│  ")
        rows.extend(_render_browse_tree_children(child, child_prefix))
    return rows


def _format_browse_tree_row(
    row: BrowseTreeRow,
    selected: int | None,
    index_width: int,
    label_width: int,
    style: TerminalStyle,
) -> str:
    if row.change is None or row.change_index is None:
        return f"  {' ' * index_width}  {_style_tree_directory(row.label, style)}"

    marker = ">" if selected == row.change_index else " "
    status = " modified" if row.change.status == "modified" else ""
    styled_label = _style_tree_file(
        row.label,
        label_width,
        style,
    )
    return (
        f"{marker} {str(row.change_index + 1).rjust(index_width)}  "
        f"{styled_label}  "
        f"{style_change_summary(row.change, style)}"
        f"{status}"
    )


def _style_tree_directory(label: str, style: TerminalStyle) -> str:
    return style.path(label)


def _style_tree_file(
    label: str,
    width: int,
    style: TerminalStyle,
) -> str:
    guide, filename = _split_tree_label(label)
    padding = " " * max(0, width - len(label))
    return f"{style.path(guide)}{style.file_path(filename + padding)}"


def _split_tree_label(label: str) -> tuple[str, str]:
    marker = "─ "
    if marker not in label:
        return "", label
    index = label.rfind(marker) + len(marker)
    return label[:index], label[index:]


def _selected_tree_row(rows: list[BrowseTreeRow], selected: int) -> int:
    for index, row in enumerate(rows):
        if row.change_index == selected:
            return index
    return 0


def _browser_common_changed_dir(changes: list[git.FileChange]) -> list[str]:
    dirs = [[part for part in change.path.split("/") if part][:-1] for change in changes]
    if not dirs:
        return []
    common = dirs[0]
    for directory in dirs[1:]:
        index = 0
        limit = min(len(common), len(directory))
        while index < limit and common[index] == directory[index]:
            index += 1
        common = common[:index]
        if not common:
            return []
    return common


def _browser_compact_root_label(common_dir: list[str]) -> str:
    if not common_dir:
        return ""
    prefix = ".../" if len(common_dir) > DEFAULT_PATH_CONTEXT_DIRS else ""
    return prefix + "/".join(common_dir[-DEFAULT_PATH_CONTEXT_DIRS:])


def _browse_commit_lines(
    commits: list[git.CommitSummary],
    style: TerminalStyle,
    selected: int | None = None,
) -> list[str]:
    if not commits:
        return [
            "No recent commits.",
            "",
        ]
    lines = [
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Choose a commit to review its files.",
    ]
    index_width = len(str(len(commits)))
    for index, commit in enumerate(commits, start=1):
        marker = ">" if selected == index - 1 else " "
        short_hash = commit.commit[:8]
        lines.append(
            f"{marker} {str(index).rjust(index_width)}  "
            f"{style.dim(short_hash)}  {commit.authored_at}  {commit.subject}"
        )
    lines.append("")
    return lines


def _browse_commit_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    commits = state.commits
    if not commits:
        return ["No recent commits.", ""]
    lines = [
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Enter: review commit   PgUp/PgDn: page   Home/End: jump",
    ]
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = _ensure_window(state.commit_scroll, state.selected, len(commits), row_capacity)
    state.commit_scroll = start
    end = min(len(commits), start + row_capacity)
    index_width = len(str(len(commits)))
    for index, commit in enumerate(commits[start:end], start=start + 1):
        marker = ">" if state.selected == index - 1 else " "
        short_hash = commit.commit[:8]
        lines.append(
            f"{marker} {str(index).rjust(index_width)}  "
            f"{style.dim(short_hash)}  {commit.authored_at}  {commit.subject}"
        )
    if len(commits) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(commits)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def _empty_browse_lines(
    args: argparse.Namespace,
    filter_text: str = "",
    total_changes: int = 0,
) -> list[str]:
    if filter_text:
        return [
            f"No changes match filter: {filter_text} ({total_changes} total).",
            "Press c to clear the filter.",
            "",
        ]
    return [empty_message(args)]


def _browse_file_screen_lines(
    state: BrowserState,
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    lines = _cached_file_lines(state, change, index, total, args, style)
    if len(lines) <= max_lines:
        state.file_scroll = 0
        return lines
    header = lines[:1]
    body = lines[1:]
    body_capacity = max(1, max_lines - 2)
    max_scroll = max(0, len(body) - body_capacity)
    state.file_scroll = max(0, min(state.file_scroll, max_scroll))
    start = state.file_scroll
    end = min(len(body), start + body_capacity)
    footer = style.dim(
        f"showing {start + 1}-{end}/{len(body)}   "
        "↑/↓ scroll   PgUp/PgDn page   b back"
    )
    return [*header, *body[start:end], footer]


def _browse_file_lines(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> list[str]:
    first_line = git.first_changed_line(
        change.path,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    anchor = f":{first_line}" if first_line else ""
    lines = [
        f"{style.bold(f'File {index + 1}/{total}')}  "
        f"{style.path(shorten_path(change.path), _link_target(change.path, first_line, args))}"
        f"{style.dim(anchor)}  "
        f"{style.bold(format_change_summary(change))}"
    ]
    risks = risk_hints(change.path)
    if risks:
        lines.append(f"  {style.warning('risk: ' + ', '.join(risks))}")
    if change.status != "deleted" and is_code_file(change.path):
        try:
            symbols = parse_change_symbols(change, args)
            lines.append(f"  purpose: {describe_file(change.path, symbols)}")
            names = modified_names(
                change.path,
                staged=args.staged,
                all_changes=args.all_changes,
                base=args.base,
                ref_range=args.ref_range,
            )
            lines.append(f"  modified: {', '.join(names)}")
        except FileNotFoundError:
            lines.append("  (file deleted or unavailable)")
    lines.extend(
        change_hunk_lines(
            change,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
            context=args.context,
            style=style,
        )
    )
    lines.append("")
    return lines


def _cached_first_changed_line(
    state: BrowserState,
    change: git.FileChange,
    args: argparse.Namespace,
) -> int | None:
    if change.path not in state.first_line_cache:
        state.first_line_cache[change.path] = git.first_changed_line(
            change.path,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
        )
    return state.first_line_cache[change.path]


def _cached_file_lines(
    state: BrowserState,
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> list[str]:
    key = _file_cache_key(change, index, total, args)
    if key not in state.file_line_cache:
        state.file_line_cache[key] = _browse_file_lines(
            change,
            index,
            total,
            args,
            style,
        )
    return state.file_line_cache[key]


def _file_cache_key(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
) -> str:
    return "\x1f".join(
        [
            change.path,
            str(index),
            str(total),
            str(args.context),
            str(args.staged),
            str(args.all_changes),
            args.base or "",
            args.ref_range or "",
        ]
    )


def _ensure_window(
    current_start: int,
    selected: int,
    total: int,
    capacity: int,
) -> int:
    if total <= capacity:
        return 0
    max_start = max(0, total - capacity)
    start = max(0, min(current_start, max_start))
    if selected < start:
        return selected
    if selected >= start + capacity:
        return min(max_start, selected - capacity + 1)
    return start


def _use_raw_keys() -> bool:
    return bool(
        hasattr(sys.stdin, "isatty")
        and sys.stdin.isatty()
        and hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
    )


def _read_browse_command(prompt: str, raw_keys: bool) -> str:
    if not raw_keys:
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return "__eof__"
        except KeyboardInterrupt:
            print()
            return "__interrupt__"

    print(prompt, end="", flush=True)
    try:
        key = _read_raw_key()
    except KeyboardInterrupt:
        print()
        return "__interrupt__"
    print()
    return key


def _read_filter_query() -> str:
    try:
        return input("filter> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "__interrupt__"


def _read_raw_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x03":
            raise KeyboardInterrupt
        if char in {"\r", "\n"}:
            return "enter"
        if char == "\x1b":
            second = sys.stdin.read(1)
            if second != "[":
                return ""
            sequence = ""
            while len(sequence) < 6:
                piece = sys.stdin.read(1)
                if not piece:
                    break
                sequence += piece
                if piece.isalpha() or piece == "~":
                    break
            return {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
                "H": "home",
                "F": "end",
                "1~": "home",
                "4~": "end",
                "5~": "pageup",
                "6~": "pagedown",
            }.get(sequence, "")
        return {
            "j": "down",
            "k": "up",
            "l": "right",
            "h": "left",
            "u": "pageup",
            "d": "pagedown",
            " ": "space",
            "/": "filter_prompt",
            "\x04": "__eof__",
        }.get(char, char)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _open_change(change: git.FileChange, args: argparse.Namespace) -> None:
    line = git.first_changed_line(
        change.path,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    repo_file = git.repo_path(change.path)
    command = _open_command(repo_file, line, args.open_cmd)
    if not command:
        print(
            "No editor opener found. Set --open-cmd or CR_OPEN_CMD, "
            "for example: --open-cmd 'code -g {fileline}'"
        )
        return
    try:
        subprocess.Popen(command)
    except OSError as exc:
        print(f"Open failed: {exc}")
        return
    print(f"Opened {shorten_path(change.path)}{':' + str(line) if line else ''}")


def _open_command(
    file_path: Path,
    line: int | None,
    configured: str | None = None,
) -> list[str] | None:
    template = configured or os.environ.get("CR_OPEN_CMD")
    if template:
        return _format_open_template(template, file_path, line)

    line_number = line or 1
    for executable in ("code", "cursor"):
        if shutil.which(executable):
            return [executable, "-g", f"{file_path}:{line_number}"]

    if platform.system() == "Darwin" and shutil.which("open"):
        return ["open", str(file_path)]

    return None


def _format_open_template(
    template: str,
    file_path: Path,
    line: int | None,
) -> list[str]:
    line_number = line or 1
    replacements = {
        "file": str(file_path),
        "line": str(line_number),
        "fileline": f"{file_path}:{line_number}",
    }
    return [part.format(**replacements) for part in shlex.split(template)]


def _link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)
