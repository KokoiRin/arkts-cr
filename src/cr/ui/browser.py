"""Interactive review browser for cr.

This module owns browse orchestration, terminal rendering, key command mapping,
background task display, and editor handoff. Review workspace state and page
navigation rules live in deeper UI modules so the CLI parser can stay shallow.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
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
from .commands import BrowserCommand, BrowserCommandAction, parse_browser_command
from . import file_actions
from .navigation import BrowserNavigation, BrowserPage
from . import tasks as task_runtime
from .tasks import TaskRecord, TaskState
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri
from .workspace import (
    ReviewScope,
    ReviewWorkspace,
    capture_scope,
    filter_changes_by_query,
    load_workspace_changes,
    restore_scope_from_state,
)


BROWSER_WORKSPACE_STATE_VERSION = 1
@dataclass
class BrowserState:
    changes: list[git.FileChange]
    commits: list[git.CommitSummary] = field(default_factory=list)
    task: "TaskState | None" = None
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
    page: str = BrowserPage.CHANGED_FILES
    filter_text: str = ""
    seen_paths: set[str] = field(default_factory=set)
    remaining_only: bool = False
    scope_selected: int = 0
    command_selected: int = 0
    command_filter_text: str = ""
    status_message: str = ""
    workspace: ReviewWorkspace | None = None

    def __post_init__(self) -> None:
        if self.workspace is None:
            self.workspace = ReviewWorkspace(
                changes=self.changes,
                previous_scope=self.previous_scope,
                selected_commit=self.selected_commit,
                selected=self.selected,
                list_scroll=self.list_scroll,
                filter_text=self.filter_text,
                seen_paths=self.seen_paths,
                remaining_only=self.remaining_only,
            )
        self._sync_from_workspace()

    def _sync_from_workspace(self) -> None:
        workspace = self.workspace
        if workspace is None:
            return
        self.changes = workspace.changes
        self.previous_scope = workspace.previous_scope
        self.selected_commit = workspace.selected_commit
        self.selected = workspace.selected
        self.list_scroll = workspace.list_scroll
        self.filter_text = workspace.filter_text
        self.seen_paths = workspace.seen_paths
        self.remaining_only = workspace.remaining_only

    def _sync_to_workspace(self) -> ReviewWorkspace:
        workspace = self.workspace
        if workspace is None:
            workspace = ReviewWorkspace(changes=self.changes)
            self.workspace = workspace
        workspace.changes = self.changes
        workspace.previous_scope = self.previous_scope
        workspace.selected_commit = self.selected_commit
        workspace.selected = self.selected
        workspace.list_scroll = self.list_scroll
        workspace.filter_text = self.filter_text
        workspace.seen_paths = self.seen_paths
        workspace.remaining_only = self.remaining_only
        return workspace

    @property
    def mode(self) -> str:
        return self.page

    @mode.setter
    def mode(self, value: str) -> None:
        self.page = value

    @property
    def visible_changes(self) -> list[git.FileChange]:
        workspace = self._sync_to_workspace()
        visible = workspace.visible_changes
        self._sync_from_workspace()
        return visible

    def clamp_selection(self) -> None:
        if self.page == BrowserPage.COMMIT_PICKER:
            total = len(self.commits)
        elif self.page == BrowserPage.SCOPE_HOME:
            total = len(_scope_home_entries())
        elif self.page == BrowserPage.COMMAND_PALETTE:
            total = len(_filtered_command_palette_entries(self))
        else:
            total = len(self.visible_changes)
        if total == 0:
            if self.page == BrowserPage.SCOPE_HOME:
                self.scope_selected = 0
            elif self.page == BrowserPage.COMMAND_PALETTE:
                self.command_selected = 0
            else:
                self.selected = 0
            if self.page == BrowserPage.FILE_DETAIL:
                BrowserNavigation.show_changed_files(self)
            return
        if self.page == BrowserPage.SCOPE_HOME:
            self.scope_selected = max(0, min(self.scope_selected, total - 1))
        elif self.page == BrowserPage.COMMAND_PALETTE:
            self.command_selected = max(0, min(self.command_selected, total - 1))
        else:
            self.selected = max(0, min(self.selected, total - 1))

    def clear_render_cache(self) -> None:
        self.first_line_cache.clear()
        self.file_line_cache.clear()
        self.file_scroll = 0

    def set_filter(self, query: str) -> None:
        self._sync_to_workspace().set_filter(query)
        self._sync_from_workspace()
        BrowserNavigation.show_changed_files(self)
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
class ScreenLayout:
    content_height: int
    task_height: int
    prompt_row: int
    task_start_row: int | None

    @property
    def max_render_lines(self) -> int:
        return max(0, self.prompt_row - 1)


@dataclass
class BrowserFrame:
    layout: ScreenLayout | None = None
    complete: bool = False
    task_panel: list[str] = field(default_factory=list)
    dirty: bool = True


@dataclass(frozen=True)
class BrowserActionResult:
    handled: bool = True
    needs_redraw: bool = False
    exit_code: int | None = None


class BrowserCommandExecutor:
    """Executes parsed browser command actions.

    This executor owns action-side state changes for already parsed commands.
    Temporary prompt input, raw-key sentinels, frame redraw scheduling, and
    workspace saving remain in the browser run loop.
    """

    def __init__(
        self,
        state: BrowserState,
        args: argparse.Namespace,
        style: TerminalStyle,
        frame: BrowserFrame,
        *,
        raw_keys: bool,
    ) -> None:
        self.state = state
        self.args = args
        self.style = style
        self.frame = frame
        self.raw_keys = raw_keys

    def execute(self, parsed_command: BrowserCommand) -> BrowserActionResult:
        state = self.state
        args = self.args
        style = self.style
        frame = self.frame
        raw_keys = self.raw_keys
        action = parsed_command.action
        if action == BrowserCommandAction.SET_FILE_FILTER:
            state.set_filter(parsed_command.value)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_FILTER:
            if state.page == BrowserPage.COMMAND_PALETTE:
                state.clear_command_filter()
            else:
                state.clear_filter()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MARK_SEEN:
            _mark_selected_seen(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MARK_TODO:
            _unmark_selected_seen(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_REMAINING:
            state.remaining_only = True
            BrowserNavigation.show_changed_files(state)
            state.selected = 0
            state.list_scroll = 0
            state.clamp_selection()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_ALL_FILES:
            state.remaining_only = False
            BrowserNavigation.show_changed_files(state)
            state.selected = 0
            state.list_scroll = 0
            state.clamp_selection()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.QUIT:
            return BrowserActionResult(exit_code=0)
        if action == BrowserCommandAction.SHOW_COMMAND_PALETTE:
            BrowserNavigation.show_command_palette(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_SCOPE_HOME:
            BrowserNavigation.show_scope_home(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_COMMITS:
            state.commits = _load_recent_commits()
            BrowserNavigation.show_commit_picker(state, clear_selected_commit=True)
            state.clamp_selection()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SWITCH_WORKTREE:
            _switch_review_scope(
                state,
                args,
                ReviewScope(False, False, None, None, _args_untracked(args)),
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.RESTORE_WORKSPACE:
            if state.previous_scope is not None:
                _restore_previous_scope(state, args)
            else:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, None, None, _args_untracked(args)),
                )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SWITCH_STAGED:
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SWITCH_ALL:
            _switch_review_scope(
                state,
                args,
                ReviewScope(False, True, None, None, _args_untracked(args)),
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SWITCH_BASE:
            ref = parsed_command.value
            if ref:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, ref, None, False),
                )
                return BrowserActionResult(needs_redraw=True)
            return BrowserActionResult()
        if action == BrowserCommandAction.SWITCH_RANGE:
            ref_range = parsed_command.value
            if ref_range:
                _switch_review_scope(
                    state,
                    args,
                    ReviewScope(False, False, None, ref_range, False),
                )
                return BrowserActionResult(needs_redraw=True)
            return BrowserActionResult()
        if action == BrowserCommandAction.HELP:
            if raw_keys:
                BrowserNavigation.show_changed_files(state)
                return BrowserActionResult(needs_redraw=True)
            _print_lines(_browse_help_lines(style))
            return BrowserActionResult()
        if action == BrowserCommandAction.OPEN_FILE:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                message = _open_change(visible[state.selected], args)
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to open.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_PATH:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                path = visible[state.selected].path
                message = file_actions.copy_text(path) or f"Copied {shorten_path(path)}"
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to copy.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_ANCHOR:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                path = visible[state.selected].path
                line = git.first_changed_line(
                    path,
                    staged=args.staged,
                    all_changes=args.all_changes,
                    base=args.base,
                    ref_range=args.ref_range,
                )
                anchor = f"{path}:{line}" if line else path
                display = f"{shorten_path(path)}:{line}" if line else shorten_path(path)
                message = file_actions.copy_text(anchor) or f"Copied {display}"
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to copy.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.REVEAL_FILE:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                path = visible[state.selected].path
                repo_file = git.repo_path(path)
                message = file_actions.reveal_path(repo_file) or f"Revealed {shorten_path(path)}"
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to reveal.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.RUN_BUILD:
            if raw_keys:
                _start_task(state, args, "build")
                return BrowserActionResult(needs_redraw=True)
            _run_task_foreground(args, "build")
            return BrowserActionResult()
        if action == BrowserCommandAction.RUN_TEST:
            if raw_keys:
                _start_task(state, args, "test")
                return BrowserActionResult(needs_redraw=True)
            _run_task_foreground(args, "test")
            return BrowserActionResult()
        if action == BrowserCommandAction.RUN_LINT:
            if raw_keys:
                _start_task(state, args, "lint")
                return BrowserActionResult(needs_redraw=True)
            _run_task_foreground(args, "lint")
            return BrowserActionResult()
        if action == BrowserCommandAction.STOP_TASK:
            _stop_task(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.RERUN_TASK:
            if raw_keys:
                _rerun_task(state, args)
                return BrowserActionResult(needs_redraw=True)
            _run_task_foreground(args, "build")
            return BrowserActionResult()
        if action == BrowserCommandAction.REFRESH:
            if state.page == BrowserPage.COMMIT_PICKER:
                state.commits = _load_recent_commits()
                state.commit_scroll = 0
            else:
                state.changes = _load_browse_changes(args)
                state.clear_render_cache()
                BrowserNavigation.show_changed_files(state)
                state.list_scroll = 0
                _show_commits_when_empty(state, args)
            state.clamp_selection()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_CHANGED_FILES:
            BrowserNavigation.show_changed_files(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.BACK:
            BrowserNavigation.go_back(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MOVE_DOWN:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, 1, args, style)
            else:
                _move_selection(state, 1)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MOVE_UP:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, -1, args, style)
            else:
                _move_selection(state, -1)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.PAGE_DOWN:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, _page_step(), args, style)
            else:
                _move_selection(state, _page_step())
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.PAGE_UP:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, -_page_step(), args, style)
            else:
                _move_selection(state, -_page_step())
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.HOME:
            if state.page == BrowserPage.FILE_DETAIL:
                state.file_scroll = 0
            elif state.page == BrowserPage.SCOPE_HOME:
                state.scope_selected = 0
            elif state.page == BrowserPage.COMMAND_PALETTE:
                state.command_selected = 0
            else:
                state.selected = 0
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.END:
            if state.page == BrowserPage.FILE_DETAIL:
                state.file_scroll = _max_file_scroll(state, args, style)
            elif state.page == BrowserPage.SCOPE_HOME:
                total = len(_scope_home_entries())
                if total:
                    state.scope_selected = total - 1
            elif state.page == BrowserPage.COMMAND_PALETTE:
                total = len(_filtered_command_palette_entries(state))
                if total:
                    state.command_selected = total - 1
            else:
                total = len(state.commits) if state.page == BrowserPage.COMMIT_PICKER else len(state.visible_changes)
                if total:
                    state.selected = total - 1
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.ENTER:
            if state.page == BrowserPage.COMMIT_PICKER:
                message = _select_commit(state, args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            if state.page == BrowserPage.SCOPE_HOME:
                message = _select_scope_home_entry(state, args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            if state.visible_changes:
                BrowserNavigation.open_file_detail(state)
                return BrowserActionResult(needs_redraw=True)
            return BrowserActionResult()
        if action == BrowserCommandAction.LEFT:
            BrowserNavigation.go_back(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.NEXT_FILE:
            visible = state.visible_changes
            if visible:
                state.selected = min(state.selected + 1, len(visible) - 1)
                BrowserNavigation.open_file_detail(state)
                return BrowserActionResult(needs_redraw=True)
            return BrowserActionResult()
        if action == BrowserCommandAction.PREVIOUS_FILE:
            if state.visible_changes:
                state.selected = max(state.selected - 1, 0)
                BrowserNavigation.open_file_detail(state)
                return BrowserActionResult(needs_redraw=True)
            return BrowserActionResult()
        if action == BrowserCommandAction.CHOOSE_NUMBER:
            return self._choose_number(parsed_command.value)
        if parsed_command.value:
            unknown_message = (
                "Unknown command. Open commands for available actions."
                if raw_keys
                else (
                    "Unknown command. Use arrows, Enter, /, c, a number, "
                    "o, n, p, b, g, r, h, m, remaining, copy path, "
                    "copy anchor, reveal, build, stop, rerun, test, lint, "
                    "staged, all, base, range, or q."
                )
            )
            _show_browser_message(
                state,
                unknown_message,
                raw_keys,
                frame,
            )
            return BrowserActionResult(needs_redraw=raw_keys)
        return BrowserActionResult(handled=False)

    def _choose_number(self, value: str) -> BrowserActionResult:
        state = self.state
        raw_keys = self.raw_keys
        frame = self.frame
        choice = int(value)
        if state.page == BrowserPage.SCOPE_HOME:
            total = len(_scope_home_entries())
            if 1 <= choice <= total:
                state.scope_selected = choice - 1
                message = _select_scope_home_entry(state, self.args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _show_browser_message(state, f"Choose 1-{total}.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if state.page == BrowserPage.COMMIT_PICKER:
            if 1 <= choice <= len(state.commits):
                state.selected = choice - 1
                message = _select_commit(state, self.args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _show_browser_message(
                state,
                f"Choose 1-{len(state.commits)}.",
                raw_keys,
                frame,
            )
            return BrowserActionResult(needs_redraw=raw_keys)
        visible = state.visible_changes
        if 1 <= choice <= len(visible):
            state.selected = choice - 1
            BrowserNavigation.open_file_detail(state)
            return BrowserActionResult(needs_redraw=True)
        _show_browser_message(state, f"Choose 1-{len(visible)}.", raw_keys, frame)
        return BrowserActionResult(needs_redraw=raw_keys)


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
        _poll_task(state.task)
        _record_completed_task(state)
        state.clamp_selection()
        visible = state.visible_changes
        if raw_keys and (needs_redraw or frame.dirty):
            _draw_browse_screen(state, args, style, frame)
            needs_redraw = False
        prompt = _browse_prompt(state.page)
        if not raw_keys:
            if state.page == BrowserPage.COMMIT_PICKER:
                _print_lines(
                    _browse_commit_lines(
                        state.commits,
                        style,
                        selected=None,
                        scope_label=_scope_label(state, args),
                    )
                )
            elif state.page == BrowserPage.COMMAND_PALETTE:
                _print_lines(_browse_command_lines(style, max_lines=_screen_height()))
            elif state.page == BrowserPage.SCOPE_HOME:
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
            elif state.page == BrowserPage.CHANGED_FILES:
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
                BrowserNavigation.show_changed_files(state)

        command_result = _read_browse_command(
            prompt,
            raw_keys,
            tick_when_idle=state.task is not None and state.task.running,
        )
        if command_result == "__tick__":
            _draw_task_panel_only(state.task, style, frame, state.task_history)
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
        if state.page == BrowserPage.COMMAND_PALETTE and command in {"enter", "right", "l"}:
            palette_command = _selected_palette_command(state)
            if palette_command is None:
                continue
            command = palette_command.command

        parsed_command = parse_browser_command(command, raw_keys=raw_keys)

        if parsed_command.action == BrowserCommandAction.FILTER_PROMPT:
            query = _read_filter_query(
                "command filter> " if state.page == BrowserPage.COMMAND_PALETTE else "filter> "
            )
            if raw_keys:
                frame.dirty = True
            if query != "__interrupt__":
                if state.page == BrowserPage.COMMAND_PALETTE:
                    state.set_command_filter(query)
                else:
                    state.set_filter(query)
                needs_redraw = True
            elif raw_keys:
                needs_redraw = True
            continue
        if parsed_command.action == BrowserCommandAction.COMMAND_PROMPT:
            command = _normalize_command_query(_read_command_query())
            if raw_keys:
                frame.dirty = True
            if command == "__interrupt__":
                if raw_keys:
                    needs_redraw = True
                continue
            parsed_command = parse_browser_command(command, raw_keys=raw_keys)
        result = BrowserCommandExecutor(
            state,
            args,
            style,
            frame,
            raw_keys=raw_keys,
        ).execute(parsed_command)
        if result.exit_code is not None:
            _save_browser_workspace_state_on_exit(state, args, repo)
            return result.exit_code
        if result.needs_redraw:
            needs_redraw = True


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
    mode = (
        BrowserPage.FILE_DETAIL
        if state.page == BrowserPage.FILE_DETAIL
        else BrowserPage.CHANGED_FILES
    )
    data = state._sync_to_workspace().state_data(args, mode=mode)
    return {
        "version": BROWSER_WORKSPACE_STATE_VERSION,
        **data,
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
    mode = state._sync_to_workspace().restore_state(args, workspace_state)
    state._sync_from_workspace()
    if mode == BrowserPage.FILE_DETAIL and state.visible_changes:
        BrowserNavigation.open_file_detail(state)
    else:
        BrowserNavigation.show_changed_files(state)
    state.list_scroll = 0
    state.file_scroll = 0
    state.commit_scroll = 0
    state.clamp_selection()


def _restore_browser_workspace_scope(
    args: argparse.Namespace,
    workspace_state: dict[str, object],
) -> None:
    restore_scope_from_state(args, workspace_state)


def _load_browse_changes(args: argparse.Namespace) -> list[git.FileChange]:
    return load_workspace_changes(args)


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
        BrowserNavigation.show_commit_picker(state)


def _select_commit(state: BrowserState, args: argparse.Namespace) -> str | None:
    if not state.commits:
        return "No recent commits."
    state.clamp_selection()
    commit = state.commits[state.selected]
    state._sync_to_workspace().select_commit(args, commit, loader=_load_browse_changes)
    state._sync_from_workspace()
    state.clear_render_cache()
    BrowserNavigation.show_changed_files(state)
    state.clamp_selection()
    return None


def _switch_review_scope(
    state: BrowserState,
    args: argparse.Namespace,
    scope: ReviewScope,
) -> None:
    state._sync_to_workspace().switch_scope(args, scope, loader=_load_browse_changes)
    state._sync_from_workspace()
    state.clear_render_cache()
    BrowserNavigation.show_changed_files(state)
    state.commit_scroll = 0
    _show_commits_when_empty(state, args)
    state.clamp_selection()


def _capture_scope(args: argparse.Namespace) -> ReviewScope:
    return capture_scope(args)


def _restore_previous_scope(state: BrowserState, args: argparse.Namespace) -> None:
    if state.previous_scope is None:
        return
    state._sync_to_workspace().restore_previous_scope(args, loader=_load_browse_changes)
    state._sync_from_workspace()
    state.clear_render_cache()
    BrowserNavigation.show_changed_files(state)
    _show_commits_when_empty(state, args)
    state.clamp_selection()


def _move_selection(state: BrowserState, delta: int) -> None:
    if state.page == BrowserPage.COMMIT_PICKER:
        total = len(state.commits)
    elif state.page == BrowserPage.SCOPE_HOME:
        total = len(_scope_home_entries())
    elif state.page == BrowserPage.COMMAND_PALETTE:
        total = len(_filtered_command_palette_entries(state))
    else:
        total = len(state.visible_changes)
    if not total:
        return
    if state.page == BrowserPage.SCOPE_HOME:
        state.scope_selected = max(0, min(state.scope_selected + delta, total - 1))
    elif state.page == BrowserPage.COMMAND_PALETTE:
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


def _task_panel_height(task: TaskState | None, available_lines: int) -> int:
    if task is None:
        return 0
    return max(3, min(10, max(5, available_lines // 4), max(3, available_lines - 6)))


def _screen_layout(task: TaskState | None, rows: int | None = None) -> ScreenLayout:
    terminal_rows = _screen_height() if rows is None else max(8, rows)
    max_render_lines = max(1, terminal_rows - 1)
    task_height = _task_panel_height(task, max_render_lines)
    content_height = max(1, max_render_lines - task_height)
    task_start_row = content_height + 1 if task_height else None
    return ScreenLayout(
        content_height=content_height,
        task_height=task_height,
        prompt_row=terminal_rows,
        task_start_row=task_start_row,
    )


def _task_panel_lines(
    task: TaskState | None,
    style: TerminalStyle,
    max_lines: int,
    history: list[TaskRecord] | None = None,
) -> list[str]:
    if task is None or max_lines <= 0:
        return []
    width = shutil.get_terminal_size((100, 30)).columns
    status = _task_status(task)
    command = " ".join(shlex.quote(part) for part in task.command)
    lines = [
        style.dim("─" * min(width, 100)),
        f"{style.bold(_task_label(task.kind))} {status}  {style.dim(command)}",
    ]
    if history:
        lines.append(_task_history_line(history[-3:]))
    capacity = max(0, max_lines - len(lines))
    body = task.lines[-capacity:] if capacity else []
    if capacity and not body:
        body = [style.dim("(waiting for output)")]
    return [*lines, *body][-max_lines:]


def _task_history_line(history: list[TaskRecord]) -> str:
    summaries = []
    for record in history:
        command = " ".join(shlex.quote(part) for part in record.command)
        summaries.append(f"{record.kind} {record.status} {command}".strip())
    return "Recent: " + " | ".join(summaries)


def _task_status(task: TaskState) -> str:
    return task_runtime.task_status(task)


def _task_label(kind: str) -> str:
    return task_runtime.task_label(kind)


def _task_name(kind: str) -> str:
    return task_runtime.task_name(kind)


def _missing_task_command_message(kind: str) -> str:
    return task_runtime.missing_task_command_message(kind)


def _record_completed_task(state: BrowserState) -> None:
    task_runtime.record_completed_task(state)


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    frame: BrowserFrame | None = None,
) -> None:
    state.clamp_selection()
    visible = state.visible_changes
    layout = _screen_layout(state.task)
    max_lines = layout.max_render_lines
    content_lines = layout.content_height
    task_panel_height = layout.task_height
    if state.page == BrowserPage.COMMIT_PICKER:
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_commit_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.page == BrowserPage.SCOPE_HOME:
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_scope_home_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.page == BrowserPage.COMMAND_PALETTE:
        lines = [
            *_browse_help_lines(style),
            _scope_context_line(state, args, style),
            *_browse_command_palette_screen_lines(
                state,
                style,
                max(1, content_lines - len(_browse_help_lines(style)) - 1),
            ),
        ]
    elif state.page == BrowserPage.CHANGED_FILES:
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
    if task_panel_height:
        content_frame = lines[:content_lines]
        if len(content_frame) < content_lines:
            content_frame.extend([""] * (content_lines - len(content_frame)))
        lines = [
            *content_frame,
            *_task_panel_lines(
                state.task,
                style,
                task_panel_height,
                state.task_history,
            ),
        ]
    print("\033[2J\033[H", end="")
    _print_lines(lines[:max_lines])
    print(
        f"\033[{layout.prompt_row};1H\033[2K{_browse_prompt(state.page)}",
        end="",
        flush=True,
    )
    rendered_panel = _task_panel_lines(
        state.task,
        style,
        task_panel_height,
        state.task_history,
    )
    if state.task is not None:
        state.task.last_rendered_panel = rendered_panel
    if frame is not None:
        frame.layout = layout
        frame.complete = True
        frame.task_panel = rendered_panel
        frame.dirty = False


def _draw_task_panel_only(
    task: TaskState | None,
    style: TerminalStyle,
    frame: BrowserFrame | None = None,
    history: list[TaskRecord] | None = None,
) -> bool:
    if task is None:
        return False
    layout = _screen_layout(task)
    height = layout.task_height
    if frame is not None:
        if frame.dirty or not frame.complete or frame.layout != layout:
            frame.dirty = True
            return False
    lines = _task_panel_lines(task, style, height, history)
    previous_panel = frame.task_panel if frame is not None else task.last_rendered_panel
    if lines == previous_panel:
        return False
    task.last_rendered_panel = lines
    if frame is not None:
        frame.task_panel = lines
    start_row = layout.task_start_row or 1
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
    if mode == BrowserPage.FILE_DETAIL:
        return "cr:file> "
    if mode == BrowserPage.COMMIT_PICKER:
        return "cr:commits> "
    if mode == BrowserPage.SCOPE_HOME:
        return "cr:scopes> "
    if mode == BrowserPage.COMMAND_PALETTE:
        return "cr:commands> "
    return "cr:list> "


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _normalize_command_query(command: str) -> str:
    normalized = command.strip()
    if normalized in {"", "?"}:
        return BrowserPage.COMMAND_PALETTE
    return normalized


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("Interactive review"),
        "  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list",
        "  /: filter files     c: clear filter      m: seen      remaining: todo",
        "  : command prompt    build/test/lint: tasks    copy path/anchor/reveal: file actions",
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
                CommandEntry("scopes / scope", "show Review Scope home", BrowserPage.SCOPE_HOME),
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
                CommandEntry("copy path", "copy selected file path", "copy path"),
                CommandEntry("copy anchor", "copy selected file path and line", "copy anchor"),
                CommandEntry("reveal", "reveal selected file in file browser", "reveal"),
                CommandEntry("refresh", "reload current review scope", "refresh"),
            ),
        ),
        CommandGroup(
            "Session",
            (
                CommandEntry(BrowserPage.COMMAND_PALETTE, "show this command list", BrowserPage.COMMAND_PALETTE),
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
        ScopeHomeEntry("Recent commits", "Choose a commit as the Review Scope", BrowserPage.COMMIT_PICKER),
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
    if entry.action == BrowserPage.COMMIT_PICKER:
        state.commits = _load_recent_commits()
        BrowserNavigation.show_commit_picker(state, clear_selected_commit=True)
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
    if state.page == BrowserPage.SCOPE_HOME:
        return "scope home"
    if state.page == BrowserPage.COMMIT_PICKER:
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
    if state.page in {BrowserPage.SCOPE_HOME, BrowserPage.COMMIT_PICKER}:
        return label
    if state.page == BrowserPage.COMMAND_PALETTE:
        return f"{label} > Commands"
    if state.page == BrowserPage.FILE_DETAIL:
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


def _start_task(
    state: BrowserState,
    args: argparse.Namespace,
    kind: str,
) -> None:
    task_runtime.start_task(state, args, kind, repo=git.repo_root())


def _stop_task(state: BrowserState) -> None:
    task_runtime.stop_task(state)


def _rerun_task(state: BrowserState, args: argparse.Namespace) -> None:
    task_runtime.rerun_task(state, args, repo=git.repo_root())


def _run_task_foreground(args: argparse.Namespace, kind: str) -> None:
    task_runtime.run_task_foreground(args, kind, repo=git.repo_root())


def _failed_task_state(
    command: list[str],
    message: str,
    kind: str = "build",
) -> TaskState:
    return task_runtime.failed_task_state(command, message, kind)


def _poll_task(task: TaskState | None) -> None:
    task_runtime.poll_task(task)


def _maybe_escalate_task_stop(task: TaskState) -> None:
    task_runtime.maybe_escalate_task_stop(task)


def _drain_task_output(task: TaskState) -> None:
    task_runtime.drain_task_output(task)


def _build_command(repo: Path, configured: str | None = None) -> list[str] | None:
    return task_runtime.build_command(repo, configured)


def _task_command(
    repo: Path,
    args: argparse.Namespace,
    kind: str,
) -> list[str] | None:
    return task_runtime.task_command(repo, args, kind)


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
