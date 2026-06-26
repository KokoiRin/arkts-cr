import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import page_content
from cr.ui import source_file
from cr.ui import task_problems
from cr.ui.browser import (
    BrowserState,
    _browse_file_lines,
    _browse_file_screen_lines,
    _browse_list_lines,
    _browse_list_screen_lines,
    _draw_browse_screen,
    filter_changes_by_query,
)
from cr.ui.navigation import BrowserPage
from cr.ui.tasks import TaskState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class SourceFilePageContentTests(unittest.TestCase):

    def test_source_file_screen_renders_source_rows_and_error(self):
        view = source_file.SourceFileView(
            path="src/Foo.ets",
            target_line=2,
            scroll=0,
            total_lines=3,
            rows=[
                source_file.SourceFileRow(1, "first", is_selected=True),
                source_file.SourceFileRow(2, "target", is_target=True, is_selected=True),
                source_file.SourceFileRow(3, "third", is_selected=True),
            ],
        )

        lines = page_content.source_file_screen_lines(
            view,
            TerminalStyle(False),
            max_lines=8,
            context_lines=8,
            selection_start=1,
            selection_end=3,
            mark_line=2,
            symbol_label="struct Foo > method build",
            problem_label="1/2 ERROR TS123 bad value",
        )
        text = "\n".join(lines)

        self.assertIn("Source src/Foo.ets", text)
        self.assertIn("context: 8", text)
        self.assertIn("selection: 1-3", text)
        self.assertIn("mark: 2", text)
        self.assertIn("symbol: struct Foo > method build", text)
        self.assertIn("problem: 1/2 ERROR TS123 bad value", text)
        self.assertIn("* 1  first", text)
        self.assertIn("> 2  target", text)
        self.assertIn("* 3  third", text)

        error = source_file.SourceFileView(
            path="src/Missing.ets",
            target_line=1,
            scroll=0,
            total_lines=0,
            rows=[],
            error="Source file not found.",
        )
        error_text = "\n".join(
            page_content.source_file_screen_lines(
                error,
                TerminalStyle(False),
                max_lines=5,
            )
        )

        self.assertIn("Source src/Missing.ets", error_text)
        self.assertIn("Source file not found.", error_text)

if __name__ == "__main__":
    unittest.main()
