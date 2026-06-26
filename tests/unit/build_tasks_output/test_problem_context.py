import unittest

from cr.ui import problem_context


class ProblemContextBehaviorTests(unittest.TestCase):
    def test_problem_context_includes_problem_source_task_output_and_diff_sections(self):
        # Behavior: 当用户在Task Panel / Task Output中输出「Problem Context 包含 问题 源码 Task Output and diff sections」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        text = problem_context.problem_context_markdown(
            anchor="src/Foo.ets:5",
            problem_text="src/Foo.ets:5:1\nSeverity: error\nbad call",
            source_text="src/Foo.ets:5\n\n```text\n> 5  bad()\n```",
            diff_text="# File Diff: src/Foo.ets\n\n```diff\n+bad()\n```",
            task_output_text="```text\n> 8  src/Foo.ets:5:1 error bad call\n```",
        )
        no_diff = problem_context.problem_context_markdown(
            anchor="src/Foo.ets:5",
            problem_text="",
            source_text="src/Foo.ets:5\n\n```text\n> 5  bad()\n```",
            diff_text="",
        )

        self.assertIn("# Problem Context: src/Foo.ets:5", text)
        self.assertIn("## Problem", text)
        self.assertIn("Severity: error", text)
        self.assertIn("## Source", text)
        self.assertIn("> 5  bad()", text)
        self.assertIn("## Task Output", text)
        self.assertIn("> 8  src/Foo.ets:5:1 error bad call", text)
        self.assertIn("## Diff", text)
        self.assertIn("# File Diff: src/Foo.ets", text)
        self.assertNotIn("No diff in current review scope.", text)
        self.assertNotIn("## Task Output", no_diff)
        self.assertNotIn("## Problem", no_diff)
        self.assertIn("No diff in current review scope.", no_diff)


if __name__ == "__main__":
    unittest.main()
