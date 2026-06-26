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


class FileDetailPageContentTests(unittest.TestCase):

    def test_browse_file_screen_scrolls_long_content(self):
        # Behavior: 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        full_lines = ["File 1/1  src/Sample.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            top = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )
            state.file_scroll = 10
            lower = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        self.assertEqual(top[:2], ["File 1/1  src/Sample.ts", "line 1"])
        self.assertIn("showing 1-4/20", top[-1])
        self.assertIn("line 11", lower)
        self.assertIn("showing 11-14/20", lower[-1])
    def test_browse_file_screen_shows_review_queue_dock(self):
        # Behavior: 当用户在file detail中展示文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 2, 0, source="staged"),
            FileChange("src/Second.ts", 5, 1, source="unstaged"),
            FileChange("src/Third.ts", 1, 3, source="unstaged"),
        ]
        state = BrowserState(
            changes,
            page=BrowserPage.FILE_DETAIL,
            selected=1,
            seen_paths={"src/First.ts"},
            review_notes={"src/Second.ts": "check edge"},
        )
        full_lines = ["File 2/3  src/Second.ts"] + [
            f"line {index}" for index in range(1, 9)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                3,
                args,
                TerminalStyle(False),
                max_lines=14,
            )

        text = "\n".join(lines)
        self.assertIn("Changed files 2/3", text)
        self.assertIn("Progress: 1/3 seen", text)
        self.assertIn("  1 [x] src/First.ts", text)
        self.assertIn("> 2 [ ] src/Second.ts", text)
        self.assertIn("note", text)
        self.assertIn("unstaged", text)
        self.assertIn("+5 -1", text)
    def test_browse_file_screen_omits_review_queue_dock_when_short(self):
        # Behavior: 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        changes = [
            FileChange("src/First.ts", 1, 0),
            FileChange("src/Second.ts", 1, 0),
        ]
        state = BrowserState(changes, page=BrowserPage.FILE_DETAIL, selected=1)
        full_lines = ["File 2/2  src/Second.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            lines = _browse_file_screen_lines(
                state,
                changes[1],
                1,
                2,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        text = "\n".join(lines)
        self.assertNotIn("Changed files", text)
        self.assertIn("showing 1-4/20", lines[-1])
    def test_browse_file_lines_show_seen_or_todo_status(self):
        # Behavior: 当用户在file detail中展示文件详情时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        todo_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=False,
                        )
                        seen_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            seen=True,
                        )

        self.assertIn("todo", todo_lines[0])
        self.assertIn("seen", seen_lines[0])
    def test_browse_lines_show_review_notes(self):
        # Behavior: 当用户在file detail中展示文件详情、评审备注时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        change = FileChange("src/Sample.ts", 1, 1)
        review_notes = {"src/Sample.ts": "check lifecycle edge case"}

        with patch("cr.ui.browser.git.first_changed_line", return_value=1):
            with patch("cr.ui.browser.risk_hints", return_value=[]):
                with patch("cr.ui.browser.is_code_file", return_value=False):
                    with patch("cr.ui.browser.change_hunk_lines", return_value=[]):
                        list_lines = _browse_list_lines(
                            [change],
                            args,
                            TerminalStyle(False),
                            selected=0,
                            review_notes=review_notes,
                        )
                        screen_lines = _browse_list_screen_lines(
                            BrowserState([change], review_notes=review_notes),
                            args,
                            TerminalStyle(False),
                            max_lines=8,
                        )
                        detail_lines = _browse_file_lines(
                            change,
                            0,
                            1,
                            args,
                            TerminalStyle(False),
                            review_note=review_notes["src/Sample.ts"],
                        )

        self.assertIn("note", "\n".join(list_lines))
        self.assertIn("note", "\n".join(screen_lines))
        self.assertIn("note: check lifecycle edge case", "\n".join(detail_lines))

if __name__ == "__main__":
    unittest.main()
