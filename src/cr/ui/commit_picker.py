"""Commit Picker rules for recent-commit scope selection."""

from __future__ import annotations

from ..vcs import git


def filter_commits_by_query(
    commits: list[git.CommitSummary],
    query: str,
) -> list[git.CommitSummary]:
    normalized = query.strip().casefold()
    if not normalized:
        return commits
    return [
        commit
        for commit in commits
        if normalized in commit_search_text(commit).casefold()
    ]


def selected_commit(
    commits: list[git.CommitSummary],
    selected: int,
    query: str = "",
) -> git.CommitSummary | None:
    visible_commits = filter_commits_by_query(commits, query)
    if selected < 0 or selected >= len(visible_commits):
        return None
    return visible_commits[selected]


def commit_search_text(commit: git.CommitSummary) -> str:
    file_label = "file" if commit.files == 1 else "files"
    summary = f"{commit.files} {file_label}, +{commit.added} -{commit.deleted}"
    compact_summary = f"{commit.files} {file_label} +{commit.added} -{commit.deleted}"
    return (
        f"{commit.commit} {commit.authored_at} {commit.subject} "
        f"{summary} {compact_summary}"
    )
