import unittest
from unittest.mock import patch

from cr.review.data import build_review_data
from cr.vcs.git import FileChange


class ReviewDataTests(unittest.TestCase):
    def test_build_review_data_attaches_matching_review_notes(self):
        change = FileChange("src/Sample.ts", 2, 1)

        with patch("cr.review.data.git.first_changed_line", return_value=3):
            with patch(
                "cr.review.data.git.file_diff",
                return_value="@@ -1 +1 @@\n-old\n+new\n",
            ):
                data = build_review_data(
                    [change],
                    review_notes={
                        "src/Sample.ts": "check lifecycle edge case",
                        "docs/Other.md": "not in copied prompt",
                    },
                )

        self.assertEqual(
            data["files"][0]["review_note"],
            "check lifecycle edge case",
        )
        self.assertNotIn("docs/Other.md", str(data))


if __name__ == "__main__":
    unittest.main()
