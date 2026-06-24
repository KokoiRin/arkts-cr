"""Interactive review browser for cr.

This module owns browse orchestration, prompt-input interpretation,
selected-file action execution, and browser session startup/shutdown.
Page-specific terminal content, terminal input protocol, review workspace
state, page navigation rules, Browser Frame layout, task runtime, and platform
file action details live in deeper UI modules so the CLI parser can stay
shallow.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import sys
import time

from ..review.changes import (
    change_hunk_lines,
    is_code_file,
    modified_names,
    other_change_counts,
    parse_change_symbols,
)
from ..review.data import build_review_data
from ..review.prompt import render_prompt_handoff
from ..review.risk import risk_hints
from ..review.tree import shorten_path
from ..source.purpose import describe_file
from ..vcs import git
from .commands import BrowserCommand, BrowserCommandAction, parse_browser_command
from . import command_catalog as command_catalog_module
from .command_catalog import CommandEntry, CommandGroup, PaletteCommand
from . import file_actions
from . import frame as frame_module
from .frame import BrowserFrame, ScreenLayout
from . import handoff as handoff_module
from . import input as input_module
from .navigation import BrowserNavigation, BrowserPage, BrowserPageSnapshot
from . import page_content
from . import selected_file_actions
from . import tasks as task_runtime
from .tasks import TaskRecord, TaskState
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri
from . import workspace_persistence
from .workspace import (
    ReviewScope,
    ReviewWorkspace,
    capture_scope,
    filter_changes_by_query,
    load_workspace_changes,
)


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
    review_notes: dict[str, str] = field(default_factory=dict)
    scope_selected: int = 0
    command_selected: int = 0
    command_filter_text: str = ""
    status_message: str = ""
    workspace: ReviewWorkspace | None = None
    page_back_stack: list[BrowserPageSnapshot] = field(default_factory=list)
    page_forward_stack: list[BrowserPageSnapshot] = field(default_factory=list)

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
                review_notes=self.review_notes,
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
        self.review_notes = workspace.review_notes

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
        workspace.review_notes = self.review_notes
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


BrowseTreeRow = page_content.BrowseTreeRow
ScopeHomeEntry = page_content.ScopeHomeEntry
_BrowseTreeNode = page_content._BrowseTreeNode


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
                message = selected_file_actions.copy_selected_path(
                    path,
                    getattr(args, "copy_cmd", None),
                    copy_text=file_actions.copy_text,
                )
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to copy.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_ANCHOR:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                path = visible[state.selected].path
                message = selected_file_actions.copy_selected_anchor(
                    path,
                    args,
                    getattr(args, "copy_cmd", None),
                    first_changed_line=git.first_changed_line,
                    copy_text=file_actions.copy_text,
                )
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to copy.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_REVIEW_NOTES:
            message = _copy_review_notes(state, args, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_PROMPT:
            message = _copy_prompt_handoff(state, args, selected_only=False)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_FILE_PROMPT:
            message = _copy_prompt_handoff(state, args, selected_only=True)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SAVE_PROMPT:
            message = _save_prompt_handoff(
                state,
                args,
                parsed_command.value,
                selected_only=False,
            )
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SAVE_FILE_PROMPT:
            message = _save_prompt_handoff(
                state,
                args,
                parsed_command.value,
                selected_only=True,
            )
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.REVEAL_FILE:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                path = visible[state.selected].path
                message = selected_file_actions.reveal_selected_path(
                    path,
                    getattr(args, "reveal_cmd", None),
                    repo_path=git.repo_path,
                    reveal_path=file_actions.reveal_path,
                )
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to reveal.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SHOW_FILE_ACTION_DIAGNOSTICS:
            lines = _file_action_diagnostic_lines(args)
            if raw_keys:
                _show_browser_message(state, " | ".join(lines), raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _print_lines(lines)
            return BrowserActionResult()
        if action == BrowserCommandAction.SET_REVIEW_NOTE:
            message = _set_selected_review_note(state, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SHOW_REVIEW_NOTES:
            lines = _review_note_lines(state, parsed_command.value)
            if raw_keys:
                _show_browser_message(state, " | ".join(lines), raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _print_lines(lines)
            return BrowserActionResult()
        if action == BrowserCommandAction.SHOW_TASK_DIAGNOSTICS:
            lines = task_runtime.task_diagnostic_lines(git.repo_root(), args)
            if raw_keys:
                _show_browser_message(state, " | ".join(lines), raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _print_lines(lines)
            return BrowserActionResult()
        if action == BrowserCommandAction.SHOW_TASK_SCHEMA_HELP:
            lines = task_runtime.task_schema_help_lines()
            if raw_keys:
                _show_browser_message(state, " | ".join(lines), raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _print_lines(lines)
            return BrowserActionResult()
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
                BrowserNavigation.reset_history(state)
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
        if action == BrowserCommandAction.FORWARD:
            BrowserNavigation.go_forward(state)
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
                    "copy anchor, copy notes, copy prompt, save prompt, reveal, "
                    "note, notes, tasks, build, stop, rerun, test, lint, staged, "
                    "all, base, range, or q."
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
                        review_notes=state.review_notes,
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
                        state.review_notes.get(visible[state.selected].path, ""),
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
        if command_result == input_module.TICK:
            _draw_task_panel_only(state.task, style, frame, state.task_history)
            if frame.dirty:
                needs_redraw = True
            continue
        if command_result == input_module.EOF_COMMAND:
            _save_browser_workspace_state_on_exit(state, args, repo)
            return 0
        if command_result == input_module.INTERRUPT:
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
            if query != input_module.INTERRUPT:
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
            if command == input_module.INTERRUPT:
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
    return workspace_persistence.should_restore_workspace_state(args)


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


def _set_selected_review_note(state: BrowserState, note: str) -> str:
    return selected_file_actions.set_selected_review_note(state, note)


def _review_note_lines(state: BrowserState, query: str = "") -> list[str]:
    notes = {path: text.strip() for path, text in state.review_notes.items() if text.strip()}
    if not notes:
        return ["Review notes: none"]

    text_query = query.strip()
    normalized_query = text_query.casefold()
    filtered_notes = notes
    if normalized_query:
        filtered_notes = {
            path: text
            for path, text in notes.items()
            if normalized_query in path.casefold() or normalized_query in text.casefold()
        }
        if not filtered_notes:
            return [f'Review notes matching "{text_query}": none']

    lines = [f'Review notes matching "{text_query}":' if text_query else "Review notes:"]
    seen_paths: set[str] = set()
    index = 1
    for change in state.changes:
        note = filtered_notes.get(change.path)
        if note is None:
            continue
        lines.append(f"{index}. {shorten_path(change.path)}: {note}")
        seen_paths.add(change.path)
        index += 1

    for path in sorted(path for path in filtered_notes if path not in seen_paths):
        lines.append(f"{index}. {shorten_path(path)}: {filtered_notes[path]}")
        index += 1
    return lines


def _copy_review_notes(
    state: BrowserState,
    args: argparse.Namespace,
    query: str = "",
) -> str:
    text_query = query.strip()
    lines = _review_note_lines(state, text_query)
    note_count = len(lines) - 1
    if note_count == 0:
        if text_query:
            return "No matching review notes to copy."
        return "No review notes to copy."
    message = file_actions.copy_text(
        "\n".join(lines),
        getattr(args, "copy_cmd", None),
    )
    if message:
        return message
    if text_query:
        return f"Copied {note_count} matching review notes"
    return f"Copied {note_count} review notes"


def _copy_prompt_handoff(
    state: BrowserState,
    args: argparse.Namespace,
    *,
    selected_only: bool,
) -> str:
    return selected_file_actions.copy_prompt_handoff(
        state,
        args,
        selected_only=selected_only,
        copy_text=file_actions.copy_text,
        handoff_text=_prompt_handoff_text,
    )


def _save_prompt_handoff(
    state: BrowserState,
    args: argparse.Namespace,
    requested_path: str = "",
    *,
    selected_only: bool,
) -> str:
    return selected_file_actions.save_prompt_handoff(
        state,
        args,
        requested_path,
        selected_only=selected_only,
        repo_root=git.repo_root,
        save_prompt_text=handoff_module.save_prompt_text,
        handoff_text=_prompt_handoff_text,
    )


def _prompt_handoff_text(
    state: BrowserState,
    args: argparse.Namespace,
    *,
    selected_only: bool,
) -> tuple[str, int] | None:
    return selected_file_actions.prompt_handoff_text(
        state,
        args,
        selected_only=selected_only,
        build_data=build_review_data,
        render_prompt=render_prompt_handoff,
        other_counts=other_change_counts,
    )


def _file_action_diagnostic_lines(args: argparse.Namespace) -> list[str]:
    repo = git.repo_root()
    sample_file = repo / "{selected-file}"
    sources = [
        file_actions.open_command_source(
            sample_file,
            1,
            getattr(args, "open_cmd", None),
        ),
        file_actions.copy_command_source("{text}", getattr(args, "copy_cmd", None)),
        file_actions.reveal_command_source(
            sample_file,
            getattr(args, "reveal_cmd", None),
        ),
    ]
    return [
        "File actions:",
        *[
            f"{source.kind}: {file_actions.command_source_label(source)}"
            for source in sources
        ],
    ]


def _browser_workspace_state_path(repo: Path) -> Path:
    return workspace_persistence.workspace_state_path(repo)


def _save_browser_workspace_state_on_exit(
    state: BrowserState,
    args: argparse.Namespace,
    repo: Path,
) -> None:
    if not workspace_persistence.should_save_workspace_state(args):
        return
    _save_browser_workspace_state(state, args, repo)


def _save_browser_workspace_state(
    state: BrowserState,
    args: argparse.Namespace,
    repo: Path,
) -> None:
    workspace_persistence.save_workspace_state(
        state._sync_to_workspace(),
        args,
        repo,
        mode=_browser_workspace_state_mode(state),
    )


def _browser_workspace_state_data(
    state: BrowserState,
    args: argparse.Namespace,
) -> dict[str, object]:
    return workspace_persistence.workspace_state_data(
        state._sync_to_workspace(),
        args,
        mode=_browser_workspace_state_mode(state),
    )


def _browser_workspace_state_mode(state: BrowserState) -> str:
    mode = (
        BrowserPage.FILE_DETAIL
        if state.page == BrowserPage.FILE_DETAIL
        else BrowserPage.CHANGED_FILES
    )
    return mode


def _load_browser_workspace_state(repo: Path) -> dict[str, object] | None:
    return workspace_persistence.load_workspace_state(repo)


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
    workspace_persistence.restore_workspace_scope(args, workspace_state)


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
    BrowserNavigation.reset_history(state)
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
    BrowserNavigation.reset_history(state)
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
    BrowserNavigation.reset_history(state)
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
    return frame_module.screen_height()


def _file_body_capacity() -> int:
    return max(1, _screen_height() - 3)


def _task_panel_height(task: TaskState | None, available_lines: int) -> int:
    return frame_module.task_panel_height(task, available_lines)


def _screen_layout(task: TaskState | None, rows: int | None = None) -> ScreenLayout:
    return frame_module.screen_layout(task, rows)


def _task_panel_lines(
    task: TaskState | None,
    style: TerminalStyle,
    max_lines: int,
    history: list[TaskRecord] | None = None,
) -> list[str]:
    return frame_module.task_panel_lines(task, style, max_lines, history)


def _task_history_line(history: list[TaskRecord]) -> str:
    return frame_module.task_history_line(history)


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
    return frame_module.draw_task_panel_only(task, style, frame, history)


def _fit_terminal_line(line: str) -> str:
    return frame_module.fit_terminal_line(line)


def _browse_prompt(mode: str) -> str:
    return page_content.browse_prompt(mode)


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _normalize_command_query(command: str) -> str:
    normalized = command.strip()
    if normalized in {"", "?"}:
        return BrowserPage.COMMAND_PALETTE
    return normalized


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return page_content.browse_help_lines(style)


def _command_catalog() -> tuple[CommandGroup, ...]:
    return command_catalog_module.command_catalog()


def _command_palette_entries() -> list[PaletteCommand]:
    return command_catalog_module.command_palette_entries()


def _scope_home_entries() -> tuple[ScopeHomeEntry, ...]:
    return page_content.scope_home_entries()


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
    return command_catalog_module.filtered_command_palette_entries(
        state.command_filter_text
    )


def _selected_palette_command(state: BrowserState) -> PaletteCommand | None:
    state.clamp_selection()
    return command_catalog_module.selected_palette_command(
        state.command_filter_text,
        state.command_selected,
    )


def _browse_command_lines(style: TerminalStyle, max_lines: int) -> list[str]:
    return command_catalog_module.command_list_lines(style, max_lines)


def _browse_command_palette_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    state.clamp_selection()
    screen = command_catalog_module.command_palette_screen_lines(
        state.command_filter_text,
        state.command_selected,
        state.command_scroll,
        style,
        max_lines,
    )
    state.command_scroll = screen.scroll
    return screen.lines


def _browse_scope_home_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.browse_scope_home_screen_lines(state, style, max_lines)


def _scope_label(state: BrowserState, args: argparse.Namespace) -> str:
    return page_content.scope_label(state, args)


def _product_breadcrumb(state: BrowserState, args: argparse.Namespace) -> str:
    return page_content.product_breadcrumb(state, args)


def _args_untracked(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "untracked", False))


def _scope_context_line(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    return page_content.scope_context_line(state, args, style, _fit_terminal_line)


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
    review_notes: dict[str, str] | None = None,
) -> list[str]:
    return page_content.browse_list_lines(
        changes,
        args,
        style,
        selected=selected,
        total_changes=total_changes,
        filter_text=filter_text,
        scope_label_text=scope_label,
        seen_paths=seen_paths,
        seen_count=seen_count,
        remaining_only=remaining_only,
        review_notes=review_notes,
    )


def _browse_list_screen_lines(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.browse_list_screen_lines(state, args, style, max_lines)


def _browse_tree_rows(changes: list[git.FileChange]) -> list[BrowseTreeRow]:
    return page_content.browse_tree_rows(changes)


def _insert_browse_tree(
    root: _BrowseTreeNode,
    change: git.FileChange,
    change_index: int,
    common_dir: list[str],
) -> None:
    page_content.insert_browse_tree(root, change, change_index, common_dir)


def _render_browse_tree_children(
    node: _BrowseTreeNode,
    prefix: str,
) -> list[BrowseTreeRow]:
    return page_content.render_browse_tree_children(node, prefix)


def _format_browse_tree_row(
    row: BrowseTreeRow,
    selected: int | None,
    index_width: int,
    label_width: int,
    style: TerminalStyle,
    seen_paths: set[str] | None = None,
    review_notes: dict[str, str] | None = None,
) -> str:
    return page_content.format_browse_tree_row(
        row,
        selected,
        index_width,
        label_width,
        style,
        seen_paths,
        review_notes,
    )


def _style_tree_directory(label: str, style: TerminalStyle) -> str:
    return page_content.style_tree_directory(label, style)


def _style_tree_file(
    label: str,
    width: int,
    style: TerminalStyle,
) -> str:
    return page_content.style_tree_file(label, width, style)


def _split_tree_label(label: str) -> tuple[str, str]:
    return page_content.split_tree_label(label)


def _selected_tree_row(rows: list[BrowseTreeRow], selected: int) -> int:
    return page_content.selected_tree_row(rows, selected)


def _browser_common_changed_dir(changes: list[git.FileChange]) -> list[str]:
    return page_content.browser_common_changed_dir(changes)


def _browser_compact_root_label(common_dir: list[str]) -> str:
    return page_content.browser_compact_root_label(common_dir)


def _browse_commit_lines(
    commits: list[git.CommitSummary],
    style: TerminalStyle,
    selected: int | None = None,
    scope_label: str = "",
) -> list[str]:
    return page_content.browse_commit_lines(
        commits,
        style,
        selected=selected,
        scope_label_text=scope_label,
    )


def _browse_commit_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.browse_commit_screen_lines(state, style, max_lines)


def _empty_browse_lines(
    args: argparse.Namespace,
    filter_text: str = "",
    total_changes: int = 0,
    scope_label: str = "",
) -> list[str]:
    return page_content.empty_browse_lines(
        args,
        filter_text,
        total_changes,
        scope_label_text=scope_label,
    )


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
    review_note: str = "",
) -> list[str]:
    return page_content.browse_file_lines(
        change,
        index,
        total,
        args,
        style,
        scope_label_text=scope_label,
        seen=seen,
        review_note=review_note,
        first_changed_line=git.first_changed_line,
        link_target=_link_target,
        risk_hints=risk_hints,
        is_code_file=is_code_file,
        parse_change_symbols=parse_change_symbols,
        describe_file=describe_file,
        modified_names=modified_names,
        change_hunk_lines=change_hunk_lines,
    )


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
    review_note = state.review_notes.get(change.path, "")
    scope_label = _product_breadcrumb(state, args)
    key = _file_cache_key(change, index, total, args, seen, scope_label, review_note)
    if key not in state.file_line_cache:
        state.file_line_cache[key] = _browse_file_lines(
            change,
            index,
            total,
            args,
            style,
            scope_label,
            seen,
            review_note,
        )
    return state.file_line_cache[key]


def _file_cache_key(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    seen: bool = False,
    scope_label: str = "",
    review_note: str = "",
) -> str:
    return page_content.file_cache_key(
        change,
        index,
        total,
        args,
        seen=seen,
        scope_label_text=scope_label,
        review_note=review_note,
    )


def _ensure_window(
    current_start: int,
    selected: int,
    total: int,
    capacity: int,
) -> int:
    return page_content.ensure_window(current_start, selected, total, capacity)


def _use_raw_keys() -> bool:
    return input_module.use_raw_keys()


def _read_browse_command(
    prompt: str,
    raw_keys: bool,
    tick_when_idle: bool = False,
) -> str:
    return input_module.read_browse_command(
        prompt,
        raw_keys,
        tick_when_idle,
        raw_key_reader=_read_raw_key,
    )


def _read_filter_query(prompt: str = "filter> ") -> str:
    return input_module.read_filter_query(prompt)


def _read_command_query() -> str:
    return input_module.read_command_query()


def _read_raw_key(timeout: float | None = None) -> str:
    return input_module.read_raw_key(timeout)


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
    return selected_file_actions.open_selected_change(
        change,
        args,
        first_changed_line=git.first_changed_line,
        repo_path=git.repo_path,
        open_path=file_actions.open_path,
    )


def _link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)
