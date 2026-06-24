"""Platform file actions used by the interactive browser.

This module owns clipboard and file-browser subprocess details. Browser command
execution decides what selected file action to run; this module only translates
that action into a small platform command and reports launch failures.
"""

from __future__ import annotations

from pathlib import Path
import os
import platform
import shlex
import shutil
import subprocess


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
    command = configured_copy_command(text, configured)
    if command is None:
        return "No clipboard command found."
    try:
        subprocess.run(command, input=text, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"Copy failed: {exc}"
    return None


def configured_copy_command(
    text: str,
    configured: str | None = None,
) -> list[str] | None:
    template = configured or os.environ.get("CR_COPY_CMD")
    if template:
        return _format_template(template, {"text": text})
    return clipboard_command()


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
    command = configured_reveal_command(path, configured)
    if command is None:
        return "No file browser command found."
    try:
        subprocess.Popen(command)
    except OSError as exc:
        return f"Reveal failed: {exc}"
    return None


def configured_reveal_command(
    path: Path,
    configured: str | None = None,
) -> list[str] | None:
    template = configured or os.environ.get("CR_REVEAL_CMD")
    if template:
        return _format_template(
            template,
            {
                "file": str(path),
                "dir": str(path.parent),
            },
        )
    return reveal_command(path)


def _format_template(template: str, replacements: dict[str, str]) -> list[str]:
    return [part.format(**replacements) for part in shlex.split(template)]
