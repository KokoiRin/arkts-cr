import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliBrowserWorkspaceWorkflowTests(CliTestCase):

    def test_cli_browser_restores_saved_workspace_filter_and_file(self):
        # Behavior: 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            first_session = self._cr_input(
                repo,
                "filter Second\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(first_session.returncode, 0, first_session.stderr)
            self.assertTrue((repo / ".git" / "cr" / "browse-state.json").exists())

            second_session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(second_session.returncode, 0, second_session.stderr)
            self.assertIn("File 1/1", second_session.stdout)
            self.assertIn("Second.ts", second_session.stdout)
            self.assertNotIn("First.ts", second_session.stdout)
    def test_cli_browser_explicit_scope_ignores_saved_workspace(self):
        # Behavior: 当用户在scope home中保存工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": True,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "",
                        "selected_path": "src/Sample.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "1\nq\n",
                "browse",
                "--staged",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertNotIn("+export const sample = 'worktree'", session.stdout)
    def test_cli_browser_ignores_malformed_saved_workspace(self):
        # Behavior: 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
            sample.write_text("export const sample = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not json", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "browse", "--context", "0")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
    def test_cli_browser_pathspec_ignores_saved_workspace_filter(self):
        # Behavior: 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": False,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "Second",
                        "selected_path": "src/Second.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--context",
                "0",
                "src/First.ts",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertNotIn("Second.ts", session.stdout)
            self.assertNotIn("Filter: Second", session.stdout)
    def test_cli_browser_can_mark_seen_and_show_remaining_files(self):
        # Behavior: 当用户在CLI browser中展示工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen", session.stdout)
            self.assertIn("remaining only", session.stdout)
            self.assertIn("[x]", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("[ ]", session.stdout)
            self.assertIn("Second.ts", session.stdout)
    def test_cli_browser_can_unmark_seen_and_return_to_all_files(self):
        # Behavior: 当用户在CLI browser中验证工作区时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nallfiles\ntodo\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen remaining only", session.stdout)
            self.assertIn("Progress: 0/2 seen", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("Second.ts", session.stdout)

if __name__ == "__main__":
    unittest.main()
