"""Terminal presentation helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TextIO
from urllib.parse import quote


class TerminalStyle:
    def __init__(self, enabled: bool = False, links_enabled: bool = False):
        self.enabled = enabled
        self.links_enabled = links_enabled

    def wrap(self, text: str, code: str) -> str:
        if not self.enabled or not text:
            return text
        return f"\033[{code}m{text}\033[0m"

    def link(self, text: str, target: str | None) -> str:
        if not self.links_enabled or not text or not target:
            return text
        return f"\033]8;;{target}\033\\{text}\033]8;;\033\\"

    def bold(self, text: str) -> str:
        return self.wrap(text, "1")

    def dim(self, text: str) -> str:
        return self.wrap(text, "2")

    def path(self, text: str, target: str | None = None) -> str:
        return self.link(self.wrap(text, "36"), target)

    def file_path(self, text: str, target: str | None = None) -> str:
        return self.link(self.wrap(text, "37"), target)

    def hunk(self, text: str) -> str:
        return self.wrap(text, "36;1")

    def added(self, text: str) -> str:
        return self.wrap(text, "32")

    def deleted(self, text: str) -> str:
        return self.wrap(text, "31")

    def warning(self, text: str) -> str:
        return self.wrap(text, "33")


def file_uri(path: Path, line: int | None = None) -> str:
    uri = path.resolve().as_uri()
    if line is None:
        return uri
    return f"{uri}#L{line}"


def vscode_uri(path: Path, line: int | None = None) -> str:
    resolved = str(path.resolve())
    suffix = f":{line}" if line is not None else ""
    return f"vscode://file/{quote(resolved)}{suffix}"


def make_style(
    mode: str,
    stream: TextIO,
    links_mode: str = "auto",
    link_scheme: str = "file",
) -> TerminalStyle:
    del link_scheme
    color_enabled = _enabled_by_mode(mode, stream, respect_no_color=True)
    links_enabled = _enabled_by_mode(links_mode, stream, respect_no_color=False)
    return TerminalStyle(color_enabled, links_enabled)


def _enabled_by_mode(
    mode: str,
    stream: TextIO,
    respect_no_color: bool,
) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    if respect_no_color and os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(stream, "isatty") and stream.isatty()
