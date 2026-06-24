"""Regex-based source outlines for the first cr release.

This module intentionally provides a coarse ArkTS / ETS / TS structure view.
It does not try to be a complete parser; callers should expect readable,
best-effort symbols and graceful unknowns when the text shape is ambiguous.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from pathlib import Path


CODE_EXTENSIONS = {".ets", ".ts"}
CONTROL_WORDS = {
    "catch",
    "do",
    "else",
    "for",
    "if",
    "switch",
    "try",
    "while",
}


@dataclass
class Symbol:
    kind: str
    name: str
    line: int
    indent: int
    end_line: int
    children: list["Symbol"] = field(default_factory=list)


CONTAINER_RE = re.compile(
    r"^\s*(?:export\s+)?(?:abstract\s+)?(?P<kind>class|struct|interface)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
)
FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\("
)
METHOD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected)\s+)?(?:(?:static|async)\s+)*"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\([^)]*\)\s*(?::[^={;]+)?[;{]?\s*$"
)
ARROW_FUNCTION_RE = re.compile(
    r"^\s*(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*="
    r"\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
)


def parse_file(path: str | Path) -> list[Symbol]:
    source = Path(path).read_text(encoding="utf-8")
    return parse_outline(source)


def parse_outline(source: str) -> list[Symbol]:
    lines = source.splitlines()
    roots: list[Symbol] = []
    stack: list[Symbol] = []

    for index, line in enumerate(lines, start=1):
        symbol = _match_symbol(lines, index, line)
        if symbol is None:
            continue

        while stack and stack[-1].indent >= symbol.indent:
            stack.pop()
        if symbol.kind == "method" and (
            not stack or stack[-1].kind not in {"class", "struct", "interface"}
        ):
            continue

        if stack:
            stack[-1].children.append(symbol)
        else:
            roots.append(symbol)
        stack.append(symbol)

    return roots


def flatten_symbols(symbols: list[Symbol]) -> list[Symbol]:
    result: list[Symbol] = []

    def visit(symbol: Symbol) -> None:
        result.append(symbol)
        for child in symbol.children:
            visit(child)

    for symbol in symbols:
        visit(symbol)
    return result


def modified_symbols(symbols: list[Symbol], changed_lines: set[int]) -> list[str]:
    if not changed_lines:
        return ["unknown"]

    matched: list[Symbol] = []
    for symbol in flatten_symbols(symbols):
        if any(symbol.line <= line <= symbol.end_line for line in changed_lines):
            matched.append(symbol)

    leaves = [
        symbol
        for symbol in matched
        if symbol.kind in {"function", "method"}
        and not any(
            child in matched and child.kind in {"function", "method"}
            for child in symbol.children
        )
    ]
    selected = leaves or [symbol for symbol in matched if symbol.kind in {"function", "method"}]
    names = _unique(symbol.name for symbol in selected)
    return names or ["unknown"]


def render_outline(
    path: str | Path,
    symbols: list[Symbol],
    modified: set[str] | None = None,
) -> str:
    modified = modified or set()
    lines = [str(path)]
    if not symbols:
        lines.append("(no symbols found)")
        return "\n".join(lines)

    lines.extend(_render_symbols(symbols, "", modified))
    return "\n".join(lines)


def render_outline_body(symbols: list[Symbol], modified: set[str] | None = None) -> list[str]:
    if not symbols:
        return ["(no symbols found)"]
    return _render_symbols(symbols, "", modified or set())


def _render_symbols(symbols: list[Symbol], prefix: str, modified: set[str]) -> list[str]:
    lines: list[str] = []
    for index, symbol in enumerate(symbols):
        is_last = index == len(symbols) - 1
        branch = "└─" if is_last else "├─"
        marker = " *" if symbol.name in modified else ""
        lines.append(
            f"{prefix}{branch} {symbol.kind} {symbol.name}{marker} (line {symbol.line})"
        )
        child_prefix = prefix + ("   " if is_last else "│  ")
        lines.extend(_render_symbols(symbol.children, child_prefix, modified))
    return lines


def _match_symbol(lines: list[str], index: int, line: str) -> Symbol | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("//"):
        return None

    indent = len(line) - len(line.lstrip(" "))
    container = CONTAINER_RE.match(line)
    if container:
        return Symbol(
            kind=container.group("kind"),
            name=container.group("name"),
            line=index,
            indent=indent,
            end_line=_estimate_end_line(lines, index),
        )

    function = FUNCTION_RE.match(line)
    if function:
        return Symbol(
            kind="function",
            name=function.group("name"),
            line=index,
            indent=indent,
            end_line=_estimate_end_line(lines, index),
        )

    arrow = ARROW_FUNCTION_RE.match(line)
    if arrow:
        return Symbol(
            kind="function",
            name=arrow.group("name"),
            line=index,
            indent=indent,
            end_line=_estimate_end_line(lines, index),
        )

    method = METHOD_RE.match(line)
    if method:
        name = method.group("name")
        if name not in CONTROL_WORDS:
            return Symbol(
                kind="method",
                name=name,
                line=index,
                indent=indent,
                end_line=_estimate_end_line(lines, index),
            )
    return None


def _estimate_end_line(lines: list[str], start_line: int) -> int:
    balance = 0
    seen_open = False
    for offset, raw_line in enumerate(lines[start_line - 1 :], start=start_line):
        line = _strip_line_comment(raw_line)
        balance += line.count("{")
        if "{" in line:
            seen_open = True
        balance -= line.count("}")
        if seen_open and balance <= 0:
            return offset
    return len(lines)


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
