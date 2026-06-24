"""Directory tree rendering for changed files.

The tree is a presentation helper only. It keeps no Git or parser knowledge;
callers provide changed paths plus optional leaf annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .git import FileChange
from .terminal import TerminalStyle


DEFAULT_PATH_CONTEXT_DIRS = 3


@dataclass
class _Node:
    name: str
    children: dict[str, "_Node"] = field(default_factory=dict)
    change: FileChange | None = None


def render_change_tree(
    changes: list[FileChange],
    annotations: dict[str, str] | None = None,
    style: TerminalStyle | None = None,
    link_targets: dict[str, str] | None = None,
) -> str:
    annotations = annotations or {}
    style = style or TerminalStyle(False)
    link_targets = link_targets or {}
    common_dir = _common_changed_dir(changes)
    root = _Node("")
    root_label = _compact_root_label(common_dir)
    for change in sorted(changes, key=lambda item: item.path):
        _insert(root, change, common_dir)

    lines = _render_children(root, "", annotations, style, link_targets)
    if root_label and lines:
        root_line = f"└─ {style.path(root_label)}"
        child_lines = [f"   {line}" for line in lines]
        lines = [root_line, *child_lines]
    return "\n".join(lines) if lines else "(no changed files)"


def _insert(root: _Node, change: FileChange, common_dir: list[str]) -> None:
    node = root
    parts = [part for part in change.path.split("/") if part]
    if common_dir and parts[: len(common_dir)] == common_dir:
        parts = parts[len(common_dir) :]
    for part in parts:
        node = node.children.setdefault(part, _Node(part))
    node.change = change


def _render_children(
    node: _Node,
    prefix: str,
    annotations: dict[str, str],
    style: TerminalStyle,
    link_targets: dict[str, str],
) -> list[str]:
    lines: list[str] = []
    items = sorted(node.children.values(), key=lambda child: child.name)
    for index, child in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└─" if is_last else "├─"
        lines.append(f"{prefix}{branch} {_label(child, annotations, style, link_targets)}")
        child_prefix = prefix + ("   " if is_last else "│  ")
        lines.extend(
            _render_children(child, child_prefix, annotations, style, link_targets)
        )
    return lines


def _label(
    node: _Node,
    annotations: dict[str, str],
    style: TerminalStyle,
    link_targets: dict[str, str],
) -> str:
    if node.change is None:
        return style.path(node.name)
    annotation = annotations.get(node.change.path, "")
    suffix = f" {annotation}" if annotation else ""
    return (
        f"{style.path(node.name, link_targets.get(node.change.path))} "
        f"{style_change_summary(node.change, style)}"
        f"{suffix}"
    )


def shorten_path(path: str, context_dirs: int = DEFAULT_PATH_CONTEXT_DIRS) -> str:
    parts = [part for part in path.split("/") if part]
    keep = context_dirs + 1
    if len(parts) <= keep:
        return path
    return ".../" + "/".join(parts[-keep:])


def _common_changed_dir(changes: list[FileChange]) -> list[str]:
    dirs = [[part for part in change.path.split("/") if part][:-1] for change in changes]
    if not dirs:
        return []
    common = dirs[0]
    for directory in dirs[1:]:
        index = 0
        limit = min(len(common), len(directory))
        while index < limit and common[index] == directory[index]:
            index += 1
        common = common[:index]
        if not common:
            return []
    return common


def _compact_root_label(common_dir: list[str]) -> str:
    if not common_dir:
        return ""
    prefix = ".../" if len(common_dir) > DEFAULT_PATH_CONTEXT_DIRS else ""
    return prefix + "/".join(common_dir[-DEFAULT_PATH_CONTEXT_DIRS:])


def format_change_summary(change: FileChange) -> str:
    added = "?" if change.added is None else str(change.added)
    deleted = "?" if change.deleted is None else str(change.deleted)
    summary = f"+{added} -{deleted}"
    if change.status == "deleted":
        return f"{summary} deleted"
    if change.status == "added":
        return f"{summary} added"
    if change.status == "untracked":
        return f"{summary} untracked"
    if change.status == "renamed" and change.old_path:
        return f"{summary} renamed from {change.old_path}"
    return summary


def style_change_summary(
    change: FileChange,
    style: TerminalStyle,
    width: int | None = None,
) -> str:
    summary = format_change_summary(change)
    padded = summary.ljust(width) if width is not None else summary
    if not style.enabled:
        return padded
    if change.status == "deleted":
        return style.deleted(padded)
    if change.status in {"added", "untracked"}:
        return style.added(padded)
    if change.status == "renamed":
        return style.warning(padded)
    added = "?" if change.added is None else str(change.added)
    deleted = "?" if change.deleted is None else str(change.deleted)
    if width is not None:
        return style.added(f"+{added}") + " " + style.deleted(f"-{deleted}".ljust(width - len(added) - 2))
    return f"{style.added('+' + added)} {style.deleted('-' + deleted)}"
