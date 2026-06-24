"""Command language parsing for the interactive browser.

This module turns command text and key aliases into stable product actions.
It does not execute actions, read terminal input, render output, or mutate
browser state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .navigation import BrowserPage


class BrowserCommandAction:
    FILTER_PROMPT = "filter_prompt"
    COMMAND_PROMPT = "command_prompt"
    SET_FILE_FILTER = "set_file_filter"
    CLEAR_FILTER = "clear_filter"
    MARK_SEEN = "mark_seen"
    MARK_TODO = "mark_todo"
    SHOW_REMAINING = "show_remaining"
    SHOW_ALL_FILES = "show_all_files"
    QUIT = "quit"
    SHOW_COMMAND_PALETTE = "show_command_palette"
    SHOW_SCOPE_HOME = "show_scope_home"
    SHOW_COMMITS = "show_commits"
    SWITCH_WORKTREE = "switch_worktree"
    RESTORE_WORKSPACE = "restore_workspace"
    SWITCH_STAGED = "switch_staged"
    SWITCH_ALL = "switch_all"
    SWITCH_BASE = "switch_base"
    SWITCH_RANGE = "switch_range"
    HELP = "help"
    OPEN_FILE = "open_file"
    COPY_PATH = "copy_path"
    COPY_ANCHOR = "copy_anchor"
    REVEAL_FILE = "reveal_file"
    SHOW_FILE_ACTION_DIAGNOSTICS = "show_file_action_diagnostics"
    SET_REVIEW_NOTE = "set_review_note"
    SHOW_TASK_DIAGNOSTICS = "show_task_diagnostics"
    SHOW_TASK_SCHEMA_HELP = "show_task_schema_help"
    RUN_BUILD = "run_build"
    RUN_TEST = "run_test"
    RUN_LINT = "run_lint"
    STOP_TASK = "stop_task"
    RERUN_TASK = "rerun_task"
    REFRESH = "refresh"
    SHOW_CHANGED_FILES = "show_changed_files"
    BACK = "back"
    FORWARD = "forward"
    MOVE_DOWN = "move_down"
    MOVE_UP = "move_up"
    PAGE_DOWN = "page_down"
    PAGE_UP = "page_up"
    HOME = "home"
    END = "end"
    ENTER = "enter"
    LEFT = "left"
    NEXT_FILE = "next_file"
    PREVIOUS_FILE = "previous_file"
    CHOOSE_NUMBER = "choose_number"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BrowserCommand:
    action: str
    value: str = ""


def parse_browser_command(command: str, *, raw_keys: bool = False) -> BrowserCommand:
    if command == "filter_prompt":
        return BrowserCommand(BrowserCommandAction.FILTER_PROMPT)
    if command == "command_prompt":
        return BrowserCommand(BrowserCommandAction.COMMAND_PROMPT)
    if command.startswith("/") and not raw_keys:
        return BrowserCommand(BrowserCommandAction.SET_FILE_FILTER, command[1:])
    if command.startswith("filter "):
        return BrowserCommand(
            BrowserCommandAction.SET_FILE_FILTER,
            command.removeprefix("filter "),
        )
    if command in {"c", "clear"}:
        return BrowserCommand(BrowserCommandAction.CLEAR_FILTER)
    if command in {"m", "seen", "done"}:
        return BrowserCommand(BrowserCommandAction.MARK_SEEN)
    if command in {"todo", "unseen", "unmark"}:
        return BrowserCommand(BrowserCommandAction.MARK_TODO)
    if command == "remaining":
        return BrowserCommand(BrowserCommandAction.SHOW_REMAINING)
    if command in {"allfiles", "show all"}:
        return BrowserCommand(BrowserCommandAction.SHOW_ALL_FILES)
    if command in {"q", "quit", "exit"}:
        return BrowserCommand(BrowserCommandAction.QUIT)
    if command in {BrowserPage.COMMAND_PALETTE, "cmds", "help commands"}:
        return BrowserCommand(BrowserCommandAction.SHOW_COMMAND_PALETTE)
    if command in {BrowserPage.SCOPE_HOME, "scope"}:
        return BrowserCommand(BrowserCommandAction.SHOW_SCOPE_HOME)
    if command in {"g", BrowserPage.COMMIT_PICKER, "log"}:
        return BrowserCommand(BrowserCommandAction.SHOW_COMMITS)
    if command == "worktree":
        return BrowserCommand(BrowserCommandAction.SWITCH_WORKTREE)
    if command in {"w", "workspace"}:
        return BrowserCommand(BrowserCommandAction.RESTORE_WORKSPACE)
    if command in {"staged", "index"}:
        return BrowserCommand(BrowserCommandAction.SWITCH_STAGED)
    if command == "all":
        return BrowserCommand(BrowserCommandAction.SWITCH_ALL)
    if command.startswith("base "):
        return BrowserCommand(
            BrowserCommandAction.SWITCH_BASE,
            command.removeprefix("base ").strip(),
        )
    if command.startswith("range "):
        return BrowserCommand(
            BrowserCommandAction.SWITCH_RANGE,
            command.removeprefix("range ").strip(),
        )
    if command in {"h", "?", "help"}:
        return BrowserCommand(BrowserCommandAction.HELP)
    if command in {"o", "open"}:
        return BrowserCommand(BrowserCommandAction.OPEN_FILE)
    if command in {"copy", "copy path"}:
        return BrowserCommand(BrowserCommandAction.COPY_PATH)
    if command == "copy anchor":
        return BrowserCommand(BrowserCommandAction.COPY_ANCHOR)
    if command in {"reveal", "show in finder"}:
        return BrowserCommand(BrowserCommandAction.REVEAL_FILE)
    if command in {"file actions", "actions", "action sources"}:
        return BrowserCommand(BrowserCommandAction.SHOW_FILE_ACTION_DIAGNOSTICS)
    if command == "note":
        return BrowserCommand(BrowserCommandAction.SET_REVIEW_NOTE)
    if command.startswith("note "):
        return BrowserCommand(
            BrowserCommandAction.SET_REVIEW_NOTE,
            command.removeprefix("note ").strip(),
        )
    if command in {"tasks help", "task help", "tasks schema", "task schema"}:
        return BrowserCommand(BrowserCommandAction.SHOW_TASK_SCHEMA_HELP)
    if command in {"tasks", "task sources"}:
        return BrowserCommand(BrowserCommandAction.SHOW_TASK_DIAGNOSTICS)
    if command in {"build", "compile"}:
        return BrowserCommand(BrowserCommandAction.RUN_BUILD)
    if command in {"test", "tests"}:
        return BrowserCommand(BrowserCommandAction.RUN_TEST)
    if command == "lint":
        return BrowserCommand(BrowserCommandAction.RUN_LINT)
    if command in {"stop", "cancel"}:
        return BrowserCommand(BrowserCommandAction.STOP_TASK)
    if command in {"rebuild", "rerun"}:
        return BrowserCommand(BrowserCommandAction.RERUN_TASK)
    if command in {"r", "refresh"}:
        return BrowserCommand(BrowserCommandAction.REFRESH)
    if command in {"s", "summary", BrowserPage.CHANGED_FILES, "ls"}:
        return BrowserCommand(BrowserCommandAction.SHOW_CHANGED_FILES)
    if command in {"b", "back"}:
        return BrowserCommand(BrowserCommandAction.BACK)
    if command in {"forward", "fwd"}:
        return BrowserCommand(BrowserCommandAction.FORWARD)
    if command in {"down", "j"}:
        return BrowserCommand(BrowserCommandAction.MOVE_DOWN)
    if command in {"up", "k"}:
        return BrowserCommand(BrowserCommandAction.MOVE_UP)
    if command in {"pagedown", "space", "d"}:
        return BrowserCommand(BrowserCommandAction.PAGE_DOWN)
    if command in {"pageup", "u"}:
        return BrowserCommand(BrowserCommandAction.PAGE_UP)
    if command in {"home", "0"}:
        return BrowserCommand(BrowserCommandAction.HOME)
    if command in {"end", "$"}:
        return BrowserCommand(BrowserCommandAction.END)
    if command in {"enter", "right", "l"}:
        return BrowserCommand(BrowserCommandAction.ENTER)
    if command in {"left", "h"}:
        return BrowserCommand(BrowserCommandAction.LEFT)
    if command in {"n", "next"}:
        return BrowserCommand(BrowserCommandAction.NEXT_FILE)
    if command in {"p", "prev", "previous"}:
        return BrowserCommand(BrowserCommandAction.PREVIOUS_FILE)
    if command.isdigit():
        return BrowserCommand(BrowserCommandAction.CHOOSE_NUMBER, command)
    return BrowserCommand(BrowserCommandAction.UNKNOWN, command)
