import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import task_problems
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace

class TaskProblemsBehaviorTests(unittest.TestCase):

    def test_extracts_repo_local_problem_anchors_from_task_output(self):
        # Behavior: 当用户在Task Problems中解析「提取 仓库 本地 问题 anchors from Task Output」时，系统应产出正确的结构化结果 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("sample", encoding="utf-8")

            problems = task_problems.extract_task_problems(
                repo,
                [
                    "\033[31msrc/Foo.ets:12:3 error: bad call\033[0m",
                    f"{source}:20 warning: check this",
                ],
            )

        self.assertEqual(len(problems), 2)
        self.assertEqual(problems[0].path, "src/Foo.ets")
        self.assertEqual(problems[0].line, 12)
        self.assertEqual(problems[0].column, 3)
        self.assertIn("bad call", problems[0].summary)
        self.assertEqual(problems[1].path, "src/Foo.ets")
        self.assertEqual(problems[1].line, 20)
        self.assertIsNone(problems[1].column)

    def test_extracts_diagnostic_facts_from_common_problem_lines(self):
        # Behavior: 当用户在Task Problems中查看「提取 diagnostic facts from common 问题 行」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("sample", encoding="utf-8")

            problems = task_problems.extract_task_problems(
                repo,
                [
                    "src/Foo.ets:12:3 error TS2322: bad call",
                    "src/Foo.ets:20 warning [W001]: check this",
                    "src/Foo.ets:30 plain anchor only",
                    "ERROR src/Foo.ets:40 [E123]: prefix bad",
                    "src/Foo.ets:50 error bad Foo1",
                ],
            )

        self.assertEqual(problems[0].severity, "error")
        self.assertEqual(problems[0].code, "TS2322")
        self.assertEqual(problems[0].message, "bad call")
        self.assertEqual(problems[1].severity, "warning")
        self.assertEqual(problems[1].code, "W001")
        self.assertEqual(problems[1].message, "check this")
        self.assertIsNone(problems[2].severity)
        self.assertIsNone(problems[2].code)
        self.assertEqual(problems[2].message, "")
        self.assertIn("plain anchor only", problems[2].summary)
        self.assertEqual(problems[3].severity, "error")
        self.assertEqual(problems[3].code, "E123")
        self.assertEqual(problems[3].message, "prefix bad")
        self.assertEqual(problems[4].severity, "error")
        self.assertIsNone(problems[4].code)
        self.assertEqual(problems[4].message, "bad Foo1")

    def test_severity_filter_preserves_original_problem_order(self):
        # Behavior: 当用户在Task Problems中过滤「severity 过滤 保留 original 问题 order」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        problems = [
            task_problems.TaskProblem("src/A.ets", 1, None, "a", 1, severity="warning"),
            task_problems.TaskProblem("src/B.ets", 2, None, "b", 2, severity="error"),
            task_problems.TaskProblem("src/C.ets", 3, None, "c", 3),
            task_problems.TaskProblem("src/D.ets", 4, None, "d", 4, severity="error"),
        ]

        errors = task_problems.filter_task_problems(problems, "error")
        all_problems = task_problems.filter_task_problems(problems, "")

        self.assertEqual([problem.path for problem in errors], ["src/B.ets", "src/D.ets"])
        self.assertEqual(all_problems, problems)

    def test_severity_sort_buckets_problems_without_reordering_each_bucket(self):
        # Behavior: 当用户在Task Problems中排序或选择「severity 排序 buckets 问题 不包含 reordering each bucket」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        problems = [
            task_problems.TaskProblem("src/W1.ets", 1, None, "w1", 1, severity="warning"),
            task_problems.TaskProblem("src/E1.ets", 2, None, "e1", 2, severity="error"),
            task_problems.TaskProblem("src/U.ets", 3, None, "u", 3),
            task_problems.TaskProblem("src/N.ets", 4, None, "n", 4, severity="note"),
            task_problems.TaskProblem("src/E2.ets", 5, None, "e2", 5, severity="error"),
            task_problems.TaskProblem("src/I.ets", 6, None, "i", 6, severity="info"),
        ]

        severity_sorted = task_problems.sort_task_problems(problems, "severity")
        output_sorted = task_problems.sort_task_problems(problems, "output")
        unknown_sorted = task_problems.sort_task_problems(problems, "anything")

        self.assertEqual(
            [problem.path for problem in severity_sorted],
            [
                "src/E1.ets",
                "src/E2.ets",
                "src/W1.ets",
                "src/I.ets",
                "src/N.ets",
                "src/U.ets",
            ],
        )
        self.assertEqual(output_sorted, problems)
        self.assertEqual(unknown_sorted, problems)

    def test_text_query_matches_path_summary_severity_code_or_message(self):
        # Behavior: 当用户在Task Problems中执行操作「文本查询 匹配 路径 summary severity code or message」时，系统应产出正确的结构化结果 [Requirement: TODO]
        problems = [
            task_problems.TaskProblem(
                "src/Foo.ets",
                12,
                3,
                "src/Foo.ets:12:3 error TS2322: bad call",
                1,
                severity="error",
                code="TS2322",
                message="bad call",
            ),
            task_problems.TaskProblem(
                "src/Bar.ets",
                8,
                None,
                "src/Bar.ets:8 warning W001: noisy lifecycle",
                2,
                severity="warning",
                code="W001",
                message="noisy lifecycle",
            ),
            task_problems.TaskProblem("src/Baz.ets", 3, None, "plain anchor", 3),
        ]

        by_path = task_problems.filter_task_problems_by_query(problems, "foo")
        by_summary = task_problems.filter_task_problems_by_query(problems, "plain")
        by_severity = task_problems.filter_task_problems_by_query(problems, "WARNING")
        by_code = task_problems.filter_task_problems_by_query(problems, "ts2322")
        by_message = task_problems.filter_task_problems_by_query(problems, "life")
        all_problems = task_problems.filter_task_problems_by_query(problems, "  ")

        self.assertEqual([problem.path for problem in by_path], ["src/Foo.ets"])
        self.assertEqual([problem.path for problem in by_summary], ["src/Baz.ets"])
        self.assertEqual([problem.path for problem in by_severity], ["src/Bar.ets"])
        self.assertEqual([problem.path for problem in by_code], ["src/Foo.ets"])
        self.assertEqual([problem.path for problem in by_message], ["src/Bar.ets"])
        self.assertEqual(all_problems, problems)

    def test_severity_count_label_summarizes_visible_problem_set(self):
        # Behavior: 当用户在Task Problems中执行操作「severity count label summarizes 可见 问题 set」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        problems = [
            task_problems.TaskProblem("src/A.ets", 1, None, "a", 1, severity="warning"),
            task_problems.TaskProblem("src/B.ets", 2, None, "b", 2, severity="error"),
            task_problems.TaskProblem("src/C.ets", 3, None, "c", 3),
            task_problems.TaskProblem("src/D.ets", 4, None, "d", 4, severity="error"),
            task_problems.TaskProblem("src/E.ets", 5, None, "e", 5, severity="note"),
        ]

        label = task_problems.problem_severity_count_label(problems)
        empty = task_problems.problem_severity_count_label([])

        self.assertEqual(label, "2 errors, 1 warning, 1 note, 1 unknown")
        self.assertEqual(empty, "")

    def test_problem_extraction_ignores_urls_missing_files_and_outside_paths(self):
        # Behavior: 当用户在Task Problems中解析「问题 extraction 忽略 urls 缺失 文件 and outside 路径」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            outside = Path(tmp).parent / "Outside.ets"
            outside.write_text("sample", encoding="utf-8")
            try:
                problems = task_problems.extract_task_problems(
                    repo,
                    [
                        "https://example.com/file.ts:10:1",
                        "src/Missing.ets:7:2 error",
                        f"{outside}:3:1 outside",
                    ],
                )
            finally:
                outside.unlink(missing_ok=True)

        self.assertEqual(problems, [])

    def test_problem_handoff_text_preserves_diagnostic_facts(self):
        # Behavior: 当用户在Task Problems中恢复状态「问题 handoff text 保留 diagnostic facts」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        problems = [
            task_problems.TaskProblem(
                path="src/Foo.ets",
                line=12,
                column=3,
                summary="src/Foo.ets:12:3 error: bad call",
                output_line=1,
                severity="error",
                code="TS2322",
                message="bad call",
            ),
            task_problems.TaskProblem(
                path="src/Bar.ets",
                line=8,
                column=None,
                summary="src/Bar.ets:8 warning",
                output_line=2,
                severity="warning",
            ),
        ]

        selected = task_problems.problem_handoff_text(problems[0])
        all_text = task_problems.problems_handoff_text(problems)

        self.assertIn("src/Foo.ets:12:3", selected)
        self.assertIn("Severity: error", selected)
        self.assertIn("Code: TS2322", selected)
        self.assertIn("Message: bad call", selected)
        self.assertIn("bad call", selected)
        self.assertIn("# Task problems", all_text)
        self.assertIn("1. src/Foo.ets:12:3 [ERROR TS2322]", all_text)
        self.assertIn("   Message: bad call", all_text)
        self.assertIn("2. src/Bar.ets:8", all_text)


if __name__ == "__main__":
    unittest.main()
