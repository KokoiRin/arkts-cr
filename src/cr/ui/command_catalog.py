"""Command catalog and command palette rendering for the browser.

This module owns the stable command surface: grouped help entries, executable
palette entries, palette filtering, and command-list row rendering. Browser
state, key input, page transitions, and action execution stay in browser.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from .navigation import BrowserPage
from .terminal import TerminalStyle


@dataclass(frozen=True)
class CommandEntry:
    command: str
    description: str
    action: str | None = None


@dataclass(frozen=True)
class CommandGroup:
    title: str
    entries: tuple[CommandEntry, ...]


@dataclass(frozen=True)
class PaletteCommand:
    group: str
    label: str
    command: str
    description: str


@dataclass(frozen=True)
class CommandPaletteScreen:
    lines: list[str]
    scroll: int


def command_catalog() -> tuple[CommandGroup, ...]:
    return (
        CommandGroup(
            "Navigation",
            (
                CommandEntry("Enter / 1..N", "open selected file or choose by number"),
                CommandEntry("b / back", "return through page history"),
                CommandEntry("forward", "return to the page left by back", "forward"),
                CommandEntry("n / p", "next or previous file"),
                CommandEntry(
                    "scopes / scope",
                    "show Review Scope home",
                    BrowserPage.SCOPE_HOME,
                ),
                CommandEntry("g / commits", "show recent commits", "g"),
            ),
        ),
        CommandGroup(
            "Review scope",
            (
                CommandEntry("worktree", "review unstaged worktree changes", "worktree"),
                CommandEntry("staged", "review staged/index changes", "staged"),
                CommandEntry("all", "review staged and unstaged local changes", "all"),
                CommandEntry("base REF", "review changes against a base ref"),
                CommandEntry("range OLD..NEW", "review an explicit ref range"),
            ),
        ),
        CommandGroup(
            "Tasks",
            (
                CommandEntry("build", "run configured repo build", "build"),
                CommandEntry("test / tests", "run configured repo tests", "test"),
                CommandEntry("lint", "run configured repo lint", "lint"),
                CommandEntry("tasks", "show task command sources", "tasks"),
                CommandEntry("tasks help", "show .cr/tasks.json format", "tasks help"),
                CommandEntry("stop / cancel", "stop running task", "stop"),
                CommandEntry("rerun / rebuild", "run recent task again", "rerun"),
            ),
        ),
        CommandGroup(
            "Files",
            (
                CommandEntry("/QUERY / filter QUERY", "filter changed files by path"),
                CommandEntry("clear", "clear active file filter", "clear"),
                CommandEntry(
                    "source staged",
                    "show staged files in current scope",
                    "source staged",
                ),
                CommandEntry(
                    "source unstaged",
                    "show unstaged files in current scope",
                    "source unstaged",
                ),
                CommandEntry(
                    "source mixed",
                    "show mixed files in current scope",
                    "source mixed",
                ),
                CommandEntry("source all", "clear active source filter", "source all"),
                CommandEntry("m / seen / done", "mark selected file as seen", "m"),
                CommandEntry("todo / unseen / unmark", "mark selected file as todo", "todo"),
                CommandEntry("remaining", "show files not marked seen", "remaining"),
                CommandEntry("allfiles / show all", "show all changed files", "allfiles"),
                CommandEntry("open", "open selected file in editor", "open"),
                CommandEntry("copy path", "copy selected file path", "copy path"),
                CommandEntry("copy anchor", "copy selected file path and line", "copy anchor"),
                CommandEntry("copy notes", "copy review notes summary", "copy notes"),
                CommandEntry("copy notes QUERY", "copy filtered review notes summary"),
                CommandEntry("copy prompt", "copy current review prompt", "copy prompt"),
                CommandEntry(
                    "copy prompt file",
                    "copy selected file review prompt",
                    "copy prompt file",
                ),
                CommandEntry("save prompt", "save current review prompt", "save prompt"),
                CommandEntry(
                    "save prompt file",
                    "save selected file review prompt",
                    "save prompt file",
                ),
                CommandEntry("reveal", "reveal selected file in file browser", "reveal"),
                CommandEntry("stage", "stage selected file", "stage"),
                CommandEntry("unstage", "unstage selected file", "unstage"),
                CommandEntry(
                    "file actions",
                    "show open/copy/reveal command sources",
                    "file actions",
                ),
                CommandEntry("note TEXT", "set selected file review note"),
                CommandEntry("note", "clear selected file review note"),
                CommandEntry("notes", "show all review notes", "notes"),
                CommandEntry("notes QUERY", "filter review notes by path or note text"),
                CommandEntry("refresh", "reload current review scope", "refresh"),
            ),
        ),
        CommandGroup(
            "Session",
            (
                CommandEntry(
                    BrowserPage.COMMAND_PALETTE,
                    "show this command list",
                    BrowserPage.COMMAND_PALETTE,
                ),
                CommandEntry("help", "show compact key help", "help"),
                CommandEntry("quit", "exit browser", "quit"),
            ),
        ),
    )


def command_palette_entries() -> list[PaletteCommand]:
    entries: list[PaletteCommand] = []
    for group in command_catalog():
        for entry in group.entries:
            if entry.action is None:
                continue
            entries.append(
                PaletteCommand(
                    group=group.title,
                    label=entry.command,
                    command=entry.action,
                    description=entry.description,
                )
            )
    return entries


def filtered_command_palette_entries(query: str) -> list[PaletteCommand]:
    normalized = query.strip().casefold()
    entries = command_palette_entries()
    if not normalized:
        return entries

    matches: list[tuple[int, int, PaletteCommand]] = []
    for index, entry in enumerate(entries):
        score = command_palette_match_score(entry, normalized)
        if score is not None:
            matches.append((score, index, entry))
    return [entry for _, _, entry in sorted(matches, key=lambda item: (item[0], item[1]))]


def command_palette_match_score(
    entry: PaletteCommand,
    query: str,
) -> int | None:
    command = entry.command.casefold()
    label = entry.label.casefold()
    group = entry.group.casefold()
    description = entry.description.casefold()
    if query in {command, label}:
        return 0
    if command.startswith(query) or label.startswith(query):
        return 1
    if query in command or query in label:
        return 2
    if query in group:
        return 3
    if query in description:
        return 4
    return None


def selected_palette_command(query: str, selected: int) -> PaletteCommand | None:
    entries = filtered_command_palette_entries(query)
    if not entries:
        return None
    selected = max(0, min(selected, len(entries) - 1))
    return entries[selected]


def command_palette_screen_lines(
    query: str,
    selected: int,
    scroll: int,
    style: TerminalStyle,
    max_lines: int,
) -> CommandPaletteScreen:
    entries = filtered_command_palette_entries(query)
    total_entries = len(command_palette_entries())
    text_query = query.strip()
    lines = [
        style.bold("Command palette"),
        "/: filter commands   c: clear filter   Enter: run selected command   b/←: back",
    ]
    if text_query:
        lines.append(
            f"Filter: {text_query} "
            f"({len(entries)}/{total_entries} matches)"
        )
    lines.append("")
    if not entries:
        message = "No matching commands." if text_query else "No executable commands."
        return CommandPaletteScreen([*lines, message][:max_lines], scroll)
    selected = max(0, min(selected, len(entries) - 1))
    command_width = max(len(entry.label) for entry in entries)
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = ensure_window(scroll, selected, len(entries), row_capacity)
    end = min(len(entries), start + row_capacity)
    for index, entry in enumerate(entries[start:end], start):
        marker = ">" if index == selected else " "
        lines.append(
            f"{marker} {entry.group.ljust(12)} "
            f"{entry.label.ljust(command_width)}  {entry.description}"
        )
    if len(entries) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(entries)}"))
    else:
        lines.append("")
    return CommandPaletteScreen(lines[:max_lines], start)


def ensure_window(scroll: int, selected: int, total: int, capacity: int) -> int:
    if total <= capacity:
        return 0
    if selected < scroll:
        return selected
    if selected >= scroll + capacity:
        return selected - capacity + 1
    return max(0, min(scroll, total - capacity))


def command_list_lines(style: TerminalStyle, max_lines: int) -> list[str]:
    lines = [
        style.bold("Commands"),
        "Use : then type a command. b/back returns to the file list.",
        "",
    ]
    command_width = max(
        len(entry.command)
        for group in command_catalog()
        for entry in group.entries
    )
    for group in command_catalog():
        lines.append(style.bold(group.title))
        for entry in group.entries:
            lines.append(
                f"  {entry.command.ljust(command_width)}  {entry.description}"
            )
        lines.append("")
    if len(lines) <= max_lines:
        return lines
    clipped = lines[: max(1, max_lines - 1)]
    clipped.append(style.dim(f"showing 1-{len(clipped)}/{len(lines)}"))
    return clipped
