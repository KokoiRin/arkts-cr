import json
import os
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliBrowserTaskWorkflowTests(CliTestCase):

    def test_cli_interactive_browser_can_run_build_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            build_script = repo / "build.sh"
            build_script.write_text(
                "#!/bin/sh\npwd > build.out\n",
                encoding="utf-8",
            )
            os.chmod(build_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            subdir = repo / "src"
            session = self._cr_input(
                subdir,
                "build\nq\n",
                "browse",
                "--build-cmd",
                "./build.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Build: ./build.sh", session.stdout)
            self.assertIn("Build succeeded.", session.stdout)
            self.assertEqual(
                Path((repo / "build.out").read_text(encoding="utf-8").strip()).resolve(),
                repo.resolve(),
            )
    def test_cli_interactive_browser_can_run_test_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            test_script = repo / "test.sh"
            test_script.write_text(
                "#!/bin/sh\necho test ran > test.out\n",
                encoding="utf-8",
            )
            os.chmod(test_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            session = self._cr_input(
                repo,
                "test\nq\n",
                "browse",
                "--test-cmd",
                "./test.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Test: ./test.sh", session.stdout)
            self.assertIn("Test succeeded.", session.stdout)
            self.assertEqual(
                (repo / "test.out").read_text(encoding="utf-8").strip(),
                "test ran",
            )

if __name__ == "__main__":
    unittest.main()
