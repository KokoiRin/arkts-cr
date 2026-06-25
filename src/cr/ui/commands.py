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
    SET_SOURCE_FILTER = "set_source_filter"
    CLEAR_SOURCE_FILTER = "clear_source_filter"
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
    OPEN_HUNK = "open_hunk"
    OPEN_LINE = "open_line"
    COPY_PATH = "copy_path"
    COPY_ANCHOR = "copy_anchor"
    COPY_DIFF = "copy_diff"
    COPY_HUNK = "copy_hunk"
    COPY_LINE = "copy_line"
    COPY_CHANGE = "copy_change"
    COPY_REVIEW_NOTES = "copy_review_notes"
    COPY_PROMPT = "copy_prompt"
    COPY_FILE_PROMPT = "copy_file_prompt"
    SAVE_DIFF = "save_diff"
    SAVE_PROMPT = "save_prompt"
    SAVE_FILE_PROMPT = "save_file_prompt"
    REVEAL_FILE = "reveal_file"
    STAGE_FILE = "stage_file"
    UNSTAGE_FILE = "unstage_file"
    SHOW_FILE_ACTION_DIAGNOSTICS = "show_file_action_diagnostics"
    SET_REVIEW_NOTE = "set_review_note"
    SHOW_REVIEW_NOTES = "show_review_notes"
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
    FIND_IN_FILE = "find_in_file"
    NEXT_MATCH = "next_match"
    PREVIOUS_MATCH = "previous_match"
    NEXT_CHANGE = "next_change"
    PREVIOUS_CHANGE = "previous_change"
    NEXT_HUNK = "next_hunk"
    PREVIOUS_HUNK = "previous_hunk"
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
    if command.startswith("source "):
        source = command.removeprefix("source ").strip()
        if source in {"all", "clear"}:
            return BrowserCommand(BrowserCommandAction.CLEAR_SOURCE_FILTER)
        return BrowserCommand(BrowserCommandAction.SET_SOURCE_FILTER, source)
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
    if command == "open hunk":
        return BrowserCommand(BrowserCommandAction.OPEN_HUNK)
    if command == "open line":
        return BrowserCommand(BrowserCommandAction.OPEN_LINE)
    if command in {"copy", "copy path"}:
        return BrowserCommand(BrowserCommandAction.COPY_PATH)
    if command == "copy anchor":
        return BrowserCommand(BrowserCommandAction.COPY_ANCHOR)
    if command == "copy diff":
        return BrowserCommand(BrowserCommandAction.COPY_DIFF)
    if command == "copy hunk":
        return BrowserCommand(BrowserCommandAction.COPY_HUNK)
    if command == "copy line":
        return BrowserCommand(BrowserCommandAction.COPY_LINE)
    if command == "copy change":
        return BrowserCommand(BrowserCommandAction.COPY_CHANGE)
    if command in {"copy notes", "notes copy"}:
        return BrowserCommand(BrowserCommandAction.COPY_REVIEW_NOTES)
    if command.startswith("copy notes "):
        return BrowserCommand(
            BrowserCommandAction.COPY_REVIEW_NOTES,
            command.removeprefix("copy notes ").strip(),
        )
    if command == "copy prompt":
        return BrowserCommand(BrowserCommandAction.COPY_PROMPT)
    if command in {"copy prompt file", "copy file prompt"}:
        return BrowserCommand(BrowserCommandAction.COPY_FILE_PROMPT)
    if command == "save diff":
        return BrowserCommand(BrowserCommandAction.SAVE_DIFF)
    if command.startswith("save diff "):
        return BrowserCommand(
            BrowserCommandAction.SAVE_DIFF,
            command.removeprefix("save diff ").strip(),
        )
    if command == "save prompt":
        return BrowserCommand(BrowserCommandAction.SAVE_PROMPT)
    if command.startswith("save prompt file "):
        return BrowserCommand(
            BrowserCommandAction.SAVE_FILE_PROMPT,
            command.removeprefix("save prompt file ").strip(),
        )
    if command in {"save prompt file", "save file prompt"}:
        return BrowserCommand(BrowserCommandAction.SAVE_FILE_PROMPT)
    if command.startswith("save prompt "):
        return BrowserCommand(
            BrowserCommandAction.SAVE_PROMPT,
            command.removeprefix("save prompt ").strip(),
        )
    if command in {"reveal", "show in finder"}:
        return BrowserCommand(BrowserCommandAction.REVEAL_FILE)
    if command in {"stage", "add"}:
        return BrowserCommand(BrowserCommandAction.STAGE_FILE)
    if command in {"unstage", "reset"}:
        return BrowserCommand(BrowserCommandAction.UNSTAGE_FILE)
    if command in {"file actions", "actions", "action sources"}:
        return BrowserCommand(BrowserCommandAction.SHOW_FILE_ACTION_DIAGNOSTICS)
    if command == "note":
        return BrowserCommand(BrowserCommandAction.SET_REVIEW_NOTE)
    if command.startswith("note "):
        return BrowserCommand(
            BrowserCommandAction.SET_REVIEW_NOTE,
            command.removeprefix("note ").strip(),
        )
    if command in {"notes", "review notes"}:
        return BrowserCommand(BrowserCommandAction.SHOW_REVIEW_NOTES)
    if command.startswith("notes "):
        return BrowserCommand(
            BrowserCommandAction.SHOW_REVIEW_NOTES,
            command.removeprefix("notes ").strip(),
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
    if command == "find" or command.startswith("find "):
        return BrowserCommand(
            BrowserCommandAction.FIND_IN_FILE,
            command.removeprefix("find").strip(),
        )
    if command in {"next match", "match next"}:
        return BrowserCommand(BrowserCommandAction.NEXT_MATCH)
    if command in {"prev match", "previous match", "match prev", "match previous"}:
        return BrowserCommand(BrowserCommandAction.PREVIOUS_MATCH)
    if command in {"next change", "change next"}:
        return BrowserCommand(BrowserCommandAction.NEXT_CHANGE)
    if command in {
        "prev change",
        "previous change",
        "change prev",
        "change previous",
    }:
        return BrowserCommand(BrowserCommandAction.PREVIOUS_CHANGE)
    if command in {"next hunk", "hunk next", "]"}:
        return BrowserCommand(BrowserCommandAction.NEXT_HUNK)
    if command in {"prev hunk", "previous hunk", "hunk prev", "hunk previous", "["}:
        return BrowserCommand(BrowserCommandAction.PREVIOUS_HUNK)
    if command in {"n", "next"}:
        return BrowserCommand(BrowserCommandAction.NEXT_FILE)
    if command in {"p", "prev", "previous"}:
        return BrowserCommand(BrowserCommandAction.PREVIOUS_FILE)
    if command.isdigit():
        return BrowserCommand(BrowserCommandAction.CHOOSE_NUMBER, command)
    return BrowserCommand(BrowserCommandAction.UNKNOWN, command)
