"""Markdown composition for focused problem/source/diff handoff.

This module owns only text assembly for the browser's problem-context handoff.
It does not read files, inspect Git, render terminal pages, copy to clipboards,
or mutate browser state.
"""

from __future__ import annotations


def problem_context_markdown(
    *,
    anchor: str,
    source_text: str,
    problem_text: str = "",
    diff_text: str = "",
) -> str:
    lines = [f"# Problem Context: {anchor}", ""]
    clean_problem = problem_text.strip()
    if clean_problem:
        lines.extend(["## Problem", "", clean_problem, ""])
    lines.extend(["## Source", "", source_text.strip(), "", "## Diff", ""])
    clean_diff = diff_text.strip()
    if clean_diff:
        lines.append(clean_diff)
    else:
        lines.append("No diff in current review scope.")
    return "\n".join(lines)
