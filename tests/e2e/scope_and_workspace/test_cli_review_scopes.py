import json
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliReviewScopeTests(CliTestCase):

    def test_cli_review_compares_against_named_base(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、compares时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
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
            self._run(repo, "git", "commit", "-m", "base")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from head')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "head")

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertIn("No working tree changes.", default_review.stdout)

            review = self._cr(repo, "review", "--base", "HEAD~1", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("Sample.ets:3", review.stdout)

            diff = self._cr(repo, "diff", "--base", "HEAD~1", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            json_review = self._cr(repo, "review", "--base", "HEAD~1", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 1, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})
    def test_cli_review_compares_explicit_ref_range_without_checkout(self):
        # Behavior: 当用户在scope home遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
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
            self._run(repo, "git", "commit", "-m", "base")
            self._run(repo, "git", "branch", "-M", "main")
            self._run(repo, "git", "branch", "feature")
            self._run(repo, "git", "checkout", "feature")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from feature')
  }

  helper() {
    return 'feature only'
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "feature")
            self._run(repo, "git", "checkout", "main")

            review = self._cr(repo, "review", "--range", "main..feature", "--no-hunks")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +5 -1", review.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", review.stdout)
            self.assertIn(
                "purpose: ArkTS page/component SamplePage with methods build, helper",
                review.stdout,
            )
            self.assertIn("method helper", review.stdout)

            diff = self._cr(repo, "diff", "--range", "main..feature", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", diff.stdout)

            json_review = self._cr(repo, "review", "--range", "main..feature", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build", "helper"])
            self.assertIn("build, helper", data["files"][0]["purpose"])
    def test_cli_includes_untracked_files_only_when_requested(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、includes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tracked = repo / "README.md"
            new_page = repo / "src" / "pages" / "NewPage.ets"
            tracked.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            new_page.parent.mkdir(parents=True)
            new_page.write_text(
                "struct NewPage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            default_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(default_diff.returncode, 0, default_diff.stderr)
            self.assertIn("No working tree changes.", default_diff.stdout)
            self.assertNotIn("NewPage.ets", default_diff.stdout)

            diff = self._cr(repo, "diff", "--untracked", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("NewPage.ets +5 -0 untracked", diff.stdout)
            self.assertIn("modified: build", diff.stdout)
            self.assertNotIn("No working tree changes.", diff.stdout)

            review = self._cr(repo, "review", "--untracked", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/NewPage.ets", review.stdout)
            self.assertIn("+5 -0 untracked", review.stdout)
            self.assertIn("src/pages/NewPage.ets:1", review.stdout)
            self.assertIn("+struct NewPage", review.stdout)
            self.assertIn("purpose: ArkTS page/component NewPage", review.stdout)
            self.assertIn("method build *", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 0})
            self.assertEqual(data["files"][0]["status"], "untracked")
            self.assertEqual(data["files"][0]["first_changed_line"], 1)
            self.assertEqual(data["files"][0]["anchor"], "src/pages/NewPage.ets:1")
            self.assertTrue(any("+struct NewPage" in line for line in data["files"][0]["hunks"]))

            staged = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertIn("No staged changes.", staged.stdout)
            self.assertNotIn("NewPage.ets", staged.stdout)

            all_changes = self._cr(repo, "review", "--all", "--untracked", "--code")
            self.assertEqual(all_changes.returncode, 0, all_changes.stderr)
            self.assertIn("src/pages/NewPage.ets", all_changes.stdout)
    def test_cli_can_review_staged_changes(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello staged')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")

            unstaged = self._cr(repo, "diff")
            self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
            self.assertIn("No working tree changes.", unstaged.stdout)

            staged_diff = self._cr(repo, "diff", "--staged")
            self.assertEqual(staged_diff.returncode, 0, staged_diff.stderr)
            self.assertIn("Sample.ets +1 -1 modified: build", staged_diff.stdout)

            staged_review = self._cr(repo, "review", "--staged")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn("Sample.ets +1 -1", staged_review.stdout)
            self.assertIn("+    Text('hello staged')", staged_review.stdout)
            self.assertIn("modified: build", staged_review.stdout)
    def test_cli_can_review_staged_deletions(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "helper.ts"
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "helper.ts")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()
            self._run(repo, "git", "add", "helper.ts")

            review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)
    def test_cli_notes_when_the_other_git_side_has_changes(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、notes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'b'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'b'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Note: staged changes also exist; use --staged to review them.", diff.stdout)
            self.assertIn("unstaged.ts", diff.stdout)
            self.assertNotIn("  └─ staged.ts +1 -1", diff.stdout)

            staged_review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn(
                "Note: unstaged changes also exist; omit --staged to review them.",
                staged_review.stdout,
            )
            self.assertIn("staged.ts", staged_review.stdout)
            self.assertNotIn("  └─ unstaged.ts +1 -1", staged_review.stdout)

            json_review = self._cr(repo, "review", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["other_changes"], {"staged": 1, "unstaged": 0})
    def test_cli_can_review_all_staged_and_unstaged_changes_together(self):
        # Behavior: 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'staged'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'unstaged'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--all", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", diff.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", diff.stdout)
            self.assertNotIn("also exist", diff.stdout)

            review = self._cr(repo, "review", "--all", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", review.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", review.stdout)
            self.assertIn("+  return 'staged'", review.stdout)
            self.assertIn("+  return 'unstaged'", review.stdout)
            self.assertNotIn("also exist", review.stdout)

            json_review = self._cr(repo, "review", "--all", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 2)
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

            bad_scope = self._cr(repo, "review", "--all", "--staged")
            self.assertEqual(bad_scope.returncode, 2)
            self.assertIn("not allowed with argument", bad_scope.stderr)
if __name__ == "__main__":
    unittest.main()
