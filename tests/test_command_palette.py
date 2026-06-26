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


class CommandPaletteTests(unittest.TestCase):
    def test_command_palette_lists_selected_file_index_actions(self):
        commands = {entry.command for entry in command_catalog.command_palette_entries()}

        self.assertIn("stage", commands)
        self.assertIn("unstage", commands)

    def test_command_palette_lists_source_filter_actions(self):
        commands = {entry.command for entry in command_catalog.command_palette_entries()}

        self.assertIn("source staged", commands)
        self.assertIn("source unstaged", commands)
        self.assertIn("source mixed", commands)
        self.assertIn("source all", commands)

    def test_command_palette_entries_include_only_executable_commands(self):
        entries = _command_palette_entries()
        commands = [entry.command for entry in entries]

        self.assertIn("build", commands)
        self.assertIn("test", commands)
        self.assertIn("lint", commands)
        self.assertIn("copy path", commands)
        self.assertIn("copy anchor", commands)
        self.assertIn("reveal", commands)
        self.assertIn("file actions", commands)
        self.assertIn("tasks", commands)
        self.assertIn("tasks help", commands)
        self.assertIn("notes", commands)
        self.assertIn("copy notes", commands)
        self.assertIn("save notes", commands)
        self.assertIn("copy prompt", commands)
        self.assertIn("copy prompt file", commands)
        self.assertIn("done next", commands)
        self.assertIn("copy diff", commands)
        self.assertIn("open hunk", commands)
        self.assertIn("open line", commands)
        self.assertIn("copy hunk", commands)
        self.assertIn("copy line", commands)
        self.assertIn("copy change", commands)
        self.assertIn("find TEXT", commands)
        self.assertIn("next match", commands)
        self.assertIn("prev match", commands)
        self.assertIn("next change", commands)
        self.assertIn("prev change", commands)
        self.assertIn("save diff", commands)
        self.assertIn("next hunk", commands)
        self.assertIn("prev hunk", commands)
        self.assertIn("save prompt", commands)
        self.assertIn("save prompt file", commands)
        self.assertIn("staged", commands)
        self.assertIn("forward", commands)
        self.assertIn("remaining", commands)
        self.assertNotIn("b", commands)
        self.assertNotIn("n", commands)
        self.assertNotIn("base REF", commands)
        self.assertNotIn("range OLD..NEW", commands)
        self.assertNotIn("note TEXT", commands)
        self.assertNotIn("note change TEXT", commands)
        self.assertNotIn("notes QUERY", commands)
        self.assertNotIn("copy notes QUERY", commands)
        self.assertNotIn("Enter / 1..N", commands)

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

    def test_commands_mode_selection_does_not_change_selected_file(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            selected=1,
            page="commands",
        )

        _move_selection(state, 1)

        self.assertEqual(state.selected, 1)
        self.assertEqual(state.command_selected, 1)

    def test_command_palette_screen_marks_selected_command(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page="commands",
            command_selected=1,
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("命令面板", text)
        self.assertIn("Enter：执行选中命令", text)
        self.assertIn("> ", text)

    def test_command_palette_screen_shows_filter_and_empty_results(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page="commands",
            command_filter_text="zz-missing",
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        total = len(_command_palette_entries())
        self.assertIn(f"过滤：zz-missing （0/{total} 个匹配）", text)
        self.assertIn("没有匹配命令。", text)
        self.assertNotIn("运行仓库配置的编译命令", text)

    def test_command_palette_screen_shows_filter_match_count(self):
        state = BrowserState([], page="commands", command_filter_text="build")
        lines = _browse_command_palette_screen_lines(
            state,
            TerminalStyle(False),
            max_lines=20,
        )
        text = "\n".join(lines)
        total = len(_command_palette_entries())
        matches = len(_filtered_command_palette_entries(state))

        self.assertIn(f"过滤：build （{matches}/{total} 个匹配）", text)
        self.assertGreater(matches, 0)

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
