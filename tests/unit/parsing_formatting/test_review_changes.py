import unittest

from cr.review.changes import format_counts
from cr.vcs.git import FileChange


class ReviewChangeFormattingTests(unittest.TestCase):
    def test_format_counts_handles_binary_stats(self):
        # Behavior: 当系统处理产品行为的changes、format、counts、handles时，系统应统计出正确结果 [Requirement: TODO]
        self.assertEqual(format_counts(FileChange("asset.bin", None, None)), "+? -?")


if __name__ == "__main__":
    unittest.main()
