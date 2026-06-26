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

    def test_browser_command_executor_steps_source_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:2:1 error",
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
                view_result = executor.execute(parse_browser_command("view problem"))
                next_result = executor.execute(parse_browser_command("next problem"))
                selected_after_next = state.problem_selected
                path_after_next = state.source_file_path
                line_after_next = state.source_file_line
                prev_result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(view_result.handled)
        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertEqual(selected_after_next, 1)
        self.assertEqual(path_after_next, "src/Two.ets")
        self.assertEqual(line_after_next, 2)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertTrue(prev_result.handled)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.source_file_path, "src/One.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)

    def test_browser_command_executor_views_selected_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
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
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)

    def test_browser_command_executor_views_sorted_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=0,
                problem_sort="severity",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 warning W1: noisy",
                        "src/Two.ets:2:1 error E1: bad",
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
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)

    def test_browser_command_executor_reports_no_task_problem_to_view(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertIn("No task problem to view.", state.status_message)


if __name__ == "__main__":
    unittest.main()
