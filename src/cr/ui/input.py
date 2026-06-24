"""Terminal input protocol for the interactive browser.

This module owns raw-key availability checks, line-input sentinels, raw escape
sequence parsing, and temporary query readers. Browser session code interprets
the returned command strings; this module does not mutate browser state or draw
the screen.
"""

from __future__ import annotations

from collections.abc import Callable
import select
import sys
import termios
from typing import TextIO
import tty


TICK = "__tick__"
EOF_COMMAND = "__eof__"
INTERRUPT = "__interrupt__"
FILTER_PROMPT_COMMAND = "filter_prompt"
COMMAND_PROMPT_COMMAND = "command_prompt"
RAW_IDLE_TIMEOUT_SECONDS = 0.2


def use_raw_keys(stdin: TextIO | None = None, stdout: TextIO | None = None) -> bool:
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    return bool(
        hasattr(stdin, "isatty")
        and stdin.isatty()
        and hasattr(stdout, "isatty")
        and stdout.isatty()
    )


def read_browse_command(
    prompt: str,
    raw_keys: bool,
    tick_when_idle: bool = False,
    *,
    raw_key_reader: Callable[[float | None], str] | None = None,
) -> str:
    if not raw_keys:
        try:
            return input(prompt).strip()
        except EOFError:
            print()
            return EOF_COMMAND
        except KeyboardInterrupt:
            print()
            return INTERRUPT

    raw_key_reader = read_raw_key if raw_key_reader is None else raw_key_reader
    try:
        key = raw_key_reader(RAW_IDLE_TIMEOUT_SECONDS if tick_when_idle else None)
    except KeyboardInterrupt:
        print()
        return INTERRUPT
    if key == TICK:
        return key
    return key


def read_filter_query(prompt: str = "filter> ") -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return INTERRUPT


def read_command_query() -> str:
    try:
        return input("command> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return INTERRUPT


def read_raw_key(timeout: float | None = None, stdin: TextIO | None = None) -> str:
    stdin = sys.stdin if stdin is None else stdin
    fd = stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if timeout is not None:
            ready, _, _ = select.select([stdin], [], [], timeout)
            if not ready:
                return TICK
        char = stdin.read(1)
        if char == "\x03":
            raise KeyboardInterrupt
        if char in {"\r", "\n"}:
            return "enter"
        if char == "\x1b":
            second = stdin.read(1)
            if second != "[":
                return ""
            sequence = ""
            while len(sequence) < 6:
                piece = stdin.read(1)
                if not piece:
                    break
                sequence += piece
                if piece.isalpha() or piece == "~":
                    break
            return {
                "A": "up",
                "B": "down",
                "C": "right",
                "D": "left",
                "H": "home",
                "F": "end",
                "1~": "home",
                "4~": "end",
                "5~": "pageup",
                "6~": "pagedown",
            }.get(sequence, "")
        return {
            "j": "down",
            "k": "up",
            "l": "right",
            "h": "left",
            "u": "pageup",
            "d": "pagedown",
            " ": "space",
            "/": FILTER_PROMPT_COMMAND,
            ":": COMMAND_PROMPT_COMMAND,
            "\x04": EOF_COMMAND,
        }.get(char, char)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
