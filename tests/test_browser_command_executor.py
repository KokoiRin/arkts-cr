import unittest
from contextlib import redirect_stdout
from io import StringIO

from cr.ui.browser import (
    BrowserActionResult,
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
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


class BrowserCommandExecutorTests(unittest.TestCase):
    def test_browser_command_executor_reports_quit_intent(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("q"))

        self.assertEqual(result, BrowserActionResult(exit_code=0))

    def test_browser_command_executor_changes_page_and_requests_redraw(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("commands"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.COMMAND_PALETTE)

    def test_browser_command_executor_reports_unknown_command_feedback(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("wat"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Unknown command.", output.getvalue())

    def test_browser_command_executor_runs_forward_navigation(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("forward"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)

    def test_browser_command_executor_opens_page_help(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE, source_file_path="src/Foo.ets")
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("help"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.SOURCE_FILE)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
