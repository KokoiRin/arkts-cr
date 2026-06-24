"""Compact diff hunk rendering for terminal review.

This module keeps only the parts people usually read during review: hunk
headers, surrounding context, and added/deleted lines. Git metadata headers
stay hidden unless Git itself emits a one-line non-hunk message.
"""

from __future__ import annotations

import re

from .terminal import TerminalStyle


SKIP_PREFIXES = (
    "diff --git ",
    "index ",
    "old mode ",
    "new mode ",
    "deleted file mode ",
    "new file mode ",
    "similarity index ",
    "rename from ",
    "rename to ",
)

HUNK_RE = re.compile(
    r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@"
)


def render_diff_hunks(
    diff: str,
    max_lines: int = 80,
    style: TerminalStyle | None = None,
) -> list[str]:
    style = style or TerminalStyle(False)
    lines: list[str] = []
    in_hunk = False
    old_line: int | None = None
    new_line: int | None = None

    for raw_line in diff.splitlines():
        if raw_line.startswith(SKIP_PREFIXES):
            continue
        if raw_line.startswith("--- ") or raw_line.startswith("+++ "):
            continue
        if raw_line.startswith("@@"):
            in_hunk = True
            hunk = HUNK_RE.match(raw_line)
            old_line = int(hunk.group("old")) if hunk else None
            new_line = int(hunk.group("new")) if hunk else None
            lines.append(style.hunk(raw_line))
            continue
        if in_hunk:
            rendered, old_line, new_line = _render_numbered_line(
                raw_line,
                old_line,
                new_line,
                style,
            )
            lines.append(rendered)
        elif raw_line:
            lines.append(raw_line)

    if len(lines) <= max_lines:
        return lines

    remaining = len(lines) - max_lines
    return [*lines[:max_lines], f"... {remaining} more diff lines"]


def _render_numbered_line(
    raw_line: str,
    old_line: int | None,
    new_line: int | None,
    style: TerminalStyle,
) -> tuple[str, int | None, int | None]:
    if old_line is None or new_line is None:
        return raw_line, old_line, new_line

    if raw_line.startswith("-"):
        rendered = f"{old_line:>4} {'':>4} | -{raw_line[1:]}"
        return style.deleted(rendered), old_line + 1, new_line
    if raw_line.startswith("+"):
        rendered = f"{'':>4} {new_line:>4} | +{raw_line[1:]}"
        return style.added(rendered), old_line, new_line + 1
    if raw_line.startswith(" "):
        rendered = f"{old_line:>4} {new_line:>4} | {raw_line[1:]}"
        return rendered, old_line + 1, new_line + 1
    return raw_line, old_line, new_line
