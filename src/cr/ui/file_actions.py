"""Platform file actions used by the interactive browser.

This module owns clipboard and file-browser subprocess details. Browser command
execution decides what selected file action to run; this module only translates
that action into a small platform command and reports launch failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import platform
import shlex
import shutil
import subprocess


@dataclass(frozen=True)
class FileActionCommandSource:
    kind: str
    source: str
    command: list[str] | None = None


def clipboard_command() -> list[str] | None:
    if platform.system() == "Darwin" and shutil.which("pbcopy"):
        return ["pbcopy"]
    if shutil.which("wl-copy"):
        return ["wl-copy"]
    if shutil.which("xclip"):
        return ["xclip", "-selection", "clipboard"]
    if shutil.which("xsel"):
        return ["xsel", "--clipboard", "--input"]
    if platform.system() == "Windows" and shutil.which("clip"):
        return ["clip"]
    return None


def copy_text(text: str, configured: str | None = None) -> str | None:
    source = copy_command_source(text, configured)
    command = source.command
    if command is None:
        return "No clipboard command found (missing)."
    try:
        subprocess.run(command, input=text, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"Copy failed ({command_source_label(source)}): {exc}"
    return None


def configured_copy_command(
    text: str,
    configured: str | None = None,
) -> list[str] | None:
    return copy_command_source(text, configured).command


def copy_command_source(
    text: str,
    configured: str | None = None,
) -> FileActionCommandSource:
    if configured:
        return FileActionCommandSource(
            "copy",
            "cli",
            _format_template(configured, {"text": text}),
        )
    env = os.environ.get("CR_COPY_CMD")
    if env:
        return FileActionCommandSource(
            "copy",
            "env",
            _format_template(env, {"text": text}),
        )
    command = clipboard_command()
    if command is None:
        return FileActionCommandSource("copy", "missing")
    return FileActionCommandSource("copy", "platform", command)


def reveal_command(path: Path) -> list[str] | None:
    if platform.system() == "Darwin" and shutil.which("open"):
        return ["open", "-R", str(path)]
    if platform.system() == "Windows" and shutil.which("explorer"):
        return ["explorer", f"/select,{path}"]
    if shutil.which("xdg-open"):
        target = path if path.is_dir() else path.parent
        return ["xdg-open", str(target)]
    return None


def reveal_path(path: Path, configured: str | None = None) -> str | None:
    source = reveal_command_source(path, configured)
    command = source.command
    if command is None:
        return "No file browser command found (missing)."
    try:
        subprocess.Popen(command)
    except OSError as exc:
        return f"Reveal failed ({command_source_label(source)}): {exc}"
    return None


def configured_reveal_command(
    path: Path,
    configured: str | None = None,
) -> list[str] | None:
    return reveal_command_source(path, configured).command


def reveal_command_source(
    path: Path,
    configured: str | None = None,
) -> FileActionCommandSource:
    replacements = {
        "file": str(path),
        "dir": str(path.parent),
    }
    if configured:
        return FileActionCommandSource(
            "reveal",
            "cli",
            _format_template(configured, replacements),
        )
    env = os.environ.get("CR_REVEAL_CMD")
    if env:
        return FileActionCommandSource(
            "reveal",
            "env",
            _format_template(env, replacements),
        )
    command = reveal_command(path)
    if command is None:
        return FileActionCommandSource("reveal", "missing")
    return FileActionCommandSource("reveal", "platform", command)


def _format_template(template: str, replacements: dict[str, str]) -> list[str]:
    return [part.format(**replacements) for part in shlex.split(template)]


def command_source_label(source: FileActionCommandSource) -> str:
    if source.command is None:
        return source.source
    return f"{source.source} {_format_command(source.command)}"


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)
