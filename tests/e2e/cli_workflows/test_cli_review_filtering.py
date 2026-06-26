import json
from pathlib import Path
import tempfile
import unittest

from tests.cli_test_support import CliTestCase


class CliReviewFilteringTests(CliTestCase):

    def test_cli_omits_untracked_binary_and_large_file_contents(self):
        # Behavior: 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            binary = repo / "asset.bin"
            large = repo / "large.txt"
            readme.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            binary.write_bytes(b"\x00\xff\x00\xff")
            large.write_text("x" * 210_000, encoding="utf-8")

            review = self._cr(repo, "review", "--untracked")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("asset.bin +? -0 untracked", review.stdout)
            self.assertIn("large.txt +? -0 untracked", review.stdout)
            self.assertIn("asset.bin: binary or non-UTF-8 file; content omitted", review.stdout)
            self.assertIn("large.txt: file is too large for inline diff", review.stdout)
            self.assertNotIn("+" + ("x" * 200), review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            files = {item["path"]: item for item in data["files"]}
            self.assertIsNone(files["asset.bin"]["added"])
            self.assertIsNone(files["large.txt"]["added"])
            self.assertIn("content omitted", "\n".join(files["asset.bin"]["hunks"]))
            self.assertIn("too large for inline diff", "\n".join(files["large.txt"]["hunks"]))
    def test_cli_flags_lockfile_config_and_generated_risks(self):
        # Behavior: 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            lockfile = repo / "package-lock.json"
            config = repo / "tsconfig.json"
            generated = repo / "src" / "generated" / "client.ts"
            generated.parent.mkdir(parents=True)
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v1'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {"strict": true}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v2'\n}\n", encoding="utf-8")

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("risk", review.stdout)
            self.assertIn("package-lock.json", review.stdout)
            self.assertIn("lockfile", review.stdout)
            self.assertIn("tsconfig.json", review.stdout)
            self.assertIn("config", review.stdout)
            self.assertIn("src/generated/client.ts", review.stdout)
            self.assertIn("generated", review.stdout)
            self.assertIn("risk: lockfile", review.stdout)
            self.assertIn("risk: config", review.stdout)
            self.assertIn("risk: generated", review.stdout)

            full_review = self._cr(repo, "review", "package-lock.json")
            self.assertEqual(full_review.returncode, 0, full_review.stderr)
            self.assertIn("  risk: lockfile", full_review.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            risks = {item["path"]: item["risk_hints"] for item in data["files"]}
            self.assertEqual(risks["package-lock.json"], ["lockfile"])
            self.assertEqual(risks["tsconfig.json"], ["config"])
            self.assertEqual(risks["src/generated/client.ts"], ["generated"])
    def test_cli_review_sorts_large_reviews_by_risk_or_churn(self):
        # Behavior: 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            risk_sorted = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(risk_sorted.returncode, 0, risk_sorted.stderr)
            self.assertLess(
                risk_sorted.stdout.index("package-lock.json"),
                risk_sorted.stdout.index("README.md"),
            )

            churn_sorted = self._cr(repo, "review", "--summary", "--sort", "churn")
            self.assertEqual(churn_sorted.returncode, 0, churn_sorted.stderr)
            self.assertLess(
                churn_sorted.stdout.index("src/app.ts"),
                churn_sorted.stdout.index("package-lock.json"),
            )

            json_review = self._cr(repo, "review", "--json", "--summary", "--sort", "risk")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["path"], "package-lock.json")
    def test_cli_review_picks_one_file_by_summary_index(self):
        # Behavior: 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("idx", summary.stdout)
            self.assertLess(
                summary.stdout.index("1  package-lock.json"),
                summary.stdout.index("2  src/app.ts"),
            )

            picked = self._cr(repo, "review", "--sort", "risk", "--pick", "2")
            self.assertEqual(picked.returncode, 0, picked.stderr)
            self.assertIn("1 files", picked.stdout)
            self.assertIn("src/app.ts", picked.stdout)
            self.assertIn("+  const value = 'v2'", picked.stdout)
            self.assertNotIn("package-lock.json", picked.stdout)
            self.assertNotIn("README.md", picked.stdout)

            bad_pick = self._cr(repo, "review", "--pick", "9")
            self.assertEqual(bad_pick.returncode, 2)
            self.assertIn("--pick must be between 1 and 3", bad_pick.stderr)
    def test_cli_review_tracks_seen_files_and_filters_remaining(self):
        # Behavior: 当用户在CLI review中过滤过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v2'\n}\n",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--seen", "README.md")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("seen", summary.stdout)
            self.assertIn("README.md", summary.stdout)
            self.assertIn("yes", summary.stdout)
            self.assertIn("src/app.ts", summary.stdout)
            self.assertIn("no", summary.stdout)

            remaining = self._cr(
                repo,
                "review",
                "--summary",
                "--seen",
                "README.md",
                "--remaining",
            )
            self.assertEqual(remaining.returncode, 0, remaining.stderr)
            self.assertIn("src/app.ts", remaining.stdout)
            self.assertNotIn("README.md", remaining.stdout)

            no_remaining = self._cr(
                repo,
                "review",
                "--seen",
                "README.md,src/app.ts",
                "--remaining",
            )
            self.assertEqual(no_remaining.returncode, 0, no_remaining.stderr)
            self.assertIn("No remaining changes.", no_remaining.stdout)

            json_review = self._cr(repo, "review", "--json", "--seen", "README.md")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            seen_by_path = {item["path"]: item["seen"] for item in data["files"]}
            self.assertTrue(seen_by_path["README.md"])
            self.assertFalse(seen_by_path["src/app.ts"])

            prompt = self._cr(repo, "review", "--prompt", "--seen", "README.md")
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("state: seen", prompt.stdout)
    def test_cli_filters_to_code_files_and_path_prefixes(self):
        # Behavior: 当用户在CLI review中过滤过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            helper = repo / "src" / "utils" / "helper.ts"
            readme = repo / "README.md"
            page.parent.mkdir(parents=True)
            helper.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello page')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'b'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello docs\n", encoding="utf-8")

            review = self._cr(repo, "review", "--code", "src/pages")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/Sample.ets +1 -1", review.stdout)
            self.assertNotIn("src/utils/helper.ts", review.stdout)
            self.assertNotIn("README.md", review.stdout)

            diff = self._cr(repo, "diff", "--code", "src/pages")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("src/pages", diff.stdout)
            self.assertNotIn("src/utils", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

            code_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(code_diff.returncode, 0, code_diff.stderr)
            self.assertIn("src/pages/Sample.ets", code_diff.stdout)
            self.assertIn("src/utils/helper.ts", code_diff.stdout)
            self.assertNotIn("README.md", code_diff.stdout)
    def test_code_filter_does_not_show_doc_only_stats(self):
        # Behavior: 当用户在CLI review中展示过滤时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("No working tree changes.", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)
    def test_cli_marks_deleted_code_files_without_fake_symbols(self):
        # Behavior: 当用户在CLI review遇到缺少前置条件、过滤时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "src" / "utils" / "helper.ts"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("helper.ts +0 -3 deleted", diff.stdout)
            self.assertNotIn("modified: unknown", diff.stdout)

            review = self._cr(repo, "review", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/utils/helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)
if __name__ == "__main__":
    unittest.main()
