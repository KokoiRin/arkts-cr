"""Review workspace state for the interactive browser.

This module owns active Review Scope data, changed files, review filtering,
progress markers, per-file review notes, and selected-file state. It does not
render terminal output, handle keys, manage background tasks, or open editors.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..review.changes import selected_changes, sort_changes
from ..vcs import git


@dataclass(frozen=True)
class ReviewScope:
    staged: bool
    all_changes: bool
    base: Optional[str]
    ref_range: Optional[str]
    untracked: bool


ChangedFileLoader = Callable[[argparse.Namespace], list[git.FileChange]]


def load_workspace_changes(args: argparse.Namespace) -> list[git.FileChange]:
    return sort_changes(selected_changes(args), args.sort)


def apply_scope_to_args(args: argparse.Namespace, scope: ReviewScope) -> None:
    args.staged = scope.staged
    args.all_changes = scope.all_changes
    args.base = scope.base
    args.ref_range = scope.ref_range
    args.untracked = scope.untracked


def capture_scope(args: argparse.Namespace) -> ReviewScope:
    return ReviewScope(
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
        untracked=args.untracked,
    )


@dataclass(frozen=True)
class ReviewProgressAdvance:
    marked_path: str | None
    target_path: str | None
    had_next_before: bool = False


@dataclass
class ReviewWorkspace:
    changes: list[git.FileChange]
    previous_scope: Optional[ReviewScope] = None
    selected_commit: Optional[git.CommitSummary] = None
    selected: int = 0
    list_scroll: int = 0
    filter_text: str = ""
    source_filter: str = ""
    seen_paths: set[str] = field(default_factory=set)
    remaining_only: bool = False
    review_notes: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(
        cls,
        args: argparse.Namespace,
        *,
        loader: ChangedFileLoader = load_workspace_changes,
    ) -> "ReviewWorkspace":
        return cls(changes=loader(args))

    @property
    def visible_changes(self) -> list[git.FileChange]:
        changes = filter_changes_by_query(self.changes, self.filter_text)
        changes = filter_changes_by_source(changes, self.source_filter)
        if self.remaining_only:
            return [change for change in changes if change.path not in self.seen_paths]
        return changes

    def set_filter(self, query: str) -> None:
        self.filter_text = query.strip()
        self.selected = 0
        self.list_scroll = 0
        self.clamp_selection()

    def clear_filter(self) -> None:
        self.set_filter("")

    def set_source_filter(self, source: str) -> None:
        normalized = normalize_source_filter(source)
        self.source_filter = normalized
        self.selected = 0
        self.list_scroll = 0
        self.clamp_selection()

    def clear_source_filter(self) -> None:
        self.set_source_filter("")

    def mark_selected_seen(self) -> bool:
        visible = self.visible_changes
        if not visible:
            return False
        self.clamp_selection()
        self.seen_paths.add(visible[self.selected].path)
        self.clamp_selection()
        return True

    def unmark_selected_seen(self) -> bool:
        visible = self.visible_changes
        if not visible:
            return False
        self.clamp_selection()
        self.seen_paths.discard(visible[self.selected].path)
        self.clamp_selection()
        return True

    def mark_selected_seen_and_advance(self) -> ReviewProgressAdvance:
        visible_before = self.visible_changes
        if not visible_before:
            return ReviewProgressAdvance(None, None)

        self.clamp_selection()
        current_index = self.selected
        current_path = visible_before[current_index].path
        had_next_before = current_index + 1 < len(visible_before)
        self.seen_paths.add(current_path)

        visible_after = self.visible_changes
        if not visible_after:
            self.clamp_selection()
            return ReviewProgressAdvance(
                current_path,
                None,
                had_next_before=had_next_before,
            )

        if self.remaining_only:
            self.selected = min(current_index, len(visible_after) - 1)
        elif had_next_before:
            self.selected = min(current_index + 1, len(visible_after) - 1)
        else:
            self.selected = min(current_index, len(visible_after) - 1)
        self.clamp_selection()
        return ReviewProgressAdvance(
            current_path,
            visible_after[self.selected].path,
            had_next_before=had_next_before,
        )

    def clamp_selection(self) -> None:
        total = len(self.visible_changes)
        if total == 0:
            self.selected = 0
            return
        self.selected = max(0, min(self.selected, total - 1))

    def switch_scope(
        self,
        args: argparse.Namespace,
        scope: ReviewScope,
        *,
        loader: ChangedFileLoader = load_workspace_changes,
    ) -> None:
        apply_scope_to_args(args, scope)
        self.selected_commit = None
        self.previous_scope = None
        self.filter_text = ""
        self.source_filter = ""
        self.changes = loader(args)
        self.selected = 0
        self.list_scroll = 0
        self.clamp_selection()

    def select_commit(
        self,
        args: argparse.Namespace,
        commit: git.CommitSummary,
        *,
        loader: ChangedFileLoader = load_workspace_changes,
    ) -> None:
        if self.previous_scope is None:
            self.previous_scope = capture_scope(args)
        self.selected_commit = commit
        args.ref_range = git.commit_ref_range(commit)
        args.base = None
        args.staged = False
        args.all_changes = False
        args.untracked = False
        self.filter_text = ""
        self.source_filter = ""
        self.changes = loader(args)
        self.selected = 0
        self.list_scroll = 0
        self.clamp_selection()

    def restore_previous_scope(
        self,
        args: argparse.Namespace,
        *,
        loader: ChangedFileLoader = load_workspace_changes,
    ) -> None:
        if self.previous_scope is None:
            return
        self.switch_scope(args, self.previous_scope, loader=loader)

    def reload_changes(
        self,
        args: argparse.Namespace,
        *,
        loader: ChangedFileLoader = load_workspace_changes,
        preserve_selected_path: str | None = None,
    ) -> None:
        self.changes = loader(args)
        self._restore_selection(
            {
                "selected_path": preserve_selected_path,
                "selected_index": self.selected,
            }
        )

    def state_data(self, args: argparse.Namespace, *, mode: str) -> dict[str, object]:
        visible = self.visible_changes
        selected_path = None
        if visible and 0 <= self.selected < len(visible):
            selected_path = visible[self.selected].path
        return {
            "scope": {
                "staged": bool(args.staged),
                "all_changes": bool(args.all_changes),
                "base": args.base,
                "ref_range": args.ref_range,
                "untracked": bool(args.untracked),
            },
            "filter_text": self.filter_text,
            "source_filter": self.source_filter,
            "selected_path": selected_path,
            "selected_index": self.selected,
            "mode": mode,
            "seen_paths": sorted(self.seen_paths),
            "remaining_only": self.remaining_only,
            "review_notes": clean_review_notes(self.review_notes),
        }

    def restore_state(
        self,
        args: argparse.Namespace,
        workspace_state: dict[str, object],
    ) -> object:
        restore_scope_from_state(args, workspace_state)
        filter_text = workspace_state.get("filter_text")
        self.filter_text = filter_text if isinstance(filter_text, str) else ""
        source_filter = workspace_state.get("source_filter")
        self.source_filter = normalize_source_filter(source_filter)
        self.seen_paths = string_set(workspace_state.get("seen_paths"))
        self.remaining_only = workspace_state.get("remaining_only") is True
        self.review_notes = clean_review_notes(workspace_state.get("review_notes"))
        self._restore_selection(workspace_state)
        return workspace_state.get("mode")

    def _restore_selection(self, workspace_state: dict[str, object]) -> None:
        visible = self.visible_changes
        if not visible:
            self.selected = 0
            return
        selected_path = workspace_state.get("selected_path")
        if isinstance(selected_path, str):
            for index, change in enumerate(visible):
                if change.path == selected_path:
                    self.selected = index
                    return
        selected_index = workspace_state.get("selected_index")
        if isinstance(selected_index, int):
            self.selected = max(0, min(selected_index, len(visible) - 1))
        else:
            self.selected = 0


def filter_changes_by_query(
    changes: list[git.FileChange],
    query: str,
) -> list[git.FileChange]:
    normalized = query.strip().casefold()
    if not normalized:
        return changes
    return [change for change in changes if normalized in change.path.casefold()]


def filter_changes_by_source(
    changes: list[git.FileChange],
    source: str,
) -> list[git.FileChange]:
    normalized = normalize_source_filter(source)
    if not normalized:
        return changes
    return [change for change in changes if change.source == normalized]


def normalize_source_filter(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip().casefold()
    if normalized in {"staged", "unstaged", "mixed"}:
        return normalized
    return ""


def restore_scope_from_state(
    args: argparse.Namespace,
    workspace_state: dict[str, object],
) -> None:
    scope = workspace_state.get("scope")
    if not isinstance(scope, dict):
        return
    args.staged = bool(scope.get("staged"))
    args.all_changes = bool(scope.get("all_changes"))
    args.base = optional_string(scope.get("base"))
    args.ref_range = optional_string(scope.get("ref_range"))
    args.untracked = bool(scope.get("untracked"))


def optional_string(value: object) -> Optional[str]:
    return value if isinstance(value, str) else None


def string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def clean_review_notes(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    notes: dict[str, str] = {}
    for path, note in value.items():
        if not isinstance(path, str) or not isinstance(note, str):
            continue
        text = note.strip()
        if text:
            notes[path] = text
    return notes
