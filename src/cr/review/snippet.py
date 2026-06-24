"""Compact Markdown snippets for selected review files.

This module renders small review fragments from structured review data. It does
not choose browser selections, call Git, copy text, or write files.
"""

from __future__ import annotations


def render_file_diff_snippet(file_data: dict[str, object]) -> str:
    path = file_data["path"]
    lines = [
        f"# File Diff: {path}",
        "",
        f"- change: {file_data['summary']} ({file_data['status']})",
    ]
    anchor = file_data.get("anchor")
    if anchor:
        lines.append(f"- anchor: {anchor}")
    risks = file_data.get("risk_hints") or []
    if risks:
        lines.append(f"- risk: {', '.join(str(risk) for risk in risks)}")
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
        lines.extend(["", "```diff", *(str(line) for line in hunks), "```"])
    else:
        lines.extend(["", "- changes: omitted"])
    return "\n".join(lines)


def _focus_text(file_data: dict[str, object]) -> str:
    symbols = file_data.get("modified_symbols") or []
    return ", ".join(str(symbol) for symbol in symbols if symbol != "unknown")
