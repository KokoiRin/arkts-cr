"""File Detail hunk navigation rules.

This module owns rendered File Detail hunk discovery and target-scroll
calculation. It does not render file content, parse browser commands, mutate
browser state, or read Git diff data.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")
HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class HunkJumpResult:
    scroll: int
    message: str
    changed: bool


def jump_to_hunk(
    lines: list[str],
    current_scroll: int,
    direction: str,
    *,
    max_scroll: int | None = None,
) -> HunkJumpResult:
    hunks = hunk_scroll_positions(lines)
    if not hunks:
        return HunkJumpResult(current_scroll, "No diff hunks in current file.", False)

    if direction == "previous":
        candidates = [position for position in hunks if position < current_scroll]
        if not candidates:
            return HunkJumpResult(current_scroll, "Already at first hunk.", False)
        target = candidates[-1]
    else:
        candidates = [position for position in hunks if position > current_scroll]
        if not candidates:
            return HunkJumpResult(current_scroll, "Already at last hunk.", False)
        target = candidates[0]

    target = _clamp_scroll(target, max_scroll)
    hunk_number = _hunk_number_for_target(hunks, target)
    return HunkJumpResult(target, f"Moved to hunk {hunk_number}/{len(hunks)}.", True)


def hunk_scroll_positions(lines: list[str]) -> list[int]:
    positions: list[int] = []
    body = lines[1:]
    for index, line in enumerate(body):
        if _is_hunk_header(line):
            positions.append(index)
    return positions


def active_hunk_new_line(lines: list[str], current_scroll: int) -> int | None:
    body = lines[1:]
    hunk_headers = [
        (index, _plain_text(line).lstrip())
        for index, line in enumerate(body)
        if _is_hunk_header(line)
    ]
    if not hunk_headers:
        return None
    active = hunk_headers[0]
    for hunk in hunk_headers:
        if hunk[0] <= current_scroll:
            active = hunk
        else:
            break
    match = HUNK_HEADER_RE.match(active[1])
    if not match:
        return None
    return int(match.group("new"))


def _is_hunk_header(line: str) -> bool:
    return _plain_text(line).lstrip().startswith("@@")


def _plain_text(line: str) -> str:
    return ANSI_ESCAPE_RE.sub("", line)


def _clamp_scroll(target: int, max_scroll: int | None) -> int:
    if max_scroll is None:
        return target
    return max(0, min(target, max_scroll))


def _hunk_number_for_target(hunks: list[int], target: int) -> int:
    for index, position in enumerate(hunks, 1):
        if position >= target:
            return index
    return len(hunks)
