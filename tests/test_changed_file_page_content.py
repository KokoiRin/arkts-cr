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


class ChangedFilePageContentTests(unittest.TestCase):

    def test_browse_tree_highlights_guides_and_uses_plain_white_file_names(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/pages/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/pages/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(True, True))

        text = output.getvalue()
        self.assertIn("\033[36m└─ src/pages\033[0m", text)
        self.assertIn("\033[36m   └─ \033[0m", text)
        self.assertIn("\033[37mSample.ts", text)
        self.assertNotIn("\033[36mSample.ts", text)
        self.assertNotIn("\033]8;;", text)
    def test_page_content_owns_prompt_labels_and_scroll_window(self):
        self.assertEqual(page_content.browse_prompt(BrowserPage.SCOPE_HOME), "cr:scopes> ")
        self.assertEqual(page_content.browse_prompt(BrowserPage.FILE_DETAIL), "cr:file> ")
        self.assertEqual(page_content.ensure_window(0, 8, 20, 5), 4)
        self.assertEqual(page_content.ensure_window(4, 2, 20, 5), 2)
    def test_page_content_builds_compacted_changed_file_tree(self):
        changes = [
            FileChange("src/pages/home/HomeView.ets", 1, 0),
            FileChange("src/pages/home/HomeModel.ets", 2, 1),
        ]

        rows = page_content.browse_tree_rows(changes)

        self.assertEqual(rows[0].label, "└─ src/pages/home")
        self.assertEqual(rows[1].label, "   ├─ HomeModel.ets")
        self.assertEqual(rows[2].label, "   └─ HomeView.ets")
    def test_page_content_changed_file_rows_show_source_badges(self):
        change = FileChange("src/Sample.ts", 1, 1, source="mixed")

        lines = page_content.browse_list_lines(
            [change],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            seen_paths=set(),
            review_notes={"src/Sample.ts": "check lifecycle"},
        )

        row = "\n".join(lines)
        self.assertIn("mixed", row)
        self.assertIn("[ ]", row)
        self.assertIn("modified", row)
        self.assertIn("note", row)
    def test_page_content_changed_file_header_shows_source_summary(self):
        lines = page_content.browse_list_lines(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 2, 1, source="unstaged"),
                FileChange("src/Mixed.ts", 3, 2, source="mixed"),
            ],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1, unstaged 1, mixed 1", "\n".join(lines))
    def test_page_content_source_summary_omits_zero_and_empty_sources(self):
        staged_lines = page_content.browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
        )
        comparison_lines = page_content.browse_list_lines(
            [FileChange("src/CommitOnly.ts", 1, 0)],
            argparse_namespace(),
            TerminalStyle(),
        )

        self.assertIn("Sources: staged 1", "\n".join(staged_lines))
        self.assertNotIn("unstaged 0", "\n".join(staged_lines))
        self.assertNotIn("Sources:", "\n".join(comparison_lines))
    def test_page_content_changed_file_header_shows_source_filter(self):
        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        lines = page_content.browse_list_screen_lines(
            state,
            argparse_namespace(),
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("Source: staged", "\n".join(lines))
    def test_browse_list_lines_wrapper_passes_source_filter(self):
        lines = _browse_list_lines(
            [FileChange("src/Staged.ts", 1, 0, source="staged")],
            argparse_namespace(),
            TerminalStyle(),
            selected=0,
            source_filter="staged",
        )

        self.assertIn("Source: staged", "\n".join(lines))
    def test_browse_filter_matches_paths_and_clamps_selection(self):
        changes = [
            FileChange("src/pages/Home.ets", 1, 1),
            FileChange("src/components/Button.ts", 2, 0),
            FileChange("README.md", 1, 0),
        ]
        self.assertEqual(
            [change.path for change in filter_changes_by_query(changes, "BUTTON")],
            ["src/components/Button.ts"],
        )

        state = BrowserState(changes, selected=2)
        state.set_filter("src/")
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/pages/Home.ets", "src/components/Button.ts"],
        )
        self.assertEqual(state.selected, 0)

        state.selected = 99
        state.clamp_selection()
        self.assertEqual(state.selected, 1)

        state.set_filter("missing")
        self.assertEqual(state.visible_changes, [])
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.mode, "list")
    def test_browse_screen_only_measures_visible_list_rows(self):
        changes = [FileChange(f"src/File{index}.ts", 1, 0) for index in range(30)]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(changes)
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=1) as first_line:
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/File0.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertLess(first_line.call_count, len(changes))
        self.assertIn("showing rows", text)
        self.assertIn("File0.ts", text)
        self.assertNotIn("File29.ts", text)

if __name__ == "__main__":
    unittest.main()
