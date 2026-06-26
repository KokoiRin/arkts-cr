import json
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliReviewOutputTests(CliTestCase):

    def test_cli_diff_outline_and_review_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            diff = self._cr(repo, "diff")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Changed file tree:", diff.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            outline = self._cr(repo, "outline", "Sample.ets")
            self.assertEqual(outline.returncode, 0, outline.stderr)
            self.assertIn("purpose: ArkTS page/component SamplePage", outline.stdout)
            self.assertIn("struct SamplePage", outline.stdout)
            self.assertIn("method build", outline.stdout)

            review = self._cr(repo, "review")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("Summary:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("focus", review.stdout)
            self.assertIn("Changed file tree:", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("modified: build", review.stdout)
            self.assertIn("method build *", review.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-    Text('hello')", review.stdout)
            self.assertIn("+    Text('hello world')", review.stdout)

            summary = self._cr(repo, "review", "--summary")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("Summary:", summary.stdout)
            self.assertIn("Changed file tree:", summary.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", summary.stdout)
            self.assertNotIn("\n  changes:", summary.stdout)
            self.assertNotIn("purpose:", summary.stdout)
            self.assertNotIn("outline:", summary.stdout)

            no_hunks = self._cr(repo, "review", "--no-hunks")
            self.assertEqual(no_hunks.returncode, 0, no_hunks.stderr)
            self.assertIn("Summary:", no_hunks.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", no_hunks.stdout)
            self.assertIn("modified: build", no_hunks.stdout)
            self.assertIn("outline:", no_hunks.stdout)
            self.assertNotIn("\n  changes:", no_hunks.stdout)
            self.assertNotIn("-    Text('hello')", no_hunks.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 1)
            self.assertEqual(data["summary"]["added"], 1)
            self.assertEqual(data["summary"]["deleted"], 1)
            self.assertEqual(data["files"][0]["path"], "Sample.ets")
            self.assertEqual(data["files"][0]["status"], "modified")
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertIn("ArkTS page/component SamplePage", data["files"][0]["purpose"])
            self.assertTrue(any("+    Text('hello world')" in line for line in data["files"][0]["hunks"]))
            self.assertNotIn("Review changes:", json_review.stdout)

            json_summary = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_summary.returncode, 0, json_summary.stderr)
            summary_data = json.loads(json_summary.stdout)
            self.assertEqual(summary_data["files"][0]["hunks"], [])
    def test_cli_can_emit_clickable_file_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const value = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const value = 'new'\n", encoding="utf-8")

            default_review = self._cr(repo, "review", "--summary")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033]8;;", default_review.stdout)

            linked_review = self._cr(
                repo,
                "review",
                "--summary",
                "--links",
                "always",
            )
            self.assertEqual(linked_review.returncode, 0, linked_review.stderr)
            self.assertIn("\033]8;;file://", linked_review.stdout)
            self.assertIn("#L1", linked_review.stdout)
            self.assertIn("\033]8;;\033\\", linked_review.stdout)

            vscode_browse = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--links",
                "always",
                "--link-scheme",
                "vscode",
            )
            self.assertEqual(vscode_browse.returncode, 0, vscode_browse.stderr)
            self.assertNotIn("\033]8;;", vscode_browse.stdout)
            self.assertIn("Sample.ts", vscode_browse.stdout)
    def test_cli_review_accepts_configurable_hunk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )

            no_context = self._cr(repo, "review", "--json", "--context", "0")
            self.assertEqual(no_context.returncode, 0, no_context.stderr)
            no_context_hunks = "\n".join(json.loads(no_context.stdout)["files"][0]["hunks"])
            self.assertIn("-    Text('hello')", no_context_hunks)
            self.assertIn("+    Text('hello world')", no_context_hunks)
            self.assertNotIn("  build() {", no_context_hunks)

            wider_context = self._cr(repo, "review", "--json", "--context", "3")
            self.assertEqual(wider_context.returncode, 0, wider_context.stderr)
            wider_hunks = "\n".join(json.loads(wider_context.stdout)["files"][0]["hunks"])
            self.assertIn("  build() {", wider_hunks)

            bad_context = self._cr(repo, "review", "--context", "-1")
            self.assertEqual(bad_context.returncode, 2)
            self.assertIn("context must be >= 0", bad_context.stderr)
    def test_cli_compacts_deep_paths_and_can_color_diff_hunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "a" / "b" / "c" / "d" / "e" / "f" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "export function sample(): string {\n  return 'old'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "export function sample(): string {\n  return 'new'\n}\n",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--color", "always")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn(".../d/e/f", review.stdout)
            self.assertIn(".../d/e/f/Sample.ts", review.stdout)
            self.assertNotIn("a/b/c/d/e/f/Sample.ts", review.stdout)
            self.assertIn("\033[32m", review.stdout)
            self.assertIn("\033[31m", review.stdout)

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033[", default_review.stdout)
    def test_cli_review_shows_first_changed_line_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("anchor", review.stdout)
            self.assertIn("Sample.ets:7", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build line 7", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["first_changed_line"], 7)
            self.assertEqual(data["files"][0]["anchor"], "Sample.ets:7")
    def test_cli_review_emits_prompt_ready_markdown_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            lockfile = repo / "package-lock.json"
            page.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello prompt')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")

            prompt = self._cr(
                repo,
                "review",
                "--prompt",
                "--sort",
                "risk",
                "--context",
                "0",
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("# Code Review Handoff", prompt.stdout)
            self.assertIn("Please review these changes.", prompt.stdout)
            self.assertIn("## Summary", prompt.stdout)
            self.assertIn("- Files: 2", prompt.stdout)
            self.assertIn("## Files", prompt.stdout)
            self.assertLess(
                prompt.stdout.index("package-lock.json"),
                prompt.stdout.index("src/pages/Sample.ets"),
            )
            self.assertIn("risk: lockfile", prompt.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", prompt.stdout)
            self.assertIn("focus: build", prompt.stdout)
            self.assertIn("```diff", prompt.stdout)
            self.assertIn("+    Text('hello prompt')", prompt.stdout)
            self.assertNotIn("Review changes:", prompt.stdout)
            self.assertNotIn('"summary"', prompt.stdout)
if __name__ == "__main__":
    unittest.main()
