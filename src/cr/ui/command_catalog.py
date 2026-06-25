"""Command catalog and command palette rendering for the browser.

This module owns the stable command surface: grouped help entries, executable
palette entries, palette filtering, and command-list row rendering. Browser
state, key input, page transitions, and action execution stay in browser.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from .navigation import BrowserPage
from .terminal import TerminalStyle


@dataclass(frozen=True)
class CommandEntry:
    command: str
    description: str
    action: str | None = None


@dataclass(frozen=True)
class CommandGroup:
    title: str
    entries: tuple[CommandEntry, ...]


@dataclass(frozen=True)
class PaletteCommand:
    group: str
    label: str
    command: str
    description: str


@dataclass(frozen=True)
class CommandPaletteScreen:
    lines: list[str]
    scroll: int


_GROUP_SEARCH_ALIASES = {
    "导航": "navigation nav",
    "审查范围": "review scope",
    "任务": "task tasks",
    "文件": "file files",
    "会话": "session",
}

_COMMAND_SEARCH_ALIASES = {
    "open": "editor",
    "open hunk": "editor",
    "open line": "editor",
}


def command_catalog() -> tuple[CommandGroup, ...]:
    return (
        CommandGroup(
            "导航",
            (
                CommandEntry("Enter / 1..N", "打开选中文件或按编号选择"),
                CommandEntry("b / back", "沿页面历史返回"),
                CommandEntry("forward", "回到刚才返回前离开的页面", "forward"),
                CommandEntry("n / p", "下一个或上一个文件"),
                CommandEntry(
                    "scopes / scope",
                    "打开审查范围首页",
                    BrowserPage.SCOPE_HOME,
                ),
                CommandEntry("g / commits", "查看最近提交", "g"),
            ),
        ),
        CommandGroup(
            "审查范围",
            (
                CommandEntry("worktree", "审查未暂存的工作区改动", "worktree"),
                CommandEntry("staged", "审查已暂存/index 改动", "staged"),
                CommandEntry("all", "审查已暂存和未暂存的本地改动", "all"),
                CommandEntry("base REF", "审查相对某个基准 ref 的改动"),
                CommandEntry("range OLD..NEW", "审查指定 ref 区间"),
            ),
        ),
        CommandGroup(
            "任务",
            (
                CommandEntry("build", "运行仓库配置的编译命令", "build"),
                CommandEntry("test / tests", "运行仓库配置的测试命令", "test"),
                CommandEntry("lint", "运行仓库配置的 lint 命令", "lint"),
                CommandEntry("tasks", "查看任务命令来源", "tasks"),
                CommandEntry("tasks help", "查看 .cr/tasks.json 格式", "tasks help"),
                CommandEntry("task output", "打开当前任务输出", "task output"),
                CommandEntry("problems", "打开当前任务问题列表", "problems"),
                CommandEntry("problems errors", "只看错误问题", "problems errors"),
                CommandEntry("problems warnings", "只看警告问题", "problems warnings"),
                CommandEntry("problems info", "只看 info 问题", "problems info"),
                CommandEntry("problems note", "只看 note 问题", "problems note"),
                CommandEntry("problems all", "查看全部任务问题", "problems all"),
                CommandEntry(
                    "problems find TEXT",
                    "按文本过滤任务问题",
                    "problems find TEXT",
                ),
                CommandEntry(
                    "problems clear find",
                    "清除任务问题文本过滤",
                    "problems clear find",
                ),
                CommandEntry(
                    "problems sort severity",
                    "按严重度排序任务问题",
                    "problems sort severity",
                ),
                CommandEntry(
                    "problems sort output",
                    "恢复任务输出中的问题顺序",
                    "problems sort output",
                ),
                CommandEntry(
                    "problems group file",
                    "按文件分组任务问题",
                    "problems group file",
                ),
                CommandEntry(
                    "problems group none",
                    "恢复平铺任务问题列表",
                    "problems group none",
                ),
                CommandEntry("view problem", "查看选中问题的源码位置", "view problem"),
                CommandEntry("copy problem", "复制选中问题", "copy problem"),
                CommandEntry("copy problems", "复制当前问题列表", "copy problems"),
                CommandEntry(
                    "copy file problems",
                    "复制当前文件的问题列表",
                    "copy file problems",
                ),
                CommandEntry(
                    "copy problem context",
                    "复制问题源码和 diff 上下文",
                    "copy problem context",
                ),
                CommandEntry(
                    "save problem context",
                    "保存问题源码和 diff 上下文",
                    "save problem context",
                ),
                CommandEntry("copy task", "复制当前任务输出", "copy task"),
                CommandEntry("save task", "保存当前任务输出", "save task"),
                CommandEntry("stop / cancel", "停止运行中的任务", "stop"),
                CommandEntry("rerun / rebuild", "重跑最近一次任务", "rerun"),
            ),
        ),
        CommandGroup(
            "文件",
            (
                CommandEntry("/QUERY / filter QUERY", "按路径过滤改动文件"),
                CommandEntry("clear", "清除当前文件过滤", "clear"),
                CommandEntry(
                    "source staged",
                    "只看当前范围里的已暂存文件",
                    "source staged",
                ),
                CommandEntry(
                    "source unstaged",
                    "只看当前范围里的未暂存文件",
                    "source unstaged",
                ),
                CommandEntry(
                    "source mixed",
                    "只看当前范围里的混合文件",
                    "source mixed",
                ),
                CommandEntry("source all", "清除当前来源过滤", "source all"),
                CommandEntry("m / seen / done", "标记选中文件已看", "m"),
                CommandEntry("done next / seen next", "标记已看并移动到下个文件", "done next"),
                CommandEntry("todo / unseen / unmark", "标记选中文件待看", "todo"),
                CommandEntry("remaining", "只看未标记已看的文件", "remaining"),
                CommandEntry("allfiles / show all", "显示全部改动文件", "allfiles"),
                CommandEntry("open", "在编辑器打开选中文件", "open"),
                CommandEntry("open hunk", "在编辑器打开当前 diff hunk", "open hunk"),
                CommandEntry("open line", "在编辑器打开当前文件详情行", "open line"),
                CommandEntry("copy path", "复制选中文件路径", "copy path"),
                CommandEntry("copy anchor", "复制选中文件路径和行号", "copy anchor"),
                CommandEntry("copy diff", "复制选中文件 diff 片段", "copy diff"),
                CommandEntry("copy hunk", "复制当前 diff hunk 片段", "copy hunk"),
                CommandEntry("copy line", "复制当前行锚点", "copy line"),
                CommandEntry("copy source", "复制当前源码上下文", "copy source"),
                CommandEntry(
                    "source context N",
                    "设置复制源码时的上下文半径",
                    "source context 3",
                ),
                CommandEntry(
                    "source select START END",
                    "选择源码行范围",
                    "source select 1 3",
                ),
                CommandEntry("source mark", "标记当前源码行", "source mark"),
                CommandEntry(
                    "source select to",
                    "选中源码标记到当前行",
                    "source select to",
                ),
                CommandEntry("source clear mark", "清除源码标记", "source clear mark"),
                CommandEntry(
                    "source clear selection",
                    "清除已选择的源码行范围",
                    "source clear selection",
                ),
                CommandEntry("copy change", "复制当前文件详情改动行", "copy change"),
                CommandEntry(
                    "find TEXT",
                    "在当前文件或任务输出页查找文本",
                    "find TEXT",
                ),
                CommandEntry(
                    "next match",
                    "跳到当前页下一个查找匹配",
                    "next match",
                ),
                CommandEntry(
                    "prev match",
                    "跳到当前页上一个查找匹配",
                    "prev match",
                ),
                CommandEntry(
                    "next change",
                    "跳到文件详情下一个改动行",
                    "next change",
                ),
                CommandEntry(
                    "prev change",
                    "跳到文件详情上一个改动行",
                    "prev change",
                ),
                CommandEntry("next hunk", "跳到下一个 diff hunk", "next hunk"),
                CommandEntry("prev hunk", "跳到上一个 diff hunk", "prev hunk"),
                CommandEntry("copy notes", "复制审查备注汇总", "copy notes"),
                CommandEntry("copy notes QUERY", "复制过滤后的审查备注汇总"),
                CommandEntry("copy prompt", "复制当前审查提示", "copy prompt"),
                CommandEntry(
                    "copy prompt file",
                    "复制选中文件的审查提示",
                    "copy prompt file",
                ),
                CommandEntry(
                    "save diff",
                    "保存选中文件 diff 片段",
                    "save diff",
                ),
                CommandEntry("save prompt", "保存当前审查提示", "save prompt"),
                CommandEntry(
                    "save prompt file",
                    "保存选中文件的审查提示",
                    "save prompt file",
                ),
                CommandEntry("reveal", "在文件管理器中显示选中文件", "reveal"),
                CommandEntry("stage", "暂存选中文件", "stage"),
                CommandEntry("unstage", "取消暂存选中文件", "unstage"),
                CommandEntry(
                    "file actions",
                    "查看 open/copy/reveal 命令来源",
                    "file actions",
                ),
                CommandEntry("note TEXT", "设置选中文件审查备注"),
                CommandEntry("note change TEXT", "给当前改动行追加备注"),
                CommandEntry("note", "清除选中文件审查备注"),
                CommandEntry("notes", "显示全部审查备注", "notes"),
                CommandEntry("notes QUERY", "按路径或备注文本过滤审查备注"),
                CommandEntry("refresh", "重新加载当前审查范围", "refresh"),
            ),
        ),
        CommandGroup(
            "会话",
            (
                CommandEntry(
                    BrowserPage.COMMAND_PALETTE,
                    "显示命令面板",
                    BrowserPage.COMMAND_PALETTE,
                ),
                CommandEntry("help", "显示当前页面帮助", "help"),
                CommandEntry("quit", "退出浏览器", "quit"),
            ),
        ),
    )


def command_palette_entries() -> list[PaletteCommand]:
    entries: list[PaletteCommand] = []
    for group in command_catalog():
        for entry in group.entries:
            if entry.action is None:
                continue
            entries.append(
                PaletteCommand(
                    group=group.title,
                    label=entry.command,
                    command=entry.action,
                    description=entry.description,
                )
            )
    return entries


def filtered_command_palette_entries(query: str) -> list[PaletteCommand]:
    normalized = query.strip().casefold()
    entries = command_palette_entries()
    if not normalized:
        return entries

    matches: list[tuple[int, int, PaletteCommand]] = []
    for index, entry in enumerate(entries):
        score = command_palette_match_score(entry, normalized)
        if score is not None:
            matches.append((score, index, entry))
    return [entry for _, _, entry in sorted(matches, key=lambda item: (item[0], item[1]))]


def command_palette_match_score(
    entry: PaletteCommand,
    query: str,
) -> int | None:
    command = entry.command.casefold()
    label = entry.label.casefold()
    group = entry.group.casefold()
    description = entry.description.casefold()
    group_aliases = _GROUP_SEARCH_ALIASES.get(entry.group, "").casefold()
    command_aliases = _COMMAND_SEARCH_ALIASES.get(entry.command, "").casefold()
    if query in {command, label}:
        return 0
    if command.startswith(query) or label.startswith(query):
        return 1
    if query in command or query in label:
        return 2
    if query in group or query in group_aliases:
        return 3
    if query in description or query in command_aliases:
        return 4
    return None


def selected_palette_command(query: str, selected: int) -> PaletteCommand | None:
    entries = filtered_command_palette_entries(query)
    if not entries:
        return None
    selected = max(0, min(selected, len(entries) - 1))
    return entries[selected]


def command_palette_screen_lines(
    query: str,
    selected: int,
    scroll: int,
    style: TerminalStyle,
    max_lines: int,
) -> CommandPaletteScreen:
    entries = filtered_command_palette_entries(query)
    total_entries = len(command_palette_entries())
    text_query = query.strip()
    lines = [
        style.bold("命令面板"),
        "/：过滤命令   c：清除过滤   Enter：执行选中命令   b/←：返回",
    ]
    if text_query:
        lines.append(
            f"过滤：{text_query} "
            f"（{len(entries)}/{total_entries} 个匹配）"
        )
    lines.append("")
    if not entries:
        message = "没有匹配命令。" if text_query else "没有可执行命令。"
        return CommandPaletteScreen([*lines, message][:max_lines], scroll)
    selected = max(0, min(selected, len(entries) - 1))
    command_width = max(len(entry.label) for entry in entries)
    row_capacity = max(1, max_lines - len(lines) - 1)
    start = ensure_window(scroll, selected, len(entries), row_capacity)
    end = min(len(entries), start + row_capacity)
    for index, entry in enumerate(entries[start:end], start):
        marker = ">" if index == selected else " "
        lines.append(
            f"{marker} {entry.group.ljust(12)} "
            f"{entry.label.ljust(command_width)}  {entry.description}"
        )
    if len(entries) > row_capacity:
        lines.append(style.dim(f"显示 {start + 1}-{end}/{len(entries)}"))
    else:
        lines.append("")
    return CommandPaletteScreen(lines[:max_lines], start)


def ensure_window(scroll: int, selected: int, total: int, capacity: int) -> int:
    if total <= capacity:
        return 0
    if selected < scroll:
        return selected
    if selected >= scroll + capacity:
        return selected - capacity + 1
    return max(0, min(scroll, total - capacity))


def command_list_lines(style: TerminalStyle, max_lines: int) -> list[str]:
    lines = _command_list_lines(style, include_group_spacing=True)
    if len(lines) > max_lines:
        lines = _command_list_lines(style, include_group_spacing=False)
    if len(lines) <= max_lines:
        return lines
    clipped = lines[: max(1, max_lines - 1)]
    clipped.append(style.dim(f"显示 1-{len(clipped)}/{len(lines)}"))
    return clipped


def _command_list_lines(
    style: TerminalStyle,
    *,
    include_group_spacing: bool,
) -> list[str]:
    lines = [
        style.bold("命令"),
        "输入 : 后键入命令。b/back 返回上一页，help 查看当前页能做什么。",
        "",
    ]
    command_width = max(
        len(entry.command)
        for group in command_catalog()
        for entry in group.entries
    )
    for group in command_catalog():
        lines.append(style.bold(group.title))
        for entry in group.entries:
            lines.append(
                f"  {entry.command.ljust(command_width)}  {entry.description}"
            )
        if include_group_spacing:
            lines.append("")
    return lines
