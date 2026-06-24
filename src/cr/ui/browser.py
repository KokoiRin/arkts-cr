"""Interactive review browser for cr.

This module owns the browse session state, terminal rendering, key command
mapping, path filtering, and editor handoff. The CLI parser only delegates to
``run_browser`` so interactive behavior stays local as it grows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import signal
import platform
import select
import shlex
import shutil
import subprocess
import sys
import time
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


BROWSER_WORKSPACE_STATE_VERSION = 1
BUILD_STOP_KILL_GRACE_SECONDS = 2.0
TASK_LABELS = {
    "build": "Build",
    "test": "Test",
    "lint": "Lint",
}


@dataclass
class BrowserState:
    changes: list[git.FileChange]
    commits: list[git.CommitSummary] = field(default_factory=list)
    build: "BuildState | None" = None
    task_history: list["TaskRecord"] = field(default_factory=list)
    previous_scope: "ReviewScope | None" = None
    selected_commit: git.CommitSummary | None = None
    first_line_cache: dict[str, int | None] = field(default_factory=dict)
    file_line_cache: dict[str, list[str]] = field(default_factory=dict)
    selected: int = 0
    list_scroll: int = 0
    commit_scroll: int = 0
    command_scroll: int = 0
    file_scroll: int = 0
    mode: str = "list"
    filter_text: str = ""
    seen_paths: set[str] = field(default_factory=set)
    remaining_only: bool = False
    scope_selected: int = 0
    command_selected: int = 0
    command_filter_text: str = ""
    status_message: str = ""

    @property
    def visible_changes(self) -> list[git.FileChange]:
        changes = filter_changes_by_query(self.changes, self.filter_text)
        if self.remaining_only:
            return [change for change in changes if change.path not in self.seen_paths]
        return changes

    def clamp_selection(self) -> None:
        if self.mode == "commits":
            total = len(self.commits)
        elif self.mode == "scopes":
            total = len(_scope_home_entries())
        elif self.mode == "commands":
            total = len(_filtered_command_palette_entries(self))
        else:
            total = len(self.visible_changes)
        if total == 0:
            if self.mode == "scopes":
                self.scope_selected = 0
            elif self.mode == "commands":
                self.command_selected = 0
            else:
                self.selected = 0
            if self.mode == "file":
                self.mode = "list"
            return
        if self.mode == "scopes":
            self.scope_selected = max(0, min(self.scope_selected, total - 1))
        elif self.mode == "commands":
            self.command_selected = max(0, min(self.command_selected, total - 1))
        else:
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

    def set_command_filter(self, query: str) -> None:
        self.command_filter_text = query.strip()
        self.command_selected = 0
        self.command_scroll = 0
        self.clamp_selection()

    def clear_command_filter(self) -> None:
        self.set_command_filter("")


@dataclass
class BrowseTreeRow:
    label: str
    change: git.FileChange | None = None
    change_index: int | None = None


@dataclass(frozen=True)
class CommandEntry:
    command: str
    description: str
    action: str | None = None


@dataclass(frozen=True)
class CommandGroup:
    title: str
    entries: tuple[CommandEntry, ...]


@dataclass(frozen=True)
class ScopeHomeEntry:
    label: str
    description: str
    action: str | None = None


@dataclass(frozen=True)
class PaletteCommand:
    group: str
    label: str
    command: str
    description: str


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


@dataclass(frozen=True)
class TaskRecord:
    kind: str
    status: str
    command: list[str]
    returncode: int | None = None


@dataclass
class BuildState:
    command: list[str]
    process: subprocess.Popen[bytes]
    kind: str = "build"
    lines: list[str] = field(default_factory=list)
    last_rendered_panel: list[str] = field(default_factory=list)
    partial: str = ""
    returncode: int | None = None
    start_error: str | None = None
    process_group_id: int | None = None
    stop_requested: bool = False
    stop_requested_at: float | None = None
    stop_escalated: bool = False
    history_recorded: bool = False

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


@dataclass
class BrowserFrame:
    layout: ScreenLayout | None = None
    complete: bool = False
    build_panel: list[str] = field(default_factory=list)
    dirty: bool = True


def run_browser(args: argparse.Namespace) -> int:
    repo = git.repo_root()
    style = make_style(args.color, sys.stdout, args.links)
    workspace_state = None
    if _should_restore_browser_workspace_state(args):
        workspace_state = _load_browser_workspace_state(repo)
        if workspace_state is not None:
            _restore_browser_workspace_scope(args, workspace_state)
    state = BrowserState(changes=_load_browse_changes(args))
    if workspace_state is not None:
        _restore_browser_workspace_state(state, args, workspace_state)
    _show_commits_when_empty(state, args)
    raw_keys = _use_raw_keys()
    frame = BrowserFrame()
    needs_redraw = True

    if not raw_keys:
        _print_lines(_browse_help_lines(style))
    while True:
        _poll_build(state.build)
        _record_completed_build(state)
        state.clamp_selection()
        visible = state.visible_changes
        if raw_keys and (needs_redraw or frame.dirty):
            _draw_browse_screen(state, args, style, frame)
            needs_redraw = False
        prompt = _browse_prompt(state.mode)
        if not raw_keys:
            if state.mode == "commits":
                _print_lines(
                    _browse_commit_lines(
                        state.commits,
                        style,
                        selected=None,
                        scope_label=_scope_label(state, args),
                    )
                )
            elif state.mode == "commands":
                _print_lines(_browse_command_lines(style, max_lines=_screen_height()))
            elif state.mode == "scopes":
                _print_lines(
                    [
                        _scope_context_line(state, args, style),
                        *_browse_scope_home_screen_lines(
                            state,
                            style,
                            max(1, _screen_height() - 2),
                        ),
                    ]
                )
            elif state.mode == "list":
                _print_lines(
                    _browse_list_lines(
                        visible,
                        args,
                        style,
                        selected=None,
                        total_changes=len(state.changes),
                        filter_text=state.filter_text,
                        scope_label=_scope_label(state, args),
                        seen_paths=state.seen_paths,
                        seen_count=sum(
                            1 for change in state.changes if change.path in state.seen_paths
                        ),
                        remaining_only=state.remaining_only,
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
                        _scope_label(state, args),
                        visible[state.selected].path in state.seen_paths,
                    )
                )
            else:
                _print_lines(
                    _empty_browse_lines(
                        args,
                        state.filter_text,
                        total_changes=len(state.changes),
                        scope_label=_scope_label(state, args),
                    )
                )
                state.mode = "list"

        command_result = _read_browse_command(
            prompt,
            raw_keys,
            tick_when_idle=state.build is not None and state.build.running,
        )
        if command_result == "__tick__":
            _draw_build_panel_only(state.build, style, frame, state.task_history)
            if frame.dirty:
                needs_redraw = True
            continue
        if command_result == "__eof__":
            _save_browser_workspace_state_on_exit(state, args, repo)
            return 0
        if command_result == "__interrupt__":
            _save_browser_workspace_state_on_exit(state, args, repo)
            return 130
        command = command_result
        if state.mode == "commands" and command in {"enter", "right", "l"}:
            palette_command = _selected_palette_command(state)
            if palette_command is None:
                continue
            command = palette_command.command

        if command == "filter_prompt":
            query = _read_filter_query(
                "command filter> " if state.mode == "commands" else "filter> "
            )
            if raw_keys:
                frame.dirty = True
            if query != "__interrupt__":
                if state.mode == "commands":
                    state.set_command_filter(query)
                else:
                    state.set_filter(query)
                needs_redraw = True
            elif raw_keys:
                needs_redraw = True
            continue
        if command == "command_prompt":
            command = _normalize_command_query(_read_command_query())
            if raw_keys:
                frame.dirty = True
            if command == "__interrupt__":
                if raw_keys:
                    needs_redraw = True
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
            if state.mode == "commands":
                state.clear_command_filter()
            else:
                state.clear_filter()
            needs_redraw = True
            continue
        if command in {"m", "seen", "done"}:
            _mark_selected_seen(state)
            needs_redraw = True
            continue
        if command in {"todo", "unseen", "unmark"}:
            _unmark_selected_seen(state)
            needs_redraw = True
            continue
        if command == "remaining":
            state.remaining_only = True
            state.mode = "list"
            state.selected = 0
            state.list_scroll = 0
            state.clamp_selection()
            needs_redraw = True
            continue
        if command in {"allfiles", "show all"}:
            state.remaining_only = False
            state.mode = "list"
            state.selected = 0
            state.list_scroll = 0
            state.clamp_selection()
            needs_redraw = True
            continue
        if command in {"q", "quit", "exit"}:
            _save_browser_workspace_state_on_exit(state, args, repo)
            return 0
        if command in {"commands", "cmds", "help commands"}:
            state.mode = "commands"
            needs_redraw = True
            continue
        if command in {"scopes", "scope"}:
            state.mode = "scopes"
            state.scope_selected = 0
            needs_redraw = True
            continue
        if command in {"g", "commits", "log"}:
            state.commits = _load_recent_commits()
            state.mode = "commits"
            state.selected_commit = None
            state.selected = 0
            state.commit_scroll = 0
            state.clamp_selection()
            needs_redraw = True
            continue
        if command == "worktree":
            _switch_review_scope(
                state,
                args,
                ReviewScope(False, False, None, None, _args_untracked(args)),
            )
            needs_redraw = True
            continue
        if command in {"w", "workspace"}:
            if state.previous_scope is not None:
                _restore_previous_scope(state, args)
            else:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, None, None, _args_untracked(args)),
                )
            needs_redraw = True
            continue
        if command in {"staged", "index"}:
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )
            needs_redraw = True
            continue
        if command == "all":
            _switch_review_scope(
                state,
                args,
                ReviewScope(False, True, None, None, _args_untracked(args)),
            )
            needs_redraw = True
            continue
        if command.startswith("base "):
            ref = command.removeprefix("base ").strip()
            if ref:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, ref, None, False),
                )
                needs_redraw = True
            continue
        if command.startswith("range "):
            ref_range = command.removeprefix("range ").strip()
            if ref_range:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, None, ref_range, False),
                )
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
                message = _open_change(visible[state.selected], args)
                _show_browser_message(state, message, raw_keys, frame)
                if raw_keys:
                    needs_redraw = True
            else:
                _show_browser_message(state, "No changed file to open.", raw_keys, frame)
                if raw_keys:
                    needs_redraw = True
            continue
        if command in {"build", "compile"}:
            if raw_keys:
                _start_build(state, args)
                needs_redraw = True
            else:
                _run_task_foreground(args, "build")
            continue
        if command in {"test", "tests"}:
            if raw_keys:
                _start_task(state, args, "test")
                needs_redraw = True
            else:
                _run_task_foreground(args, "test")
            continue
        if command == "lint":
            if raw_keys:
                _start_task(state, args, "lint")
                needs_redraw = True
            else:
                _run_task_foreground(args, "lint")
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
            if command in {"b", "back"} and state.mode in {"commands", "scopes"}:
                state.mode = "list"
                state.file_scroll = 0
            elif command in {"b", "back"} and state.mode == "file":
                state.mode = "list"
                state.file_scroll = 0
            elif command in {"b", "back"} and state.selected_commit is not None:
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
            elif state.mode == "scopes":
                state.scope_selected = 0
            elif state.mode == "commands":
                state.command_selected = 0
            else:
                state.selected = 0
            needs_redraw = True
            continue
        if command in {"end", "$"}:
            if state.mode == "file":
                state.file_scroll = _max_file_scroll(state, args, style)
            elif state.mode == "scopes":
                total = len(_scope_home_entries())
                if total:
                    state.scope_selected = total - 1
            elif state.mode == "commands":
                total = len(_filtered_command_palette_entries(state))
                if total:
                    state.command_selected = total - 1
            else:
                total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
                if total:
                    state.selected = total - 1
            needs_redraw = True
            continue
        if command in {"enter", "right", "l"}:
            if state.mode == "commits":
                message = _select_commit(state, args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                needs_redraw = True
            elif state.mode == "scopes":
                message = _select_scope_home_entry(state, args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                needs_redraw = True
            elif state.visible_changes:
                state.mode = "file"
                state.file_scroll = 0
                needs_redraw = True
            continue
        if command in {"left", "h"}:
            if state.mode in {"commands", "scopes"}:
                state.mode = "list"
                state.file_scroll = 0
            elif state.mode == "file":
                state.mode = "list"
                state.file_scroll = 0
            elif state.selected_commit is not None:
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
            if state.mode == "scopes":
                total = len(_scope_home_entries())
                if 1 <= choice <= total:
                    state.scope_selected = choice - 1
                    message = _select_scope_home_entry(state, args)
                    if message:
                        _show_browser_message(state, message, raw_keys, frame)
                    needs_redraw = True
                else:
                    _show_browser_message(state, f"Choose 1-{total}.", raw_keys, frame)
                    if raw_keys:
                        needs_redraw = True
                continue
            if state.mode == "commits":
                if 1 <= choice <= len(state.commits):
                    state.selected = choice - 1
                    message = _select_commit(state, args)
                    if message:
                        _show_browser_message(state, message, raw_keys, frame)
                    needs_redraw = True
                else:
                    _show_browser_message(
                        state,
                        f"Choose 1-{len(state.commits)}.",
                        raw_keys,
                        frame,
                    )
                    if raw_keys:
                        needs_redraw = True
                continue
            visible = state.visible_changes
            if 1 <= choice <= len(visible):
                state.selected = choice - 1
                state.mode = "file"
                needs_redraw = True
            else:
                _show_browser_message(state, f"Choose 1-{len(visible)}.", raw_keys, frame)
                if raw_keys:
                    needs_redraw = True
            continue
        if command:
            unknown_message = (
                "Unknown command. Open commands for available actions."
                if raw_keys
                else (
                    "Unknown command. Use arrows, Enter, /, c, a number, "
                    "o, n, p, b, g, r, h, m, remaining, build, stop, rerun, "
                    "test, lint, staged, all, base, range, or q."
                )
            )
            _show_browser_message(
                state,
                unknown_message,
                raw_keys,
                frame,
            )
            if raw_keys:
                needs_redraw = True


def filter_changes_by_query(
    changes: list[git.FileChange],
    query: str,
) -> list[git.FileChange]:
    normalized = query.strip().casefold()
    if not normalized:
        return changes
    return [change for change in changes if normalized in change.path.casefold()]


def _should_restore_browser_workspace_state(args: argparse.Namespace) -> bool:
    return (
        not args.staged
        and not args.all_changes
        and args.base is None
        and args.ref_range is None
        and not args.untracked
        and not args.paths
    )


def _mark_selected_seen(state: BrowserState) -> None:
    visible = state.visible_changes
    if not visible:
        return
    state.clamp_selection()
    state.seen_paths.add(visible[state.selected].path)
    state.clamp_selection()


def _unmark_selected_seen(state: BrowserState) -> None:
    visible = state.visible_changes
    if not visible:
        return
    state.clamp_selection()
    state.seen_paths.discard(visible[state.selected].path)
    state.clamp_selection()


def _browser_workspace_state_path(repo: Path) -> Path:
    return repo / ".git" / "cr" / "browse-state.json"


def _save_browser_workspace_state_on_exit(
    state: BrowserState,
    args: argparse.Namespace,
    repo: Path,
) -> None:
    if args.paths:
        return
    _save_browser_workspace_state(state, args, repo)


def _save_browser_workspace_state(
    state: BrowserState,
    args: argparse.Namespace,
    repo: Path,
) -> None:
    path = _browser_workspace_state_path(repo)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(
                _browser_workspace_state_data(state, args),
                ensure_ascii=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        tmp_path.replace(path)
    except OSError:
        return


def _browser_workspace_state_data(
    state: BrowserState,
    args: argparse.Namespace,
) -> dict[str, object]:
    visible = state.visible_changes
    selected_path = None
    if visible and 0 <= state.selected < len(visible):
        selected_path = visible[state.selected].path
    return {
        "version": BROWSER_WORKSPACE_STATE_VERSION,
        "scope": {
            "staged": bool(args.staged),
            "all_changes": bool(args.all_changes),
            "base": args.base,
            "ref_range": args.ref_range,
            "untracked": bool(args.untracked),
        },
        "filter_text": state.filter_text,
        "selected_path": selected_path,
        "selected_index": state.selected,
        "mode": "file" if state.mode == "file" else "list",
        "seen_paths": sorted(state.seen_paths),
        "remaining_only": state.remaining_only,
    }


def _load_browser_workspace_state(repo: Path) -> dict[str, object] | None:
    path = _browser_workspace_state_path(repo)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("version") != BROWSER_WORKSPACE_STATE_VERSION:
        return None
    scope = raw.get("scope")
    if not isinstance(scope, dict):
        return None
    return raw


def _restore_browser_workspace_state(
    state: BrowserState,
    args: argparse.Namespace,
    workspace_state: dict[str, object],
) -> None:
    _restore_browser_workspace_scope(args, workspace_state)
    filter_text = workspace_state.get("filter_text")
    state.filter_text = filter_text if isinstance(filter_text, str) else ""
    state.seen_paths = _string_set(workspace_state.get("seen_paths"))
    state.remaining_only = workspace_state.get("remaining_only") is True
    _restore_browser_workspace_selection(state, workspace_state)
    mode = workspace_state.get("mode")
    state.mode = "file" if mode == "file" and state.visible_changes else "list"
    state.list_scroll = 0
    state.file_scroll = 0
    state.commit_scroll = 0
    state.clamp_selection()


def _restore_browser_workspace_scope(
    args: argparse.Namespace,
    workspace_state: dict[str, object],
) -> None:
    scope = workspace_state.get("scope")
    if not isinstance(scope, dict):
        return
    args.staged = bool(scope.get("staged"))
    args.all_changes = bool(scope.get("all_changes"))
    args.base = _optional_string(scope.get("base"))
    args.ref_range = _optional_string(scope.get("ref_range"))
    args.untracked = bool(scope.get("untracked"))


def _restore_browser_workspace_selection(
    state: BrowserState,
    workspace_state: dict[str, object],
) -> None:
    visible = state.visible_changes
    if not visible:
        state.selected = 0
        return
    selected_path = workspace_state.get("selected_path")
    if isinstance(selected_path, str):
        for index, change in enumerate(visible):
            if change.path == selected_path:
                state.selected = index
                return
    selected_index = workspace_state.get("selected_index")
    if isinstance(selected_index, int):
        state.selected = max(0, min(selected_index, len(visible) - 1))
    else:
        state.selected = 0


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _load_browse_changes(args: argparse.Namespace) -> list[git.FileChange]:
    return sort_changes(selected_changes(args), args.sort)


def _load_recent_commits() -> list[git.CommitSummary]:
    try:
        return git.recent_commits()
    except git.GitError:
        return []


def _show_commits_when_empty(state: BrowserState, args: argparse.Namespace) -> None:
    if state.changes or args.base or args.ref_range or args.staged or args.all_changes:
        return
    state.commits = _load_recent_commits()
    if state.commits:
        state.mode = "commits"
        state.selected = 0


def _select_commit(state: BrowserState, args: argparse.Namespace) -> str | None:
    if not state.commits:
        return "No recent commits."
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
    return None


def _switch_review_scope(
    state: BrowserState,
    args: argparse.Namespace,
    scope: ReviewScope,
) -> None:
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
    state.commit_scroll = 0
    _show_commits_when_empty(state, args)
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
    if state.mode == "commits":
        total = len(state.commits)
    elif state.mode == "scopes":
        total = len(_scope_home_entries())
    elif state.mode == "commands":
        total = len(_filtered_command_palette_entries(state))
    else:
        total = len(state.visible_changes)
    if not total:
        return
    if state.mode == "scopes":
        state.scope_selected = max(0, min(state.scope_selected + delta, total - 1))
    elif state.mode == "commands":
        state.command_selected = max(0, min(state.command_selected + delta, total - 1))
    else:
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
    history: list[TaskRecord] | None = None,
) -> list[str]:
    if build is None or max_lines <= 0:
        return []
    width = shutil.get_terminal_size((100, 30)).columns
    status = _build_status(build)
    command = " ".join(shlex.quote(part) for part in build.command)
    lines = [
        style.dim("─" * min(width, 100)),
        f"{style.bold(_task_label(build.kind))} {status}  {style.dim(command)}",
    ]
    if history:
        lines.append(_task_history_line(history[-3:]))
    capacity = max(0, max_lines - len(lines))
    body = build.lines[-capacity:] if capacity else []
    if capacity and not body:
        body = [style.dim("(waiting for output)")]
    return [*lines, *body][-max_lines:]


def _task_history_line(history: list[TaskRecord]) -> str:
    summaries = []
    for record in history:
        command = " ".join(shlex.quote(part) for part in record.command)
        summaries.append(f"{record.kind} {record.status} {command}".strip())
    return "Recent: " + " | ".join(summaries)


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


def _task_label(kind: str) -> str:
    return TASK_LABELS.get(kind, kind.replace("-", " ").title())


def _task_name(kind: str) -> str:
    return kind.replace("-", " ")


def _missing_task_command_message(kind: str) -> str:
    if kind == "build":
        return (
            "No build command configured. Set --build-cmd or CR_BUILD_CMD; "
            "DouyinHarmony defaults to './remote buildEntry --app douyin'."
        )
    if kind == "test":
        return "No test command configured. Set --test-cmd or CR_TEST_CMD."
    if kind == "lint":
        return "No lint command configured. Set --lint-cmd or CR_LINT_CMD."
    return f"No {_task_name(kind)} command configured."


def _record_completed_build(state: BrowserState) -> None:
    build = state.build
    if (
        build is None
        or not build.command
        or build.returncode is None
        or build.history_recorded
    ):
        return
    state.task_history.append(
        TaskRecord(
            kind=build.kind,
            status=_build_status(build),
            command=build.command,
            returncode=build.returncode,
        )
    )
    state.task_history = state.task_history[-5:]
    build.history_recorded = True


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    frame: BrowserFrame | None = None,
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
            _scope_context_line(state, args, style),
            *_browse_commit_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.mode == "scopes":
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_scope_home_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.mode == "commands":
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_command_palette_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.mode == "list":
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_list_screen_lines(
                state,
                args,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
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
            scope_label=_scope_label(state, args),
        )
    if build_panel_height:
        content_frame = lines[:content_lines]
        if len(content_frame) < content_lines:
            content_frame.extend([""] * (content_lines - len(content_frame)))
        lines = [
            *content_frame,
            *_build_panel_lines(
                state.build,
                style,
                build_panel_height,
                state.task_history,
            ),
        ]
    print("\033[2J\033[H", end="")
    _print_lines(lines[:max_lines])
    print(
        f"\033[{layout.prompt_row};1H\033[2K{_browse_prompt(state.mode)}",
        end="",
        flush=True,
    )
    rendered_panel = _build_panel_lines(
        state.build,
        style,
        build_panel_height,
        state.task_history,
    )
    if state.build is not None:
        state.build.last_rendered_panel = rendered_panel
    if frame is not None:
        frame.layout = layout
        frame.complete = True
        frame.build_panel = rendered_panel
        frame.dirty = False


def _draw_build_panel_only(
    build: BuildState | None,
    style: TerminalStyle,
    frame: BrowserFrame | None = None,
    history: list[TaskRecord] | None = None,
) -> bool:
    if build is None:
        return False
    layout = _screen_layout(build)
    height = layout.build_height
    if frame is not None:
        if frame.dirty or not frame.complete or frame.layout != layout:
            frame.dirty = True
            return False
    lines = _build_panel_lines(build, style, height, history)
    previous_panel = frame.build_panel if frame is not None else build.last_rendered_panel
    if lines == previous_panel:
        return False
    build.last_rendered_panel = lines
    if frame is not None:
        frame.build_panel = lines
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
    return True


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
    if mode == "scopes":
        return "cr:scopes> "
    if mode == "commands":
        return "cr:commands> "
    return "cr:list> "


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _normalize_command_query(command: str) -> str:
    normalized = command.strip()
    if normalized in {"", "?"}:
        return "commands"
    return normalized


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("Interactive review"),
        "  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list",
        "  /: filter files     c: clear filter      m: seen      remaining: todo",
        "  : command prompt    build/test/lint/stop/rerun: repo tasks",
        "  PgUp/PgDn or u/d: page    Home/End: jump",
        "  n/p: next/prev    scopes: scope home    g: commits    w: worktree    r: refresh    q: quit",
        "",
    ]


def _command_catalog() -> tuple[CommandGroup, ...]:
    return (
        CommandGroup(
            "Navigation",
            (
                CommandEntry("Enter / 1..N", "open selected file or choose by number"),
                CommandEntry("b / back", "return to file list"),
                CommandEntry("n / p", "next or previous file"),
                CommandEntry("scopes / scope", "show Review Scope home", "scopes"),
                CommandEntry("g / commits", "show recent commits", "g"),
            ),
        ),
        CommandGroup(
            "Review scope",
            (
                CommandEntry("worktree", "review unstaged worktree changes", "worktree"),
                CommandEntry("staged", "review staged/index changes", "staged"),
                CommandEntry("all", "review staged and unstaged local changes", "all"),
                CommandEntry("base REF", "review changes against a base ref"),
                CommandEntry("range OLD..NEW", "review an explicit ref range"),
            ),
        ),
        CommandGroup(
            "Tasks",
            (
                CommandEntry("build", "run configured repo build", "build"),
                CommandEntry("test / tests", "run configured repo tests", "test"),
                CommandEntry("lint", "run configured repo lint", "lint"),
                CommandEntry("stop / cancel", "stop running task", "stop"),
                CommandEntry("rerun / rebuild", "run recent task again", "rerun"),
            ),
        ),
        CommandGroup(
            "Files",
            (
                CommandEntry("/QUERY / filter QUERY", "filter changed files by path"),
                CommandEntry("clear", "clear active file filter", "clear"),
                CommandEntry("m / seen / done", "mark selected file as seen", "m"),
                CommandEntry("todo / unseen / unmark", "mark selected file as todo", "todo"),
                CommandEntry("remaining", "show files not marked seen", "remaining"),
                CommandEntry("allfiles / show all", "show all changed files", "allfiles"),
                CommandEntry("open", "open selected file in editor", "open"),
                CommandEntry("refresh", "reload current review scope", "refresh"),
            ),
        ),
        CommandGroup(
            "Session",
            (
                CommandEntry("commands", "show this command list", "commands"),
                CommandEntry("help", "show compact key help", "help"),
                CommandEntry("quit", "exit browser", "quit"),
            ),
        ),
    )


def _command_palette_entries() -> list[PaletteCommand]:
    entries: list[PaletteCommand] = []
    for group in _command_catalog():
        for entry in group.entries:
            if entry.action is None:
                continue
            entries.append(
                PaletteCommand(
                    group=group.title,
                    label=entry.command,
                    command=entry.action,
                    description=entry.description,
                )
            )
    return entries


def _scope_home_entries() -> tuple[ScopeHomeEntry, ...]:
    return (
        ScopeHomeEntry("Worktree", "Review unstaged worktree changes", "worktree"),
        ScopeHomeEntry("Staged", "Review staged/index changes", "staged"),
        ScopeHomeEntry("All local changes", "Review staged and unstaged changes", "all"),
        ScopeHomeEntry("Recent commits", "Choose a commit as the Review Scope", "commits"),
        ScopeHomeEntry("Base ref", "Type : base REF to review changes against a base"),
        ScopeHomeEntry("Explicit range", "Type : range OLD..NEW to review two refs"),
    )


def _select_scope_home_entry(
    state: BrowserState,
    args: argparse.Namespace,
) -> str | None:
    entries = _scope_home_entries()
    if not entries:
        return None
    state.clamp_selection()
    entry = entries[state.scope_selected]
    if entry.action == "worktree":
        _switch_review_scope(
            state,
            args,
            ReviewScope(False, False, None, None, _args_untracked(args)),
        )
        return None
    if entry.action == "staged":
        _switch_review_scope(state, args, ReviewScope(True, False, None, None, False))
        return None
    if entry.action == "all":
        _switch_review_scope(
            state,
            args,
            ReviewScope(False, True, None, None, _args_untracked(args)),
        )
        return None
    if entry.action == "commits":
        state.commits = _load_recent_commits()
        state.mode = "commits"
        state.selected_commit = None
        state.selected = 0
        state.commit_scroll = 0
        state.clamp_selection()
        return None
    return entry.description


def _filtered_command_palette_entries(state: BrowserState) -> list[PaletteCommand]:
    query = state.command_filter_text.strip().casefold()
    entries = _command_palette_entries()
    if not query:
        return entries

    def haystack(entry: PaletteCommand) -> str:
        return " ".join(
            [entry.group, entry.label, entry.command, entry.description]
        ).casefold()

    return [entry for entry in entries if query in haystack(entry)]


def _selected_palette_command(state: BrowserState) -> PaletteCommand | None:
    entries = _filtered_command_palette_entries(state)
    if not entries:
        return None
    state.clamp_selection()
    return entries[state.command_selected]


def _browse_command_lines(style: TerminalStyle, max_lines: int) -> list[str]:
    lines = [
        style.bold("Commands"),
        "Use : then type a command. b/back returns to the file list.",
        "",
    ]
    command_width = max(
        len(entry.command)
        for group in _command_catalog()
        for entry in group.entries
    )
    for group in _command_catalog():
        lines.append(style.bold(group.title))
        for entry in group.entries:
            lines.append(
                f"  {entry.command.ljust(command_width)}  {entry.description}"
            )
        lines.append("")
    if len(lines) <= max_lines:
        return lines
    clipped = lines[: max(1, max_lines - 1)]
    clipped.append(style.dim(f"showing 1-{len(clipped)}/{len(lines)}"))
    return clipped


def _browse_command_palette_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    entries = _filtered_command_palette_entries(state)
    lines = [
        style.bold("Command palette"),
        "/: filter commands   c: clear filter   Enter: run selected command   b/←: back",
    ]
    if state.command_filter_text:
        lines.append(f"Filter: {state.command_filter_text}")
    lines.append("")
    if not entries:
        message = "No matching commands." if state.command_filter_text else "No executable commands."
        return [*lines, message][:max_lines]
    state.clamp_selection()
    command_width = max(len(entry.label) for entry in entries)
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = _ensure_window(
        state.command_scroll,
        state.command_selected,
        len(entries),
        row_capacity,
    )
    state.command_scroll = start
    end = min(len(entries), start + row_capacity)
    for index, entry in enumerate(entries[start:end], start):
        marker = ">" if index == state.command_selected else " "
        lines.append(
            f"{marker} {entry.group.ljust(12)} "
            f"{entry.label.ljust(command_width)}  {entry.description}"
        )
    if len(entries) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(entries)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def _browse_scope_home_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    entries = _scope_home_entries()
    lines = [
        f"{style.bold('Review scopes')} ({len(entries)} entries)",
        "Enter: open scope   b: back to files   : base REF / : range OLD..NEW",
    ]
    if max_lines <= len(lines):
        return lines[:max_lines]
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = _ensure_window(0, state.scope_selected, len(entries), row_capacity)
    end = min(len(entries), start + row_capacity)
    label_width = max(len(entry.label) for entry in entries)
    for index, entry in enumerate(entries[start:end], start):
        marker = ">" if index == state.scope_selected else " "
        command_hint = f"  [{entry.action}]" if entry.action else ""
        lines.append(
            f"{marker} {index + 1}  "
            f"{entry.label.ljust(label_width)}  {entry.description}{command_hint}"
        )
    if len(entries) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(entries)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def _scope_label(state: BrowserState, args: argparse.Namespace) -> str:
    if state.mode == "scopes":
        return "scope home"
    if state.mode == "commits":
        return "recent commits"
    if state.selected_commit is not None:
        return f"commit {state.selected_commit.commit[:8]}"
    if args.ref_range:
        return f"range {args.ref_range}"
    if args.base:
        return f"base {args.base}"
    if args.staged:
        return "staged"
    if args.all_changes:
        return "all local changes"
    if _args_untracked(args):
        return "worktree + untracked"
    return "worktree"


def _product_breadcrumb(state: BrowserState, args: argparse.Namespace) -> str:
    label = _scope_label(state, args)
    if state.mode in {"scopes", "commits"}:
        return label
    if state.mode == "commands":
        return f"{label} > Commands"
    if state.mode == "file":
        visible = state.visible_changes
        if visible and 0 <= state.selected < len(visible):
            return f"{label} > Files > {visible[state.selected].path}"
    return f"{label} > Files"


def _args_untracked(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "untracked", False))


def _scope_context_line(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    line = f"Scope: {_product_breadcrumb(state, args)}"
    if state.status_message:
        line = f"{line}  |  {state.status_message}"
    return style.dim(_fit_terminal_line(line))


def _show_browser_message(
    state: BrowserState,
    message: str,
    raw_keys: bool,
    frame: BrowserFrame | None = None,
) -> None:
    if raw_keys:
        state.status_message = message
        if frame is not None:
            frame.dirty = True
        return
    print(message)


def _browse_list_lines(
    changes: list[git.FileChange],
    args: argparse.Namespace,
    style: TerminalStyle,
    selected: int | None = None,
    total_changes: int | None = None,
    filter_text: str = "",
    scope_label: str = "",
    seen_paths: set[str] | None = None,
    seen_count: int | None = None,
    remaining_only: bool = False,
) -> list[str]:
    seen_paths = seen_paths or set()
    total_changes = len(changes) if total_changes is None else total_changes
    if not changes:
        return _empty_browse_lines(args, filter_text, total_changes=total_changes)
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    lines = [
        f"Scope: {scope_label}" if scope_label else "",
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    ]
    lines = [line for line in lines if line]
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(changes)}/{total_changes} matches, c to clear)"
        )
    if total_changes:
        if seen_count is None:
            seen_count = sum(1 for change in changes if change.path in seen_paths)
        suffix = " remaining only" if remaining_only else ""
        lines.append(f"Progress: {seen_count}/{total_changes} seen{suffix}")
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
                seen_paths,
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
    header = (
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    )
    if state.changes:
        seen_count = sum(1 for change in state.changes if change.path in state.seen_paths)
        suffix = " remaining only" if state.remaining_only else ""
        header = f"{header}  Progress: {seen_count}/{len(state.changes)} seen{suffix}"
    lines = [header]
    if state.filter_text:
        lines.append(
            f"Filter: {state.filter_text} "
            f"({len(changes)}/{len(state.changes)} matches, c to clear)"
        )
    if len(changes) > 1 and max_lines >= 4:
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
                state.seen_paths,
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
    seen_paths: set[str] | None = None,
) -> str:
    if row.change is None or row.change_index is None:
        return f"  {' ' * index_width}  {_style_tree_directory(row.label, style)}"

    marker = ">" if selected == row.change_index else " "
    progress = "[x]" if row.change.path in (seen_paths or set()) else "[ ]"
    status = " modified" if row.change.status == "modified" else ""
    styled_label = _style_tree_file(
        row.label,
        label_width,
        style,
    )
    return (
        f"{marker} {str(row.change_index + 1).rjust(index_width)} {progress} "
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
    scope_label: str = "",
) -> list[str]:
    if not commits:
        return [
            f"Scope: {scope_label}" if scope_label else "",
            "No recent commits.",
            "",
        ] if scope_label else ["No recent commits.", ""]
    lines = [
        f"Scope: {scope_label}" if scope_label else "",
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Choose a commit to review its files. Press w to return to worktree.",
    ]
    lines = [line for line in lines if line]
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
    scope_label: str = "",
) -> list[str]:
    prefix = [f"Scope: {scope_label}"] if scope_label else []
    if filter_text:
        return [
            *prefix,
            f"No changes match filter: {filter_text} ({total_changes} total).",
            "Press c to clear the filter.",
            "",
        ]
    return [*prefix, empty_message(args)]


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
    scope_label: str = "",
    seen: bool = False,
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
        f"Scope: {scope_label}" if scope_label else "",
        f"{style.bold(f'File {index + 1}/{total}')}  "
        f"{style.path(shorten_path(change.path), _link_target(change.path, first_line, args))}"
        f"{style.dim(anchor)}  "
        f"{style.bold(format_change_summary(change))}  "
        f"{style.dim('seen' if seen else 'todo')}"
    ]
    lines = [line for line in lines if line]
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
    seen = change.path in state.seen_paths
    scope_label = _product_breadcrumb(state, args)
    key = _file_cache_key(change, index, total, args, seen, scope_label)
    if key not in state.file_line_cache:
        state.file_line_cache[key] = _browse_file_lines(
            change,
            index,
            total,
            args,
            style,
            scope_label,
            seen,
        )
    return state.file_line_cache[key]


def _file_cache_key(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    seen: bool = False,
    scope_label: str = "",
) -> str:
    return "\x1f".join(
        [
            change.path,
            scope_label,
            "seen" if seen else "todo",
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


def _read_filter_query(prompt: str = "filter> ") -> str:
    try:
        return input(prompt).strip()
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
    _start_task(state, args, "build")


def _start_task(
    state: BrowserState,
    args: argparse.Namespace,
    kind: str,
) -> None:
    repo = git.repo_root()
    command = _task_command(repo, args, kind)
    if command is None:
        state.build = _failed_build_state(
            [],
            _missing_task_command_message(kind),
            kind,
        )
        return
    if state.build is not None and state.build.running:
        state.build.lines.append(f"{_task_label(state.build.kind)} is already running.")
        return
    try:
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as exc:
        label = _task_label(kind)
        state.build = _failed_build_state(
            command,
            f"{label} failed to start: {exc}",
            kind,
        )
        return
    if process.stdout is not None:
        os.set_blocking(process.stdout.fileno(), False)
    state.build = BuildState(
        command=command,
        process=process,
        kind=kind,
        lines=[f"started in {repo}"],
        process_group_id=process.pid,
    )


def _stop_build(state: BrowserState) -> None:
    if state.build is None:
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait()
        state.build = BuildState(
            command=[],
            process=process,
            kind="build",
            lines=["No build is running."],
            returncode=0,
        )
        return
    if not state.build.running:
        state.build.lines.append(f"No {_task_name(state.build.kind)} is running.")
        return
    state.build.stop_requested = True
    state.build.lines.append(f"Stopping {_task_name(state.build.kind)}...")
    state.build.stop_requested_at = time.monotonic()
    if state.build.process_group_id is not None and hasattr(os, "killpg"):
        try:
            os.killpg(state.build.process_group_id, signal.SIGTERM)
            return
        except OSError as exc:
            state.build.lines.append(
                f"{_task_label(state.build.kind)} process group stop failed: {exc}"
            )
    try:
        state.build.process.terminate()
    except OSError as exc:
        state.build.lines.append(f"{_task_label(state.build.kind)} stop failed: {exc}")


def _rerun_build(state: BrowserState, args: argparse.Namespace) -> None:
    if state.build is not None and state.build.running:
        state.build.lines.append(
            f"{_task_label(state.build.kind)} is already running. Stop it before rerun."
        )
        return
    kind = state.build.kind if state.build is not None else "build"
    _start_task(state, args, kind)


def _run_build_foreground(args: argparse.Namespace) -> None:
    _run_task_foreground(args, "build")


def _run_task_foreground(args: argparse.Namespace, kind: str) -> None:
    repo = git.repo_root()
    command = _task_command(repo, args, kind)
    if command is None:
        print(_missing_task_command_message(kind))
        return
    label = _task_label(kind)
    print(f"{label}: {' '.join(shlex.quote(part) for part in command)}")
    try:
        result = subprocess.run(command, cwd=repo, check=False)
    except OSError as exc:
        print(f"{label} failed to start: {exc}")
        return
    if result.returncode == 0:
        print(f"{label} succeeded.")
    else:
        print(f"{label} failed with exit code {result.returncode}.")


def _failed_build_state(
    command: list[str],
    message: str,
    kind: str = "build",
) -> BuildState:
    process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
    process.wait()
    return BuildState(
        command=command,
        process=process,
        kind=kind,
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
            message = f"{_task_label(build.kind)} stopped."
        else:
            label = _task_label(build.kind)
            message = (
                f"{label} succeeded."
                if returncode == 0
                else f"{label} failed with exit code {returncode}."
            )
        build.lines.append(message)
        if build.process.stdout is not None:
            build.process.stdout.close()
    else:
        _maybe_escalate_build_stop(build)


def _maybe_escalate_build_stop(build: BuildState) -> None:
    if (
        not build.stop_requested
        or build.stop_requested_at is None
        or build.stop_escalated
    ):
        return
    if time.monotonic() - build.stop_requested_at < BUILD_STOP_KILL_GRACE_SECONDS:
        return
    build.stop_escalated = True
    if build.process_group_id is not None and hasattr(os, "killpg"):
        build.lines.append(
            f"{_task_label(build.kind)} did not stop; force killing process group."
        )
        try:
            os.killpg(build.process_group_id, signal.SIGKILL)
            return
        except OSError as exc:
            build.lines.append(
                f"{_task_label(build.kind)} process group force kill failed: {exc}"
            )
    build.lines.append(
        f"{_task_label(build.kind)} did not stop; force killing {_task_name(build.kind)} process."
    )
    try:
        build.process.kill()
    except OSError as exc:
        build.lines.append(f"{_task_label(build.kind)} force kill failed: {exc}")


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


def _task_command(
    repo: Path,
    args: argparse.Namespace,
    kind: str,
) -> list[str] | None:
    if kind == "build":
        return _build_command(repo, getattr(args, "build_cmd", None))
    if kind == "test":
        template = getattr(args, "test_cmd", None) or os.environ.get("CR_TEST_CMD")
        return shlex.split(template) if template else None
    if kind == "lint":
        template = getattr(args, "lint_cmd", None) or os.environ.get("CR_LINT_CMD")
        return shlex.split(template) if template else None
    return None


def _open_change(change: git.FileChange, args: argparse.Namespace) -> str:
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
        return (
            "No editor opener found. Set --open-cmd or CR_OPEN_CMD, "
            "for example: --open-cmd 'code -g {fileline}'"
        )
    try:
        subprocess.Popen(command)
    except OSError as exc:
        return f"Open failed: {exc}"
    return f"Opened {shorten_path(change.path)}{':' + str(line) if line else ''}"


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
