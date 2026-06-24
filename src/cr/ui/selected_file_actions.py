"""Selected-file workflows for the interactive browser.

This module owns action workflows that depend on the current changed-file
selection: path/anchor copy, editor/reveal handoff, review notes, and prompt
handoff selection. Platform subprocess details stay in `cr.ui.file_actions`;
browser command execution decides where returned messages are displayed.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..review.data import build_review_data
from ..review.changes import other_change_counts
from ..review.prompt import render_prompt_handoff
from ..review.tree import shorten_path
from ..vcs import git
from . import file_actions
from . import handoff as handoff_module


READ_ONLY_INDEX_ACTION_MESSAGE = (
    "Index actions are only available for local worktree/index scopes."
)


@dataclass(frozen=True)
class SelectedFileActionResult:
    message: str
    changed: bool = False


def open_selected_change(
    change,
    args,
    *,
    first_changed_line=None,
    repo_path=None,
    open_path=None,
) -> str:
    first_changed_line = (
        git.first_changed_line if first_changed_line is None else first_changed_line
    )
    repo_path = git.repo_path if repo_path is None else repo_path
    open_path = file_actions.open_path if open_path is None else open_path
    line = first_changed_line(
        change.path,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    repo_file = repo_path(change.path)
    message = open_path(repo_file, line, args.open_cmd)
    if message:
        return message
    return f"Opened {shorten_path(change.path)}{':' + str(line) if line else ''}"


def copy_selected_path(
    path: str,
    copy_cmd: str | None = None,
    *,
    copy_text=None,
) -> str:
    copy_text = file_actions.copy_text if copy_text is None else copy_text
    message = copy_text(path, copy_cmd)
    if message:
        return message
    return f"Copied {shorten_path(path)}"


def copy_selected_anchor(
    path: str,
    args,
    copy_cmd: str | None = None,
    *,
    first_changed_line=None,
    copy_text=None,
) -> str:
    first_changed_line = (
        git.first_changed_line if first_changed_line is None else first_changed_line
    )
    copy_text = file_actions.copy_text if copy_text is None else copy_text
    line = first_changed_line(
        path,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    anchor = f"{path}:{line}" if line else path
    display = f"{shorten_path(path)}:{line}" if line else shorten_path(path)
    message = copy_text(anchor, copy_cmd)
    if message:
        return message
    return f"Copied {display}"


def reveal_selected_path(
    path: str,
    reveal_cmd: str | None = None,
    *,
    repo_path=None,
    reveal_path=None,
) -> str:
    repo_path = git.repo_path if repo_path is None else repo_path
    reveal_path = file_actions.reveal_path if reveal_path is None else reveal_path
    repo_file = repo_path(path)
    message = reveal_path(repo_file, reveal_cmd)
    if message:
        return message
    return f"Revealed {shorten_path(path)}"


def stage_selected_path(
    path: str,
    args,
    *,
    stage_path=None,
) -> str:
    return stage_selected_path_result(
        path,
        args,
        stage_path=stage_path,
    ).message


def stage_selected_path_result(
    path: str,
    args,
    *,
    stage_path=None,
) -> SelectedFileActionResult:
    return _run_index_action(
        path,
        args,
        operation=git.stage_path if stage_path is None else stage_path,
        success_verb="Staged",
        failure_label="Stage",
    )


def unstage_selected_path(
    path: str,
    args,
    *,
    unstage_path=None,
) -> str:
    return unstage_selected_path_result(
        path,
        args,
        unstage_path=unstage_path,
    ).message


def unstage_selected_path_result(
    path: str,
    args,
    *,
    unstage_path=None,
) -> SelectedFileActionResult:
    return _run_index_action(
        path,
        args,
        operation=git.unstage_path if unstage_path is None else unstage_path,
        success_verb="Unstaged",
        failure_label="Unstage",
    )


def _run_index_action(
    path: str,
    args,
    *,
    operation,
    success_verb: str,
    failure_label: str,
) -> SelectedFileActionResult:
    if _is_read_only_scope(args):
        return SelectedFileActionResult(READ_ONLY_INDEX_ACTION_MESSAGE)
    try:
        operation(path)
    except git.GitError as error:
        return SelectedFileActionResult(f"{failure_label} failed: {error}")
    return SelectedFileActionResult(f"{success_verb} {shorten_path(path)}", changed=True)


def _is_read_only_scope(args) -> bool:
    return bool(getattr(args, "base", None) or getattr(args, "ref_range", None))


def set_selected_review_note(state, note: str) -> str:
    visible = state.visible_changes
    if not visible:
        return "No changed file to note."
    state.clamp_selection()
    path = visible[state.selected].path
    text = note.strip()
    if text:
        state.review_notes[path] = text
        state._sync_to_workspace()
        state.file_line_cache.clear()
        return f"Noted {shorten_path(path)}"
    state.review_notes.pop(path, None)
    state._sync_to_workspace()
    state.file_line_cache.clear()
    return f"Cleared note for {shorten_path(path)}"


def prompt_handoff_text(
    state,
    args,
    *,
    selected_only: bool,
    build_data=None,
    render_prompt=None,
    other_counts=None,
) -> tuple[str, int] | None:
    build_data = build_review_data if build_data is None else build_data
    render_prompt = render_prompt_handoff if render_prompt is None else render_prompt
    other_counts = other_change_counts if other_counts is None else other_counts
    visible = state.visible_changes
    if not visible:
        return None
    state.clamp_selection()
    changes = [visible[state.selected]] if selected_only else visible
    copied_paths = {change.path for change in changes}
    review_notes = {
        path: note
        for path, note in state.review_notes.items()
        if path in copied_paths and note.strip()
    }
    text = render_prompt(
        build_data(
            changes,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
            include_hunks=True,
            other_changes=other_counts(args),
            context=args.context,
            seen_paths=state.seen_paths,
            review_notes=review_notes,
        )
    )
    return text, len(changes)


def copy_prompt_handoff(
    state,
    args,
    *,
    selected_only: bool,
    copy_text=None,
    handoff_text=None,
) -> str:
    copy_text = file_actions.copy_text if copy_text is None else copy_text
    handoff_text = prompt_handoff_text if handoff_text is None else handoff_text
    handoff = handoff_text(state, args, selected_only=selected_only)
    if handoff is None:
        if selected_only:
            return "No changed file to copy prompt."
        return "No changed files to copy prompt."
    text, file_count = handoff
    message = copy_text(text, getattr(args, "copy_cmd", None))
    if message:
        return message
    suffix = "file" if file_count == 1 else "files"
    return f"Copied prompt for {file_count} {suffix}"


def save_prompt_handoff(
    state,
    args,
    requested_path: str = "",
    *,
    selected_only: bool,
    repo_root=None,
    save_prompt_text=None,
    handoff_text=None,
) -> str:
    repo_root = git.repo_root if repo_root is None else repo_root
    save_prompt_text = (
        handoff_module.save_prompt_text if save_prompt_text is None else save_prompt_text
    )
    handoff_text = prompt_handoff_text if handoff_text is None else handoff_text
    handoff = handoff_text(state, args, selected_only=selected_only)
    if handoff is None:
        if selected_only:
            return "No changed file to save prompt."
        return "No changed files to save prompt."
    text, file_count = handoff
    result = save_prompt_text(
        text,
        repo_root(),
        requested_path,
        selected_only=selected_only,
    )
    if result.error:
        return result.error
    suffix = "file" if file_count == 1 else "files"
    return f"Saved prompt for {file_count} {suffix} to {result.display_path}"
