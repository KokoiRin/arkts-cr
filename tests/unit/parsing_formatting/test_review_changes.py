import unittest

from cr.review.changes import format_counts
from cr.vcs.git import FileChange


class ReviewChangeFormattingTests(unittest.TestCase):
    def test_format_counts_handles_binary_stats(self):
        # Behavior: 当用户在底层解析与格式化中执行操作「format counts handles 二进制 stats」时，系统应产出稳定、可读的格式化结果 [Requirement: TODO]
        self.assertEqual(format_counts(FileChange("asset.bin", None, None)), "+? -?")


if __name__ == "__main__":
    unittest.main()
