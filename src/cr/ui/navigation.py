"""Browser navigation rules for the interactive review workbench.

This module owns page transition intent and the small state resets that must
happen with those transitions. It does not load Git data, switch review scopes,
render terminal output, or own review workspace data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


class BrowserPage:
    SCOPE_HOME = "scopes"
    COMMIT_PICKER = "commits"
    CHANGED_FILES = "list"
    FILE_DETAIL = "file"
    COMMAND_PALETTE = "commands"


@dataclass(frozen=True)
class BrowserPageSnapshot:
    page: str
    selected: int
    list_scroll: int
    file_scroll: int
    scope_selected: int
    command_selected: int
    command_scroll: int
    command_filter_text: str
    selected_commit: Optional[object]
    commit_scroll: int


class _BrowserNavigationState(Protocol):
    page: str
    file_scroll: int
    scope_selected: int
    command_selected: int
    command_scroll: int
    selected_commit: Optional[object]
    selected: int
    commit_scroll: int
    list_scroll: int
    command_filter_text: str
    page_back_stack: list[BrowserPageSnapshot]
    page_forward_stack: list[BrowserPageSnapshot]


class BrowserNavigation:
    @staticmethod
    def show_changed_files(state: _BrowserNavigationState) -> None:
        BrowserNavigation._record_transition(state, BrowserPage.CHANGED_FILES)
        state.page = BrowserPage.CHANGED_FILES
        state.file_scroll = 0

    @staticmethod
    def show_scope_home(state: _BrowserNavigationState) -> None:
        BrowserNavigation._record_transition(state, BrowserPage.SCOPE_HOME)
        state.page = BrowserPage.SCOPE_HOME
        state.scope_selected = 0

    @staticmethod
    def show_command_palette(state: _BrowserNavigationState) -> None:
        BrowserNavigation._record_transition(state, BrowserPage.COMMAND_PALETTE)
        state.page = BrowserPage.COMMAND_PALETTE
        state.command_selected = 0
        state.command_scroll = 0

    @staticmethod
    def show_commit_picker(
        state: _BrowserNavigationState,
        *,
        clear_selected_commit: bool = False,
    ) -> None:
        BrowserNavigation._record_transition(state, BrowserPage.COMMIT_PICKER)
        state.page = BrowserPage.COMMIT_PICKER
        if clear_selected_commit:
            state.selected_commit = None
        state.selected = 0
        state.commit_scroll = 0

    @staticmethod
    def open_file_detail(state: _BrowserNavigationState) -> None:
        BrowserNavigation._record_transition(state, BrowserPage.FILE_DETAIL)
        state.page = BrowserPage.FILE_DETAIL
        state.file_scroll = 0

    @staticmethod
    def replace_with_file_detail(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.FILE_DETAIL

    @staticmethod
    def replace_with_changed_files(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.CHANGED_FILES
        state.file_scroll = 0

    @staticmethod
    def go_back(state: _BrowserNavigationState) -> None:
        if state.page_back_stack:
            current = BrowserNavigation._snapshot(state)
            snapshot = state.page_back_stack.pop()
            state.page_forward_stack.append(current)
            BrowserNavigation._restore(state, snapshot)
            return
        if state.page in {
            BrowserPage.COMMAND_PALETTE,
            BrowserPage.SCOPE_HOME,
            BrowserPage.FILE_DETAIL,
        }:
            BrowserNavigation._restore_changed_files_fallback(state)
            return
        if state.selected_commit is not None:
            BrowserNavigation._restore_commit_picker_fallback(state)
            state.file_scroll = 0
            return
        BrowserNavigation._restore_changed_files_fallback(state)

    @staticmethod
    def go_forward(state: _BrowserNavigationState) -> None:
        if not state.page_forward_stack:
            return
        current = BrowserNavigation._snapshot(state)
        snapshot = state.page_forward_stack.pop()
        state.page_back_stack.append(current)
        BrowserNavigation._restore(state, snapshot)

    @staticmethod
    def reset_history(state: _BrowserNavigationState) -> None:
        state.page_back_stack.clear()
        state.page_forward_stack.clear()

    @staticmethod
    def _record_transition(state: _BrowserNavigationState, next_page: str) -> None:
        if state.page == next_page:
            return
        state.page_back_stack.append(BrowserNavigation._snapshot(state))
        state.page_forward_stack.clear()

    @staticmethod
    def _snapshot(state: _BrowserNavigationState) -> BrowserPageSnapshot:
        return BrowserPageSnapshot(
            page=state.page,
            selected=state.selected,
            list_scroll=state.list_scroll,
            file_scroll=state.file_scroll,
            scope_selected=state.scope_selected,
            command_selected=state.command_selected,
            command_scroll=state.command_scroll,
            command_filter_text=state.command_filter_text,
            selected_commit=state.selected_commit,
            commit_scroll=state.commit_scroll,
        )

    @staticmethod
    def _restore(
        state: _BrowserNavigationState,
        snapshot: BrowserPageSnapshot,
    ) -> None:
        state.page = snapshot.page
        state.selected = snapshot.selected
        state.list_scroll = snapshot.list_scroll
        state.file_scroll = snapshot.file_scroll
        state.scope_selected = snapshot.scope_selected
        state.command_selected = snapshot.command_selected
        state.command_scroll = snapshot.command_scroll
        state.command_filter_text = snapshot.command_filter_text
        state.selected_commit = snapshot.selected_commit
        state.commit_scroll = snapshot.commit_scroll

    @staticmethod
    def _restore_changed_files_fallback(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.CHANGED_FILES
        state.file_scroll = 0

    @staticmethod
    def _restore_commit_picker_fallback(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.COMMIT_PICKER
        state.selected = 0
        state.commit_scroll = 0
