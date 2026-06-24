"""Review Notes summary, filtering, and copy behavior.

This module owns Review Notes display text and copy status rules. It does not
edit notes, persist workspace state, parse commands, or place browser feedback
inside the terminal frame.
"""

from __future__ import annotations

from ..review.tree import shorten_path
from ..vcs import git
from . import file_actions


def review_note_lines(
    changes: list[git.FileChange],
    review_notes: dict[str, str],
    query: str = "",
) -> list[str]:
    notes = {
        path: text.strip()
        for path, text in review_notes.items()
        if text.strip()
    }
    if not notes:
        return ["Review notes: none"]

    text_query = query.strip()
    filtered_notes = _filter_notes(notes, text_query)
    if text_query and not filtered_notes:
        return [f'Review notes matching "{text_query}": none']

    lines = [f'Review notes matching "{text_query}":' if text_query else "Review notes:"]
    seen_paths: set[str] = set()
    index = 1
    for change in changes:
        note = filtered_notes.get(change.path)
        if note is None:
            continue
        lines.append(f"{index}. {shorten_path(change.path)}: {note}")
        seen_paths.add(change.path)
        index += 1

    for path in sorted(path for path in filtered_notes if path not in seen_paths):
        lines.append(f"{index}. {shorten_path(path)}: {filtered_notes[path]}")
        index += 1
    return lines


def copy_review_notes(
    changes: list[git.FileChange],
    review_notes: dict[str, str],
    query: str = "",
    copy_cmd: str | None = None,
    *,
    copy_text=None,
) -> str:
    copy_text = file_actions.copy_text if copy_text is None else copy_text
    text_query = query.strip()
    lines = review_note_lines(changes, review_notes, text_query)
    note_count = len(lines) - 1
    if note_count == 0:
        if text_query:
            return "No matching review notes to copy."
        return "No review notes to copy."
    message = copy_text("\n".join(lines), copy_cmd)
    if message:
        return message
    if text_query:
        return f"Copied {note_count} matching review notes"
    return f"Copied {note_count} review notes"


def _filter_notes(notes: dict[str, str], query: str) -> dict[str, str]:
    normalized_query = query.casefold()
    if not normalized_query:
        return notes
    return {
        path: text
        for path, text in notes.items()
        if normalized_query in path.casefold()
        or normalized_query in text.casefold()
    }
