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


class CommandPaletteFilteringTests(unittest.TestCase):
    def test_command_palette_filter_matches_command_group_and_description(self):
        build_state = BrowserState([], page="commands", command_filter_text="build")
        stage_state = BrowserState([], page="commands", command_filter_text="scope")
        reopen_state = BrowserState([], page="commands", command_filter_text="editor")

        self.assertIn(
            "build",
            [entry.command for entry in _filtered_command_palette_entries(build_state)],
        )
        self.assertIn(
            "staged",
            [entry.command for entry in _filtered_command_palette_entries(stage_state)],
        )
        self.assertIn(
            "open",
            [entry.command for entry in _filtered_command_palette_entries(reopen_state)],
        )
    def test_command_palette_filter_ranks_command_matches_before_description_matches(self):
        unfiltered = [
            entry.command
            for entry in _filtered_command_palette_entries(
                BrowserState([], page="commands")
            )
        ]
        scope_filtered = [
            entry.command
            for entry in _filtered_command_palette_entries(
                BrowserState([], page="commands", command_filter_text="scope")
            )
        ]
        file_filtered = [
            entry.command
            for entry in _filtered_command_palette_entries(
                BrowserState([], page="commands", command_filter_text="file")
            )
        ]

        self.assertLess(unfiltered.index("forward"), unfiltered.index("scopes"))
        self.assertLess(scope_filtered.index("scopes"), scope_filtered.index("staged"))
        self.assertLess(file_filtered.index("file actions"), file_filtered.index("open"))
    def test_command_palette_filter_prompt_does_not_change_file_filter(self):
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
        frames: list[tuple[str, str, str]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, state.filter_text, state.command_filter_text))

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
                                        "filter_prompt",
                                        "commands",
                                        "filter_prompt",
                                        "q",
                                    ],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_filter_query",
                                        side_effect=["Sample", "build"],
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen",
                                            side_effect=capture_draw,
                                        ):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("commands", "Sample", ""), frames)
        self.assertEqual(frames[-1], ("commands", "Sample", "build"))
    def test_command_palette_clear_keeps_file_filter(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page="commands",
            filter_text="Sample",
            command_filter_text="build",
            command_selected=3,
        )

        state.clear_command_filter()

        self.assertEqual(state.filter_text, "Sample")
        self.assertEqual(state.command_filter_text, "")
        self.assertEqual(state.command_selected, 0)

if __name__ == "__main__":
    unittest.main()
