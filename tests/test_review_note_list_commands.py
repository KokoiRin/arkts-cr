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


class ReviewNoteListCommandTests(unittest.TestCase):
    def test_browser_command_executor_shows_review_notes_without_navigation(self):
        # Behavior: 当用户在review note遇到缺少前置条件、评审备注、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            review_notes={
                "src/First.ts": "check lifecycle edge case",
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

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("notes"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertIsNone(state.task)
        text = output.getvalue()
        self.assertIn("Review notes:", text)
        self.assertIn("1. src/First.ts: check lifecycle edge case", text)
        self.assertIn("2. docs/Old.md: stale follow-up", text)
    def test_browser_command_executor_filters_review_notes_without_navigation(self):
        # Behavior: 当用户在review note遇到缺少前置条件、评审备注、导航时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            review_notes={
                "src/First.ts": "check lifecycle edge case",
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

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("notes lifecycle"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertIsNone(state.task)
        text = output.getvalue()
        self.assertIn('Review notes matching "lifecycle":', text)
        self.assertIn("1. src/First.ts: check lifecycle edge case", text)
        self.assertIn("2. docs/Old.md: stale lifecycle follow-up", text)
        self.assertNotIn("src/Second.ts", text)
    def test_browser_command_executor_filters_review_notes_by_path_case_insensitive(self):
        # Behavior: 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/SampleView.ts", 1, 0)],
            review_notes={"src/SampleView.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("notes sample"))

        self.assertTrue(result.handled)
        self.assertIn("src/SampleView.ts", output.getvalue())
    def test_browser_command_executor_shows_empty_filtered_review_notes(self):
        # Behavior: 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
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

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("notes owner"))

        self.assertTrue(result.handled)
        self.assertIn('Review notes matching "owner": none', output.getvalue())
    def test_browser_command_executor_shows_review_notes_in_raw_status(self):
        # Behavior: 当用户在review note中展示评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        frame = BrowserFrame()
        state = BrowserState(
            [FileChange("src/First.ts", 1, 0)],
            selected=0,
            page=BrowserPage.FILE_DETAIL,
            review_notes={"src/First.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("notes", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertIsNone(state.task)
        self.assertTrue(frame.dirty)
        self.assertIn("Review notes:", state.status_message)
        self.assertIn("src/First.ts: check lifecycle edge case", state.status_message)
    def test_browser_command_executor_filters_review_notes_in_raw_status(self):
        # Behavior: 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        frame = BrowserFrame()
        state = BrowserState(
            [FileChange("src/First.ts", 1, 0)],
            review_notes={"src/First.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("notes lifecycle", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn('Review notes matching "lifecycle":', state.status_message)
        self.assertIn("src/First.ts: check lifecycle edge case", state.status_message)

if __name__ == "__main__":
    unittest.main()
