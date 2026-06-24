"""Best-effort file purpose hints for review output.

The goal is not semantic understanding. This module turns stable, visible
signals such as paths, extensions, and top-level symbols into one compact line
that helps a reviewer decide where to spend attention first.
"""

from __future__ import annotations

from pathlib import Path

from .outline import Symbol


def describe_file(path: str | Path, symbols: list[Symbol]) -> str:
    path = Path(path)
    language = _language_label(path)
    role = _role_label(path)

    primary = _first_container(symbols)
    if primary is not None:
        role = _role_from_symbol(primary.name, role)
        methods = _child_names(primary, {"method"})
        suffix = f" with methods {_join_names(methods)}" if methods else ""
        return f"{language} {role} {primary.name}{suffix}"

    functions = [symbol.name for symbol in symbols if symbol.kind == "function"]
    if functions:
        module_role = "utility module" if _is_utility_path(path) else "module"
        return f"{language} {module_role} with functions {_join_names(functions)}"

    return f"{language} {role} {path.name}"


def _first_container(symbols: list[Symbol]) -> Symbol | None:
    for symbol in symbols:
        if symbol.kind in {"class", "struct", "interface"}:
            return symbol
    return None


def _child_names(symbol: Symbol, kinds: set[str]) -> list[str]:
    return [child.name for child in symbol.children if child.kind in kinds]


def _join_names(names: list[str], limit: int = 4) -> str:
    if len(names) <= limit:
        return ", ".join(names)
    shown = ", ".join(names[:limit])
    return f"{shown}, ..."


def _language_label(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".ets":
        return "ArkTS"
    if suffix == ".ts":
        return "TypeScript"
    if suffix == ".md":
        return "Markdown"
    if suffix == ".json":
        return "JSON"
    return suffix.removeprefix(".").upper() if suffix else "Text"


def _role_label(path: Path) -> str:
    parts = {part.lower() for part in path.parts}
    name = path.stem.lower()
    if {"page", "pages", "view", "views"} & parts or name.endswith(("page", "view")):
        return "page/component"
    if {"component", "components", "widget", "widgets"} & parts:
        return "component"
    if _is_utility_path(path):
        return "utility module"
    if path.suffix.lower() == ".md":
        return "document"
    if path.suffix.lower() == ".json":
        return "data/config file"
    return "module"


def _role_from_symbol(name: str, current_role: str) -> str:
    lowered = name.lower()
    if current_role == "module" and lowered.endswith(("page", "view")):
        return "page/component"
    if current_role == "module" and lowered.endswith(("component", "widget")):
        return "component"
    return current_role


def _is_utility_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.stem.lower()
    return bool({"util", "utils", "helper", "helpers"} & parts) or name.endswith(
        ("util", "utils", "helper", "helpers")
    )
