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


if __name__ == "__main__":
    unittest.main()
