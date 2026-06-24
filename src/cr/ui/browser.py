"""Interactive review browser for cr.

This module owns the browse session state, terminal rendering, key command
mapping, path filtering, and editor handoff. The CLI parser only delegates to
``run_browser`` so interactive behavior stays local as it grows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import termios
import tty

from ..review.hunks import render_diff_hunks
from ..review.risk import risk_hints
from ..review.tree import format_change_summary, shorten_path
from ..source.outline import CODE_EXTENSIONS, modified_symbols, parse_outline
from ..source.purpose import describe_file
from ..vcs import git
from .terminal import TerminalStyle, file_uri, make_style, vscode_uri


@dataclass
class BrowserState:
    changes: list[git.FileChange]
    selected: int = 0
    mode: str = "list"
    filter_text: str = ""

    @property
    def visible_changes(self) -> list[git.FileChange]:
        return filter_changes_by_query(self.changes, self.filter_text)

    def clamp_selection(self) -> None:
        total = len(self.visible_changes)
        if total == 0:
            self.selected = 0
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
            if state.mode == "list":
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
            state.changes = _load_browse_changes(args)
            state.mode = "list"
            state.clamp_selection()
            continue
        if command in {"s", "summary", "list", "ls", "b", "back"}:
            state.mode = "list"
            continue
        if command in {"down", "j"}:
            visible = state.visible_changes
            if visible:
                state.selected = min(state.selected + 1, len(visible) - 1)
            continue
        if command in {"up", "k"}:
            if state.visible_changes:
                state.selected = max(state.selected - 1, 0)
            continue
        if command in {"enter", "right", "l"}:
            if state.visible_changes:
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
            visible = state.visible_changes
            choice = int(command)
            if 1 <= choice <= len(visible):
                state.selected = choice - 1
                state.mode = "file"
            else:
                print(f"Choose 1-{len(visible)}.")
            continue
        if command:
            print(
                "Unknown command. Use arrows, Enter, /, c, a number, "
                "o, n, p, b, r, h, or q."
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
    return _sort_changes(_selected_changes(args), args.sort)


def _draw_browse_screen(
    state: BrowserState,
    args: argparse.Namespace,
    style: TerminalStyle,
) -> None:
    state.clamp_selection()
    visible = state.visible_changes
    if state.mode == "list":
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
    return "cr:file> " if mode == "file" else "cr:list> "


def _print_lines(lines: list[str]) -> None:
    for line in lines:
        print(line)


def _browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("Interactive review"),
        "  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list",
        "  /: filter files     c: clear filter      o: open in editor",
        "  n/p: next/previous  r: refresh           q: quit",
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
    return [_empty_message(args)]


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
    if change.status != "deleted" and _is_code_file(change.path):
        try:
            symbols = _parse_change_symbols(change, args)
            lines.append(f"  purpose: {describe_file(change.path, symbols)}")
            names = _modified_names(
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
        _change_hunk_lines(
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


def _selected_changes(args: argparse.Namespace) -> list[git.FileChange]:
    changes = git.changed_files(
        args.paths,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
        include_untracked=args.untracked,
    )
    return _filter_changes(changes, code_only=args.code)


def _filter_changes(
    changes: list[git.FileChange],
    code_only: bool = False,
) -> list[git.FileChange]:
    if code_only:
        return [change for change in changes if _is_code_file(change.path)]
    return changes


def _sort_changes(
    changes: list[git.FileChange],
    sort_mode: str,
) -> list[git.FileChange]:
    if sort_mode == "git":
        return changes
    if sort_mode == "path":
        return sorted(changes, key=lambda change: change.path)
    if sort_mode == "churn":
        return sorted(changes, key=lambda change: (-_change_churn(change), change.path))
    if sort_mode == "risk":
        return sorted(
            changes,
            key=lambda change: (
                0 if risk_hints(change.path) else 1,
                -_change_churn(change),
                change.path,
            ),
        )
    return changes


def _change_churn(change: git.FileChange) -> int:
    return (change.added or 0) + (change.deleted or 0)


def _modified_names(
    path: str,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> list[str]:
    try:
        symbols = parse_outline(git.file_text(path, _range_right_ref(ref_range)))
    except FileNotFoundError:
        return ["unknown"]
    return modified_symbols(
        symbols,
        git.changed_new_lines(
            path,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
        ),
    )


def _change_hunk_lines(
    change: git.FileChange,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    context: int = 2,
    style: TerminalStyle | None = None,
) -> list[str]:
    style = style or TerminalStyle(False)
    lines = render_diff_hunks(
        git.file_diff(
            change.path,
            context=context,
            staged=staged,
            all_changes=all_changes,
            base=base,
            ref_range=ref_range,
        ),
        style=style,
    )
    rendered = [f"  {style.bold('changes:')}"]
    if not lines:
        return [*rendered, "  (no text diff available)"]
    for line in lines:
        rendered.append(f"  {line}")
    return rendered


def _empty_message(args: argparse.Namespace) -> str:
    if args.ref_range:
        return f"No changes in {args.ref_range}."
    if args.base:
        return f"No changes from {args.base}."
    if args.all_changes:
        return "No local changes."
    if args.staged:
        return "No staged changes."
    return "No working tree changes."


def _is_code_file(path: str) -> bool:
    return Path(path).suffix in CODE_EXTENSIONS


def _parse_change_symbols(change: git.FileChange, args: argparse.Namespace):
    return parse_outline(git.file_text(change.path, _range_right_ref(args.ref_range)))


def _range_right_ref(ref_range: str | None) -> str | None:
    if ref_range is None:
        return None
    return git.range_right_ref(ref_range)


def _link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)
