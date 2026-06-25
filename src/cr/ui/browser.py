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
    filter_changes,
    is_code_file,
    modified_names,
    other_change_counts,
    parse_change_symbols,
)
from ..review.data import build_review_data
from ..review.prompt import render_prompt_handoff
from ..review.risk import risk_hints
from ..review.snippet import render_file_diff_snippet
from ..review.tree import shorten_path
from ..source.purpose import describe_file
from ..vcs import git
from .commands import BrowserCommand, BrowserCommandAction, parse_browser_command
from . import commit_picker
from . import command_catalog as command_catalog_module
from .command_catalog import CommandEntry, CommandGroup, PaletteCommand
from . import file_detail_navigation
from . import file_actions
from . import frame as frame_module
from .frame import BrowserFrame, ScreenLayout
from . import handoff as handoff_module
from . import input as input_module
from .navigation import BrowserNavigation, BrowserPage, BrowserPageSnapshot
from . import page_content
from . import problem_context as problem_context_module
from . import review_notes as review_notes_module
from . import selected_file_actions
from . import source_file as source_file_module
from . import tasks as task_runtime
from . import task_problems as task_problems_module
from . import text_search
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


SOURCE_CONTEXT_MAX_LINES = 50


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
    task_scroll: int = 0
    problem_selected: int = 0
    problem_scroll: int = 0
    problem_filter: str = ""
    problem_sort: str = "output"
    problem_query: str = ""
    source_file_path: str = ""
    source_file_line: int = 1
    source_file_scroll: int = 0
    source_context_lines: int = 3
    source_selection_start: int = 0
    source_selection_end: int = 0
    page: str = BrowserPage.CHANGED_FILES
    filter_text: str = ""
    source_filter: str = ""
    file_find_text: str = ""
    task_find_text: str = ""
    source_find_text: str = ""
    seen_paths: set[str] = field(default_factory=set)
    remaining_only: bool = False
    review_notes: dict[str, str] = field(default_factory=dict)
    scope_selected: int = 0
    command_selected: int = 0
    command_filter_text: str = ""
    commit_filter_text: str = ""
    status_message: str = ""
    scope_counts: dict[str, int] = field(default_factory=dict)
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
                source_filter=self.source_filter,
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
        self.source_filter = workspace.source_filter
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
        workspace.source_filter = self.source_filter
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

    @property
    def visible_commits(self) -> list[git.CommitSummary]:
        return commit_picker.filter_commits_by_query(
            self.commits,
            self.commit_filter_text,
        )

    def clamp_selection(self) -> None:
        if self.page == BrowserPage.COMMIT_PICKER:
            total = len(self.visible_commits)
        elif self.page == BrowserPage.SCOPE_HOME:
            total = len(_scope_home_entries())
        elif self.page == BrowserPage.COMMAND_PALETTE:
            total = len(_filtered_command_palette_entries(self))
        elif self.page == BrowserPage.TASK_OUTPUT:
            total = 1
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

    def set_commit_filter(self, query: str) -> None:
        self.commit_filter_text = query.strip()
        self.selected = 0
        self.commit_scroll = 0
        self.clamp_selection()

    def clear_commit_filter(self) -> None:
        self.set_commit_filter("")


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
            if state.page == BrowserPage.COMMIT_PICKER:
                state.set_commit_filter(parsed_command.value)
            else:
                state.set_filter(parsed_command.value)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_FILTER:
            if state.page == BrowserPage.COMMAND_PALETTE:
                state.clear_command_filter()
            elif state.page == BrowserPage.COMMIT_PICKER:
                state.clear_commit_filter()
            else:
                state.clear_filter()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SET_SOURCE_FILTER:
            source = parsed_command.value
            if source not in {"staged", "unstaged", "mixed"}:
                _show_browser_message(
                    state,
                    "Unknown source filter. Use source staged, source unstaged, source mixed, or source all.",
                    raw_keys,
                    frame,
                )
                return BrowserActionResult(needs_redraw=raw_keys)
            state._sync_to_workspace().set_source_filter(source)
            state._sync_from_workspace()
            BrowserNavigation.show_changed_files(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_SOURCE_FILTER:
            state._sync_to_workspace().clear_source_filter()
            state._sync_from_workspace()
            BrowserNavigation.show_changed_files(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MARK_SEEN:
            workspace = state._sync_to_workspace()
            workspace.mark_selected_seen()
            state._sync_from_workspace()
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MARK_SEEN_AND_NEXT:
            message = _mark_selected_seen_and_move_next(state)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MARK_TODO:
            workspace = state._sync_to_workspace()
            workspace.unmark_selected_seen()
            state._sync_from_workspace()
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
            _show_scope_home(state, args)
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
            if state.page == BrowserPage.SOURCE_FILE:
                message = _open_source_file(state, args)
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                message = _open_change(visible[state.selected], args)
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
            _show_browser_message(state, "No changed file to open.", raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.OPEN_HUNK:
            message = _open_current_hunk(state, args, style)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.OPEN_LINE:
            message = _open_current_line(state, args, style)
            _show_browser_message(state, message, raw_keys, frame)
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
        if action == BrowserCommandAction.COPY_DIFF:
            message = selected_file_actions.copy_selected_diff_snippet(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_HUNK:
            message = _copy_current_hunk(state, args, style)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_LINE:
            if state.page == BrowserPage.SOURCE_FILE:
                message = _copy_source_line(state, args)
            else:
                message = _copy_current_line(state, args, style)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_SOURCE_CONTEXT:
            message = _copy_source_context(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SET_SOURCE_CONTEXT_LINES:
            message = _set_source_context_lines(state, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SET_SOURCE_SELECTION:
            message = _set_source_selection(state, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_SOURCE_SELECTION:
            message = _clear_source_selection(state)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.COPY_CHANGE:
            message = _copy_current_change(state, args, style)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SAVE_DIFF:
            message = selected_file_actions.save_selected_diff_snippet(
                state,
                args,
                parsed_command.value,
            )
            _show_browser_message(state, message, raw_keys, frame)
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
        if action == BrowserCommandAction.COPY_TASK_OUTPUT:
            message = _copy_task_output(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_TASK_PROBLEM:
            message = _copy_selected_task_problem(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_TASK_PROBLEMS:
            message = _copy_task_problems(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.COPY_PROBLEM_CONTEXT:
            message = _copy_problem_context(state, args)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SAVE_PROBLEM_CONTEXT:
            message = _save_problem_context(state, args, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.SHOW_TASK_OUTPUT:
            BrowserNavigation.show_task_output(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SET_TASK_PROBLEM_FILTER:
            BrowserNavigation.show_task_problems(
                state,
                problem_filter=parsed_command.value,
                problem_sort=state.problem_sort,
                problem_query=state.problem_query,
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_TASK_PROBLEM_FILTER:
            BrowserNavigation.show_task_problems(
                state,
                problem_sort=state.problem_sort,
                problem_query=state.problem_query,
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SET_TASK_PROBLEM_SORT:
            BrowserNavigation.show_task_problems(
                state,
                problem_filter=state.problem_filter,
                problem_sort=parsed_command.value,
                problem_query=state.problem_query,
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SET_TASK_PROBLEM_QUERY:
            BrowserNavigation.show_task_problems(
                state,
                problem_filter=state.problem_filter,
                problem_sort=state.problem_sort,
                problem_query=parsed_command.value,
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.CLEAR_TASK_PROBLEM_QUERY:
            BrowserNavigation.show_task_problems(
                state,
                problem_filter=state.problem_filter,
                problem_sort=state.problem_sort,
            )
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.SHOW_TASK_PROBLEMS:
            BrowserNavigation.show_task_problems(state)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.VIEW_TASK_PROBLEM:
            message = _view_selected_task_problem(state)
            if message:
                _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=True)
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
        if action == BrowserCommandAction.SAVE_TASK_OUTPUT:
            message = _save_task_output(state, parsed_command.value)
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
        if action == BrowserCommandAction.STAGE_FILE:
            return _run_selected_index_action(
                state,
                args,
                raw_keys,
                frame,
                empty_message="No changed file to stage.",
                action_result=lambda path: selected_file_actions.stage_selected_path_result(
                    path,
                    args,
                    stage_path=git.stage_path,
                ),
            )
        if action == BrowserCommandAction.UNSTAGE_FILE:
            return _run_selected_index_action(
                state,
                args,
                raw_keys,
                frame,
                empty_message="No changed file to unstage.",
                action_result=lambda path: selected_file_actions.unstage_selected_path_result(
                    path,
                    args,
                    unstage_path=git.unstage_path,
                ),
            )
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
        if action == BrowserCommandAction.SET_CHANGE_REVIEW_NOTE:
            message = _set_current_change_review_note(
                state,
                args,
                style,
                parsed_command.value,
            )
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
            elif state.page == BrowserPage.SCOPE_HOME:
                state.scope_counts = _load_scope_home_counts(args)
            else:
                message = _refresh_changed_files_for_command(state, args, style)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
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
            elif state.page == BrowserPage.TASK_OUTPUT:
                _scroll_task_output(state, 1)
            elif state.page == BrowserPage.TASK_PROBLEMS:
                _move_task_problem_selection(state, 1)
            elif state.page == BrowserPage.SOURCE_FILE:
                _scroll_source_file(state, 1)
            else:
                _move_selection(state, 1)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.MOVE_UP:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, -1, args, style)
            elif state.page == BrowserPage.TASK_OUTPUT:
                _scroll_task_output(state, -1)
            elif state.page == BrowserPage.TASK_PROBLEMS:
                _move_task_problem_selection(state, -1)
            elif state.page == BrowserPage.SOURCE_FILE:
                _scroll_source_file(state, -1)
            else:
                _move_selection(state, -1)
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.PAGE_DOWN:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, _page_step(), args, style)
            elif state.page == BrowserPage.TASK_OUTPUT:
                _scroll_task_output(state, _page_step())
            elif state.page == BrowserPage.TASK_PROBLEMS:
                _move_task_problem_selection(state, _page_step())
            elif state.page == BrowserPage.SOURCE_FILE:
                _scroll_source_file(state, _page_step())
            else:
                _move_selection(state, _page_step())
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.PAGE_UP:
            if state.page == BrowserPage.FILE_DETAIL:
                _scroll_file(state, -_page_step(), args, style)
            elif state.page == BrowserPage.TASK_OUTPUT:
                _scroll_task_output(state, -_page_step())
            elif state.page == BrowserPage.TASK_PROBLEMS:
                _move_task_problem_selection(state, -_page_step())
            elif state.page == BrowserPage.SOURCE_FILE:
                _scroll_source_file(state, -_page_step())
            else:
                _move_selection(state, -_page_step())
            return BrowserActionResult(needs_redraw=True)
        if action == BrowserCommandAction.NEXT_HUNK:
            message = _jump_file_hunk(state, args, style, "next")
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.PREVIOUS_HUNK:
            message = _jump_file_hunk(state, args, style, "previous")
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.NEXT_CHANGE:
            message = _jump_changed_row(state, args, style, "next")
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.PREVIOUS_CHANGE:
            message = _jump_changed_row(state, args, style, "previous")
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.FIND_IN_FILE:
            message = _find_in_current_page(state, args, style, parsed_command.value)
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.NEXT_MATCH:
            message = _find_next_match_in_current_page(state, args, style, "next")
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.PREVIOUS_MATCH:
            message = _find_next_match_in_current_page(
                state,
                args,
                style,
                "previous",
            )
            _show_browser_message(state, message, raw_keys, frame)
            return BrowserActionResult(needs_redraw=raw_keys)
        if action == BrowserCommandAction.HOME:
            if state.page == BrowserPage.FILE_DETAIL:
                state.file_scroll = 0
            elif state.page == BrowserPage.TASK_OUTPUT:
                state.task_scroll = 0
            elif state.page == BrowserPage.TASK_PROBLEMS:
                state.problem_selected = 0
                state.problem_scroll = 0
            elif state.page == BrowserPage.SOURCE_FILE:
                state.source_file_scroll = 0
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
            elif state.page == BrowserPage.TASK_OUTPUT:
                state.task_scroll = _max_task_output_scroll(state)
            elif state.page == BrowserPage.TASK_PROBLEMS:
                total = len(_current_task_problems(state))
                if total:
                    state.problem_selected = total - 1
            elif state.page == BrowserPage.SOURCE_FILE:
                state.source_file_scroll = _max_source_file_scroll(state)
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
            if state.page == BrowserPage.TASK_OUTPUT:
                return BrowserActionResult()
            if state.page == BrowserPage.TASK_PROBLEMS:
                message = _open_selected_task_problem(state, args)
                _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=raw_keys)
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
                    "copy anchor, copy diff, copy hunk, save diff, next hunk, "
                    "prev hunk, open hunk, copy notes, copy prompt, save prompt, reveal, "
                    "stage, unstage, note, notes, tasks, build, stop, rerun, test, lint, "
                    "source staged, staged, all, base, range, or q."
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
            visible_commits = state.visible_commits
            if 1 <= choice <= len(visible_commits):
                state.selected = choice - 1
                message = _select_commit(state, self.args)
                if message:
                    _show_browser_message(state, message, raw_keys, frame)
                return BrowserActionResult(needs_redraw=True)
            _show_browser_message(
                state,
                f"Choose 1-{len(visible_commits)}.",
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
                        filter_text=state.commit_filter_text,
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
            elif state.page == BrowserPage.TASK_OUTPUT:
                _print_lines(_browse_task_output_screen_lines(state, style, _screen_height()))
            elif state.page == BrowserPage.TASK_PROBLEMS:
                _print_lines(
                    _browse_task_problems_screen_lines(
                        state,
                        style,
                        _screen_height(),
                    )
                )
            elif state.page == BrowserPage.SOURCE_FILE:
                _print_lines(
                    _browse_source_file_screen_lines(
                        state,
                        style,
                        _screen_height(),
                    )
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
                        source_filter=state.source_filter,
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
            if state.page in {BrowserPage.TASK_OUTPUT, BrowserPage.TASK_PROBLEMS}:
                needs_redraw = True
                continue
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
                elif state.page == BrowserPage.COMMIT_PICKER:
                    state.set_commit_filter(query)
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


def _mark_selected_seen_and_move_next(state: BrowserState) -> str:
    was_file_detail = state.page == BrowserPage.FILE_DETAIL
    workspace = state._sync_to_workspace()
    progress = workspace.mark_selected_seen_and_advance()
    state._sync_from_workspace()

    if progress.marked_path is None:
        return "No changed file to mark seen."
    if progress.target_path is None:
        BrowserNavigation.show_changed_files(state)
        state.clamp_selection()
        return f"Marked {shorten_path(progress.marked_path)} seen. No remaining files."

    if was_file_detail:
        BrowserNavigation.open_file_detail(state)
    else:
        state.clamp_selection()

    if progress.target_path == progress.marked_path and not progress.had_next_before:
        return (
            f"Marked {shorten_path(progress.marked_path)} seen. "
            f"No next file after {shorten_path(progress.marked_path)}."
        )
    return (
        f"Marked {shorten_path(progress.marked_path)} seen. "
        f"Moved to {shorten_path(progress.target_path)}."
    )


def _set_selected_review_note(state: BrowserState, note: str) -> str:
    return selected_file_actions.set_selected_review_note(state, note)


def _set_current_change_review_note(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    note: str,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to note change."
    visible = state.visible_changes
    if not visible:
        return "No changed file to note change."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.append_selected_change_review_note(
        state,
        change,
        lines,
        state.file_scroll,
        note,
    )


def _review_note_lines(state: BrowserState, query: str = "") -> list[str]:
    return review_notes_module.review_note_lines(
        state.changes,
        state.review_notes,
        query,
    )


def _copy_review_notes(
    state: BrowserState,
    args: argparse.Namespace,
    query: str = "",
) -> str:
    return review_notes_module.copy_review_notes(
        state.changes,
        state.review_notes,
        query,
        getattr(args, "copy_cmd", None),
        copy_text=file_actions.copy_text,
    )


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


def _copy_task_output(state: BrowserState, args: argparse.Namespace) -> str:
    if state.task is None:
        return "No task output to copy."
    text = task_runtime.task_output_handoff_text(state.task)
    message = file_actions.copy_text(text, getattr(args, "copy_cmd", None))
    if message:
        return message
    return "Copied task output."


def _copy_selected_task_problem(state: BrowserState, args: argparse.Namespace) -> str:
    problems = _current_task_problems(state)
    if not problems:
        return "No task problem to copy."
    selected = max(0, min(state.problem_selected, len(problems) - 1))
    text = task_problems_module.problem_handoff_text(problems[selected])
    message = file_actions.copy_text(text, getattr(args, "copy_cmd", None))
    if message:
        return message
    return "Copied task problem."


def _copy_task_problems(state: BrowserState, args: argparse.Namespace) -> str:
    problems = _current_task_problems(state)
    if not problems:
        return "No task problems to copy."
    text = task_problems_module.problems_handoff_text(problems)
    message = file_actions.copy_text(text, getattr(args, "copy_cmd", None))
    if message:
        return message
    return f"Copied {len(problems)} task problems."


def _copy_problem_context(state: BrowserState, args: argparse.Namespace) -> str:
    text, anchor, error = _problem_context_text(
        state,
        args,
        empty_message="No problem context to copy.",
    )
    if error:
        return error
    message = file_actions.copy_text(text, getattr(args, "copy_cmd", None))
    if message:
        return message
    return f"Copied problem context {anchor}."


def _save_problem_context(
    state: BrowserState,
    args: argparse.Namespace,
    requested_path: str = "",
) -> str:
    text, _anchor, error = _problem_context_text(
        state,
        args,
        empty_message="No problem context to save.",
    )
    if error:
        return error
    result = handoff_module.save_problem_context_text(
        text,
        git.repo_root(),
        requested_path,
    )
    if result.error:
        return result.error
    return f"Saved problem context to {result.display_path}."


def _problem_context_text(
    state: BrowserState,
    args: argparse.Namespace,
    *,
    empty_message: str,
) -> tuple[str, str, str]:
    target = _problem_context_target(state)
    if target is None:
        return "", "", empty_message
    path, line, problem_text, context_lines = target
    content = source_file_module.load_source_file_content(git.repo_root(), path)
    if content.error:
        return "", "", content.error
    source_text = source_file_module.source_context_markdown(
        content,
        target_line=line,
        context_lines=context_lines,
    )
    anchor = f"{content.path}:{max(1, min(line, len(content.lines)))}"
    text = problem_context_module.problem_context_markdown(
        anchor=anchor,
        problem_text=problem_text,
        source_text=source_text,
        diff_text=_problem_context_diff(state, args, content.path),
    )
    return text, anchor, ""


def _problem_context_target(state: BrowserState) -> tuple[str, int, str, int] | None:
    if state.page == BrowserPage.TASK_PROBLEMS:
        problems = _current_task_problems(state)
        if not problems:
            return None
        selected = max(0, min(state.problem_selected, len(problems) - 1))
        problem = problems[selected]
        return (
            problem.path,
            problem.line,
            task_problems_module.problem_handoff_text(problem),
            3,
        )
    if state.page == BrowserPage.SOURCE_FILE and state.source_file_path:
        return (
            state.source_file_path,
            max(1, state.source_file_line),
            "",
            state.source_context_lines,
        )
    return None


def _problem_context_diff(
    state: BrowserState,
    args: argparse.Namespace,
    path: str,
) -> str:
    change = next((change for change in state.changes if change.path == path), None)
    if change is None:
        return ""
    review_notes = {}
    note = state.review_notes.get(change.path, "").strip()
    if note:
        review_notes[change.path] = note
    data = build_review_data(
        [change],
        staged=getattr(args, "staged", False),
        all_changes=getattr(args, "all_changes", False),
        base=getattr(args, "base", None),
        ref_range=getattr(args, "ref_range", None),
        include_hunks=True,
        other_changes=_safe_other_change_counts(args),
        context=getattr(args, "context", 2),
        seen_paths=state.seen_paths,
        review_notes=review_notes,
    )
    return render_file_diff_snippet(data["files"][0])


def _safe_other_change_counts(args: argparse.Namespace) -> dict[str, int]:
    required = (
        "all_changes",
        "base",
        "code",
        "paths",
        "ref_range",
        "staged",
        "untracked",
    )
    if not all(hasattr(args, name) for name in required):
        return {"staged": 0, "unstaged": 0}
    return other_change_counts(args)


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


def _save_task_output(state: BrowserState, requested_path: str = "") -> str:
    if state.task is None:
        return "No task output to save."
    text = task_runtime.task_output_handoff_text(state.task)
    result = handoff_module.save_task_output_text(
        text,
        git.repo_root(),
        requested_path,
    )
    if result.error:
        return result.error
    return f"Saved task output to {result.display_path}"


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


def _load_scope_home_counts(args: argparse.Namespace) -> dict[str, int]:
    counts: dict[str, int] = {}
    count_specs = (
        ("worktree", {"staged": False, "all_changes": False}),
        ("staged", {"staged": True, "all_changes": False}),
        ("all", {"staged": False, "all_changes": True}),
    )
    for key, options in count_specs:
        changes = _load_scope_count_changes(args, **options)
        if changes is not None:
            counts[key] = len(changes)
    counts["commits"] = len(_load_recent_commits())
    return counts


def _load_scope_count_changes(
    args: argparse.Namespace,
    *,
    staged: bool,
    all_changes: bool,
) -> list[git.FileChange] | None:
    try:
        changes = git.changed_files(
            getattr(args, "paths", []),
            staged=staged,
            all_changes=all_changes,
            include_untracked=getattr(args, "untracked", False) and not staged,
        )
    except git.GitError:
        return None
    return filter_changes(changes, code_only=getattr(args, "code", False))


def _show_scope_home(state: BrowserState, args: argparse.Namespace) -> None:
    state.scope_counts = _load_scope_home_counts(args)
    BrowserNavigation.show_scope_home(state)


def _refresh_changed_files_after_action(
    state: BrowserState,
    args: argparse.Namespace,
) -> None:
    state.changes = _load_browse_changes(args)
    state.clear_render_cache()
    BrowserNavigation.reset_history(state)
    BrowserNavigation.show_changed_files(state)
    state.list_scroll = 0
    _show_commits_when_empty(state, args)
    state.clamp_selection()


def _refresh_changed_files_for_command(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str | None:
    keep_file_detail = state.page == BrowserPage.FILE_DETAIL
    selected_path = _selected_visible_path(state) if keep_file_detail else None
    previous_scroll = state.file_scroll
    workspace = state._sync_to_workspace()
    workspace.reload_changes(
        args,
        loader=_load_browse_changes,
        preserve_selected_path=selected_path,
    )
    state._sync_from_workspace()
    state.first_line_cache.clear()
    state.file_line_cache.clear()
    BrowserNavigation.reset_history(state)
    _show_commits_when_empty(state, args)
    state.clamp_selection()
    if keep_file_detail and selected_path and _selected_visible_path(state) == selected_path:
        BrowserNavigation.replace_with_file_detail(state)
        state.file_scroll = min(previous_scroll, _max_file_scroll(state, args, style))
        return None
    if keep_file_detail and selected_path and state.page == BrowserPage.FILE_DETAIL:
        BrowserNavigation.replace_with_changed_files(state)
        return "Current file no longer visible after refresh."
    if state.page == BrowserPage.FILE_DETAIL:
        BrowserNavigation.replace_with_changed_files(state)
    return None


def _selected_visible_path(state: BrowserState) -> str | None:
    visible = state.visible_changes
    if not visible:
        return None
    state.clamp_selection()
    return visible[state.selected].path


def _run_selected_index_action(
    state: BrowserState,
    args: argparse.Namespace,
    raw_keys: bool,
    frame: BrowserFrame,
    *,
    empty_message: str,
    action_result,
) -> BrowserActionResult:
    visible = state.visible_changes
    if visible:
        state.clamp_selection()
        path = visible[state.selected].path
        index_result = action_result(path)
        if index_result.changed:
            _refresh_changed_files_after_action(state, args)
        _show_browser_message(state, index_result.message, raw_keys, frame)
        return BrowserActionResult(needs_redraw=raw_keys)
    _show_browser_message(state, empty_message, raw_keys, frame)
    return BrowserActionResult(needs_redraw=raw_keys)


def _show_commits_when_empty(state: BrowserState, args: argparse.Namespace) -> None:
    if state.changes or args.base or args.ref_range or args.staged or args.all_changes:
        return
    state.commits = _load_recent_commits()
    if state.commits:
        BrowserNavigation.show_commit_picker(state)


def _select_commit(state: BrowserState, args: argparse.Namespace) -> str | None:
    state.clamp_selection()
    commit = commit_picker.selected_commit(
        state.commits,
        state.selected,
        state.commit_filter_text,
    )
    if commit is None:
        return "No recent commits."
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
        total = len(state.visible_commits)
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


def _move_task_problem_selection(state: BrowserState, delta: int) -> None:
    total = len(_current_task_problems(state))
    if not total:
        return
    state.problem_selected = max(0, min(state.problem_selected + delta, total - 1))


def _scroll_source_file(state: BrowserState, delta: int) -> None:
    current = _current_source_file_view(state, _source_file_body_capacity(state.task))
    state.source_file_scroll = max(
        0,
        min(current.scroll + delta, _max_source_file_scroll(state)),
    )


def _scroll_file(
    state: BrowserState,
    delta: int,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    max_scroll = _max_file_scroll(state, args, style)
    state.file_scroll = max(0, min(state.file_scroll + delta, max_scroll))


def _scroll_task_output(state: BrowserState, delta: int) -> None:
    max_scroll = _max_task_output_scroll(state)
    state.task_scroll = max(0, min(state.task_scroll + delta, max_scroll))


def _jump_file_hunk(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    direction: str,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to jump hunks."
    visible = state.visible_changes
    if not visible:
        return "No changed file to jump hunks."
    state.clamp_selection()
    lines = _cached_file_lines(
        state,
        visible[state.selected],
        state.selected,
        len(visible),
        args,
        style,
    )
    result = file_detail_navigation.jump_to_hunk(
        lines,
        state.file_scroll,
        direction,
        max_scroll=_max_file_scroll(state, args, style),
    )
    state.file_scroll = result.scroll
    return result.message


def _jump_changed_row(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    direction: str,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to jump changes."
    visible = state.visible_changes
    if not visible:
        return "No changed file to jump changes."
    state.clamp_selection()
    lines = _cached_file_lines(
        state,
        visible[state.selected],
        state.selected,
        len(visible),
        args,
        style,
    )
    result = file_detail_navigation.jump_to_changed_row(
        lines,
        state.file_scroll,
        direction,
    )
    state.file_scroll = result.scroll
    return result.message


def _find_in_current_file(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    query: str,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to find text."
    visible = state.visible_changes
    if not visible:
        return "No changed file to find text."
    state.clamp_selection()
    lines = _cached_file_lines(
        state,
        visible[state.selected],
        state.selected,
        len(visible),
        args,
        style,
    )
    text_query = query.strip()
    if text_query:
        state.file_find_text = text_query
    result = file_detail_navigation.find_text(lines, query)
    if result.found:
        state.file_scroll = min(result.scroll, _max_file_scroll(state, args, style))
    return result.message


def _find_in_current_page(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    query: str,
) -> str:
    if state.page == BrowserPage.TASK_OUTPUT:
        return _find_in_task_output(state, query)
    if state.page == BrowserPage.SOURCE_FILE:
        return _find_in_source_file(state, query)
    return _find_in_current_file(state, args, style, query)


def _find_in_task_output(state: BrowserState, query: str) -> str:
    if state.task is None:
        return "No task output to find."
    text_query = query.strip()
    if text_query:
        state.task_find_text = text_query
    result = text_search.find_text(
        state.task.lines,
        query,
        skip_first_line=False,
    )
    if result.found:
        state.task_scroll = min(result.scroll, _max_task_output_scroll(state))
    return result.message


def _find_in_source_file(state: BrowserState, query: str) -> str:
    if not state.source_file_path:
        return "No source file to find."
    content = source_file_module.load_source_file_content(
        git.repo_root(),
        state.source_file_path,
    )
    if content.error:
        return content.error
    text_query = query.strip()
    if text_query:
        state.source_find_text = text_query
    result = text_search.find_text(
        content.lines,
        query,
        skip_first_line=False,
    )
    if result.found:
        state.source_file_line = result.scroll + 1
        state.source_file_scroll = -1
    return result.message


def _find_next_match(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    direction: str,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to find text."
    text_query = state.file_find_text.strip()
    if not text_query:
        return "Run find TEXT first."
    visible = state.visible_changes
    if not visible:
        return "No changed file to find text."
    state.clamp_selection()
    lines = _cached_file_lines(
        state,
        visible[state.selected],
        state.selected,
        len(visible),
        args,
        style,
    )
    result = file_detail_navigation.find_next_text(
        lines,
        text_query,
        state.file_scroll,
        direction,
    )
    if result.found:
        state.file_scroll = min(result.scroll, _max_file_scroll(state, args, style))
    return result.message


def _find_next_match_in_current_page(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
    direction: str,
) -> str:
    if state.page == BrowserPage.TASK_OUTPUT:
        return _find_next_task_output_match(state, direction)
    if state.page == BrowserPage.SOURCE_FILE:
        return _find_next_source_file_match(state, direction)
    return _find_next_match(state, args, style, direction)


def _find_next_task_output_match(state: BrowserState, direction: str) -> str:
    if state.task is None:
        return "No task output to find."
    text_query = state.task_find_text.strip()
    if not text_query:
        return "Run find TEXT first."
    result = text_search.find_next_text(
        state.task.lines,
        text_query,
        state.task_scroll,
        direction,
        skip_first_line=False,
    )
    if result.found:
        state.task_scroll = min(result.scroll, _max_task_output_scroll(state))
    return result.message


def _find_next_source_file_match(state: BrowserState, direction: str) -> str:
    if not state.source_file_path:
        return "No source file to find."
    text_query = state.source_find_text.strip()
    if not text_query:
        return "Run find TEXT first."
    content = source_file_module.load_source_file_content(
        git.repo_root(),
        state.source_file_path,
    )
    if content.error:
        return content.error
    result = text_search.find_next_text(
        content.lines,
        text_query,
        max(0, state.source_file_line - 1),
        direction,
        skip_first_line=False,
    )
    if result.found:
        state.source_file_line = result.scroll + 1
        state.source_file_scroll = -1
    return result.message


def _open_current_hunk(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to open hunk."
    visible = state.visible_changes
    if not visible:
        return "No changed file to open hunk."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.open_selected_hunk(
        change,
        lines,
        state.file_scroll,
        args,
    )


def _open_current_line(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to open line."
    visible = state.visible_changes
    if not visible:
        return "No changed file to open line."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.open_selected_line(
        change,
        lines,
        state.file_scroll,
        args,
    )


def _copy_current_hunk(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to copy hunk."
    visible = state.visible_changes
    if not visible:
        return "No changed file to copy hunk."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.copy_selected_hunk(
        change,
        lines,
        state.file_scroll,
        args,
    )


def _copy_current_line(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to copy line."
    visible = state.visible_changes
    if not visible:
        return "No changed file to copy line."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.copy_selected_line(
        change,
        lines,
        state.file_scroll,
        args,
    )


def _copy_source_line(
    state: BrowserState,
    args: argparse.Namespace,
) -> str:
    if not state.source_file_path:
        return "No source file line to copy."
    line_number = max(1, state.source_file_line)
    anchor = f"{state.source_file_path}:{line_number}"
    error = file_actions.copy_text(anchor, getattr(args, "copy_cmd", None))
    if error:
        return error
    return f"Copied source line {anchor}."


def _copy_source_context(
    state: BrowserState,
    args: argparse.Namespace,
) -> str:
    if state.page != BrowserPage.SOURCE_FILE or not state.source_file_path:
        return "No source file to copy."
    content = source_file_module.load_source_file_content(
        git.repo_root(),
        state.source_file_path,
    )
    if content.error:
        return content.error
    target_line = max(1, state.source_file_line)
    selection = _source_selection_range(state)
    if selection is None:
        text = source_file_module.source_context_markdown(
            content,
            target_line=target_line,
            context_lines=state.source_context_lines,
        )
    else:
        text = source_file_module.source_range_markdown(
            content,
            start_line=selection[0],
            end_line=selection[1],
            target_line=target_line,
        )
    error = file_actions.copy_text(text, getattr(args, "copy_cmd", None))
    if error:
        return error
    target_line = max(1, min(target_line, len(content.lines)))
    if selection is not None:
        start, end = _clamp_source_range(selection[0], selection[1], len(content.lines))
        return f"Copied selected source {content.path}:{start}-{end}."
    return f"Copied source context {content.path}:{target_line}."


def _set_source_context_lines(state: BrowserState, raw_value: str) -> str:
    if state.page != BrowserPage.SOURCE_FILE:
        return "Open a source file before setting source context."
    try:
        context_lines = int(raw_value)
    except ValueError:
        return "Source context must be a non-negative integer."
    if context_lines < 0:
        return "Source context must be a non-negative integer."
    state.source_context_lines = min(context_lines, SOURCE_CONTEXT_MAX_LINES)
    return f"Source context set to {state.source_context_lines}."


def _set_source_selection(state: BrowserState, raw_value: str) -> str:
    if state.page != BrowserPage.SOURCE_FILE:
        return "Open a source file before selecting source."
    parts = raw_value.split()
    if len(parts) != 2:
        return "Source selection must be two positive line numbers."
    try:
        start_line, end_line = (int(part) for part in parts)
    except ValueError:
        return "Source selection must be two positive line numbers."
    if start_line <= 0 or end_line <= 0:
        return "Source selection must be two positive line numbers."
    start, end = sorted((start_line, end_line))
    state.source_selection_start = start
    state.source_selection_end = end
    return f"Source selection set to {start}-{end}."


def _clear_source_selection(state: BrowserState) -> str:
    if state.page != BrowserPage.SOURCE_FILE:
        return "Open a source file before clearing source selection."
    state.source_selection_start = 0
    state.source_selection_end = 0
    return "Source selection cleared."


def _source_selection_range(state: BrowserState) -> tuple[int, int] | None:
    if state.source_selection_start <= 0 or state.source_selection_end <= 0:
        return None
    return tuple(sorted((state.source_selection_start, state.source_selection_end)))


def _clamp_source_range(start_line: int, end_line: int, total_lines: int) -> tuple[int, int]:
    start, end = sorted((start_line, end_line))
    start = max(1, min(start, total_lines))
    end = max(1, min(end, total_lines))
    return start, end


def _copy_current_change(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> str:
    if state.page != BrowserPage.FILE_DETAIL:
        return "Open a file detail to copy change."
    visible = state.visible_changes
    if not visible:
        return "No changed file to copy change."
    state.clamp_selection()
    change = visible[state.selected]
    lines = _cached_file_lines(
        state,
        change,
        state.selected,
        len(visible),
        args,
        style,
    )
    return selected_file_actions.copy_selected_change(
        change,
        lines,
        state.file_scroll,
        args,
    )


def _open_selected_task_problem(state: BrowserState, args: argparse.Namespace) -> str:
    problems = _current_task_problems(state)
    if not problems:
        return "No task problems to open."
    state.problem_selected = max(0, min(state.problem_selected, len(problems) - 1))
    problem = problems[state.problem_selected]
    repo_file = git.repo_root() / problem.path
    message = file_actions.open_path(
        repo_file,
        problem.line,
        getattr(args, "open_cmd", None),
    )
    if message:
        return message
    return f"Opened problem {problem.path}:{problem.line}"


def _view_selected_task_problem(state: BrowserState) -> str:
    problems = _current_task_problems(state)
    if not problems:
        return "No task problem to view."
    selected = max(0, min(state.problem_selected, len(problems) - 1))
    problem = problems[selected]
    BrowserNavigation.show_source_file(state, problem.path, problem.line)
    return ""


def _open_source_file(state: BrowserState, args: argparse.Namespace) -> str:
    if not state.source_file_path:
        return "No source file to open."
    repo_file = git.repo_root() / state.source_file_path
    message = file_actions.open_path(
        repo_file,
        state.source_file_line,
        getattr(args, "open_cmd", None),
    )
    if message:
        return message
    return f"Opened source {state.source_file_path}:{state.source_file_line}"


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


def _max_task_output_scroll(state: BrowserState) -> int:
    layout = _screen_layout(state.task)
    body_lines = max(1, layout.content_height - 2)
    return page_content.max_task_output_scroll(state, body_lines)


def _max_source_file_scroll(state: BrowserState) -> int:
    view = source_file_module.load_source_file_view(
        git.repo_root(),
        state.source_file_path,
        target_line=state.source_file_line,
        scroll=10**9,
        capacity=max(1, _source_file_body_capacity(state.task) - 2),
    )
    if view.error:
        return 0
    return view.scroll


def _page_step() -> int:
    return max(5, _screen_height() - 8)


def _screen_height() -> int:
    return frame_module.screen_height()


def _file_body_capacity() -> int:
    return max(1, _screen_height() - 3)


def _source_file_body_capacity(task: TaskState | None) -> int:
    layout = _screen_layout(task)
    return max(1, layout.content_height - 2)


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
    header_lines = [
        _scope_context_line(state, args, style),
        _contextual_action_bar(state.page, style),
    ]
    body_lines = max(1, content_lines - len(header_lines))
    if state.page == BrowserPage.COMMIT_PICKER:
        lines = [
            *header_lines,
            *_browse_commit_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.SCOPE_HOME:
        lines = [
            *header_lines,
            *_browse_scope_home_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.COMMAND_PALETTE:
        lines = [
            *header_lines,
            *_browse_command_palette_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.TASK_OUTPUT:
        lines = [
            *header_lines,
            *_browse_task_output_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.TASK_PROBLEMS:
        lines = [
            *header_lines,
            *_browse_task_problems_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.SOURCE_FILE:
        lines = [
            *header_lines,
            *_browse_source_file_screen_lines(
                state,
                style,
                body_lines,
            ),
        ]
    elif state.page == BrowserPage.CHANGED_FILES:
        lines = [
            *header_lines,
            *_browse_list_screen_lines(
                state,
                args,
                style,
                body_lines,
            ),
        ]
    elif visible:
        lines = [
            *header_lines,
            *_browse_file_screen_lines(
                state,
                visible[state.selected],
                state.selected,
                len(visible),
                args,
                style,
                body_lines,
            ),
        ]
    else:
        lines = [
            *header_lines,
            *_empty_browse_lines(
                args,
                state.filter_text,
                total_changes=len(state.changes),
                scope_label=_scope_label(state, args),
            )[:body_lines],
        ]
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


def _contextual_action_bar(page: str, style: TerminalStyle) -> str:
    return page_content.contextual_action_bar(page, style, _fit_terminal_line)


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
    source_filter: str = "",
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
        source_filter=source_filter,
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
    filter_text: str = "",
) -> list[str]:
    return page_content.browse_commit_lines(
        commits,
        style,
        selected=selected,
        scope_label_text=scope_label,
        filter_text=filter_text,
    )


def _browse_commit_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.browse_commit_screen_lines(state, style, max_lines)


def _browse_task_output_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.task_output_screen_lines(state, style, max_lines)


def _browse_task_problems_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    return page_content.task_problems_screen_lines(
        state,
        _current_task_problems(state),
        style,
        max_lines,
    )


def _browse_source_file_screen_lines(
    state: BrowserState,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    view = _current_source_file_view(state, max_lines)
    state.source_file_scroll = view.scroll
    return page_content.source_file_screen_lines(
        view,
        style,
        max_lines,
        context_lines=state.source_context_lines,
        selection_start=state.source_selection_start,
        selection_end=state.source_selection_end,
    )


def _current_task_problems(state: BrowserState) -> list[task_problems_module.TaskProblem]:
    if state.task is None:
        return []
    problems = task_problems_module.extract_task_problems(
        git.repo_root(),
        state.task.lines,
    )
    visible = task_problems_module.filter_task_problems(problems, state.problem_filter)
    visible = task_problems_module.filter_task_problems_by_query(
        visible,
        state.problem_query,
    )
    return task_problems_module.sort_task_problems(visible, state.problem_sort)


def _current_source_file_view(
    state: BrowserState,
    max_lines: int,
) -> source_file_module.SourceFileView:
    return source_file_module.load_source_file_view(
        git.repo_root(),
        state.source_file_path,
        target_line=state.source_file_line,
        scroll=state.source_file_scroll,
        capacity=max(1, max_lines - 2),
        selection_start=state.source_selection_start,
        selection_end=state.source_selection_end,
    )


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
        "↑/↓ scroll   ]/[: hunk   PgUp/PgDn page   b back"
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
