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


@dataclass(frozen=True)
class ActiveHunk:
    new_line: int
    index: int
    total: int
    lines: list[str]


@dataclass(frozen=True)
class ChangedRow:
    kind: str
    old_line: int | None
    new_line: int | None
    text: str


@dataclass(frozen=True)
class FileFindResult:
    scroll: int
    message: str
    found: bool


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


def jump_to_changed_row(
    lines: list[str],
    current_scroll: int,
    direction: str,
) -> HunkJumpResult:
    changed_rows = changed_row_positions(lines)
    if not changed_rows:
        return HunkJumpResult(
            current_scroll,
            "No changed rows in current file.",
            False,
        )
    if direction == "previous":
        before = [position for position in changed_rows if position < current_scroll]
        target = before[-1] if before else changed_rows[-1]
    else:
        after = [position for position in changed_rows if position > current_scroll]
        target = after[0] if after else changed_rows[0]
    row_number = changed_rows.index(target) + 1
    return HunkJumpResult(
        target,
        f"Moved to change {row_number}/{len(changed_rows)}.",
        True,
    )


def find_text(lines: list[str], query: str) -> FileFindResult:
    text_query = query.strip()
    if not text_query:
        return FileFindResult(0, "Enter text to find.", False)
    normalized = text_query.casefold()
    for index, line in enumerate(lines[1:]):
        if normalized in _plain_text(line).casefold():
            return FileFindResult(
                index,
                f'Found "{text_query}" at line {index + 1}.',
                True,
            )
    return FileFindResult(0, f'No matches for "{text_query}".', False)


def find_next_text(
    lines: list[str],
    query: str,
    current_scroll: int,
    direction: str,
) -> FileFindResult:
    text_query = query.strip()
    if not text_query:
        return FileFindResult(current_scroll, "Run find TEXT first.", False)
    matches = _find_match_positions(lines, text_query)
    if not matches:
        return FileFindResult(current_scroll, f'No matches for "{text_query}".', False)
    if direction == "previous":
        before = [position for position in matches if position < current_scroll]
        target = before[-1] if before else matches[-1]
    else:
        after = [position for position in matches if position > current_scroll]
        target = after[0] if after else matches[0]
    return FileFindResult(
        target,
        f'Found "{text_query}" at line {target + 1}.',
        True,
    )


def _find_match_positions(lines: list[str], query: str) -> list[int]:
    normalized = query.casefold()
    return [
        index
        for index, line in enumerate(lines[1:])
        if normalized in _plain_text(line).casefold()
    ]


def hunk_scroll_positions(lines: list[str]) -> list[int]:
    positions: list[int] = []
    body = lines[1:]
    for index, line in enumerate(body):
        if _is_hunk_header(line):
            positions.append(index)
    return positions


def changed_row_positions(lines: list[str]) -> list[int]:
    return [
        index
        for index, line in enumerate(lines[1:])
        if _is_changed_row(line)
    ]


def active_hunk_new_line(lines: list[str], current_scroll: int) -> int | None:
    hunk = active_hunk(lines, current_scroll)
    if hunk is None:
        return None
    return hunk.new_line


def current_new_line(lines: list[str], current_scroll: int) -> int | None:
    body = lines[1:]
    if current_scroll < 0 or current_scroll >= len(body):
        return None
    line = _plain_text(body[current_scroll]).lstrip()
    hunk = HUNK_HEADER_RE.match(line)
    if hunk:
        return int(hunk.group("new"))
    return _rendered_row_new_line(line)


def current_changed_row(lines: list[str], current_scroll: int) -> ChangedRow | None:
    body = lines[1:]
    if current_scroll < 0 or current_scroll >= len(body):
        return None
    return _rendered_changed_row(body[current_scroll])


def active_hunk(lines: list[str], current_scroll: int) -> ActiveHunk | None:
    body = lines[1:]
    hunk_headers = _hunk_headers(body)
    if not hunk_headers:
        return None
    active_position = 0
    for position, hunk in enumerate(hunk_headers):
        if hunk[0] <= current_scroll:
            active_position = position
        else:
            break
    active = hunk_headers[active_position]
    match = HUNK_HEADER_RE.match(active[1])
    if not match:
        return None
    next_start = (
        hunk_headers[active_position + 1][0]
        if active_position + 1 < len(hunk_headers)
        else len(body)
    )
    return ActiveHunk(
        new_line=int(match.group("new")),
        index=active_position + 1,
        total=len(hunk_headers),
        lines=[_clean_hunk_line(line) for line in body[active[0] : next_start]],
    )


def _hunk_headers(body: list[str]) -> list[tuple[int, str]]:
    return [
        (index, _plain_text(line).lstrip())
        for index, line in enumerate(body)
        if _is_hunk_header(line)
    ]


def _is_hunk_header(line: str) -> bool:
    return _plain_text(line).lstrip().startswith("@@")


def _is_changed_row(line: str) -> bool:
    text = _plain_text(line)
    if "|" not in text:
        return False
    _, content = text.split("|", 1)
    marker = content.lstrip()[:1]
    return marker in {"+", "-"}


def _rendered_row_new_line(line: str) -> int | None:
    if "|" not in line:
        return None
    prefix, text = line.split("|", 1)
    columns = prefix.split()
    if len(columns) >= 2 and columns[-1].isdigit():
        return int(columns[-1])
    if len(columns) == 1 and columns[0].isdigit():
        marker = text.lstrip()[:1]
        if marker == "+":
            return int(columns[0])
    return None


def _rendered_changed_row(line: str) -> ChangedRow | None:
    text = _plain_text(line)
    if "|" not in text:
        return None
    prefix, content = text.split("|", 1)
    marker = content.lstrip()[:1]
    columns = prefix.split()
    if marker == "+":
        new_line = _last_digit(columns)
        if new_line is None:
            return None
        return ChangedRow("added", None, new_line, _clean_hunk_line(line))
    if marker == "-":
        old_line = _first_digit(columns)
        if old_line is None:
            return None
        return ChangedRow("deleted", old_line, None, _clean_hunk_line(line))
    return None


def _first_digit(columns: list[str]) -> int | None:
    for column in columns:
        if column.isdigit():
            return int(column)
    return None


def _last_digit(columns: list[str]) -> int | None:
    for column in reversed(columns):
        if column.isdigit():
            return int(column)
    return None


def _clean_hunk_line(line: str) -> str:
    text = _plain_text(line)
    if text.startswith("  "):
        return text[2:]
    return text.lstrip()


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
