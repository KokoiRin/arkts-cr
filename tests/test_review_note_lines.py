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
        # Behavior: 当用户在review note中验证评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在review note遇到空状态、评审备注时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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


if __name__ == "__main__":
    unittest.main()
