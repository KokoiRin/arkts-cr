"""Interactive review browser for cr.

This module owns the browse session state, terminal rendering, key command
mapping, path filtering, and editor handoff. The CLI parser only delegates to
``run_browser`` so interactive behavior stays local as it grows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
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
from ..review.tree import format_change_summary, shorten_path
from ..source.purpose import describe_file
from ..vcs import git
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri


@dataclass
class BrowserState:
    changes: list[git.FileChange]
    commits: list[git.CommitSummary] = field(default_factory=list)
    selected: int = 0
    mode: str = "list"
    filter_text: str = ""

    @property
    def visible_changes(self) -> list[git.FileChange]:
        return filter_changes_by_query(self.changes, self.filter_text)

    def clamp_selection(self) -> None:
        total = len(self.commits) if self.mode == "commits" else len(self.visible_changes)
        if total == 0:
            self.selected = 0
            if self.mode == "file":
                self.mode = "list"
            return
        self.selected = max(0, min(self.selected, total - 1))

    def set_filter(self, query: str) -> None:
        self.filter_text = query.strip()
        self.mode = "list"
        self.selected = 0
        self.clamp_selection()

    def clear_filter(self) -> None:
        self.set_filter("")


def run_browser(args: argparse.Namespace) -> int:
    style = make_style(args.color, sys.stdout, args.links)
    state = BrowserState(changes=_load_browse_changes(args))
    _show_commits_when_empty(state, args)
    raw_keys = _use_raw_keys()

    if not raw_keys:
        _print_lines(_browse_help_lines(style))
    while True:
        state.clamp_selection()
        visible = state.visible_changes
        if raw_keys:
            _draw_browse_screen(state, args, style)
        prompt = _browse_prompt(state.mode)
        if not raw_keys:
            if state.mode == "commits":
                _print_lines(_browse_commit_lines(state.commits, style, selected=None))
            elif state.mode == "list":
                _print_lines(
                    _browse_list_lines(
                        visible,
                        args,
                        style,
                        selected=None,
                        total_changes=len(state.changes),
                        filter_text=state.filter_text,
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
                    )
                )
            else:
                _print_lines(
                    _empty_browse_lines(
                        args,
                        state.filter_text,
                        total_changes=len(state.changes),
                    )
                )
                state.mode = "list"

        command_result = _read_browse_command(prompt, raw_keys)
        if command_result == "__eof__":
            return 0
        if command_result == "__interrupt__":
            return 130
        command = command_result

        if command == "filter_prompt":
            query = _read_filter_query()
            if query != "__interrupt__":
                state.set_filter(query)
            continue
        if command.startswith("/") and not raw_keys:
            state.set_filter(command[1:])
            continue
        if command.startswith("filter "):
            state.set_filter(command.removeprefix("filter "))
            continue
        if command in {"c", "clear"}:
            state.clear_filter()
            continue
        if command in {"q", "quit", "exit"}:
            return 0
        if command in {"g", "commits", "log"}:
            state.commits = _load_recent_commits()
            state.mode = "commits"
            state.selected = 0
            state.clamp_selection()
            continue
        if command in {"h", "?", "help"}:
            if raw_keys:
                state.mode = "list"
            else:
                _print_lines(_browse_help_lines(style))
            continue
        if command in {"o", "open"}:
            visible = state.visible_changes
            if visible:
                state.clamp_selection()
                _open_change(visible[state.selected], args)
            else:
                print("No changed file to open.")
            continue
        if command in {"r", "refresh"}:
            if state.mode == "commits":
                state.commits = _load_recent_commits()
            else:
                state.changes = _load_browse_changes(args)
                state.mode = "list"
                _show_commits_when_empty(state, args)
            state.clamp_selection()
            continue
        if command in {"s", "summary", "list", "ls", "b", "back"}:
            state.mode = "list"
            continue
        if command in {"down", "j"}:
            total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
            if total:
                state.selected = min(state.selected + 1, total - 1)
            continue
        if command in {"up", "k"}:
            total = len(state.commits) if state.mode == "commits" else len(state.visible_changes)
            if total:
                state.selected = max(state.selected - 1, 0)
            continue
        if command in {"enter", "right", "l"}:
            if state.mode == "commits":
                _select_commit(state, args)
            elif state.visible_changes:
                state.mode = "file"
            continue
        if command in {"left", "h"}:
            state.mode = "list"
            continue
        if command in {"n", "next"}:
            visible = state.visible_changes
            if visible:
                state.selected = min(state.selected + 1, len(visible) - 1)
                state.mode = "file"
            continue
        if command in {"p", "prev", "previous"}:
            if state.visible_changes:
                state.selected = max(state.selected - 1, 0)
                state.mode = "file"
            continue
        if command.isdigit():
            choice = int(command)
            if state.mode == "commits":
                if 1 <= choice <= len(state.commits):
                    state.selected = choice - 1
                    _select_commit(state, args)
                else:
                    print(f"Choose 1-{len(state.commits)}.")
                continue
            visible = state.visible_changes
            if 1 <= choice <= len(visible):
                state.selected = choice - 1
                state.mode = "file"
            else:
                print(f"Choose 1-{len(visible)}.")
            continue
        if command:
            print(
                "Unknown command. Use arrows, Enter, /, c, a number, "
                "o, n, p, b, g, r, h, or q."
            )


def filter_changes_by_query(
    changes: list[git.FileChange],
    query: str,
) -> list[git.FileChange]:
    normalized = query.strip().casefold()
    if not normalized:
        return changes
    return [change for change in changes if normalized in change.path.casefold()]


def _load_browse_changes(args: argparse.Namespace) -> list[git.FileChange]:
    return sort_changes(selected_changes(args), args.sort)


def _load_recent_commits() -> list[git.CommitSummary]:
    try:
        return git.recent_commits()
    except git.GitError:
        return []


def _show_commits_when_empty(state: BrowserState, args: argparse.Namespace) -> None:
    if state.changes or args.base or args.ref_range:
        return
    state.commits = _load_recent_commits()
    if state.commits:
        state.mode = "commits"
        state.selected = 0


def _select_commit(state: BrowserState, args: argparse.Namespace) -> None:
    if not state.commits:
        print("No recent commits.")
        return
    state.clamp_selection()
    commit = state.commits[state.selected]
    args.ref_range = git.commit_ref_range(commit)
    args.base = None
    args.staged = False
    args.all_changes = False
    args.untracked = False
    state.filter_text = ""
    state.changes = _load_browse_changes(args)
    state.mode = "list"
    state.selected = 0
    state.clamp_selection()


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    state.clamp_selection()
    visible = state.visible_changes
    if state.mode == "commits":
        lines = [
            *_browse_help_lines(style),
            *_browse_commit_lines(state.commits, style, selected=state.selected),
        ]
    elif state.mode == "list":
        lines = [
            *_browse_help_lines(style),
            *_browse_list_lines(
                visible,
                args,
                style,
                selected=state.selected,
                total_changes=len(state.changes),
                filter_text=state.filter_text,
            ),
        ]
    elif visible:
        lines = _browse_file_lines(
            visible[state.selected],
            state.selected,
            len(visible),
            args,
            style,
        )
    else:
        lines = _empty_browse_lines(
            args,
            state.filter_text,
            total_changes=len(state.changes),
        )
    print("\033[2J\033[H", end="")
    _print_lines(lines)


def _browse_prompt(mode: str) -> str:
    if mode == "file":
        return "cr:file> "
    if mode == "commits":
        return "cr:commits> "
    return "cr:list> "


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("Interactive review"),
        "  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list",
        "  /: filter files     c: clear filter      o: open in editor",
        "  n/p: next/previous  g: recent commits    r: refresh    q: quit",
        "",
    ]


def _browse_list_lines(
    changes: list[git.FileChange],
    args: argparse.Namespace,
    style: TerminalStyle,
    selected: int | None = None,
    total_changes: int | None = None,
    filter_text: str = "",
) -> list[str]:
    total_changes = len(changes) if total_changes is None else total_changes
    if not changes:
        return _empty_browse_lines(args, filter_text, total_changes=total_changes)
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    lines = [
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    ]
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(changes)}/{total_changes} matches, c to clear)"
        )
    index_width = len(str(len(changes)))
    path_width = max(len(shorten_path(change.path)) for change in changes)
    for index, change in enumerate(changes, start=1):
        path = shorten_path(change.path)
        marker = ">" if selected == index - 1 else " "
        first_line = git.first_changed_line(
            change.path,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
        )
        lines.append(
            f"{marker} {str(index).rjust(index_width)}  "
            f"{style.path(path.ljust(path_width), _link_target(change.path, first_line, args))}  "
            f"{_style_counts(change, style)}  "
            f"{change.status}"
        )
    lines.append("")
    return lines


def _browse_commit_lines(
    commits: list[git.CommitSummary],
    style: TerminalStyle,
    selected: int | None = None,
) -> list[str]:
    if not commits:
        return [
            "No recent commits.",
            "",
        ]
    lines = [
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Choose a commit to review its files.",
    ]
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


def _empty_browse_lines(
    args: argparse.Namespace,
    filter_text: str = "",
    total_changes: int = 0,
) -> list[str]:
    if filter_text:
        return [
            f"No changes match filter: {filter_text} ({total_changes} total).",
            "Press c to clear the filter.",
            "",
        ]
    return [empty_message(args)]


def _browse_file_lines(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    style: TerminalStyle,
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
        f"{style.bold(f'File {index + 1}/{total}')}  "
        f"{style.path(shorten_path(change.path), _link_target(change.path, first_line, args))}"
        f"{style.dim(anchor)}  "
        f"{style.bold(format_change_summary(change))}"
    ]
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


def _style_counts(change: git.FileChange, style: TerminalStyle) -> str:
    added = "?" if change.added is None else str(change.added)
    deleted = "?" if change.deleted is None else str(change.deleted)
    return f"{style.added('+' + added)} {style.deleted('-' + deleted)}"


def _use_raw_keys() -> bool:
    return bool(
        hasattr(sys.stdin, "isatty")
        and sys.stdin.isatty()
        and hasattr(sys.stdout, "isatty")
        and sys.stdout.isatty()
    )


def _read_browse_command(prompt: str, raw_keys: bool) -> str:
    if not raw_keys:
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return "__eof__"
        except KeyboardInterrupt:
            print()
            return "__interrupt__"

    print(prompt, end="", flush=True)
    try:
        key = _read_raw_key()
    except KeyboardInterrupt:
        print()
        return "__interrupt__"
    print()
    return key


def _read_filter_query() -> str:
    try:
        return input("filter> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "__interrupt__"


def _read_raw_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x03":
            raise KeyboardInterrupt
        if char in {"\r", "\n"}:
            return "enter"
        if char == "\x1b":
            second = sys.stdin.read(1)
            if second != "[":
                return ""
            third = sys.stdin.read(1)
            return {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
            }.get(third, "")
        return {
            "j": "down",
            "k": "up",
            "l": "right",
            "h": "left",
            "/": "filter_prompt",
            "\x04": "__eof__",
        }.get(char, char)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _open_change(change: git.FileChange, args: argparse.Namespace) -> None:
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
        print(
            "No editor opener found. Set --open-cmd or CR_OPEN_CMD, "
            "for example: --open-cmd 'code -g {fileline}'"
        )
        return
    try:
        subprocess.Popen(command)
    except OSError as exc:
        print(f"Open failed: {exc}")
        return
    print(f"Opened {shorten_path(change.path)}{':' + str(line) if line else ''}")


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
