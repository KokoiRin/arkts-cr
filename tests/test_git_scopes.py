import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from cr.vcs import git


class GitScopeTests(unittest.TestCase):

    def test_git_all_changes_marks_mixed_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("one\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("two\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            sample.write_text("three\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(all_changes=True)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].path, "Sample.ts")
        self.assertEqual(changes[0].source, "mixed")

    def test_git_local_scopes_mark_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged_file = repo / "staged.ts"
            unstaged_file = repo / "unstaged.ts"
            staged_file.write_text("old staged\n", encoding="utf-8")
            unstaged_file.write_text("old unstaged\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            staged_file.write_text("new staged\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged_file.write_text("new unstaged\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                staged_changes = git.changed_files(staged=True)
                unstaged_changes = git.changed_files()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(
            {change.path: change.source for change in staged_changes},
            {"staged.ts": "staged"},
        )
        self.assertEqual(
            {change.path: change.source for change in unstaged_changes},
            {"unstaged.ts": "unstaged"},
        )

    def test_git_recent_commits_include_change_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "first.ts"
            second = repo / "second.ts"
            first.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("new\n", encoding="utf-8")
            second.write_text("one\ntwo\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change summary")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                commits = git.recent_commits(limit=1)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].subject, "change summary")
        self.assertEqual(commits[0].files, 2)
        self.assertEqual(commits[0].added, 3)
        self.assertEqual(commits[0].deleted, 1)

    def test_git_comparison_scopes_do_not_mark_local_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "base")
            sample.write_text("new\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "head")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(base="HEAD~1")
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].source, "")

    def _run(self, cwd, *args):
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
