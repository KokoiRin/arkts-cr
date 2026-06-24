"""Platform file actions used by the interactive browser.

This module owns clipboard and file-browser subprocess details. Browser command
execution decides what selected file action to run; this module only translates
that action into a small platform command and reports launch failures.
"""

from __future__ import annotations

from pathlib import Path
import platform
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


def copy_text(text: str) -> str | None:
    command = clipboard_command()
    if command is None:
        return "No clipboard command found."
    try:
        subprocess.run(command, input=text, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        return f"Copy failed: {exc}"
    return None


def reveal_command(path: Path) -> list[str] | None:
    if platform.system() == "Darwin" and shutil.which("open"):
        return ["open", "-R", str(path)]
    if platform.system() == "Windows" and shutil.which("explorer"):
        return ["explorer", f"/select,{path}"]
    if shutil.which("xdg-open"):
        target = path if path.is_dir() else path.parent
        return ["xdg-open", str(target)]
    return None


def reveal_path(path: Path) -> str | None:
    command = reveal_command(path)
    if command is None:
        return "No file browser command found."
    try:
        subprocess.Popen(command)
    except OSError as exc:
        return f"Reveal failed: {exc}"
    return None
