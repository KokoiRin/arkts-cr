import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
from cr.ui import review_notes
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    _review_note_lines,
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


class ReviewNoteCopyCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_review_notes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool {text}")
        state = BrowserState(
            [
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/First.ts", 1, 0),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            review_notes={
                "src/First.ts": "first current note",
                "src/Second.ts": "second current note",
                "docs/Old.md": "stale follow-up",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy notes"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertIsNone(state.task)
        copy.assert_called_once_with(
            "\n".join(
                [
                    "Review notes:",
                    "1. src/Second.ts: second current note",
                    "2. src/First.ts: first current note",
                    "3. docs/Old.md: stale follow-up",
                ]
            ),
            "copy-tool {text}",
        )
        self.assertIn("Copied 3 review notes", output.getvalue())
    def test_browser_command_executor_copies_filtered_review_notes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool {text}")
        state = BrowserState(
            [
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/First.ts", 1, 0),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            review_notes={
                "src/First.ts": "first lifecycle note",
                "src/Second.ts": "ask owner about reset",
                "docs/Old.md": "stale lifecycle follow-up",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy notes lifecycle"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertIsNone(state.task)
        copy.assert_called_once_with(
            "\n".join(
                [
                    'Review notes matching "lifecycle":',
                    "1. src/First.ts: first lifecycle note",
                    "2. docs/Old.md: stale lifecycle follow-up",
                ]
            ),
            "copy-tool {text}",
        )
        self.assertIn("Copied 2 matching review notes", output.getvalue())
    def test_browser_command_executor_does_not_copy_unmatched_review_notes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy notes owner"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy.assert_not_called()
        self.assertIn("No matching review notes to copy.", output.getvalue())
    def test_browser_command_executor_copies_filtered_review_notes_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        frame = BrowserFrame()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None):
            result = executor.execute(
                parse_browser_command("copy notes lifecycle", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn("Copied 1 matching review notes", state.status_message)
    def test_browser_command_executor_does_not_copy_empty_review_notes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy notes"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy.assert_not_called()
        self.assertIn("No review notes to copy.", output.getvalue())
    def test_browser_command_executor_reports_copy_review_notes_failures(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool {text}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.file_actions.copy_text",
            return_value="Copy failed (cli copy-tool): missing copy",
        ):
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("notes copy"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Copy failed (cli copy-tool): missing copy", output.getvalue())
    def test_browser_command_executor_copies_review_notes_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        frame = BrowserFrame()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None):
            result = executor.execute(parse_browser_command("copy notes", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn("Copied 1 review notes", state.status_message)

if __name__ == "__main__":
    unittest.main()
