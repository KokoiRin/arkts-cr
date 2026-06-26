import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
from cr.ui import selected_file_actions
from cr.ui.browser import BrowserState
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class SelectedFileNoteActionTests(unittest.TestCase):

    def test_set_selected_review_note_updates_workspace_and_clears_file_cache(self):
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        state.file_line_cache["cached"] = ["old"]

        message = selected_file_actions.set_selected_review_note(
            state,
            "check lifecycle",
        )

        self.assertEqual(message, "Noted src/Sample.ts")
        self.assertEqual(state.review_notes, {"src/Sample.ts": "check lifecycle"})
        self.assertEqual(
            state.workspace.review_notes,
            {"src/Sample.ts": "check lifecycle"},
        )
        self.assertEqual(state.file_line_cache, {})
    def test_change_note_describes_the_current_added_row(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "file level note"},
        )
        state.file_line_cache["src/Sample.ts"] = ["old"]
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        message = selected_file_actions.append_selected_change_review_note(
            state,
            state.changes[0],
            lines,
            2,
            "check lifecycle",
        )

        self.assertEqual(message, "Noted change src/Sample.ts:32")
        self.assertEqual(
            state.review_notes,
            {"src/Sample.ts": "file level note | line 32: check lifecycle"},
        )
        self.assertEqual(state.workspace.review_notes, state.review_notes)
        self.assertEqual(state.file_line_cache, {})
    def test_change_note_describes_the_current_deleted_row(self):
        state = BrowserState([FileChange("src/Sample.ts", 0, 1)])
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,0 @@",
            "    20      | -gone",
        ]

        message = selected_file_actions.append_selected_change_review_note(
            state,
            state.changes[0],
            lines,
            1,
            "confirm removal",
        )

        self.assertEqual(message, "Noted deleted change src/Sample.ts:20")
        self.assertEqual(
            state.review_notes,
            {"src/Sample.ts": "old line 20: confirm removal"},
        )

if __name__ == "__main__":
    unittest.main()
