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


class ReviewNotesTests(unittest.TestCase):
    def test_review_note_lines_order_current_changes_before_extra_notes(self):
        lines = review_notes.review_note_lines(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            {
                "docs/Old.md": "old note",
                "src/Second.ts": "second note",
                "src/First.ts": "first note",
            },
        )

        self.assertEqual(
            lines,
            [
                "Review notes:",
                "1. src/First.ts: first note",
                "2. src/Second.ts: second note",
                "3. docs/Old.md: old note",
            ],
        )

    def test_review_note_lines_filter_by_path_or_note_text(self):
        lines = review_notes.review_note_lines(
            [
                FileChange("src/SampleView.ts", 1, 0),
                FileChange("src/Other.ts", 1, 0),
            ],
            {
                "src/SampleView.ts": "ask owner",
                "src/Other.ts": "check lifecycle",
            },
            query="sample",
        )

        self.assertEqual(
            lines,
            [
                'Review notes matching "sample":',
                "1. src/SampleView.ts: ask owner",
            ],
        )

    def test_review_note_lines_show_empty_states(self):
        self.assertEqual(
            review_notes.review_note_lines([FileChange("src/Sample.ts", 1, 0)], {}),
            ["Review notes: none"],
        )
        self.assertEqual(
            review_notes.review_note_lines(
                [FileChange("src/Sample.ts", 1, 0)],
                {"src/Sample.ts": "check lifecycle"},
                query="owner",
            ),
            ['Review notes matching "owner": none'],
        )

    def test_copy_review_notes_copies_filtered_lines(self):
        copied: list[tuple[str, str | None]] = []

        def copy_text(text, copy_cmd=None):
            copied.append((text, copy_cmd))
            return None

        message = review_notes.copy_review_notes(
            [FileChange("src/Sample.ts", 1, 0)],
            {"src/Sample.ts": "check lifecycle"},
            query="lifecycle",
            copy_cmd="copy-tool",
            copy_text=copy_text,
        )

        self.assertEqual(message, "Copied 1 matching review notes")
        self.assertEqual(copied[0][1], "copy-tool")
        self.assertIn('Review notes matching "lifecycle":', copied[0][0])

    def test_copy_review_notes_skips_empty_or_unmatched_notes(self):
        copied: list[str] = []

        def copy_text(text, copy_cmd=None):
            copied.append(text)
            return None

        no_notes = review_notes.copy_review_notes(
            [FileChange("src/Sample.ts", 1, 0)],
            {},
            copy_text=copy_text,
        )
        no_matches = review_notes.copy_review_notes(
            [FileChange("src/Sample.ts", 1, 0)],
            {"src/Sample.ts": "check lifecycle"},
            query="owner",
            copy_text=copy_text,
        )

        self.assertEqual(no_notes, "No review notes to copy.")
        self.assertEqual(no_matches, "No matching review notes to copy.")
        self.assertEqual(copied, [])


class BrowserReviewNoteStateTests(unittest.TestCase):
    def test_browser_state_review_note_lines_order_current_changes_before_extra_notes(
        self,
    ):
        state = BrowserState(
            [
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/First.ts", 1, 0),
            ],
            review_notes={
                "docs/Zed.md": "last stale note",
                "src/First.ts": "first current note",
                "src/Second.ts": "second current note",
                "docs/Alpha.md": "first stale note",
            },
        )

        lines = _review_note_lines(state)

        self.assertEqual(
            lines,
            [
                "Review notes:",
                "1. src/Second.ts: second current note",
                "2. src/First.ts: first current note",
                "3. docs/Alpha.md: first stale note",
                "4. docs/Zed.md: last stale note",
            ],
        )

    def test_browser_state_review_note_lines_filter_by_note_and_path(self):
        state = BrowserState(
            [
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/SampleView.ts", 1, 0),
            ],
            review_notes={
                "src/SampleView.ts": "first current note",
                "src/Second.ts": "ask owner about reset",
                "docs/Old.md": "stale sample follow-up",
            },
        )

        self.assertEqual(
            _review_note_lines(state, query="sample"),
            [
                'Review notes matching "sample":',
                "1. src/SampleView.ts: first current note",
                "2. docs/Old.md: stale sample follow-up",
            ],
        )

    def test_browser_state_review_note_lines_filter_empty_state(self):
        self.assertEqual(
            _review_note_lines(
                BrowserState(
                    [FileChange("src/Sample.ts", 1, 0)],
                    review_notes={"src/Sample.ts": "check lifecycle edge case"},
                ),
                query="owner",
            ),
            ['Review notes matching "owner": none'],
        )

    def test_browser_state_review_note_lines_show_empty_state(self):
        self.assertEqual(
            _review_note_lines(BrowserState([FileChange("src/Sample.ts", 1, 0)])),
            ["Review notes: none"],
        )



class BrowserReviewNoteCommandTests(unittest.TestCase):
    def test_browser_command_executor_sets_and_clears_selected_file_note(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
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
            set_result = executor.execute(
                parse_browser_command("note check lifecycle edge case")
            )
            clear_result = executor.execute(parse_browser_command("note"))

        self.assertTrue(set_result.handled)
        self.assertFalse(set_result.needs_redraw)
        self.assertTrue(clear_result.handled)
        self.assertFalse(clear_result.needs_redraw)
        self.assertEqual(state.review_notes, {})
        self.assertIsNone(state.task)
        self.assertIn("Noted src/Second.ts", output.getvalue())
        self.assertIn("Cleared note for src/Second.ts", output.getvalue())

    def test_browser_command_executor_shows_review_notes_without_navigation(self):
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

    def test_browser_command_executor_saves_review_notes_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
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
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save notes"))

            saved = repo / ".cr" / "handoff" / "review-notes.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(
            text,
            "\n".join(
                [
                    "Review notes:",
                    "1. src/Second.ts: second current note",
                    "2. src/First.ts: first current note",
                    "3. docs/Old.md: stale follow-up",
                ]
            ),
        )
        self.assertIn(
            "Saved 3 review notes to .cr/handoff/review-notes.md.",
            state.status_message,
        )

    def test_browser_command_executor_saves_review_notes_requested_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                review_notes={"src/Sample.ts": "check lifecycle edge case"},
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
                    parse_browser_command("save notes tmp/review-notes.md")
                )

            saved = repo / "tmp" / "review-notes.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(
            text,
            "Review notes:\n1. src/Sample.ts: check lifecycle edge case",
        )
        self.assertIn(
            "Saved 1 review notes to tmp/review-notes.md.",
            state.status_message,
        )

    def test_browser_command_executor_does_not_save_empty_review_notes(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save notes"))

            target = repo / ".cr" / "handoff" / "review-notes.md"

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertFalse(target.exists())
        self.assertIn("No review notes to save.", state.status_message)

    def test_browser_command_executor_reports_save_review_notes_failures(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.git.repo_root", return_value=Path("/repo")):
            with patch(
                "cr.ui.browser.handoff_module.save_review_notes_text",
                return_value=handoff_module.HandoffSaveResult(
                    Path("/repo/blocked/notes.md"),
                    "blocked/notes.md",
                    "Could not save review notes to blocked/notes.md: denied",
                ),
            ):
                result = executor.execute(
                    parse_browser_command("save notes blocked/notes.md")
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn(
            "Could not save review notes to blocked/notes.md: denied",
            state.status_message,
        )

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
