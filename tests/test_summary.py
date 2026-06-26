import unittest

from cr.review.summary import render_review_summary
from cr.vcs.git import FileChange


class ReviewSummaryTests(unittest.TestCase):
    def test_renders_totals_and_one_line_per_file(self):
        # Behavior: 当用户在产品行为中渲染summary、renders、totals、one时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        changes = [
            FileChange("src/pages/Home.ets", 5, 2),
            FileChange("README.md", 1, 1),
            FileChange("src/old.ts", 0, 3, status="deleted"),
        ]
        annotations = {"src/pages/Home.ets": "modified: build"}

        text = "\n".join(render_review_summary(changes, annotations))

        self.assertIn("Summary:", text)
        self.assertIn("3 files, +6 -6", text)
        self.assertIn("src/pages/Home.ets", text)
        self.assertIn("modified", text)
        self.assertIn("build", text)
        self.assertIn("README.md", text)
        self.assertIn("src/old.ts", text)
        self.assertIn("deleted", text)


if __name__ == "__main__":
    unittest.main()
