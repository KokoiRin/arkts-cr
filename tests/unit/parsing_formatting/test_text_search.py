import unittest

from cr.ui import text_search


class TextSearchBehaviorTests(unittest.TestCase):
    def test_find_text_ignores_ansi_and_matches_case_insensitively_after_header(self):
        # Behavior: 当用户在底层解析与格式化中执行操作「find text 忽略 ansi and 匹配 case insensitively after 头部」时，系统应产出稳定、可读的格式化结果 [Requirement: TODO]
        result = text_search.find_text(
            ["Header", "compile ok", "\033[31mFAILED target\033[0m"],
            "failed",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.scroll, 1)
        self.assertEqual(result.message, 'Found "failed" at line 2.')

    def test_find_text_can_search_first_line_when_requested(self):
        # Behavior: 当用户在底层解析与格式化中执行操作「find text 可以 search first 行 when requested」时，系统应产出稳定、可读的格式化结果 [Requirement: TODO]
        result = text_search.find_text(
            ["FAILED header", "compile ok"],
            "failed",
            skip_first_line=False,
        )

        self.assertTrue(result.found)
        self.assertEqual(result.scroll, 0)
        self.assertEqual(result.message, 'Found "failed" at line 1.')

    def test_repeat_search_wraps_forward_and_backward(self):
        # Behavior: 当用户在底层解析与格式化中执行操作「repeat search wraps 前进 and backward」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        lines = ["Header", "target one", "context", "target two"]

        next_result = text_search.find_next_text(lines, "target", 0, "next")
        previous_result = text_search.find_next_text(lines, "target", 0, "previous")

        self.assertTrue(next_result.found)
        self.assertEqual(next_result.scroll, 2)
        self.assertEqual(next_result.message, 'Found "target" at line 3.')
        self.assertTrue(previous_result.found)
        self.assertEqual(previous_result.scroll, 2)
        self.assertEqual(previous_result.message, 'Found "target" at line 3.')

    def test_empty_query_and_missing_match_return_user_feedback(self):
        # Behavior: 当用户在底层解析与格式化中处理异常「空态 查询 and 缺失 match 返回 user feedback」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        empty = text_search.find_text(["Header", "body"], "")
        missing = text_search.find_next_text(["Header", "body"], "target", 0, "next")

        self.assertFalse(empty.found)
        self.assertEqual(empty.message, "Enter text to find.")
        self.assertFalse(missing.found)
        self.assertEqual(missing.message, 'No matches for "target".')


if __name__ == "__main__":
    unittest.main()
