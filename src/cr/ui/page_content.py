"""Page-specific main-content rendering for the interactive browser."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
import shlex
from typing import Any

from ..review.changes import (
    change_hunk_lines as default_change_hunk_lines,
    empty_message,
    is_code_file as default_is_code_file,
    modified_names as default_modified_names,
    parse_change_symbols as default_parse_change_symbols,
)
from ..review.risk import risk_hints as default_risk_hints
from ..review.tree import (
    DEFAULT_PATH_CONTEXT_DIRS,
    format_change_summary,
    shorten_path,
    style_change_summary,
)
from ..source.purpose import describe_file as default_describe_file
from ..vcs import git
from . import commit_picker
from .navigation import BrowserPage
from . import source_file as source_file_module
from . import tasks as task_runtime
from . import task_problems as task_problems_module
from .task_problems import TaskProblem
from .terminal import TerminalStyle, file_uri, vscode_uri


@dataclass
class BrowseTreeRow:
    label: str
    change: git.FileChange | None = None
    change_index: int | None = None


@dataclass(frozen=True)
class ScopeHomeEntry:
    label: str
    description: str
    action: str | None = None


@dataclass
class _BrowseTreeNode:
    name: str
    children: dict[str, "_BrowseTreeNode"] = field(default_factory=dict)
    change: git.FileChange | None = None
    change_index: int | None = None


def browse_prompt(page: str) -> str:
    if page == BrowserPage.FILE_DETAIL:
        return "cr:file> "
    if page == BrowserPage.COMMIT_PICKER:
        return "cr:commits> "
    if page == BrowserPage.SCOPE_HOME:
        return "cr:scopes> "
    if page == BrowserPage.COMMAND_PALETTE:
        return "cr:commands> "
    if page == BrowserPage.TASK_OUTPUT:
        return "cr:task> "
    if page == BrowserPage.TASK_PROBLEMS:
        return "cr:problems> "
    if page == BrowserPage.SOURCE_FILE:
        return "cr:source> "
    if page == BrowserPage.HELP:
        return "cr:help> "
    return "cr:list> "


def browse_help_lines(style: TerminalStyle) -> list[str]:
    return [
        style.bold("交互式代码审查"),
        "  ↑/↓ 或 j/k：移动    Enter/→：打开    ←/b：返回    forward：前进",
        "  /：过滤文件          c：清除过滤       m：标记已看  remaining：待看",
        "  :：输入命令          help：当前页帮助   commands：命令面板",
        "  PgUp/PgDn 或 u/d：翻页    Home/End：跳转    ]/[：下/上一个 hunk",
        "  n/p：上/下个文件    scopes：范围首页    g：提交列表  r：刷新  q：退出",
        "",
    ]


def contextual_action_bar(
    page: str,
    style: TerminalStyle,
    fit_line: Callable[[str], str] | None = None,
) -> str:
    actions_by_page = {
        BrowserPage.CHANGED_FILES: (
            "Enter 打开",
            "/ 过滤",
            "done next 完成并下一个",
            "stage 暂存",
            "build",
            "copy task 复制任务",
            "help 帮助",
        ),
        BrowserPage.FILE_DETAIL: (
            "]/[ 跳转 hunk",
            "next change 下个改动",
            "find 查找",
            "open line 打开行",
            "copy line 复制行",
            "done next 完成并下一个",
            "b 文件列表",
            "help 帮助",
        ),
        BrowserPage.SCOPE_HOME: (
            "Enter 选择",
            "g commits 提交",
            ":base REF",
            ":range OLD..NEW",
            "b 返回",
            "commands 命令面板",
            "help 帮助",
        ),
        BrowserPage.COMMIT_PICKER: (
            "Enter 选择",
            "/ 过滤提交",
            "c 清除",
            "b 返回",
            "commands 命令面板",
            "help 帮助",
        ),
        BrowserPage.COMMAND_PALETTE: (
            "Enter 执行",
            "/ 搜索",
            "c 清除",
            "b 返回",
            "help 帮助",
        ),
        BrowserPage.HELP: (
            "b 返回",
            "commands 命令面板",
            "q 退出",
        ),
        BrowserPage.TASK_OUTPUT: (
            "↑/↓ 滚动",
            "find 查找",
            "next match 下个匹配",
            "problems 问题列表",
            "copy task tail 复制尾部",
            "copy task 复制任务",
            "save task 保存任务",
            "stop",
            "rerun",
            "b 返回",
            "help 帮助",
        ),
        BrowserPage.TASK_PROBLEMS: (
            "Enter 打开",
            "↑/↓ 选择",
            "errors 错误",
            "warnings 警告",
            "all 全部",
            "find 查找",
            "sort severity 按严重度",
            "group file 按文件分组",
            "next file 下个文件",
            "prev file 上个文件",
            "view problem 查看源码",
            "task output 任务输出",
            "copy problem 复制问题",
            "copy problems 复制列表",
            "copy file problems 当前文件",
            "copy context 复制上下文",
            "save context 保存上下文",
            "copy task 复制任务",
            "b 返回",
            "help 帮助",
        ),
        BrowserPage.SOURCE_FILE: (
            "↑/↓ 滚动",
            "find 查找",
            "next match 下个匹配",
            "open 打开",
            "copy line 复制行",
            "copy source 复制源码",
            "copy context 复制上下文",
            "save context 保存上下文",
            "source context 上下文行数",
            "select range 选择范围",
            "source mark 标记",
            "b 返回",
            "help 帮助",
        ),
    }
    actions = actions_by_page.get(page, actions_by_page[BrowserPage.CHANGED_FILES])
    line = "操作：" + "  |  ".join(actions)
    if fit_line is not None:
        line = fit_line(line).rstrip()
    return style.dim(line)


def page_help_screen_lines(
    state: Any,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    topic_page = getattr(state, "help_topic_page", "") or BrowserPage.CHANGED_FILES
    title, purpose, commands = _page_help_topic(topic_page)
    lines = [
        style.bold(f"{title} 帮助"),
        "",
        style.bold("这个页面能做什么"),
        f"  {purpose}",
        "",
        style.bold("常用操作"),
    ]
    lines.extend(f"  {command}" for command in commands)
    lines.extend(
        [
            "",
            style.dim("通用：b 返回上一页，commands 打开命令面板，q 退出。"),
        ]
    )
    return lines[:max_lines]


def _page_help_topic(page: str) -> tuple[str, str, tuple[str, ...]]:
    topics = {
        BrowserPage.CHANGED_FILES: (
            "Changed Files",
            "查看当前审查范围里的改动文件，按路径层级浏览并进入文件详情。",
            (
                "Enter / 1..N：打开选中文件或指定编号的文件",
                "/QUERY：按路径过滤文件，c 清除过滤",
                "done next：标记已看并移动到下一个文件",
                "stage / unstage：暂存或取消暂存当前文件",
                "build / test / lint：运行仓库配置的任务",
                "copy path / copy diff / copy prompt：复制路径、diff 或审查提示",
                "scopes：切换审查范围，g / commits：查看最近提交",
            ),
        ),
        BrowserPage.FILE_DETAIL: (
            "File Detail",
            "查看单个文件的改动、hunk、源码行和审查备注。",
            (
                "↑/↓ / PgUp/PgDn / Home/End：滚动文件详情",
                "]/[ 或 next hunk / prev hunk：跳转 hunk",
                "next change / prev change：跳转改动行",
                "find TEXT / next match / prev match：查找并跳转匹配",
                "open line / open hunk：在编辑器打开当前行或 hunk",
                "copy line / copy hunk / copy change：复制当前上下文",
                "底部 Changed files：查看当前文件附近的审查队列",
                "note change TEXT：给当前改动行追加备注",
            ),
        ),
        BrowserPage.SCOPE_HOME: (
            "Scope Home",
            "选择要审查的范围：工作区、暂存区、本地全部改动、基准分支或提交。",
            (
                "Enter：选择当前范围",
                "worktree / staged / all：切换常用审查范围",
                "base REF：审查相对某个基准的改动",
                "range OLD..NEW：审查两个 ref 之间的差异",
                "g / commits：进入最近提交列表",
            ),
        ),
        BrowserPage.COMMIT_PICKER: (
            "Commit Picker",
            "从最近提交中选择一个提交作为审查对象。",
            (
                "↑/↓：选择提交",
                "Enter：打开选中提交的改动",
                "/QUERY：按提交信息过滤，c 清除过滤",
                "worktree：回到工作区改动",
            ),
        ),
        BrowserPage.COMMAND_PALETTE: (
            "Command Palette",
            "搜索并执行可执行命令，适合不记得完整命令时使用。",
            (
                "↑/↓：选择命令",
                "/QUERY：过滤命令，c 清除过滤",
                "Enter：执行选中命令",
                "help：查看当前页帮助",
            ),
        ),
        BrowserPage.TASK_OUTPUT: (
            "Task Output",
            "查看 build/test/lint 等任务输出，同时可以继续回到代码页面浏览。",
            (
                "↑/↓ / PgUp/PgDn：滚动任务输出",
                "find TEXT / next match / prev match：查找输出",
                "problems：进入解析出的问题列表",
                "copy task / save task：复制或保存完整任务输出",
                "copy task tail [N] / save task tail [PATH]：复制或保存输出尾部",
                "stop：停止运行中任务，rerun：重跑最近任务",
            ),
        ),
        BrowserPage.TASK_PROBLEMS: (
            "Task Problems",
            "查看任务输出解析出来的问题，并跳到源码或复制上下文给 AI。",
            (
                "Enter / view problem：打开选中问题的源码位置",
                "problems errors / warnings / all：切换问题级别",
                "problems find TEXT / problems clear find：过滤或清除过滤",
                "problems sort severity / output：按严重度或输出顺序排序",
                "problems group file / none：按文件分组或恢复平铺列表",
                "next problem file / prev problem file：跳到下一个或上一个问题文件",
                "copy problem / copy problems：复制当前问题或当前列表",
                "copy file problems：复制当前选中文件的可见问题",
                "copy problem context / save problem context：复制或保存源码和 diff 上下文",
                "task output：回到任务输出",
            ),
        ),
        BrowserPage.SOURCE_FILE: (
            "Source File",
            "围绕任务问题查看原始源码，并复制源码、行锚点或问题上下文。",
            (
                "↑/↓ / PgUp/PgDn：滚动源码",
                "find TEXT / next match / prev match：查找源码内容",
                "open / copy line：打开或复制当前源码行",
                "copy source：复制当前源码上下文",
                "source context N：设置复制源码的上下文行数",
                "source select START END：选择源码行范围",
                "source mark：标记当前源码行",
                "source select to：选中标记行到当前行",
                "source clear mark：清除源码标记",
                "source clear selection：清除选择源码行范围",
                "copy problem context / save problem context：复制或保存问题上下文",
            ),
        ),
    }
    return topics.get(page, topics[BrowserPage.CHANGED_FILES])


def scope_home_entries() -> tuple[ScopeHomeEntry, ...]:
    return (
        ScopeHomeEntry("Worktree", "Review unstaged worktree changes", "worktree"),
        ScopeHomeEntry("Staged", "Review staged/index changes", "staged"),
        ScopeHomeEntry("All local changes", "Review staged and unstaged changes", "all"),
        ScopeHomeEntry(
            "Recent commits",
            "Choose a commit as the Review Scope",
            BrowserPage.COMMIT_PICKER,
        ),
        ScopeHomeEntry("Base ref", "Type : base REF to review changes against a base"),
        ScopeHomeEntry("Explicit range", "Type : range OLD..NEW to review two refs"),
    )


def scope_label(state: Any, args: argparse.Namespace) -> str:
    if state.page == BrowserPage.SCOPE_HOME:
        return "scope home"
    if state.page == BrowserPage.COMMIT_PICKER:
        return "recent commits"
    if state.selected_commit is not None:
        return f"commit {state.selected_commit.commit[:8]}"
    if args.ref_range:
        return f"range {args.ref_range}"
    if args.base:
        return f"base {args.base}"
    if args.staged:
        return "staged"
    if args.all_changes:
        return "all local changes"
    if _args_untracked(args):
        return "worktree + untracked"
    return "worktree"


def product_breadcrumb(state: Any, args: argparse.Namespace) -> str:
    label = scope_label(state, args)
    if state.page in {BrowserPage.SCOPE_HOME, BrowserPage.COMMIT_PICKER}:
        return label
    if state.page == BrowserPage.COMMAND_PALETTE:
        return f"{label} > Commands"
    if state.page == BrowserPage.HELP:
        return f"{label} > Help"
    if state.page == BrowserPage.TASK_OUTPUT:
        return f"{label} > Task Output"
    if state.page == BrowserPage.TASK_PROBLEMS:
        return f"{label} > Task Problems"
    if state.page == BrowserPage.SOURCE_FILE:
        path = getattr(state, "source_file_path", "")
        if path:
            return f"{label} > Source > {path}"
        return f"{label} > Source"
    if state.page == BrowserPage.FILE_DETAIL:
        visible = state.visible_changes
        if visible and 0 <= state.selected < len(visible):
            return f"{label} > Files > {visible[state.selected].path}"
    return f"{label} > Files"


def scope_context_line(
    state: Any,
    args: argparse.Namespace,
    style: TerminalStyle,
    fit_line: Callable[[str], str],
) -> str:
    line = f"Scope: {product_breadcrumb(state, args)}"
    if state.status_message:
        line = f"{line}  |  {state.status_message}"
    return style.dim(fit_line(line))


def browse_scope_home_screen_lines(
    state: Any,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    entries = scope_home_entries()
    scope_counts = getattr(state, "scope_counts", {})
    lines = [
        f"{style.bold('Review scopes')} ({len(entries)} entries)",
        "Enter: open scope   b: back to files   : base REF / : range OLD..NEW",
    ]
    if max_lines <= len(lines):
        return lines[:max_lines]
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = ensure_window(0, state.scope_selected, len(entries), row_capacity)
    end = min(len(entries), start + row_capacity)
    display_entries = [
        (entry, scope_home_entry_label(entry, scope_counts)) for entry in entries
    ]
    label_width = max(len(label) for _entry, label in display_entries)
    for index, (entry, label) in enumerate(display_entries[start:end], start):
        marker = ">" if index == state.scope_selected else " "
        command_hint = f"  [{entry.action}]" if entry.action else ""
        lines.append(
            f"{marker} {index + 1}  "
            f"{label.ljust(label_width)}  {entry.description}{command_hint}"
        )
    if len(entries) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(entries)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def scope_home_entry_label(entry: ScopeHomeEntry, counts: dict[str, int]) -> str:
    if entry.action in {"worktree", "staged", "all"}:
        count = counts.get(entry.action)
        if count is not None:
            return f"{entry.label} ({plural_count(count, 'file')})"
    if entry.action == BrowserPage.COMMIT_PICKER:
        count = counts.get("commits")
        if count is not None:
            return f"{entry.label} ({plural_count(count, 'commit')})"
    return entry.label


def plural_count(count: int, singular: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {singular}{suffix}"


def browse_list_lines(
    changes: list[git.FileChange],
    args: argparse.Namespace,
    style: TerminalStyle,
    selected: int | None = None,
    total_changes: int | None = None,
    filter_text: str = "",
    source_filter: str = "",
    scope_label_text: str = "",
    seen_paths: set[str] | None = None,
    seen_count: int | None = None,
    remaining_only: bool = False,
    review_notes: dict[str, str] | None = None,
) -> list[str]:
    seen_paths = seen_paths or set()
    review_notes = review_notes or {}
    total_changes = len(changes) if total_changes is None else total_changes
    if not changes:
        return empty_browse_lines(args, filter_text, total_changes=total_changes)
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    lines = [
        f"Scope: {scope_label_text}" if scope_label_text else "",
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})",
    ]
    lines = [line for line in lines if line]
    source_summary = change_source_summary(changes)
    if source_summary:
        lines.append(source_summary)
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(changes)}/{total_changes} matches, c to clear)"
        )
    if source_filter:
        lines.append(f"Source: {source_filter} (source all to clear)")
    if total_changes:
        if seen_count is None:
            seen_count = sum(1 for change in changes if change.path in seen_paths)
        suffix = " remaining only" if remaining_only else ""
        lines.append(f"Progress: {seen_count}/{total_changes} seen{suffix}")
    rows = browse_tree_rows(changes)
    label_width = max(len(row.label) for row in rows)
    index_width = len(str(len(changes)))
    for row in rows:
        lines.append(
            format_browse_tree_row(
                row,
                selected,
                index_width,
                label_width,
                style,
                seen_paths,
                review_notes,
            )
        )
    lines.append("")
    return lines


def browse_list_screen_lines(
    state: Any,
    args: argparse.Namespace,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    changes = state.visible_changes
    if not changes:
        return empty_browse_lines(
            args,
            state.filter_text,
            total_changes=len(state.changes),
        )[:max_lines]
    total_added = sum(change.added or 0 for change in changes)
    total_deleted = sum(change.deleted or 0 for change in changes)
    header = (
        f"{style.bold('Changed files')} "
        f"({len(changes)} files, {style.added('+' + str(total_added))} "
        f"{style.deleted('-' + str(total_deleted))})"
    )
    if state.changes:
        seen_count = sum(1 for change in state.changes if change.path in state.seen_paths)
        suffix = " remaining only" if state.remaining_only else ""
        header = f"{header}  Progress: {seen_count}/{len(state.changes)} seen{suffix}"
    lines = [header]
    source_summary = change_source_summary(changes)
    if source_summary:
        lines.append(source_summary)
    if state.filter_text:
        lines.append(
            f"Filter: {state.filter_text} "
            f"({len(changes)}/{len(state.changes)} matches, c to clear)"
        )
    if getattr(state, "source_filter", ""):
        lines.append(f"Source: {state.source_filter} (source all to clear)")
    if len(changes) > 1 and max_lines >= 4:
        lines.append("Enter: open file   PgUp/PgDn: page   Home/End: jump")
    rows = browse_tree_rows(changes)
    selected_row = selected_tree_row(rows, state.selected)
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = ensure_window(state.list_scroll, selected_row, len(rows), row_capacity)
    state.list_scroll = start
    end = min(len(rows), start + row_capacity)
    visible_rows = rows[start:end]
    index_width = len(str(len(changes)))
    label_width = max(len(row.label) for row in visible_rows)
    for row in visible_rows:
        lines.append(
            format_browse_tree_row(
                row,
                state.selected,
                index_width,
                label_width,
                style,
                state.seen_paths,
                state.review_notes,
            )
        )
    if len(rows) > row_capacity:
        lines.append(style.dim(f"showing rows {start + 1}-{end}/{len(rows)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def browse_tree_rows(changes: list[git.FileChange]) -> list[BrowseTreeRow]:
    common_dir = browser_common_changed_dir(changes)
    root = _BrowseTreeNode("")
    for index, change in enumerate(changes):
        insert_browse_tree(root, change, index, common_dir)

    root_label = browser_compact_root_label(common_dir)
    child_prefix = "   " if root_label else ""
    rows = render_browse_tree_children(root, child_prefix)
    if root_label and rows:
        return [BrowseTreeRow(f"└─ {root_label}"), *rows]
    return rows


def change_source_summary(changes: list[git.FileChange]) -> str:
    counts: dict[str, int] = {"staged": 0, "unstaged": 0, "mixed": 0}
    for change in changes:
        if change.source in counts:
            counts[change.source] += 1
    parts = [f"{source} {count}" for source, count in counts.items() if count]
    if not parts:
        return ""
    return f"Sources: {', '.join(parts)}"


def insert_browse_tree(
    root: _BrowseTreeNode,
    change: git.FileChange,
    change_index: int,
    common_dir: list[str],
) -> None:
    node = root
    parts = [part for part in change.path.split("/") if part]
    if common_dir and parts[: len(common_dir)] == common_dir:
        parts = parts[len(common_dir) :]
    for part in parts:
        node = node.children.setdefault(part, _BrowseTreeNode(part))
    node.change = change
    node.change_index = change_index


def render_browse_tree_children(
    node: _BrowseTreeNode,
    prefix: str,
) -> list[BrowseTreeRow]:
    rows: list[BrowseTreeRow] = []
    items = sorted(node.children.values(), key=lambda child: child.name)
    for index, child in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└─" if is_last else "├─"
        rows.append(
            BrowseTreeRow(
                f"{prefix}{branch} {child.name}",
                child.change,
                child.change_index,
            )
        )
        child_prefix = prefix + ("   " if is_last else "│  ")
        rows.extend(render_browse_tree_children(child, child_prefix))
    return rows


def format_browse_tree_row(
    row: BrowseTreeRow,
    selected: int | None,
    index_width: int,
    label_width: int,
    style: TerminalStyle,
    seen_paths: set[str] | None = None,
    review_notes: dict[str, str] | None = None,
) -> str:
    if row.change is None or row.change_index is None:
        return f"  {' ' * index_width}  {style_tree_directory(row.label, style)}"

    marker = ">" if selected == row.change_index else " "
    progress = "[x]" if row.change.path in (seen_paths or set()) else "[ ]"
    status = " modified" if row.change.status == "modified" else ""
    source = f" {row.change.source}" if row.change.source else ""
    note = " note" if row.change.path in (review_notes or {}) else ""
    styled_label = style_tree_file(row.label, label_width, style)
    return (
        f"{marker} {str(row.change_index + 1).rjust(index_width)} {progress} "
        f"{styled_label}  "
        f"{style_change_summary(row.change, style)}"
        f"{status}"
        f"{source}"
        f"{note}"
    )


def style_tree_directory(label: str, style: TerminalStyle) -> str:
    return style.path(label)


def style_tree_file(label: str, width: int, style: TerminalStyle) -> str:
    guide, filename = split_tree_label(label)
    padding = " " * max(0, width - len(label))
    return f"{style.path(guide)}{style.file_path(filename + padding)}"


def split_tree_label(label: str) -> tuple[str, str]:
    marker = "─ "
    if marker not in label:
        return "", label
    index = label.rfind(marker) + len(marker)
    return label[:index], label[index:]


def selected_tree_row(rows: list[BrowseTreeRow], selected: int) -> int:
    for index, row in enumerate(rows):
        if row.change_index == selected:
            return index
    return 0


def browser_common_changed_dir(changes: list[git.FileChange]) -> list[str]:
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


def browser_compact_root_label(common_dir: list[str]) -> str:
    if not common_dir:
        return ""
    prefix = ".../" if len(common_dir) > DEFAULT_PATH_CONTEXT_DIRS else ""
    return prefix + "/".join(common_dir[-DEFAULT_PATH_CONTEXT_DIRS:])


def browse_commit_lines(
    commits: list[git.CommitSummary],
    style: TerminalStyle,
    selected: int | None = None,
    scope_label_text: str = "",
    filter_text: str = "",
) -> list[str]:
    if not commits:
        return (
            [
                f"Scope: {scope_label_text}" if scope_label_text else "",
                "No recent commits.",
                "",
            ]
            if scope_label_text
            else ["No recent commits.", ""]
        )
    visible_commits = commit_picker.filter_commits_by_query(commits, filter_text)
    if not visible_commits:
        return [
            f"Scope: {scope_label_text}" if scope_label_text else "",
            f"No recent commits match filter: {filter_text} ({len(commits)} total).",
            "Press c to clear the filter.",
            "",
        ]
    lines = [
        f"Scope: {scope_label_text}" if scope_label_text else "",
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Choose a commit to review its files. Press w to return to worktree.",
    ]
    lines = [line for line in lines if line]
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(visible_commits)}/{len(commits)} matches, c to clear)"
        )
    index_width = len(str(len(visible_commits)))
    for index, commit in enumerate(visible_commits, start=1):
        marker = ">" if selected == index - 1 else " "
        short_hash = commit.commit[:8]
        summary = commit_change_summary(commit, style)
        lines.append(
            f"{marker} {str(index).rjust(index_width)}  "
            f"{style.dim(short_hash)}  {commit.authored_at}  "
            f"{summary}  {commit.subject}"
        )
    lines.append("")
    return lines


def browse_commit_screen_lines(
    state: Any,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    commits = state.commits
    visible_commits = getattr(state, "visible_commits", commits)
    filter_text = getattr(state, "commit_filter_text", "")
    if not commits:
        return ["No recent commits.", ""]
    if not visible_commits:
        return [
            f"No recent commits match filter: {filter_text} ({len(commits)} total).",
            "Press c to clear the filter.",
            "",
        ][:max_lines]
    lines = [
        f"{style.bold('Recent commits')} ({len(commits)} shown)",
        "Enter: review commit   b: back here   w: worktree   PgUp/PgDn: page",
    ]
    if filter_text:
        lines.append(
            f"Filter: {filter_text} ({len(visible_commits)}/{len(commits)} matches, c to clear)"
        )
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = ensure_window(
        state.commit_scroll,
        state.selected,
        len(visible_commits),
        row_capacity,
    )
    state.commit_scroll = start
    end = min(len(visible_commits), start + row_capacity)
    index_width = len(str(len(visible_commits)))
    for index, commit in enumerate(visible_commits[start:end], start=start + 1):
        marker = ">" if state.selected == index - 1 else " "
        short_hash = commit.commit[:8]
        summary = commit_change_summary(commit, style)
        lines.append(
            f"{marker} {str(index).rjust(index_width)}  "
            f"{style.dim(short_hash)}  {commit.authored_at}  "
            f"{summary}  {commit.subject}"
        )
    if len(visible_commits) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(visible_commits)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def commit_change_summary(commit: git.CommitSummary, style: TerminalStyle) -> str:
    file_label = "file" if commit.files == 1 else "files"
    return (
        f"{commit.files} {file_label}, "
        f"{style.added('+' + str(commit.added))} "
        f"{style.deleted('-' + str(commit.deleted))}"
    )


def task_output_screen_lines(
    state: Any,
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    task = getattr(state, "task", None)
    if task is None:
        return [
            style.bold("Task output"),
            "No current task output.",
            "Run build, test, or lint to create output.",
            "",
        ][:max_lines]

    header = [
        style.bold(f"Task output ({task_runtime.task_label(task.kind)})"),
        f"Status: {task_runtime.task_status(task)}",
        f"Command: {_format_task_command(task.command)}",
    ]
    if max_lines <= len(header):
        return header[:max_lines]

    body = list(task.lines) if task.lines else ["(no output captured)"]
    body_capacity = max(1, max_lines - len(header) - 1)
    max_scroll = max(0, len(body) - body_capacity)
    state.task_scroll = max(0, min(getattr(state, "task_scroll", 0), max_scroll))
    start = state.task_scroll
    end = min(len(body), start + body_capacity)
    lines = [*header, *body[start:end]]
    if max_scroll:
        lines.append(
            style.dim(
                f"showing {start + 1}-{end}/{len(body)}   "
                "↑/↓ scroll   PgUp/PgDn page   b back"
            )
        )
    else:
        lines.append("")
    return lines[:max_lines]


def task_problems_screen_lines(
    state: Any,
    problems: list[TaskProblem],
    style: TerminalStyle,
    max_lines: int,
) -> list[str]:
    problem_filter = getattr(state, "problem_filter", "")
    problem_query = getattr(state, "problem_query", "")
    sort_label = " (sort: severity)" if getattr(state, "problem_sort", "output") == "severity" else ""
    if not problems:
        if problem_filter:
            return [
                style.bold(
                    _task_problems_title(
                        problem_filter,
                        problem_query,
                        sort_label,
                    )
                ),
                f"No {problem_filter} task problems found.",
                "Run problems all to show all task problems.",
                "",
            ][:max_lines]
        if problem_query:
            return [
                style.bold(_task_problems_title("", problem_query, sort_label)),
                f"No task problems match {problem_query}.",
                "Run problems clear find to clear the text filter.",
                "",
            ][:max_lines]
        return [
            style.bold(_task_problems_title("", problem_query, sort_label)),
            "No task problems found.",
            "Run build, test, or lint, then open problems from task output.",
            "",
        ][:max_lines]
    title = "Task problems"
    if problem_filter:
        title = f"{title}: {problem_filter}"
    count_label = task_problems_module.problem_severity_count_label(problems)
    count_parts = [count_label] if count_label else []
    if problem_query:
        count_parts.append(f"find: {problem_query}")
    if getattr(state, "problem_sort", "output") == "severity":
        count_parts.append("sort: severity")
    problem_group = getattr(state, "problem_group", "none")
    if problem_group == "file":
        count_parts.append("group: file")
    count_suffix = f"; {'; '.join(count_parts)}" if count_parts else ""
    lines = [
        f"{style.bold(title)} ({len(problems)} found{count_suffix})",
        "Enter: open problem   task output: logs   b: back",
    ]
    row_capacity = max(1, max_lines - len(lines) - 1)
    selected = max(0, min(getattr(state, "problem_selected", 0), len(problems) - 1))
    start = ensure_window(
        getattr(state, "problem_scroll", 0),
        selected,
        len(problems),
        row_capacity,
    )
    state.problem_selected = selected
    state.problem_scroll = start
    end = min(len(problems), start + row_capacity)
    index_width = len(str(len(problems)))
    problem_counts_by_path = _problem_counts_by_path(problems)
    previous_path = ""
    for index, problem in enumerate(problems[start:end], start):
        if problem_group == "file" and problem.path != previous_path:
            lines.append(
                style.dim(
                    f"{problem.path} ({problem_counts_by_path.get(problem.path, 0)})"
                )
            )
            previous_path = problem.path
        marker = ">" if index == selected else " "
        location = task_problems_module.problem_location(problem)
        label = task_problems_module.problem_diagnostic_label(problem)
        label_text = f"  {style.dim(label)}" if label else ""
        lines.append(
            f"{marker} {str(index + 1).rjust(index_width)}  "
            f"{style.file_path(location)}{label_text}  {problem.summary}"
        )
    if len(problems) > row_capacity:
        lines.append(style.dim(f"showing {start + 1}-{end}/{len(problems)}"))
    else:
        lines.append("")
    return lines[:max_lines]


def _problem_counts_by_path(problems: list[TaskProblem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for problem in problems:
        counts[problem.path] = counts.get(problem.path, 0) + 1
    return counts


def _task_problems_title(
    problem_filter: str,
    problem_query: str,
    sort_label: str,
) -> str:
    title = "Task problems"
    if problem_filter:
        title = f"{title}: {problem_filter}"
    if problem_query:
        title = f"{title} find: {problem_query}"
    return f"{title}{sort_label}"


def source_file_screen_lines(
    view: source_file_module.SourceFileView,
    style: TerminalStyle,
    max_lines: int,
    *,
    context_lines: int = 3,
    selection_start: int = 0,
    selection_end: int = 0,
    mark_line: int = 0,
    symbol_label: str = "",
) -> list[str]:
    source_labels = [f"context: {context_lines}"]
    if selection_start > 0 and selection_end > 0:
        start, end = sorted((selection_start, selection_end))
        if view.total_lines > 0:
            start = max(1, min(start, view.total_lines))
            end = max(1, min(end, view.total_lines))
        source_labels.append(f"selection: {start}-{end}")
    if mark_line > 0:
        mark = mark_line
        if view.total_lines > 0:
            mark = max(1, min(mark, view.total_lines))
        source_labels.append(f"mark: {mark}")
    if symbol_label.strip():
        source_labels.append(f"symbol: {symbol_label.strip()}")
    lines = [
        f"{style.bold('Source')} {style.file_path(view.path)}  "
        f"{style.dim('; '.join(source_labels))}",
    ]
    if view.error:
        lines.extend([view.error, ""])
        return lines[:max_lines]
    width = len(str(max(view.total_lines, 1)))
    for row in view.rows:
        marker = ">" if row.is_target else "*" if row.is_selected else " "
        lines.append(f"{marker} {str(row.line_number).rjust(width)}  {row.text}")
    if view.total_lines > len(view.rows):
        start = view.scroll + 1
        end = view.scroll + len(view.rows)
        lines.append(style.dim(f"showing {start}-{end}/{view.total_lines}"))
    else:
        lines.append("")
    return lines[:max_lines]


def max_task_output_scroll(state: Any, max_lines: int) -> int:
    task = getattr(state, "task", None)
    if task is None:
        return 0
    header_count = 3
    body = task.lines if task.lines else ["(no output captured)"]
    body_capacity = max(1, max_lines - header_count - 1)
    return max(0, len(body) - body_capacity)


def _format_task_command(command: list[str]) -> str:
    if not command:
        return "(no command)"
    return shlex.join(command)


def empty_browse_lines(
    args: argparse.Namespace,
    filter_text: str = "",
    total_changes: int = 0,
    scope_label_text: str = "",
) -> list[str]:
    prefix = [f"Scope: {scope_label_text}"] if scope_label_text else []
    if filter_text:
        return [
            *prefix,
            f"No changes match filter: {filter_text} ({total_changes} total).",
            "Press c to clear the filter.",
            "",
        ]
    return [*prefix, empty_message(args)]


def browse_file_lines(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    style: TerminalStyle,
    scope_label_text: str = "",
    seen: bool = False,
    review_note: str = "",
    *,
    first_changed_line: Callable[..., int | None] = git.first_changed_line,
    link_target: Callable[[str, int | None, argparse.Namespace], str] | None = None,
    risk_hints: Callable[[str], list[str]] = default_risk_hints,
    is_code_file: Callable[[str], bool] = default_is_code_file,
    parse_change_symbols: Callable[..., Any] = default_parse_change_symbols,
    describe_file: Callable[[str, Any], str] = default_describe_file,
    modified_names: Callable[..., list[str]] = default_modified_names,
    change_hunk_lines: Callable[..., list[str]] = default_change_hunk_lines,
) -> list[str]:
    first_line = first_changed_line(
        change.path,
        staged=args.staged,
        all_changes=args.all_changes,
        base=args.base,
        ref_range=args.ref_range,
    )
    if link_target is None:
        link_target = default_link_target
    anchor = f":{first_line}" if first_line else ""
    lines = [
        f"Scope: {scope_label_text}" if scope_label_text else "",
        f"{style.bold(f'File {index + 1}/{total}')}  "
        f"{style.path(shorten_path(change.path), link_target(change.path, first_line, args))}"
        f"{style.dim(anchor)}  "
        f"{style.bold(format_change_summary(change))}  "
        f"{style.dim('seen' if seen else 'todo')}",
    ]
    lines = [line for line in lines if line]
    risks = risk_hints(change.path)
    if review_note:
        lines.append(f"  note: {review_note}")
    if risks:
        lines.append(f"  {style.warning('risk: ' + ', '.join(risks))}")
    if change.status != "deleted" and is_code_file(change.path):
        try:
            symbols = parse_change_symbols(change, args)
            lines.append(f"  purpose: {describe_file(change.path, symbols)}")
            names = modified_names(
                change.path,
                staged=args.staged,
                all_changes=args.all_changes,
                base=args.base,
                ref_range=args.ref_range,
            )
            lines.append(f"  modified: {', '.join(names)}")
        except FileNotFoundError:
            lines.append("  (file deleted or unavailable)")
    lines.extend(
        change_hunk_lines(
            change,
            staged=args.staged,
            all_changes=args.all_changes,
            base=args.base,
            ref_range=args.ref_range,
            context=args.context,
            style=style,
        )
    )
    lines.append("")
    return lines


def file_detail_review_queue_lines(
    changes: list[git.FileChange],
    selected: int,
    seen_paths: set[str] | None,
    review_notes: dict[str, str] | None,
    style: TerminalStyle,
    *,
    max_lines: int = 4,
    available_lines: int = 0,
) -> list[str]:
    if len(changes) <= 1 or max_lines < 2 or available_lines < 10:
        return []
    selected = max(0, min(selected, len(changes) - 1))
    seen = seen_paths or set()
    notes = review_notes or {}
    row_capacity = max(1, max_lines - 1)
    start = ensure_window(0, selected, len(changes), row_capacity)
    end = min(len(changes), start + row_capacity)
    seen_count = sum(1 for change in changes if change.path in seen)
    lines = [
        style.dim(
            f"Changed files {selected + 1}/{len(changes)}  "
            f"Progress: {seen_count}/{len(changes)} seen"
        )
    ]
    for index, change in enumerate(changes[start:end], start):
        marker = ">" if index == selected else " "
        progress = "[x]" if change.path in seen else "[ ]"
        note = " note" if change.path in notes else ""
        source = f" {change.source}" if change.source else ""
        lines.append(
            f"{marker} {index + 1} {progress} "
            f"{shorten_path(change.path)}  "
            f"{format_change_summary(change)}"
            f"{source}"
            f"{note}"
        )
    return lines[:max_lines]


def file_cache_key(
    change: git.FileChange,
    index: int,
    total: int,
    args: argparse.Namespace,
    seen: bool = False,
    scope_label_text: str = "",
    review_note: str = "",
) -> str:
    return "\x1f".join(
        [
            change.path,
            scope_label_text,
            "seen" if seen else "todo",
            review_note,
            str(index),
            str(total),
            str(args.context),
            str(args.staged),
            str(args.all_changes),
            args.base or "",
            args.ref_range or "",
        ]
    )


def ensure_window(
    current_start: int,
    selected: int,
    total: int,
    capacity: int,
) -> int:
    if total <= capacity:
        return 0
    max_start = max(0, total - capacity)
    start = max(0, min(current_start, max_start))
    if selected < start:
        return selected
    if selected >= start + capacity:
        return min(max_start, selected - capacity + 1)
    return start


def default_link_target(
    path: str,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    repo_file = git.repo_path(path)
    return link_target_for_repo_file(repo_file, line, args)


def link_target_for_repo_file(
    repo_file: Path,
    line: int | None,
    args: argparse.Namespace,
) -> str:
    if args.link_scheme == "vscode":
        return vscode_uri(repo_file, line)
    return file_uri(repo_file, line)


def _args_untracked(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "untracked", False))
