"""Browser navigation rules for the interactive review workbench.

This module owns page transition intent and the small state resets that must
happen with those transitions. It does not load Git data, switch review scopes,
render terminal output, or implement a real history stack.
"""

from __future__ import annotations

from typing import Optional, Protocol


class BrowserPage:
    SCOPE_HOME = "scopes"
    COMMIT_PICKER = "commits"
    CHANGED_FILES = "list"
    FILE_DETAIL = "file"
    COMMAND_PALETTE = "commands"


class _BrowserNavigationState(Protocol):
    page: str
    file_scroll: int
    scope_selected: int
    command_selected: int
    command_scroll: int
    selected_commit: Optional[object]
    selected: int
    commit_scroll: int


class BrowserNavigation:
    @staticmethod
    def show_changed_files(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.CHANGED_FILES
        state.file_scroll = 0

    @staticmethod
    def show_scope_home(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.SCOPE_HOME
        state.scope_selected = 0

    @staticmethod
    def show_command_palette(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.COMMAND_PALETTE
        state.command_selected = 0
        state.command_scroll = 0

    @staticmethod
    def show_commit_picker(
        state: _BrowserNavigationState,
        *,
        clear_selected_commit: bool = False,
    ) -> None:
        state.page = BrowserPage.COMMIT_PICKER
        if clear_selected_commit:
            state.selected_commit = None
        state.selected = 0
        state.commit_scroll = 0

    @staticmethod
    def open_file_detail(state: _BrowserNavigationState) -> None:
        state.page = BrowserPage.FILE_DETAIL
        state.file_scroll = 0

    @staticmethod
    def go_back(state: _BrowserNavigationState) -> None:
        if state.page in {
            BrowserPage.COMMAND_PALETTE,
            BrowserPage.SCOPE_HOME,
            BrowserPage.FILE_DETAIL,
        }:
            BrowserNavigation.show_changed_files(state)
            return
        if state.selected_commit is not None:
            BrowserNavigation.show_commit_picker(state)
            state.file_scroll = 0
            return
        BrowserNavigation.show_changed_files(state)
