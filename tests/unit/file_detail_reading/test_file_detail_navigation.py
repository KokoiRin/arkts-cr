import unittest

from cr.ui import file_detail_navigation


class FileDetailNavigationBehaviorTests(unittest.TestCase):
    def test_hunk_navigation_moves_between_rendered_hunk_headers(self):
        # Behavior: 当用户在File Detail中查看「hunk 导航 移动 between rendered hunk 头部」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: ArkTS page/component SamplePage",
            "  @@ -1,3 +1,4 @@",
            "  -old",
            "  +new",
            "  context",
            "  \033[36;1m@@ -20,2 +21,3 @@\033[0m",
            "  +next",
        ]

        first = file_detail_navigation.jump_to_hunk(lines, 0, "next")
        second = file_detail_navigation.jump_to_hunk(lines, first.scroll, "next")
        previous = file_detail_navigation.jump_to_hunk(lines, second.scroll, "previous")

        self.assertTrue(first.changed)
        self.assertEqual(first.scroll, 1)
        self.assertEqual(first.message, "Moved to hunk 1/2.")
        self.assertTrue(second.changed)
        self.assertEqual(second.scroll, 5)
        self.assertEqual(second.message, "Moved to hunk 2/2.")
        self.assertTrue(previous.changed)
        self.assertEqual(previous.scroll, 1)
        self.assertEqual(previous.message, "Moved to hunk 1/2.")

    def test_hunk_navigation_reports_edges_and_empty_diff(self):
        # Behavior: 当用户在File Detail中导航「hunk 导航 提示 edges and 空态 diff」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +1 @@",
            "  +new",
        ]

        first_edge = file_detail_navigation.jump_to_hunk(lines, 0, "previous")
        last_edge = file_detail_navigation.jump_to_hunk(lines, 0, "next")
        no_hunks = file_detail_navigation.jump_to_hunk(["File 1/1"], 3, "next")

        self.assertFalse(first_edge.changed)
        self.assertEqual(first_edge.scroll, 0)
        self.assertEqual(first_edge.message, "Already at first hunk.")
        self.assertFalse(last_edge.changed)
        self.assertEqual(last_edge.scroll, 0)
        self.assertEqual(last_edge.message, "Already at last hunk.")
        self.assertFalse(no_hunks.changed)
        self.assertEqual(no_hunks.scroll, 3)
        self.assertEqual(no_hunks.message, "No diff hunks in current file.")

    def test_hunk_navigation_clamps_scroll_to_visible_window(self):
        # Behavior: 当用户在File Detail中导航「hunk 导航 clamps scroll to 可见 window」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  context",
            "  context",
            "  @@ -50 +50 @@",
            "  +new",
        ]

        result = file_detail_navigation.jump_to_hunk(
            lines,
            0,
            "next",
            max_scroll=1,
        )

        self.assertTrue(result.changed)
        self.assertEqual(result.scroll, 1)
        self.assertEqual(result.message, "Moved to hunk 1/1.")

    def test_active_hunk_line_uses_nearest_rendered_hunk_header(self):
        # Behavior: 当用户在File Detail中查看「active hunk 行 使用 nearest rendered hunk 头部」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1,3 +4,4 @@",
            "  +first",
            "  context",
            "  \033[36;1m@@ -20,2 +31,3 @@\033[0m",
            "  +second",
        ]

        before_first = file_detail_navigation.active_hunk_new_line(lines, 0)
        second = file_detail_navigation.active_hunk_new_line(lines, 5)
        none = file_detail_navigation.active_hunk_new_line(["File 1/1"], 0)

        self.assertEqual(before_first, 4)
        self.assertEqual(second, 31)
        self.assertIsNone(none)

    def test_current_new_line_ignores_deleted_and_metadata_rows(self):
        # Behavior: 当用户在File Detail中执行操作「当前 new 行 忽略 已删除 and metadata rows」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1,2 +10,2 @@",
            "     1   10 | context",
            "     \033[32m11 | +added\033[0m",
            "    2      | -deleted",
            "  purpose: sample",
        ]

        hunk_header = file_detail_navigation.current_new_line(lines, 0)
        context_line = file_detail_navigation.current_new_line(lines, 1)
        added_line = file_detail_navigation.current_new_line(lines, 2)
        deleted_line = file_detail_navigation.current_new_line(lines, 3)
        metadata_line = file_detail_navigation.current_new_line(lines, 4)
        out_of_range = file_detail_navigation.current_new_line(lines, 99)

        self.assertEqual(hunk_header, 10)
        self.assertEqual(context_line, 10)
        self.assertEqual(added_line, 11)
        self.assertIsNone(deleted_line)
        self.assertIsNone(metadata_line)
        self.assertIsNone(out_of_range)

    def test_current_changed_row_distinguishes_added_and_deleted_rows(self):
        # Behavior: 当用户在File Detail中执行操作「当前 changed row distinguishes added and 已删除 rows」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1,2 +10,2 @@",
            "     1   10 | context",
            "     \033[32m11 | +added\033[0m",
            "    2      | -deleted",
        ]

        added = file_detail_navigation.current_changed_row(lines, 2)
        deleted = file_detail_navigation.current_changed_row(lines, 3)
        context = file_detail_navigation.current_changed_row(lines, 1)
        out_of_range = file_detail_navigation.current_changed_row(lines, 99)

        self.assertIsNotNone(added)
        self.assertEqual(added.kind, "added")
        self.assertIsNone(added.old_line)
        self.assertEqual(added.new_line, 11)
        self.assertEqual(added.text, "   11 | +added")
        self.assertIsNotNone(deleted)
        self.assertEqual(deleted.kind, "deleted")
        self.assertEqual(deleted.old_line, 2)
        self.assertIsNone(deleted.new_line)
        self.assertEqual(deleted.text, "  2      | -deleted")
        self.assertIsNone(context)
        self.assertIsNone(out_of_range)

    def test_active_hunk_extracts_sanitized_diff_lines_and_position(self):
        # Behavior: 当用户在File Detail中查看「active hunk 提取 sanitized diff 行 and position」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1,3 +4,4 @@",
            "     1    4 | context",
            "       \033[32m5 | +first\033[0m",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        first = file_detail_navigation.active_hunk(lines, 0)
        second = file_detail_navigation.active_hunk(lines, 5)
        none = file_detail_navigation.active_hunk(["File 1/1"], 0)

        self.assertIsNotNone(first)
        self.assertEqual(first.new_line, 4)
        self.assertEqual(first.index, 1)
        self.assertEqual(first.total, 2)
        self.assertEqual(
            first.lines,
            [
                "@@ -1,3 +4,4 @@",
                "   1    4 | context",
                "     5 | +first",
            ],
        )
        self.assertIsNotNone(second)
        self.assertEqual(second.new_line, 31)
        self.assertEqual(second.index, 2)
        self.assertEqual(second.total, 2)
        self.assertEqual(
            second.lines,
            [
                "@@ -20,2 +31,3 @@",
                "  20   31 | context",
                "        32 | +second",
            ],
        )
        self.assertIsNone(none)

    def test_file_detail_find_matches_rendered_text_without_ansi_styles(self):
        # Behavior: 当用户在File Detail中查看「File Detail find 匹配 rendered text 不包含 ansi styles」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1 +1 @@",
            "       1 | context",
            "       \033[32m2 | +TargetValue\033[0m",
        ]

        result = file_detail_navigation.find_text(lines, "targetvalue")
        empty = file_detail_navigation.find_text(lines, "   ")
        missing = file_detail_navigation.find_text(lines, "owner")

        self.assertEqual(result.scroll, 3)
        self.assertEqual(result.message, 'Found "targetvalue" at line 4.')
        self.assertTrue(result.found)
        self.assertEqual(empty.scroll, 0)
        self.assertEqual(empty.message, "Enter text to find.")
        self.assertFalse(empty.found)
        self.assertEqual(missing.scroll, 0)
        self.assertEqual(missing.message, 'No matches for "owner".')
        self.assertFalse(missing.found)

    def test_repeated_file_detail_find_wraps_in_both_directions(self):
        # Behavior: 当用户在File Detail中执行操作「repeated File Detail find wraps in both directions」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  target first",
            "  context",
            "  Target second",
            "  context",
            "  target third",
        ]

        next_result = file_detail_navigation.find_next_text(
            lines,
            "target",
            1,
            "next",
        )
        next_wrap = file_detail_navigation.find_next_text(
            lines,
            "target",
            4,
            "next",
        )
        previous_result = file_detail_navigation.find_next_text(
            lines,
            "target",
            3,
            "previous",
        )
        previous_wrap = file_detail_navigation.find_next_text(
            lines,
            "target",
            0,
            "previous",
        )

        self.assertEqual(next_result.scroll, 2)
        self.assertEqual(next_result.message, 'Found "target" at line 3.')
        self.assertEqual(next_wrap.scroll, 0)
        self.assertEqual(previous_result.scroll, 2)
        self.assertEqual(previous_wrap.scroll, 4)

    def test_changed_row_navigation_wraps_between_added_and_deleted_rows(self):
        # Behavior: 当用户在File Detail中导航「changed row 导航 wraps between added and 已删除 rows」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1,5 +1,5 @@",
            "     1    1 | context",
            "       \033[32m2 | +added\033[0m",
            "    3      | -deleted",
            "     4    3 | context",
            "          4 | +second",
        ]

        next_result = file_detail_navigation.jump_to_changed_row(lines, 1, "next")
        next_wrap = file_detail_navigation.jump_to_changed_row(lines, 5, "next")
        previous_result = file_detail_navigation.jump_to_changed_row(
            lines,
            4,
            "previous",
        )
        previous_wrap = file_detail_navigation.jump_to_changed_row(
            lines,
            1,
            "previous",
        )
        none = file_detail_navigation.jump_to_changed_row(
            ["File 1/1", "  @@ -1 +1 @@", "     1    1 | context"],
            0,
            "next",
        )

        self.assertEqual(next_result.scroll, 2)
        self.assertEqual(next_result.message, "Moved to change 1/3.")
        self.assertEqual(next_wrap.scroll, 2)
        self.assertEqual(previous_result.scroll, 3)
        self.assertEqual(previous_wrap.scroll, 5)
        self.assertFalse(none.changed)
        self.assertEqual(none.message, "No changed rows in current file.")


if __name__ == "__main__":
    unittest.main()
