"""Prompt-ready Markdown rendering for review handoff.

This format is for copying into chat or an AI review request. It favors compact
context and stable labels over terminal tables.
"""

from __future__ import annotations


def render_prompt_handoff(data: dict[str, object]) -> str:
    summary = data["summary"]
    files = data["files"]
    other_changes = data.get("other_changes", {"staged": 0, "unstaged": 0})

    lines = [
        "# Code Review Handoff",
        "",
        "Please review these changes.",
        "",
        "## Summary",
        f"- Files: {summary['files']}",
        f"- Added: {summary['added']}",
        f"- Deleted: {summary['deleted']}",
    ]
    if other_changes.get("staged") or other_changes.get("unstaged"):
        lines.append(
            "- Other changes: "
            f"staged {other_changes.get('staged', 0)}, "
            f"unstaged {other_changes.get('unstaged', 0)}"
        )

    lines.extend(["", "## Files"])
    for index, file_data in enumerate(files, start=1):
        lines.extend(_file_summary(index, file_data))

    lines.extend(["", "## Details"])
    for file_data in files:
        lines.extend(_file_detail(file_data))

    return "\n".join(lines)


def _file_summary(index: int, file_data: dict[str, object]) -> list[str]:
    path = file_data["path"]
    lines = [
        f"{index}. `{path}` {file_data['summary']} ({file_data['status']})",
    ]
    anchor = file_data.get("anchor")
    if anchor:
        lines.append(f"   - anchor: {anchor}")
    risks = file_data.get("risk_hints") or []
    if risks:
        lines.append(f"   - risk: {', '.join(risks)}")
    if file_data.get("seen"):
        lines.append("   - state: seen")
    review_note = file_data.get("review_note")
    if review_note:
        lines.append(f"   - review note: {review_note}")
    purpose = file_data.get("purpose")
    if purpose:
        lines.append(f"   - purpose: {purpose}")
    focus = _focus_text(file_data)
    if focus:
        lines.append(f"   - focus: {focus}")
    return lines


def _file_detail(file_data: dict[str, object]) -> list[str]:
    path = file_data["path"]
    lines = [f"", f"### `{path}`"]
    risks = file_data.get("risk_hints") or []
    if risks:
        lines.append(f"- risk: {', '.join(risks)}")
    if file_data.get("seen"):
        lines.append("- state: seen")
    review_note = file_data.get("review_note")
    if review_note:
        lines.append(f"- review note: {review_note}")
    purpose = file_data.get("purpose")
    if purpose:
        lines.append(f"- purpose: {purpose}")
    focus = _focus_text(file_data)
    if focus:
        lines.append(f"- focus: {focus}")

    hunks = file_data.get("hunks") or []
    if hunks:
        lines.extend(["", "```diff", *hunks, "```"])
    else:
        lines.append("- changes: omitted")
    return lines


def _focus_text(file_data: dict[str, object]) -> str:
    symbols = file_data.get("modified_symbols") or []
    return ", ".join(symbol for symbol in symbols if symbol != "unknown")
