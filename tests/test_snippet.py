import unittest

from cr.review.snippet import render_file_diff_snippet


class FileDiffSnippetTests(unittest.TestCase):
    def test_file_diff_snippet_renders_compact_selected_file_context(self):
        text = render_file_diff_snippet(
            {
                "path": "src/Sample.ets",
                "status": "modified",
                "summary": "+2 -1",
                "anchor": "src/Sample.ets:12",
                "risk_hints": ["high churn"],
                "seen": True,
                "review_note": "check lifecycle edge case",
                "purpose": "ArkTS page/component SamplePage",
                "modified_symbols": ["build"],
                "hunks": ["@@ -1 +1 @@", "-old", "+new"],
            }
        )

        self.assertIn("# File Diff: src/Sample.ets", text)
        self.assertIn("- change: +2 -1 (modified)", text)
        self.assertIn("- anchor: src/Sample.ets:12", text)
        self.assertIn("- state: seen", text)
        self.assertIn("- review note: check lifecycle edge case", text)
        self.assertIn("- purpose: ArkTS page/component SamplePage", text)
        self.assertIn("- focus: build", text)
        self.assertIn("```diff\n@@ -1 +1 @@\n-old\n+new\n```", text)
        self.assertNotIn("Please review these changes.", text)


if __name__ == "__main__":
    unittest.main()
