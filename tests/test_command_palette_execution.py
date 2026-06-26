import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import command_catalog
from cr.ui.browser import (
    BrowserState,
    _browse_command_palette_screen_lines,
    _command_palette_entries,
    _draw_browse_screen,
    _filtered_command_palette_entries,
    _move_selection,
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


class CommandPaletteExecutionTests(unittest.TestCase):
    def test_command_palette_enter_executes_selected_command_not_file_open(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        build_index = next(
            index
            for index, entry in enumerate(_command_palette_entries())
            if entry.command == "build"
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                commands = [
                                    "commands",
                                    *["down"] * build_index,
                                    "enter",
                                    "q",
                                ]
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=commands,
                                ):
                                    with patch("cr.ui.browser._draw_browse_screen"):
                                        with patch("cr.ui.browser._start_task") as start_build:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        start_build.assert_called_once()
    def test_command_palette_back_returns_to_list_without_changing_file_selection(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        frames: list[tuple[str, int]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, state.selected))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[
                            FileChange("src/First.ts", 1, 0),
                            FileChange("src/Second.ts", 1, 0),
                        ],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=["down", "commands", "down", "left", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("commands", 1), frames)
        self.assertEqual(frames[-1], ("list", 1))
    def test_command_palette_enter_executes_filtered_command(self):
        args = argparse_namespace(
            color="never",
            links="file",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                with patch(
                                    "cr.ui.browser._read_browse_command",
                                    side_effect=[
                                        "commands",
                                        "filter_prompt",
                                        "enter",
                                        "q",
                                    ],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_filter_query",
                                        return_value="build",
                                    ):
                                        with patch("cr.ui.browser._draw_browse_screen"):
                                            with patch("cr.ui.browser._start_task") as start_build:
                                                from cr.ui.browser import run_browser

                                                result = run_browser(args)

        self.assertEqual(result, 0)
        start_build.assert_called_once()

if __name__ == "__main__":
    unittest.main()
