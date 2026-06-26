import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from cr.ui.browser import BrowserCommandExecutor, BrowserFrame, BrowserState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class SelectedDiffCommandTests(unittest.TestCase):

    def test_browser_command_executor_copies_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ) as copy_diff:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy diff"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy_diff.assert_called_once_with(state, args)
        self.assertIn("Copied diff for src/Sample.ts", output.getvalue())

    def test_browser_command_executor_copies_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ):
            result = executor.execute(parse_browser_command("copy diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Copied diff for src/Sample.ts", state.status_message)

    def test_browser_command_executor_saves_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to tmp/current.md",
        ) as save_diff:
            with redirect_stdout(output):
                result = executor.execute(
                    parse_browser_command("save diff tmp/current.md")
                )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        save_diff.assert_called_once_with(state, args, "tmp/current.md")
        self.assertIn(
            "Saved diff for src/Sample.ts to tmp/current.md",
            output.getvalue(),
        )

    def test_browser_command_executor_saves_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to .cr/handoff/review-diff.md",
        ):
            result = executor.execute(parse_browser_command("save diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Saved diff for src/Sample.ts", state.status_message)
