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


class ReviewNoteEditCommandTests(unittest.TestCase):
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

if __name__ == "__main__":
    unittest.main()
