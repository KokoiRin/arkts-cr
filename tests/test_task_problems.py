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


class TaskProblemBrowserPageTests(unittest.TestCase):
    def test_browser_command_executor_opens_task_problems_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.TASK_OUTPUT,
            problem_selected=3,
            problem_scroll=4,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.problem_scroll, 0)

        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)

    def test_browser_command_executor_filters_task_problems_by_severity(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            problem_selected=3,
            problem_scroll=4,
            problem_sort="severity",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        show_errors = executor.execute(parse_browser_command("problems errors"))
        filter_after_errors = state.problem_filter
        selected_after_errors = state.problem_selected
        scroll_after_errors = state.problem_scroll
        clear_filter = executor.execute(parse_browser_command("problems all"))

        self.assertTrue(show_errors.handled)
        self.assertTrue(show_errors.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(filter_after_errors, "error")
        self.assertEqual(selected_after_errors, 0)
        self.assertEqual(scroll_after_errors, 0)
        self.assertEqual(state.problem_sort, "severity")
        self.assertTrue(clear_filter.handled)
        self.assertTrue(clear_filter.needs_redraw)
        self.assertEqual(state.problem_filter, "")
        self.assertEqual(state.problem_sort, "severity")

    def test_browser_command_executor_filters_task_problems_by_query(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            problem_filter="error",
            problem_sort="severity",
            problem_selected=3,
            problem_scroll=4,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_query = executor.execute(parse_browser_command("problems find Foo"))
        query_after_set = state.problem_query
        selected_after_set = state.problem_selected
        scroll_after_set = state.problem_scroll
        clear_query = executor.execute(parse_browser_command("problems clear find"))

        self.assertTrue(set_query.handled)
        self.assertTrue(set_query.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(query_after_set, "Foo")
        self.assertEqual(selected_after_set, 0)
        self.assertEqual(scroll_after_set, 0)
        self.assertEqual(state.problem_filter, "error")
        self.assertEqual(state.problem_sort, "severity")
        self.assertTrue(clear_query.handled)
        self.assertTrue(clear_query.needs_redraw)
        self.assertEqual(state.problem_query, "")

    def test_browser_command_executor_sorts_task_problems_by_severity(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            problem_selected=3,
            problem_scroll=4,
            problem_filter="warning",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        sort_by_severity = executor.execute(
            parse_browser_command("problems sort severity")
        )
        sort_by_output = executor.execute(parse_browser_command("problems sort output"))

        self.assertTrue(sort_by_severity.handled)
        self.assertTrue(sort_by_severity.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_filter, "warning")
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.problem_scroll, 0)
        self.assertTrue(sort_by_output.handled)
        self.assertEqual(state.problem_sort, "output")

    def test_browser_command_executor_groups_task_problems_by_file(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.TASK_OUTPUT,
            problem_selected=3,
            problem_scroll=4,
            problem_filter="warning",
            problem_query="Foo",
            problem_sort="severity",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        group_by_file = executor.execute(parse_browser_command("problems group file"))
        group_none = executor.execute(parse_browser_command("problems group none"))

        self.assertTrue(group_by_file.handled)
        self.assertTrue(group_by_file.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertTrue(group_none.handled)
        self.assertEqual(state.problem_group, "none")
        self.assertEqual(state.problem_filter, "warning")
        self.assertEqual(state.problem_query, "Foo")
        self.assertEqual(state.problem_sort, "severity")
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.problem_scroll, 0)

    def test_browser_command_executor_moves_task_problem_selection(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                        "src/Three.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                down = executor.execute(parse_browser_command("down", raw_keys=True))
                selected_after_down = state.problem_selected
                end = executor.execute(parse_browser_command("end", raw_keys=True))
                selected_after_end = state.problem_selected
                home = executor.execute(parse_browser_command("home", raw_keys=True))

        self.assertTrue(down.needs_redraw)
        self.assertTrue(end.needs_redraw)
        self.assertTrue(home.needs_redraw)
        self.assertEqual(selected_after_down, 1)
        self.assertEqual(selected_after_end, 2)
        self.assertEqual(state.problem_selected, 0)

    def test_browser_command_executor_jumps_to_next_task_problem_file(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/One.ets:2:1 warning",
                        "src/Two.ets:3:1 error",
                        "src/Three.ets:4:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("next problem file"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 2)

    def test_browser_command_executor_jumps_to_previous_task_problem_file(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=4,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                        "src/Two.ets:3:1 warning",
                        "src/Three.ets:4:1 error",
                        "src/Three.ets:5:1 warning",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("prev problem file"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.problem_selected, 1)

    def test_browser_command_executor_jumps_between_visible_task_problem_files(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets", "Three.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_filter="error",
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/Two.ets:2:1 warning W2: skipped",
                        "src/Three.ets:3:1 error E3: bad three",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("next problem file"))

        self.assertTrue(result.handled)
        self.assertEqual(state.problem_selected, 1)

    def test_browser_command_executor_keeps_task_problem_selection_at_file_edges(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_result = executor.execute(parse_browser_command("next problem file"))
                next_message = state.status_message
                selected_after_next = state.problem_selected
                state.problem_selected = 0
                prev_result = executor.execute(parse_browser_command("prev problem file"))
                previous_message = state.status_message

        self.assertTrue(next_result.handled)
        self.assertTrue(prev_result.handled)
        self.assertEqual(selected_after_next, 1)
        self.assertIn("已经在最后一个问题文件。", next_message)
        self.assertEqual(state.problem_selected, 0)
        self.assertIn("已经在第一个问题文件。", previous_message)

    def test_browser_command_executor_opens_selected_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:22:4 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(parse_browser_command("enter", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        open_path.assert_called_once_with(second, 22, "editor {fileline}")
        self.assertIn("Opened problem src/Two.ets:22", state.status_message)

    def test_browser_command_executor_opens_filtered_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_filter="warning",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad",
                        "src/Two.ets:22:4 warning W1: noisy",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(parse_browser_command("enter", raw_keys=True))

        self.assertTrue(result.handled)
        open_path.assert_called_once_with(second, 22, "editor {fileline}")
        self.assertIn("Opened problem src/Two.ets:22", state.status_message)

    def test_browser_command_executor_opens_grouped_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_group="file",
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:22:4 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(parse_browser_command("enter", raw_keys=True))

        self.assertTrue(result.handled)
        open_path.assert_called_once_with(second, 22, "editor {fileline}")
        self.assertIn("Opened problem src/Two.ets:22", state.status_message)

    def test_browser_command_executor_opens_queried_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_query="noisy",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad",
                        "src/Two.ets:22:4 error E2: noisy",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(parse_browser_command("enter", raw_keys=True))

        self.assertTrue(result.handled)
        open_path.assert_called_once_with(second, 22, "editor {fileline}")
        self.assertIn("Opened problem src/Two.ets:22", state.status_message)


class TaskProblemCopyAndSaveCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_selected_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                problem_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:22:4 error: bad call",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.problem_scroll, 1)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Two.ets:22:4", copied)
        self.assertIn("bad call", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied task problem.", state.status_message)

    def test_browser_command_executor_copies_source_file_current_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:2:1", copied)
        self.assertIn("Severity: error", copied)
        self.assertIn("Code: TS123", copied)
        self.assertIn("bad value", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied source problem.", state.status_message)

    def test_browser_command_executor_does_not_copy_stale_source_file_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No current source problem to copy.", state.status_message)

    def test_browser_command_executor_copies_file_detail_current_row_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:4:1 error E1: bad one",
                        "src/Two.ets:2:1 error E2: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text",
                        return_value=None,
                    ) as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy problem", raw_keys=True)
                        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/One.ets:4:1", copied)
        self.assertIn("bad one", copied)
        self.assertNotIn("src/Two.ets", copied)
        self.assertNotIn("bad two", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.problem_selected, 1)
        self.assertIn("Copied file problem src/One.ets:4.", state.status_message)

    def test_browser_command_executor_does_not_copy_file_detail_row_without_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Two.ets:2:1 error E2: bad two"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy problem", raw_keys=True)
                        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("No current file problem to copy.", state.status_message)

    def test_browser_command_executor_saves_selected_task_problem_default_path(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                problem_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error TS1: first bad",
                        "src/Two.ets:1:1 warning TS2: second bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save problem"))

            saved = repo / ".cr" / "handoff" / "task-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.problem_scroll, 1)
        self.assertIn("src/Two.ets:1:1", text)
        self.assertIn("Severity: warning", text)
        self.assertIn("Code: TS2", text)
        self.assertIn("second bad", text)
        self.assertIn(
            "Saved task problem to .cr/handoff/task-problem.md.",
            state.status_message,
        )

    def test_browser_command_executor_saves_source_file_current_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(
                    parse_browser_command("save problem tmp/source-problem.md")
                )

            saved = repo / "tmp" / "source-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Foo.ets:2:1", text)
        self.assertIn("Severity: error", text)
        self.assertIn("Code: TS123", text)
        self.assertIn("bad value", text)
        self.assertIn(
            "Saved source problem to tmp/source-problem.md.",
            state.status_message,
        )

    def test_browser_command_executor_does_not_save_stale_source_file_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(
                    parse_browser_command("save problem tmp/source-problem.md")
                )

            saved = repo / "tmp" / "source-problem.md"

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertFalse(saved.exists())
        self.assertIn("No current source problem to save.", state.status_message)

    def test_browser_command_executor_saves_file_detail_current_row_task_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text(
                "one\ntwo\nthree\nfour\n",
                encoding="utf-8",
            )
            (source_dir / "Two.ets").write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:4:1 warning W1: warn one",
                        "src/Two.ets:2:1 error E2: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/One.ets",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command(
                            "save problem tmp/file-detail-problem.md",
                            raw_keys=True,
                        )
                    )

            saved = repo / "tmp" / "file-detail-problem.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/One.ets:4:1", text)
        self.assertIn("Severity: warning", text)
        self.assertIn("Code: W1", text)
        self.assertIn("warn one", text)
        self.assertNotIn("src/Two.ets", text)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn(
            "Saved file problem src/One.ets:4 to tmp/file-detail-problem.md.",
            state.status_message,
        )

    def test_browser_command_executor_copies_all_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_OUTPUT,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:22:4 warning",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Task problems", copied)
        self.assertIn("1. src/One.ets:1:1", copied)
        self.assertIn("2. src/Two.ets:22:4", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied 2 task problems.", state.status_message)

    def test_browser_command_executor_copies_filtered_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_filter="error",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad",
                        "src/Two.ets:22:4 warning W1: noisy",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/One.ets:1:1", copied)
        self.assertNotIn("src/Two.ets", copied)
        self.assertIn("Copied 1 task problems.", state.status_message)

    def test_browser_command_executor_copies_selected_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/One.ets:2:1 warning W2: warn one",
                        "src/Two.ets:3:1 error E3: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy file problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("1. src/One.ets:1:1", copied)
        self.assertIn("2. src/One.ets:2:1", copied)
        self.assertNotIn("src/Two.ets", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied 2 task problems for src/One.ets.", state.status_message)

    def test_browser_command_executor_copies_visible_selected_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_filter="error",
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/One.ets:2:1 warning W2: warn one",
                        "src/Two.ets:3:1 error E3: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy file problems"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/One.ets:1:1", copied)
        self.assertNotIn("src/One.ets:2:1", copied)
        self.assertNotIn("src/Two.ets", copied)
        self.assertIn("Copied 1 task problems for src/One.ets.", state.status_message)

    def test_browser_command_executor_copies_file_detail_current_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("sample", encoding="utf-8")
            (source_dir / "Two.ets").write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/One.ets:2:1 warning W2: warn one",
                        "src/Two.ets:3:1 error E3: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy file problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("1. src/One.ets:1:1", copied)
        self.assertIn("2. src/One.ets:2:1", copied)
        self.assertNotIn("src/Two.ets", copied)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("Copied 2 task problems for src/One.ets.", state.status_message)

    def test_browser_command_executor_reports_file_detail_current_file_without_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("sample", encoding="utf-8")
            (source_dir / "Two.ets").write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Two.ets:3:1 error E3: bad two"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy file problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No task problems for src/One.ets.", state.status_message)

    def test_browser_command_executor_saves_file_detail_current_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("sample", encoding="utf-8")
            (source_dir / "Two.ets").write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad one",
                        "src/Two.ets:3:1 error E3: bad two",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(
                    parse_browser_command("save file problems tmp/one-problems.md")
                )

            saved = repo / "tmp" / "one-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertIn("1. src/One.ets:1:1 [ERROR E1]", text)
        self.assertNotIn("src/Two.ets", text)
        self.assertIn(
            "Saved 1 task problems for src/One.ets to tmp/one-problems.md.",
            state.status_message,
        )

    def test_browser_command_executor_reports_empty_selected_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy file problems"))

        self.assertTrue(result.handled)
        copy_text.assert_not_called()
        self.assertIn("No task problems to copy.", state.status_message)

    def test_browser_command_executor_copies_queried_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_query="noisy",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error E1: bad",
                        "src/Two.ets:22:4 warning W1: noisy",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Two.ets:22:4", copied)
        self.assertNotIn("src/One.ets", copied)
        self.assertIn("Copied 1 task problems.", state.status_message)

    def test_browser_command_executor_copies_sorted_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for name in ("One.ets", "Two.ets"):
                (repo / "src").mkdir(exist_ok=True)
                (repo / "src" / name).write_text("sample", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_sort="severity",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 warning W1: noisy",
                        "src/Two.ets:22:4 error E1: bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertLess(copied.index("src/Two.ets:22:4"), copied.index("src/One.ets:1:1"))
        self.assertIn("1. src/Two.ets:22:4", copied)
        self.assertIn("2. src/One.ets:1:1", copied)

    def test_browser_command_executor_saves_task_problems_default_path(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error TS1: first bad",
                        "src/Two.ets:1:1 warning TS2: second bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save problems"))

            saved = repo / ".cr" / "handoff" / "task-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertIn("1. src/One.ets:1:1 [ERROR TS1]", text)
        self.assertIn("2. src/Two.ets:1:1 [WARNING TS2]", text)
        self.assertIn(
            "Saved 2 task problems to .cr/handoff/task-problems.md.",
            state.status_message,
        )

    def test_browser_command_executor_saves_file_task_problems_requested_path(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("two\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error TS1: first bad",
                        "src/Two.ets:1:1 error TS2: second bad",
                        "src/Two.ets:1:1 warning TS3: third bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(
                    parse_browser_command("save file problems tmp/two-problems.md")
                )

            saved = repo / "tmp" / "two-problems.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("# Task problems", text)
        self.assertNotIn("src/One.ets", text)
        self.assertIn("1. src/Two.ets:1:1 [ERROR TS2]", text)
        self.assertIn("2. src/Two.ets:1:1 [WARNING TS3]", text)
        self.assertIn(
            "Saved 2 task problems for src/Two.ets to tmp/two-problems.md.",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
