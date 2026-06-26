import unittest

from cr.ui import text_search


class TextSearchBehaviorTests(unittest.TestCase):
    def test_find_text_ignores_ansi_and_matches_case_insensitively_after_header(self):
        result = text_search.find_text(
            ["Header", "compile ok", "\033[31mFAILED target\033[0m"],
            "failed",
        )

        self.assertTrue(result.found)
        self.assertEqual(result.scroll, 1)
        self.assertEqual(result.message, 'Found "failed" at line 2.')

    def test_find_text_can_search_first_line_when_requested(self):
        result = text_search.find_text(
            ["FAILED header", "compile ok"],
            "failed",
            skip_first_line=False,
        )

        self.assertTrue(result.found)
        self.assertEqual(result.scroll, 0)
        self.assertEqual(result.message, 'Found "failed" at line 1.')

    def test_repeat_search_wraps_forward_and_backward(self):
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
        empty = text_search.find_text(["Header", "body"], "")
        missing = text_search.find_next_text(["Header", "body"], "target", 0, "next")

        self.assertFalse(empty.found)
        self.assertEqual(empty.message, "Enter text to find.")
        self.assertFalse(missing.found)
        self.assertEqual(missing.message, 'No matches for "target".')


if __name__ == "__main__":
    unittest.main()
