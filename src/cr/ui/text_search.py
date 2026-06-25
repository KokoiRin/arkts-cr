"""Rendered text search helpers for browser pages.

This module owns plain-text matching over already-rendered terminal lines. It
does not know BrowserState, Git diff structure, task runtime, or page-specific
scroll fields.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class TextFindResult:
    scroll: int
    message: str
    found: bool


def find_text(
    lines: list[str],
    query: str,
    *,
    skip_first_line: bool = True,
) -> TextFindResult:
    text_query = query.strip()
    if not text_query:
        return TextFindResult(0, "Enter text to find.", False)
    matches = _find_match_positions(
        lines,
        text_query,
        skip_first_line=skip_first_line,
    )
    if not matches:
        return TextFindResult(0, f'No matches for "{text_query}".', False)
    target = matches[0]
    return TextFindResult(
        target.scroll,
        f'Found "{text_query}" at line {target.display_line}.',
        True,
    )


def find_next_text(
    lines: list[str],
    query: str,
    current_scroll: int,
    direction: str,
    *,
    skip_first_line: bool = True,
) -> TextFindResult:
    text_query = query.strip()
    if not text_query:
        return TextFindResult(current_scroll, "Run find TEXT first.", False)
    matches = _find_match_positions(
        lines,
        text_query,
        skip_first_line=skip_first_line,
    )
    if not matches:
        return TextFindResult(current_scroll, f'No matches for "{text_query}".', False)
    positions = [match.scroll for match in matches]
    if direction == "previous":
        before = [position for position in positions if position < current_scroll]
        target_scroll = before[-1] if before else positions[-1]
    else:
        after = [position for position in positions if position > current_scroll]
        target_scroll = after[0] if after else positions[0]
    match = matches[positions.index(target_scroll)]
    return TextFindResult(
        match.scroll,
        f'Found "{text_query}" at line {match.display_line}.',
        True,
    )


@dataclass(frozen=True)
class _TextMatch:
    scroll: int
    display_line: int


def _find_match_positions(
    lines: list[str],
    query: str,
    *,
    skip_first_line: bool,
) -> list[_TextMatch]:
    normalized = query.casefold()
    start = 1 if skip_first_line else 0
    return [
        _TextMatch(scroll=index - start, display_line=index - start + 1)
        for index, line in enumerate(lines[start:], start=start)
        if normalized in plain_text(line).casefold()
    ]


def plain_text(line: str) -> str:
    return ANSI_ESCAPE_RE.sub("", line)
