import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliBrowserEntryNavigationTests(CliTestCase):

    def test_cli_defaults_to_interactive_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "pages" / "Sample.ets"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('old')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            session = self._cr_input(repo, "q\n")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Enter", session.stdout)
            self.assertIn("j/k", session.stdout)
            self.assertIn("Sample.ets", session.stdout)
            self.assertIn("cr:list>", session.stdout)
    def test_cli_defaults_to_browser_when_options_are_passed(self):
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

            session = self._cr_input(repo, "q\n", "--context", "0", "--sort", "path")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
    def test_cli_interactive_browser_opens_file_and_navigates(self):
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
                "1\nn\nb\nr\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("File 1/2", session.stdout)
            self.assertIn("File 2/2", session.stdout)
            self.assertIn("-export const first = 'old'", session.stdout)
            self.assertIn("+export const first = 'new'", session.stdout)
            self.assertIn("Changed files", session.stdout)
    def test_cli_browser_command_list_is_discoverable_in_line_mode(self):
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

            session = self._cr_input(
                repo,
                "commands\nb\ncmds\nb\nhelp commands\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertGreaterEqual(session.stdout.count("命令"), 3)
            self.assertIn("审查范围", session.stdout)
            self.assertIn("任务", session.stdout)
            self.assertIn("cr:commands>", session.stdout)
            self.assertIn("Changed files", session.stdout)
    def test_cli_interactive_browser_filters_files_in_line_mode(self):
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
                "filter First\nc\n/Second\nr\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: First (1/2 matches, c to clear)", session.stdout)
            self.assertIn("Filter: Second (1/2 matches, c to clear)", session.stdout)
            self.assertIn("File 1/1", session.stdout)
            self.assertIn("Second.ts", session.stdout)
            self.assertIn("-export const second = 'old'", session.stdout)
            self.assertIn("+export const second = 'new'", session.stdout)
    def test_cli_interactive_browser_can_open_current_file(self):
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

            session = self._cr_input(
                repo,
                "1\no\nq\n",
                "browse",
                "--context",
                "0",
                "--open-cmd",
                "true",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Opened src/Sample.ts:1", session.stdout)

if __name__ == "__main__":
    unittest.main()
