"""Persistence helpers for the interactive review workspace.

This module owns the `.git/cr/browse-state.json` file path, schema wrapping,
load/save tolerance, and default-session restore/save eligibility. Review
workspace state semantics stay in `cr.ui.workspace`; browser.py only decides
when to call these helpers during session startup and shutdown.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workspace import ReviewWorkspace, restore_scope_from_state


BROWSER_WORKSPACE_STATE_VERSION = 1


def workspace_state_path(repo: Path) -> Path:
    return repo / ".git" / "cr" / "browse-state.json"


def should_restore_workspace_state(args: argparse.Namespace) -> bool:
    return (
        not args.staged
        and not args.all_changes
        and args.base is None
        and args.ref_range is None
        and not args.untracked
        and not args.paths
    )


def should_save_workspace_state(args: argparse.Namespace) -> bool:
    return not bool(args.paths)


def workspace_state_data(
    workspace: ReviewWorkspace,
    args: argparse.Namespace,
    *,
    mode: str,
) -> dict[str, object]:
    return {
        "version": BROWSER_WORKSPACE_STATE_VERSION,
        **workspace.state_data(args, mode=mode),
    }


def save_workspace_state(
    workspace: ReviewWorkspace,
    args: argparse.Namespace,
    repo: Path,
    *,
    mode: str,
) -> None:
    path = workspace_state_path(repo)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(
                workspace_state_data(workspace, args, mode=mode),
                ensure_ascii=False,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        tmp_path.replace(path)
    except OSError:
        return


def load_workspace_state(repo: Path) -> dict[str, object] | None:
    path = workspace_state_path(repo)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("version") != BROWSER_WORKSPACE_STATE_VERSION:
        return None
    scope = raw.get("scope")
    if not isinstance(scope, dict):
        return None
    return raw


def restore_workspace_scope(
    args: argparse.Namespace,
    workspace_state: dict[str, object],
) -> None:
    restore_scope_from_state(args, workspace_state)
