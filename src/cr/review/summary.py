"""Compact review summary rendering.

The summary is a scan-first view: totals plus one row per changed file. It is
kept separate from the tree/detail renderers so large reviews can start with a
stable, low-noise navigation aid.
"""

from __future__ import annotations

from .tree import format_change_summary, shorten_path, style_change_summary
from ..ui.terminal import TerminalStyle
from ..vcs.git import FileChange


def render_review_summary(
    changes: list[FileChange],
    annotations: dict[str, str] | None = None,
    anchors: dict[str, str] | None = None,
    link_targets: dict[str, str] | None = None,
    risks: dict[str, list[str]] | None = None,
    seen_paths: set[str] | None = None,
    style: TerminalStyle | None = None,
) -> list[str]:
    annotations = annotations or {}
    anchors = anchors or {}
    link_targets = link_targets or {}
    risks = risks or {}
    seen_paths = seen_paths or set()
    style = style or TerminalStyle(False)
    show_seen = bool(seen_paths)
    total_added = _sum_known(change.added for change in changes)
    total_deleted = _sum_known(change.deleted for change in changes)
    display_paths = {change.path: shorten_path(change.path) for change in changes}
    path_width = max([len("path"), *(len(path) for path in display_paths.values())])
    change_width = max(
        [len("change"), *(len(format_change_summary(change)) for change in changes)]
    )
    status_width = max([len("status"), *(len(change.status) for change in changes)])
    anchor_width = max(
        [len("anchor"), *(len(anchors.get(change.path, "-")) for change in changes)]
    )
    risk_width = max(
        [
            len("risk"),
            *(len(_risk_text(risks.get(change.path, []))) for change in changes),
        ]
    )
    index_width = max(len("idx"), len(str(len(changes))))

    lines = [
        style.bold("Summary:"),
        (
            f"  {len(changes)} files, "
            f"{style.added('+' + str(total_added))} "
            f"{style.deleted('-' + str(total_deleted))}"
        ),
        (
            f"  {'idx'.rjust(index_width)}  "
            f"{'path'.ljust(path_width)}  "
            f"{'change'.ljust(change_width)}  "
            f"{'status'.ljust(status_width)}  "
            f"{'anchor'.ljust(anchor_width)}  "
            f"{'risk'.ljust(risk_width)}  "
            f"{'seen  ' if show_seen else ''}"
            "focus"
        ),
    ]

    for index, change in enumerate(changes, start=1):
        focus = _focus_text(annotations.get(change.path, ""))
        anchor = anchors.get(change.path, "-")
        risk = _risk_text(risks.get(change.path, []))
        seen = "yes" if change.path in seen_paths else "no"
        display_path = display_paths[change.path]
        display_change = style_change_summary(change, style, change_width)
        target = link_targets.get(change.path)
        lines.append(
            f"  {str(index).rjust(index_width)}  "
            f"{style.path(display_path.ljust(path_width), target)}  "
            f"{display_change}  "
            f"{change.status.ljust(status_width)}  "
            f"{style.path(anchor.ljust(anchor_width), target)}  "
            f"{_style_risk(risk.ljust(risk_width), style)}  "
            f"{seen.ljust(4) + '  ' if show_seen else ''}"
            f"{focus}"
        )
    return lines


def _sum_known(values: object) -> int:
    return sum(value for value in values if value is not None)


def _focus_text(annotation: str) -> str:
    if annotation.startswith("modified: "):
        return annotation.removeprefix("modified: ")
    return annotation or "-"


def _risk_text(risks: list[str]) -> str:
    return ", ".join(risks) if risks else "-"


def _style_risk(risk: str, style: TerminalStyle) -> str:
    return risk if risk.strip() == "-" else style.warning(risk)
