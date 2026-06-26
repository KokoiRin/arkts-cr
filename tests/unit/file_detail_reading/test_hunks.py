import unittest

from cr.review.hunks import render_diff_hunks


class HunkRenderTests(unittest.TestCase):
    def test_renders_hunks_without_git_file_headers(self):
        # Behavior: 当用户在File Detail中查看「渲染 hunk 省略 Git 文件头」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        diff = """\
diff --git a/src/pages/Home.ets b/src/pages/Home.ets
index 1111111..2222222 100644
--- a/src/pages/Home.ets
+++ b/src/pages/Home.ets
@@ -3,5 +3,5 @@ struct Home {
   build() {
-    Text('hello')
+    Text('hello world')
   }
 }
"""

        lines = render_diff_hunks(diff)

        self.assertEqual(lines[0], "@@ -3,5 +3,5 @@ struct Home {")
        self.assertIn("   3    3 |   build() {", lines)
        self.assertIn("   4      | -    Text('hello')", lines)
        self.assertIn("        4 | +    Text('hello world')", lines)
        self.assertIn("   5    5 |   }", lines)
        self.assertFalse(any(line.startswith("diff --git") for line in lines))
        self.assertFalse(any(line.startswith("index ") for line in lines))

    def test_truncates_long_hunks(self):
        # Behavior: 当用户在File Detail中解析「截断 过长 hunk」时，系统应产出正确的结构化结果 [Requirement: TODO]
        diff = "@@ -1 +1 @@\n" + "\n".join(f"+line {index}" for index in range(5))

        lines = render_diff_hunks(diff, max_lines=3)

        self.assertEqual(lines[-1], "... 3 more diff lines")


if __name__ == "__main__":
    unittest.main()
