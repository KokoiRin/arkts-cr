import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliBrowserScopeWorkflowTests(CliTestCase):

    def test_cli_browser_shows_recent_commits_when_no_worktree_changes(self):
        # Behavior: 当用户在Review Scope 与工作区中查看「CLI browser 显示 最近 commit when 无 worktree changes」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'from commit'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change sample")

            sample.write_text("export const sample = 'staged only'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")

            session = self._cr_input(
                repo,
                "1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("change sample", session.stdout)
            self.assertIn("1 file, +1 -1", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'from commit'", session.stdout)
    def test_cli_browser_can_switch_from_worktree_to_recent_commits(self):
        # Behavior: 当用户在Review Scope 与工作区中切换「CLI browser 可以 切换 from worktree to 最近 commit」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\nw\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("Scope: recent commits", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("committed sample", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)
            self.assertIn("-export const sample = 'committed'", session.stdout)
            self.assertIn("+export const sample = 'working tree'", session.stdout)
    def test_cli_browser_filters_recent_commits_in_line_mode(self):
        # Behavior: 当用户在Review Scope 与工作区中过滤「CLI browser 过滤 最近 commit in line-mode」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'docs'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "docs update")

            sample.write_text("export const sample = 'login'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "login flow")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n/login\n1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: login (1/", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("login flow", session.stdout)
            self.assertIn("+export const sample = 'login'", session.stdout)
    def test_cli_browser_can_open_scope_home_in_line_mode(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「CLI browser 可以打开 Scope Home in line-mode」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(repo, "scopes\nq\n", "browse")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: scope home", session.stdout)
            self.assertIn("Review scopes", session.stdout)
            self.assertIn("Worktree", session.stdout)
            self.assertIn("Staged", session.stdout)
            self.assertIn("cr:scopes>", session.stdout)
    def test_cli_browser_back_from_commit_file_returns_to_commit_file_list(self):
        # Behavior: 当用户在Review Scope 与工作区中执行操作「CLI browser 返回 from commit 文件 返回 to commit 文件 list」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            alpha = repo / "src" / "Alpha.ts"
            beta = repo / "src" / "Beta.ts"
            alpha.parent.mkdir(parents=True)
            alpha.write_text("export const alpha = 'old'\n", encoding="utf-8")
            beta.write_text("export const beta = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            alpha.write_text("export const alpha = 'committed'\n", encoding="utf-8")
            beta.write_text("export const beta = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change both files")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\n2\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("+export const alpha = 'committed'", session.stdout)
            self.assertIn("+export const beta = 'committed'", session.stdout)
    def test_cli_browser_can_switch_review_scopes_in_line_mode(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「CLI browser 可以 切换 review 范围 in line-mode」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'staged'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "staged\n1\nb\nall\n1\nb\nworktree\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertIn("Scope: all local changes", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: worktree", session.stdout)
            self.assertIn("-export const sample = 'staged'", session.stdout)
    def test_cli_browser_can_switch_to_base_and_range_scopes(self):
        # Behavior: 当用户在Review Scope 与工作区中切换「CLI browser 可以 切换 to base and range 范围」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "base HEAD~1\n1\nb\nrange HEAD~1..HEAD\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: base HEAD~1", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: range HEAD~1..HEAD", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)

if __name__ == "__main__":
    unittest.main()
