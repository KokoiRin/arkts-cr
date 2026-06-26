import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
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


class ProblemContextEmptyFailureCommandTests(unittest.TestCase):

    def test_browser_command_executor_reports_empty_problem_context_copy(self):
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
            result = executor.execute(parse_browser_command("copy problem context"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No problem context to copy.", state.status_message)
    def test_browser_command_executor_reports_missing_problem_context_source(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Missing.ets",
                source_file_line=2,
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
                    result = executor.execute(
                        parse_browser_command("copy problem context")
                    )

        self.assertTrue(result.handled)
        copy_text.assert_not_called()
        self.assertIn("Source file not found.", state.status_message)
    def test_browser_command_executor_reports_empty_problem_context_save(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.handoff_module.save_problem_context_text") as save_text:
            result = executor.execute(parse_browser_command("save problem context"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        save_text.assert_not_called()
        self.assertIn("No problem context to save.", state.status_message)
    def test_browser_command_executor_reports_problem_context_save_failure(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=4,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            failure = handoff_module.HandoffSaveResult(
                repo / "blocked" / "problem.md",
                "blocked/problem.md",
                "Could not save problem context to blocked/problem.md: denied",
            )
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.handoff_module.save_problem_context_text",
                    return_value=failure,
                ):
                    result = executor.execute(
                        parse_browser_command("save problem context blocked/problem.md")
                    )

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Foo.ets")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 4)
        self.assertIn(
            "Could not save problem context to blocked/problem.md: denied",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
