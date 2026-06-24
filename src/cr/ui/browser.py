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
import select
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
    build: "BuildState | None" = None
    previous_scope: "ReviewScope | None" = None
    selected_commit: git.CommitSummary | None = None
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


@dataclass(frozen=True)
class ReviewScope:
    staged: bool
    all_changes: bool
    base: str | None
    ref_range: str | None
    untracked: bool


@dataclass
class BuildState:
    command: list[str]
    process: subprocess.Popen[bytes]
    lines: list[str] = field(default_factory=list)
    last_rendered_panel: list[str] = field(default_factory=list)
    partial: str = ""
    returncode: int | None = None
    start_error: str | None = None
    stop_requested: bool = False

    @property
    def running(self) -> bool:
        return self.returncode is None and self.start_error is None


@dataclass(frozen=True)
class ScreenLayout:
    content_height: int
    build_height: int
    prompt_row: int
    build_start_row: int | None

    @property
    def max_render_lines(self) -> int:
        return max(0, self.prompt_row - 1)


def run_browser(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    state = BrowserState(changes=_load_browse_changes(args))
    _show_commits_when_empty(state, args)
    raw_keys = _use_raw_keys()
    needs_redraw = True

    if not raw_keys:
        _print_lines(_browse_help_lines(style))
    while True:
        _poll_build(state.build)
        state.clamp_selection()
        visible = state.visible_changes
        if raw_keys and needs_redraw:
            _draw_browse_screen(state, args, style)
            needs_redraw = False
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

        command_result = _read_browse_command(
            prompt,
            raw_keys,
            tick_when_idle=state.build is not None and state.build.running,
        )
        if command_result == "__tick__":
            _draw_build_panel_only(state.build, style)
            continue
        if command_result == "__eof__":
            return 0
        if command_result == "__interrupt__":
            return 130
        command = command_result

        if command == "filter_prompt":
            query = _read_filter_query()
            if query != "__interrupt__":
                state.set_filter(query)
                needs_redraw = True
            continue
        if command == "command_prompt":
            command = _read_command_query()
            if command == "__interrupt__":
                continue
        if command.startswith("/") and not raw_keys:
            state.set_filter(command[1:])
            needs_redraw = True
            continue
        if command.startswith("filter "):
            state.set_filter(command.removeprefix("filter "))
            needs_redraw = True
            continue
        if command in {"c", "clear"}:
            state.clear_filter()
            needs_redraw = True
            continue
        if command in {"q", "quit", "exit"}:
            return 0
        if command in {"g", "commits", "log"}:
            state.commits = _load_recent_commits()
            state.mode = "commits"
            state.selected = 0
            state.commit_scroll = 0
            state.clamp_selection()
            needs_redraw = True
            continue
        if command in {"w", "worktree", "workspace"}:
            if state.previous_scope is not None:
                _restore_previous_scope(state, args)
                needs_redraw = True
            continue
        if command in {"h", "?", "help"}:
            if raw_keys:
                state.mode = "list"
                needs_redraw = True
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
        if command in {"build", "compile"}:
            if raw_keys:
                _start_build(state, args)
                needs_redraw = True
            else:
                _run_build_foreground(args)
            continue
        if command in {"stop", "cancel"}:
            _stop_build(state)
            needs_redraw = True
            continue
        if command in {"rebuild", "rerun"}:
            if raw_keys:
                _rerun_build(state, args)
                needs_redraw = True
            else:
                _run_build_foreground(args)
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
            needs_redraw = True
            continue
        if command in {"s", "summary", "list", "ls", "b", "back"}:
            if command in {"b", "back"} and state.selected_commit is not None:
                state.mode = "commits"
                state.file_scroll = 0
            else:
                state.mode = "list"
                state.file_scroll = 0
            needs_redraw = True
            continue
        if command in {"down", "j"}:
            if state.mode == "file":
                _scroll_file(state, 1, args, style)
            else:
                _move_selection(state, 1)
            needs_redraw = True
            continue
        if command in {"up", "k"}:
            if state.mode == "file":
                _scroll_file(state, -1, args, style)
            else:
                _move_selection(state, -1)
            needs_redraw = True
            continue
        if command in {"pagedown", "space", "d"}:
            if state.mode == "file":
                _scroll_file(state, _page_step(), args, style)
            else:
                _move_selection(state, _page_step())
            needs_redraw = True
            continue
        if command in {"pageup", "u"}:
            if state.mode == "file":
                _scroll_file(state, -_page_step(), args, style)
            else:
                _move_selection(state, -_page_step())
            needs_redraw = True
            continue
        if command in {"home", "0"}:
            if state.mode == "file":
                state.file_scroll = 0
            else:
                state.selected = 0
            needs_redraw = True
            continue
        if command in {"end", "$"}:
            if state.mode == "file":
                state.file_scroll = _max_file_scroll(state, args, style)
            else:
                total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
                if total:
                    state.selected = total - 1
            needs_redraw = True
            continue
        if command in {"enter", "right", "l"}:
            if state.mode == "commits":
                _select_commit(state, args)
                needs_redraw = True
            elif state.visible_changes:
                state.mode = "file"
                state.file_scroll = 0
                needs_redraw = True
            continue
        if command in {"left", "h"}:
            if state.selected_commit is not None:
                state.mode = "commits"
                state.file_scroll = 0
            else:
                state.mode = "list"
                state.file_scroll = 0
            needs_redraw = True
            continue
        if command in {"n", "next"}:
            visible = state.visible_changes
            if visible:
                state.selected = min(state.selected + 1, len(visible) - 1)
                state.mode = "file"
                state.file_scroll = 0
                needs_redraw = True
            continue
        if command in {"p", "prev", "previous"}:
            if state.visible_changes:
                state.selected = max(state.selected - 1, 0)
                state.mode = "file"
                state.file_scroll = 0
                needs_redraw = True
            continue
        if command.isdigit():
            choice = int(command)
            if state.mode == "commits":
                if 1 <= choice <= len(state.commits):
                    state.selected = choice - 1
                    _select_commit(state, args)
                    needs_redraw = True
                else:
                    print(f"Choose 1-{len(state.commits)}.")
                continue
            visible = state.visible_changes
            if 1 <= choice <= len(visible):
                state.selected = choice - 1
                state.mode = "file"
                needs_redraw = True
            else:
                print(f"Choose 1-{len(visible)}.")
            continue
        if command:
            print(
                "Unknown command. Use arrows, Enter, /, c, a number, "
                "o, n, p, b, g, r, h, build, stop, rerun, or q."
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
    if state.previous_scope is None:
        state.previous_scope = _capture_scope(args)
    state.selected_commit = commit
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


def _capture_scope(args: argparse.Namespace) -> ReviewScope:
    return ReviewScope(
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
        untracked=args.untracked,
    )


def _restore_previous_scope(state: BrowserState, args: argparse.Namespace) -> None:
    scope = state.previous_scope
    if scope is None:
        return
    args.staged = scope.staged
    args.all_changes = scope.all_changes
    args.base = scope.base
    args.ref_range = scope.ref_range
    args.untracked = scope.untracked
    state.selected_commit = None
    state.previous_scope = None
    state.filter_text = ""
    state.changes = _load_browse_changes(args)
    state.clear_render_cache()
    state.mode = "list"
    state.selected = 0
    state.list_scroll = 0
    _show_commits_when_empty(state, args)
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


def _build_panel_height(build: BuildState | None, available_lines: int) -> int:
    if build is None:
        return 0
    return max(3, min(10, max(5, available_lines // 4), max(3, available_lines - 6)))


def _screen_layout(build: BuildState | None, rows: int | None = None) -> ScreenLayout:
    terminal_rows = _screen_height() if rows is None else max(8, rows)
    max_render_lines = max(1, terminal_rows - 1)
    build_height = _build_panel_height(build, max_render_lines)
    content_height = max(1, max_render_lines - build_height)
    build_start_row = content_height + 1 if build_height else None
    return ScreenLayout(
        content_height=content_height,
        build_height=build_height,
        prompt_row=terminal_rows,
        build_start_row=build_start_row,
    )


def _build_panel_lines(
    build: BuildState | None,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    if build is None or max_lines <= 0:
        return []
    width = shutil.get_terminal_size((100, 30)).columns
    status = _build_status(build)
    command = " ".join(shlex.quote(part) for part in build.command)
    lines = [
        style.dim("─" * min(width, 100)),
        f"{style.bold('Build')} {status}  {style.dim(command)}",
    ]
    capacity = max(0, max_lines - len(lines))
    body = build.lines[-capacity:] if capacity else []
    if capacity and not body:
        body = [style.dim("(waiting for output)")]
    return [*lines, *body][-max_lines:]


def _build_status(build: BuildState) -> str:
    if build.start_error is not None:
        return "failed to start"
    if build.returncode is None and build.stop_requested:
        return "stopping"
    if build.returncode is None:
        return "running"
    if not build.command:
        return "idle"
    if build.stop_requested:
        return "stopped"
    if build.returncode == 0:
        return "succeeded"
    return f"failed ({build.returncode})"


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    state.clamp_selection()
    visible = state.visible_changes
    layout = _screen_layout(state.build)
    max_lines = layout.max_render_lines
    content_lines = layout.content_height
    build_panel_height = layout.build_height
    if state.mode == "commits":
        lines = [
            *_browse_help_lines(style),
            *_browse_commit_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style))),
            ),
        ]
    elif state.mode == "list":
        lines = [
            *_browse_help_lines(style),
            *_browse_list_screen_lines(
                state,
                args,
                style,
                max(1, content_lines - len(_browse_help_lines(style))),
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
            content_lines,
        )
    else:
        lines = _empty_browse_lines(
            args,
            state.filter_text,
            total_changes=len(state.changes),
        )
    if build_panel_height:
        content_frame = lines[:content_lines]
        if len(content_frame) < content_lines:
            content_frame.extend([""] * (content_lines - len(content_frame)))
        lines = [
            *content_frame,
            *_build_panel_lines(state.build, style, build_panel_height),
        ]
    print("\033[2J\033[H", end="")
    _print_lines(lines[:max_lines])
    print(
        f"\033[{layout.prompt_row};1H\033[2K{_browse_prompt(state.mode)}",
        end="",
        flush=True,
    )
    if state.build is not None:
        state.build.last_rendered_panel = _build_panel_lines(
            state.build,
            style,
            build_panel_height,
        )


def _draw_build_panel_only(
    build: BuildState | None,
    style: TerminalStyle,
) -> None:
    if build is None:
        return
    layout = _screen_layout(build)
    height = layout.build_height
    lines = _build_panel_lines(build, style, height)
    if lines == build.last_rendered_panel:
        return
    build.last_rendered_panel = lines
    start_row = layout.build_start_row or 1
    output: list[str] = ["\0337", f"\033[{start_row};1H"]
    for index in range(height):
        output.append("\033[2K")
        if index < len(lines):
            output.append(_fit_terminal_line(lines[index]))
        if index != height - 1:
            output.append("\n")
    output.append("\0338")
    sys.stdout.write("".join(output))
    sys.stdout.flush()


def _fit_terminal_line(line: str) -> str:
    if "\033[" in line:
        return line
    width = shutil.get_terminal_size((100, 30)).columns
    return line[: max(0, width - 1)]


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
        "  : command prompt    build/stop/rerun: repo build task",
        "  PgUp/PgDn or u/d: page    Home/End: jump",
        "  n/p: next/previous        g: commits    w: worktree    r: refresh    q: quit",
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
        "Choose a commit to review its files. Press w to return to worktree.",
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
        "Enter: review commit   b: back here   w: worktree   PgUp/PgDn: page",
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


def _read_browse_command(
    prompt: str,
    raw_keys: bool,
    tick_when_idle: bool = False,
) -> str:
    if not raw_keys:
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return "__eof__"
        except KeyboardInterrupt:
            print()
            return "__interrupt__"

    try:
        key = _read_raw_key(timeout=0.2 if tick_when_idle else None)
    except KeyboardInterrupt:
        print()
        return "__interrupt__"
    if key == "__tick__":
        return key
    return key


def _read_filter_query() -> str:
    try:
        return input("filter> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "__interrupt__"


def _read_command_query() -> str:
    try:
        return input("command> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "__interrupt__"


def _read_raw_key(timeout: float | None = None) -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if timeout is not None:
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                return "__tick__"
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
            ":": "command_prompt",
            "\x04": "__eof__",
        }.get(char, char)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _start_build(state: BrowserState, args: argparse.Namespace) -> None:
    repo = git.repo_root()
    command = _build_command(repo, args.build_cmd)
    if command is None:
        state.build = _failed_build_state(
            [],
            "No build command configured. Set --build-cmd or CR_BUILD_CMD; "
            "DouyinHarmony defaults to './remote buildEntry --app douyin'.",
        )
        return
    if state.build is not None and state.build.running:
        state.build.lines.append("Build is already running.")
        return
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError as exc:
        state.build = _failed_build_state(command, f"Build failed to start: {exc}")
        return
    if process.stdout is not None:
        os.set_blocking(process.stdout.fileno(), False)
    state.build = BuildState(
        command=command,
        process=process,
        lines=[f"started in {repo}"],
    )


def _stop_build(state: BrowserState) -> None:
    if state.build is None:
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait()
        state.build = BuildState(
            command=[],
            process=process,
            lines=["No build is running."],
            returncode=0,
        )
        return
    if not state.build.running:
        state.build.lines.append("No build is running.")
        return
    state.build.stop_requested = True
    state.build.lines.append("Stopping build...")
    try:
        state.build.process.terminate()
    except OSError as exc:
        state.build.lines.append(f"Build stop failed: {exc}")


def _rerun_build(state: BrowserState, args: argparse.Namespace) -> None:
    if state.build is not None and state.build.running:
        state.build.lines.append("Build is already running. Stop it before rerun.")
        return
    _start_build(state, args)


def _run_build_foreground(args: argparse.Namespace) -> None:
    repo = git.repo_root()
    command = _build_command(repo, args.build_cmd)
    if command is None:
        print(
            "No build command configured. Set --build-cmd or CR_BUILD_CMD; "
            "DouyinHarmony defaults to './remote buildEntry --app douyin'."
        )
        return
    print(f"Build: {' '.join(shlex.quote(part) for part in command)}")
    try:
        result = subprocess.run(command, cwd=repo, check=False)
    except OSError as exc:
        print(f"Build failed to start: {exc}")
        return
    if result.returncode == 0:
        print("Build succeeded.")
    else:
        print(f"Build failed with exit code {result.returncode}.")


def _failed_build_state(command: list[str], message: str) -> BuildState:
    process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
    return BuildState(
        command=command,
        process=process,
        lines=[message],
        returncode=1,
        start_error=message,
    )


def _poll_build(build: BuildState | None) -> None:
    if build is None or build.start_error is not None:
        return
    if build.returncode is not None:
        return
    _drain_build_output(build)
    returncode = build.process.poll()
    if returncode is not None and build.returncode is None:
        _drain_build_output(build)
        if build.partial:
            build.lines.append(build.partial)
            build.partial = ""
        build.returncode = returncode
        if build.stop_requested:
            message = "Build stopped."
        else:
            message = (
                "Build succeeded."
                if returncode == 0
                else f"Build failed with exit code {returncode}."
            )
        build.lines.append(message)
        if build.process.stdout is not None:
            build.process.stdout.close()


def _drain_build_output(build: BuildState) -> None:
    if build.process.stdout is None:
        return
    fd = build.process.stdout.fileno()
    while True:
        try:
            chunk = os.read(fd, 4096)
        except BlockingIOError:
            break
        except OSError as exc:
            build.lines.append(f"output read failed: {exc}")
            break
        if not chunk:
            break
        text = chunk.decode(errors="replace")
        combined = build.partial + text
        parts = combined.splitlines(keepends=True)
        build.partial = ""
        for part in parts:
            if part.endswith("\n") or part.endswith("\r"):
                build.lines.append(part.rstrip("\r\n"))
            else:
                build.partial = part
        if len(build.lines) > 200:
            build.lines = build.lines[-200:]


def _build_command(repo: Path, configured: str | None = None) -> list[str] | None:
    template = configured or os.environ.get("CR_BUILD_CMD")
    if template:
        return shlex.split(template)
    if repo.name == "DouyinHarmony" and (repo / "remote").exists():
        return ["./remote", "buildEntry", "--app", "douyin"]
    return None


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
