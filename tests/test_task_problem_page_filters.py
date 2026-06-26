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

class TaskProblemPageFilterTests(unittest.TestCase):

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

if __name__ == "__main__":
    unittest.main()
