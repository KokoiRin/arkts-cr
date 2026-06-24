"""Small Git boundary for cr commands.

All subprocess calls are isolated here so the rest of the tool can work with
plain Python data structures and surface concise Git errors to the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess


MAX_INLINE_TEXT_BYTES = 200_000
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int | None
    deleted: int | None
    status: str = "modified"
    old_path: str | None = None


@dataclass(frozen=True)
class CommitSummary:
    commit: str
    parent: str | None
    authored_at: str
    subject: str


class GitError(RuntimeError):
    pass


def diff_stat(
    paths: list[str] | None = None,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> str:
    return _git(
        _with_paths(
            _diff_args(
                staged,
                "--stat",
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
            paths,
        )
    ).stdout.strip()


def changed_files(
    paths: list[str] | None = None,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
    include_untracked: bool = False,
) -> list[FileChange]:
    statuses = _changed_statuses(paths, staged, all_changes, base, ref_range)
    output = _git(
        _with_paths(
            _diff_args(
                staged,
                "--numstat",
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
            paths,
        )
    ).stdout
    changes: list[FileChange] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, deleted, path = parts[0], parts[1], parts[2]
        status, old_path = statuses.get(path, ("modified", None))
        changes.append(
            FileChange(
                path=path,
                added=None if added == "-" else int(added),
                deleted=None if deleted == "-" else int(deleted),
                status=status,
                old_path=old_path,
            )
        )
    if include_untracked and not staged and ref_range is None:
        changes.extend(_untracked_changes(paths))
    return changes


def _changed_statuses(
    paths: list[str] | None = None,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> dict[str, tuple[str, str | None]]:
    output = _git(
        _with_paths(
            _diff_args(
                staged,
                "--name-status",
                "--find-renames",
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
            paths,
        )
    ).stdout
    statuses: dict[str, tuple[str, str | None]] = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        raw_status = parts[0]
        status_code = raw_status[0]
        if status_code == "D":
            statuses[parts[1]] = ("deleted", None)
        elif status_code == "A":
            statuses[parts[1]] = ("added", None)
        elif status_code == "R" and len(parts) >= 3:
            statuses[parts[2]] = ("renamed", parts[1])
        elif status_code == "M":
            statuses[parts[1]] = ("modified", None)
        else:
            statuses[parts[-1]] = ("modified", None)
    return statuses


def changed_new_lines(
    path: str,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> set[int]:
    if not staged and ref_range is None and _is_untracked(path):
        added = _text_line_count(path)
        return set(range(1, added + 1)) if added is not None else set()

    output = _git(
        [
            *_diff_args(
                staged,
                "--unified=0",
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
            "--",
            path,
        ]
    ).stdout
    changed: set[int] = set()
    current_line: int | None = None

    for line in output.splitlines():
        hunk = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if hunk:
            current_line = int(hunk.group(1))
            continue

        if current_line is None:
            continue
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            changed.add(current_line)
            current_line += 1
        elif line.startswith("-"):
            changed.add(current_line)
        elif line.startswith(" "):
            current_line += 1

    return changed


def first_changed_line(
    path: str,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> int | None:
    lines = [
        line
        for line in changed_new_lines(path, staged, all_changes, base, ref_range)
        if line > 0
    ]
    return min(lines) if lines else None


def file_diff(
    path: str,
    context: int = 2,
    staged: bool = False,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> str:
    if not staged and ref_range is None and _is_untracked(path):
        return _untracked_file_diff(path)

    return _git(
        [
            *_diff_args(
                staged,
                f"--unified={context}",
                all_changes=all_changes,
                base=base,
                ref_range=ref_range,
            ),
            "--",
            path,
        ]
    ).stdout


def repo_path(path: str) -> Path:
    return repo_root() / path


def repo_root() -> Path:
    root = _git(["rev-parse", "--show-toplevel"]).stdout.strip()
    return Path(root)


def file_text(path: str, ref: str | None = None) -> str:
    if ref is None:
        return repo_path(path).read_text(encoding="utf-8")
    return _git(["show", f"{ref}:{path}"]).stdout


def range_right_ref(ref_range: str) -> str:
    parts = ref_range.split("..")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise GitError("range must use OLD..NEW")
    return parts[1]


def recent_commits(limit: int = 20) -> list[CommitSummary]:
    output = _git(
        [
            "log",
            "-n",
            str(max(1, limit)),
            "--pretty=format:%H%x1f%P%x1f%cs%x1f%s",
        ]
    ).stdout
    commits: list[CommitSummary] = []
    for line in output.splitlines():
        parts = line.split("\x1f", 3)
        if len(parts) != 4:
            continue
        commit, parents, authored_at, subject = parts
        parent = parents.split()[0] if parents else None
        commits.append(CommitSummary(commit, parent, authored_at, subject))
    return commits


def commit_ref_range(commit: CommitSummary) -> str:
    left = commit.parent or EMPTY_TREE
    return f"{left}..{commit.commit}"


def _with_paths(args: list[str], paths: list[str] | None) -> list[str]:
    if not paths:
        return args
    return [*args, "--", *paths]


def _untracked_changes(paths: list[str] | None) -> list[FileChange]:
    output = _git(
        _with_paths(["ls-files", "--others", "--exclude-standard"], paths)
    ).stdout
    changes: list[FileChange] = []
    for path in output.splitlines():
        changes.append(
            FileChange(
                path=path,
                added=_text_line_count(path),
                deleted=0,
                status="untracked",
            )
        )
    return changes


def _is_untracked(path: str) -> bool:
    output = _git(["ls-files", "--others", "--exclude-standard", "--", path]).stdout
    return path in output.splitlines()


def _text_line_count(path: str) -> int | None:
    if _is_too_large_for_inline_diff(path):
        return None
    lines = _read_text_lines(path)
    return len(lines) if lines is not None else None


def _untracked_file_diff(path: str) -> str:
    size = _file_size(path)
    if size is not None and size > MAX_INLINE_TEXT_BYTES:
        return (
            f"{path}: file is too large for inline diff "
            f"({size} bytes > {MAX_INLINE_TEXT_BYTES} bytes); content omitted"
        )
    lines = _read_text_lines(path)
    if lines is None:
        return f"{path}: binary or non-UTF-8 file; content omitted"
    header = f"@@ -0,0 +1,{len(lines)} @@"
    return "\n".join([header, *(f"+{line}" for line in lines)])


def _is_too_large_for_inline_diff(path: str) -> bool:
    size = _file_size(path)
    return size is not None and size > MAX_INLINE_TEXT_BYTES


def _file_size(path: str) -> int | None:
    try:
        return repo_path(path).stat().st_size
    except FileNotFoundError:
        return None


def _read_text_lines(path: str) -> list[str] | None:
    try:
        return repo_path(path).read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return None


def _diff_args(
    staged: bool,
    *args: str,
    all_changes: bool = False,
    base: str | None = None,
    ref_range: str | None = None,
) -> list[str]:
    command = ["diff"]
    if ref_range:
        command.append(ref_range)
    elif base:
        command.append(base)
    elif all_changes:
        command.append("HEAD")
    elif staged:
        command.append("--cached")
    return [*command, *args]


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise GitError(message)
    return result
