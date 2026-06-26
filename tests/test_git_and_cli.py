import os
import json
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import cr.ui.browser as browser_module
from cr.ui import input as browser_input
from cr.ui import commit_picker
from cr.ui import page_content
from cr.ui import source_file
from cr.ui import task_problems
from cr.ui.browser import (
    TaskState,
    BrowserActionResult,
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    ReviewWorkspace,
    TaskRecord,
    _build_command,
    _task_panel_lines,
    _task_status,
    _browse_command_lines,
    _browse_command_palette_screen_lines,
    _command_palette_entries,
    _filtered_command_palette_entries,
    _browse_file_lines,
    _browse_file_screen_lines,
    _browse_list_lines,
    _browse_list_screen_lines,
    _browser_workspace_state_path,
    _save_browser_workspace_state,
    _load_browser_workspace_state,
    _draw_task_panel_only,
    _draw_browse_screen,
    _move_selection,
    _normalize_command_query,
    _poll_task,
    _record_completed_task,
    _read_browse_command,
    _restore_browser_workspace_state,
    _rerun_task,
    _screen_layout,
    _show_browser_message,
    _start_task,
    _stop_task,
    _switch_review_scope,
    _task_command,
    filter_changes_by_query,
    ReviewScope,
)
from cr.review.changes import format_counts
from cr.review.data import build_review_data
from cr.review.prompt import render_prompt_handoff
from cr.review.snippet import render_file_diff_snippet
from cr.ui import command_catalog
from cr.ui import frame as frame_module
from cr.ui.terminal import TerminalStyle
from cr.vcs import git
from cr.vcs.git import CommitSummary, FileChange


ROOT = Path(__file__).resolve().parents[1]


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class CliTests(unittest.TestCase):
    def test_browser_command_executor_copies_source_enum_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            source = repo / "src" / "Status.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "export const enum FeedStatus {",
                        "  Loading = 'loading',",
                        "  Ready = 'ready',",
                        "}",
                        "function after() {",
                        "  return FeedStatus.Ready",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            change = FileChange("src/Status.ets", 1, 0)
            copied: list[str] = []
            state = browser_module.BrowserState(
                [change],
                page=browser_module.BrowserPage.SOURCE_FILE,
                source_file_path="src/Status.ets",
                source_file_line=2,
                selected=0,
            )
            executor = browser_module.BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    side_effect=lambda text, _cmd: copied.append(text),
                ):
                    result = executor.execute(parse_browser_command("copy source symbol"))

        self.assertTrue(result.handled)
        self.assertIn("Copied source symbol src/Status.ets:1-4.", state.status_message)
        self.assertEqual(len(copied), 1)
        self.assertIn("Symbol: enum FeedStatus", copied[0])
        self.assertIn("  Loading = 'loading',", copied[0])
        self.assertNotIn("function after", copied[0])

    def test_prompt_handoff_renders_review_notes_in_summary_and_detail(self):
        prompt = render_prompt_handoff(
            {
                "summary": {"files": 1, "added": 2, "deleted": 1},
                "other_changes": {"staged": 0, "unstaged": 0},
                "files": [
                    {
                        "path": "src/Sample.ts",
                        "summary": "+2 -1",
                        "status": "modified",
                        "anchor": "src/Sample.ts:3",
                        "risk_hints": [],
                        "seen": False,
                        "purpose": None,
                        "modified_symbols": [],
                        "review_note": "check lifecycle edge case",
                        "hunks": ["@@ -1 +1 @@", "-old", "+new"],
                    }
                ],
            }
        )

        self.assertEqual(prompt.count("review note: check lifecycle edge case"), 2)
        self.assertIn("   - review note: check lifecycle edge case", prompt)
        self.assertIn("- review note: check lifecycle edge case", prompt)

    def test_file_diff_snippet_renders_compact_selected_file_context(self):
        text = render_file_diff_snippet(
            {
                "path": "src/Sample.ets",
                "status": "modified",
                "summary": "+2 -1",
                "anchor": "src/Sample.ets:12",
                "risk_hints": ["high churn"],
                "seen": True,
                "review_note": "check lifecycle edge case",
                "purpose": "ArkTS page/component SamplePage",
                "modified_symbols": ["build"],
                "hunks": ["@@ -1 +1 @@", "-old", "+new"],
            }
        )

        self.assertIn("# File Diff: src/Sample.ets", text)
        self.assertIn("- change: +2 -1 (modified)", text)
        self.assertIn("- anchor: src/Sample.ets:12", text)
        self.assertIn("- state: seen", text)
        self.assertIn("- review note: check lifecycle edge case", text)
        self.assertIn("- purpose: ArkTS page/component SamplePage", text)
        self.assertIn("- focus: build", text)
        self.assertIn("```diff\n@@ -1 +1 @@\n-old\n+new\n```", text)
        self.assertNotIn("Please review these changes.", text)

    def test_build_review_data_attaches_matching_review_notes(self):
        change = FileChange("src/Sample.ts", 2, 1)

        with patch("cr.review.data.git.first_changed_line", return_value=3):
            with patch(
                "cr.review.data.git.file_diff",
                return_value="@@ -1 +1 @@\n-old\n+new\n",
            ):
                data = build_review_data(
                    [change],
                    review_notes={
                        "src/Sample.ts": "check lifecycle edge case",
                        "docs/Other.md": "not in copied prompt",
                    },
                )

        self.assertEqual(
            data["files"][0]["review_note"],
            "check lifecycle edge case",
        )
        self.assertNotIn("docs/Other.md", str(data))

    def test_browse_source_file_screen_lines_show_current_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('hello')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("symbol: struct Foo > method build", text)
        self.assertIn("> 3", text)

    def test_browse_source_file_screen_lines_show_matching_task_problem(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("problem: 1/1 ERROR TS123", text)
        self.assertIn("bad value", text)

    def test_browse_source_file_screen_lines_hides_stale_task_problem(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertNotIn("problem:", text)
        self.assertNotIn("bad value", text)

    def test_browser_command_executor_reports_quit_intent(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("q"))

        self.assertEqual(result, BrowserActionResult(exit_code=0))

    def test_browser_command_executor_changes_page_and_requests_redraw(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("commands"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.COMMAND_PALETTE)

    def test_browser_command_executor_reports_unknown_command_feedback(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("wat"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Unknown command.", output.getvalue())

    def test_browser_command_executor_opens_selected_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            open_cmd="code -g {fileline}",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
                with patch("cr.ui.browser.file_actions.open_path", return_value=None) as open_path:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("open"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        open_path.assert_called_once_with(repo_file, 12, "code -g {fileline}")
        self.assertIn("Opened src/Sample.ts:12", output.getvalue())

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

    def test_browser_command_executor_copies_selected_path(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy path"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy.assert_called_once_with("src/Sample.ts", "copy-tool")
        self.assertIn("Copied src/Sample.ts", output.getvalue())

    def test_browser_command_executor_applies_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source staged", raw_keys=True))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.source_filter, "staged")
        self.assertEqual(state.selected, 0)
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Staged.ts"],
        )

    def test_browser_command_executor_rejects_unknown_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 0, source="staged")])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("source generated"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")
        self.assertIn("Unknown source filter", output.getvalue())

    def test_browser_command_executor_clears_source_filter(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0, source="staged")],
            source_filter="staged",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with redirect_stdout(StringIO()):
            result = executor.execute(parse_browser_command("source all"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")

    def test_browser_command_executor_copies_selected_anchor(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        copy.assert_called_once_with("src/Sample.ts:12", None)
        self.assertIn("Copied src/Sample.ts:12", output.getvalue())

    def test_browser_command_executor_copies_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ) as copy_diff:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy diff"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy_diff.assert_called_once_with(state, args)
        self.assertIn("Copied diff for src/Sample.ts", output.getvalue())

    def test_browser_command_executor_copies_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.copy_selected_diff_snippet",
            return_value="Copied diff for src/Sample.ts",
        ):
            result = executor.execute(parse_browser_command("copy diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Copied diff for src/Sample.ts", state.status_message)

    def test_browser_command_executor_saves_selected_diff_snippet(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to tmp/current.md",
        ) as save_diff:
            with redirect_stdout(output):
                result = executor.execute(
                    parse_browser_command("save diff tmp/current.md")
                )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        save_diff.assert_called_once_with(state, args, "tmp/current.md")
        self.assertIn(
            "Saved diff for src/Sample.ts to tmp/current.md",
            output.getvalue(),
        )

    def test_browser_command_executor_saves_selected_diff_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.selected_file_actions.save_selected_diff_snippet",
            return_value="Saved diff for src/Sample.ts to .cr/handoff/review-diff.md",
        ):
            result = executor.execute(parse_browser_command("save diff", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Saved diff for src/Sample.ts", state.status_message)

    def test_browser_command_executor_marks_done_and_moves_next_in_changed_files(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_marks_done_and_opens_next_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=8,
            review_notes={"src/First.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("seen next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertEqual(state.review_notes["src/First.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_does_not_skip_remaining_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
            remaining_only=True,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )
        self.assertEqual(state.selected, 0)
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_last_visible_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/Second.ts"})
        self.assertIn("No next file after src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_empty_visible_files(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, set())
        self.assertIn("No changed file to mark seen.", state.status_message)

    def test_browser_command_executor_jumps_to_next_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1 +1 @@",
            "  +first",
            "  context",
            "  @@ -20 +21 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(
                    parse_browser_command("next hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 1)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to hunk 1/2.", state.status_message)

    def test_browser_command_executor_jumps_to_previous_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=5,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +1 @@",
            "  +first",
            "  context",
            "  @@ -20 +21 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(parse_browser_command("[", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.file_scroll, 3)
        self.assertIn("Moved to hunk 2/2.", state.status_message)

    def test_browser_command_executor_jumps_between_changed_rows_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1,5 +1,5 @@",
            "     1    1 | context",
            "       \033[32m2 | +added\033[0m",
            "    3      | -deleted",
            "     4    3 | context",
            "          4 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            next_result = executor.execute(
                parse_browser_command("next change", raw_keys=True)
            )
            previous_result = executor.execute(
                parse_browser_command("prev change", raw_keys=True)
            )

        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertTrue(previous_result.handled)
        self.assertTrue(previous_result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 5)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Moved to change 3/3.", state.status_message)

    def test_browser_command_executor_reports_changed_row_navigation_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next change", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to jump changes.", state.status_message)

    def test_browser_command_executor_reports_changed_row_navigation_without_changed_rows(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +1 @@",
            "     1    1 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("next change", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No changed rows in current file.", state.status_message)

    def test_browser_command_executor_opens_current_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=3,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  context",
            "  @@ -20,2 +31,3 @@",
            "  +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/repo/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(
                        parse_browser_command("open hunk", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            31,
            "editor {fileline}",
        )
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Opened hunk src/Sample.ts:31", state.status_message)

    def test_browser_command_executor_reports_open_hunk_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd=None)
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.open_path") as open_path:
            result = executor.execute(parse_browser_command("open hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to open hunk.", state.status_message)

    def test_browser_command_executor_opens_current_line_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/repo/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    result = executor.execute(
                        parse_browser_command("open line", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            32,
            "editor {fileline}",
        )
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Opened line src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_copies_current_line_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy line", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with("src/Sample.ts:32", "copy-tool")
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied line src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_line_action_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("open line", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to open line.", state.status_message)

    def test_browser_command_executor_reports_line_action_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy line", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_views_current_file_detail_source_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 32)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)

    def test_browser_command_executor_views_current_file_detail_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "  other() {",
                        "    return 'nope'",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command("view source symbol", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 4)
        self.assertEqual(state.source_selection_start, 2)
        self.assertEqual(state.source_selection_end, 6)
        self.assertIn(
            "Selected source symbol class Sample > method render src/Sample.ts:2-6.",
            state.status_message,
        )

    def test_browser_command_executor_reports_view_source_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_reports_view_source_symbol_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command("view source symbol", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_views_source_symbol_line_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text("const value = 1\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -1,1 +1,1 @@",
                "          1 | +const value = 1",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(
                        parse_browser_command("view source symbol", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Sample.ts")
        self.assertEqual(state.source_file_line, 1)
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_view_source_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view source", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to view source.", state.status_message)

    def test_browser_command_executor_copies_file_detail_source_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text",
                        return_value=None,
                    ) as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy source", raw_keys=True)
                        )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Sample.ts:4", copied)
        self.assertIn("Symbol: class Sample > method render", copied)
        self.assertIn("> 4      const title = 'new'", copied)
        self.assertNotIn("class Sample {", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Copied source context src/Sample.ts:4.", state.status_message)

    def test_browser_command_executor_reports_file_detail_copy_source_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy source", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("No current new-file line in File Detail.", state.status_message)


    def test_browser_command_executor_does_not_use_selected_problem_for_file_detail_context(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            other = repo / "src" / "Other.ts"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
            other.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0), FileChange("src/Other.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
                source_context_lines=1,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ts:2:1 error TS9: other bad"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/2  src/Sample.ts",
                "  @@ -3,1 +3,2 @@",
                "     3    3 | three",
                "          4 | +four",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.build_review_data",
                        return_value={"files": [{"path": "src/Sample.ts"}]},
                    ):
                        with patch(
                            "cr.ui.browser.render_file_diff_snippet",
                            return_value="# File Diff: src/Sample.ts",
                        ):
                            with patch(
                                "cr.ui.browser.file_actions.copy_text",
                                return_value=None,
                            ) as copy_text:
                                result = executor.execute(
                                    parse_browser_command(
                                        "copy problem context",
                                        raw_keys=True,
                                    )
                                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("# Problem Context: src/Sample.ts:4", copied)
        self.assertIn("## Source", copied)
        self.assertIn("## Diff", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertNotIn("src/Other.ts", copied)
        self.assertNotIn("other bad", copied)
        self.assertIn("# File Diff: src/Sample.ts", copied)


    def test_browser_command_executor_copies_file_detail_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    const title = 'old'",
                        "    const title = 'new'",
                        "    return title",
                        "  }",
                        "  other() {",
                        "    return 'nope'",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Sample.ts",
                "  @@ -3,2 +3,3 @@",
                "     3    3 |     const title = 'old'",
                "          4 | +   const title = 'new'",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text",
                        return_value=None,
                    ) as copy_text:
                        result = executor.execute(
                            parse_browser_command("copy source symbol", raw_keys=True)
                        )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("src/Sample.ts:2-6", copied)
        self.assertIn("Symbol: class Sample > method render", copied)
        self.assertIn("const title = 'new'", copied)
        self.assertNotIn("other() {", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("Copied source symbol src/Sample.ts:2-6.", state.status_message)

    def test_browser_command_executor_reports_file_detail_copy_symbol_without_new_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20      | -deleted",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy source symbol", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertIn("No current new-file line in File Detail.", state.status_message)

    def test_browser_command_executor_copies_current_change_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy change", raw_keys=True)
                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("# Changed Row: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:32", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied change for src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_copy_change_without_changed_row(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy change", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No current changed row in File Detail.", state.status_message)

    def test_browser_command_executor_reports_copy_change_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(
                parse_browser_command("copy change", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to copy change.", state.status_message)

    def test_browser_command_executor_notes_current_change_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=2,
            review_notes={"src/Sample.ts": "file note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command(
                    "note change check lifecycle",
                    raw_keys=True,
                )
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIsNotNone(state.task)
        self.assertEqual(
            state.review_notes,
            {"src/Sample.ts": "file note | line 32: check lifecycle"},
        )
        self.assertIn("Noted change src/Sample.ts:32", state.status_message)

    def test_browser_command_executor_reports_change_note_without_changed_row(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=1,
            review_notes={"src/Sample.ts": "file note"},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            result = executor.execute(
                parse_browser_command("note change check lifecycle", raw_keys=True)
            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.review_notes, {"src/Sample.ts": "file note"})
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("No current changed row in File Detail.", state.status_message)

    def test_browser_command_executor_reports_change_note_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(
            parse_browser_command("note change check lifecycle", raw_keys=True)
        )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.review_notes, {})
        self.assertIn("Open a file detail to note change.", state.status_message)

    def test_browser_command_executor_copies_current_hunk_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=3,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  context",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value=None,
            ) as copy_text:
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertIn("# Hunk Diff: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:31", copied)
        self.assertIn("- hunk: 2/2", copied)
        self.assertIn("```text", copied)
        self.assertIn("@@ -20,2 +31,3 @@", copied)
        self.assertIn("  20   31 | context", copied)
        self.assertIn("        32 | +second", copied)
        self.assertNotIn("+first", copied)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn("Copied hunk 2/2 for src/Sample.ts:31", state.status_message)

    def test_browser_command_executor_reports_copy_hunk_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to copy hunk.", state.status_message)

    def test_browser_command_executor_reports_copy_hunk_without_hunks(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd=None)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._cached_file_lines", return_value=["File 1/1"]):
            with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No diff hunks in current file.", state.status_message)

    def test_browser_command_executor_surfaces_copy_hunk_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1", "  @@ -1 +9 @@", "        9 | +new"],
        ):
            with patch(
                "cr.ui.browser.file_actions.copy_text",
                return_value="Copy failed (cli copy-tool): missing copy",
            ):
                result = executor.execute(
                    parse_browser_command("copy hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Copy failed (cli copy-tool): missing copy", state.status_message)

    def test_browser_command_executor_reports_open_hunk_without_hunks(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd=None)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._cached_file_lines", return_value=["File 1/1"]):
            with patch("cr.ui.browser.file_actions.open_path") as open_path:
                result = executor.execute(
                    parse_browser_command("open hunk", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        open_path.assert_not_called()
        self.assertIn("No diff hunks in current file.", state.status_message)

    def test_browser_command_executor_surfaces_open_hunk_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(open_cmd="editor {fileline}")
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1", "  @@ -1 +9 @@"],
        ):
            with patch(
                "cr.ui.browser.git.repo_path",
                return_value=Path("/repo/src/Sample.ts"),
            ):
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value="Open failed (cli editor): missing editor",
                ):
                    result = executor.execute(
                        parse_browser_command("open hunk", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn("Open failed (cli editor): missing editor", state.status_message)

    def test_browser_command_executor_reports_hunk_navigation_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next hunk", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to jump hunks.", state.status_message)

    def test_browser_command_executor_finds_text_in_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1 +1 @@",
            "       1 | context",
            "       2 | +TargetValue",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(
                    parse_browser_command("find targetvalue", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 3)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertEqual(state.file_find_text, "targetvalue")
        self.assertIn('Found "targetvalue" at line 4.', state.status_message)

    def test_browser_command_executor_repeats_file_detail_find_matches(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  target first",
            "  context",
            "  Target second",
            "  context",
            "  target third",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                find = executor.execute(
                    parse_browser_command("find target", raw_keys=True)
                )
                next_match = executor.execute(
                    parse_browser_command("next match", raw_keys=True)
                )
                previous_match = executor.execute(
                    parse_browser_command("prev match", raw_keys=True)
                )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.file_find_text, "target")
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn('Found "target" at line 1.', state.status_message)

    def test_browser_command_executor_reports_find_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to find text.", state.status_message)

    def test_browser_command_executor_reports_repeat_find_outside_file_detail(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        state.file_find_text = "target"
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to find text.", state.status_message)

    def test_browser_command_executor_reports_empty_and_missing_find(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1  src/Sample.ts", "  context"],
        ):
            empty = executor.execute(parse_browser_command("find", raw_keys=True))
            missing = executor.execute(parse_browser_command("find owner", raw_keys=True))

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.file_find_text, "owner")
        self.assertIn('No matches for "owner".', state.status_message)

    def test_browser_command_executor_reports_repeat_find_without_query(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Run find TEXT first.", state.status_message)

    def test_browser_command_executor_reports_repeat_find_without_matches(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        state.file_find_text = "owner"
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1  src/Sample.ts", "  context"],
        ):
            result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn('No matches for "owner".', state.status_message)


    def test_browser_command_executor_anchor_falls_back_to_path_without_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
        )
        state = BrowserState([FileChange("asset.bin", None, None)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch("cr.ui.browser.git.first_changed_line", return_value=None):
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(StringIO()):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        copy.assert_called_once_with("asset.bin", None)

    def test_browser_command_executor_reveals_selected_file(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(reveal_cmd="reveal-tool --file {file}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
            with patch("cr.ui.browser.file_actions.reveal_path", return_value=None) as reveal:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        reveal.assert_called_once_with(repo_file, "reveal-tool --file {file}")
        self.assertIn("Revealed src/Sample.ts", output.getvalue())

    def test_browser_command_executor_stages_selected_file_and_refreshes_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        state.file_line_cache["old"] = ["stale"]
        BrowserNavigation.open_file_detail(state)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.stage_path", return_value=None) as stage:
            with patch(
                "cr.ui.browser._load_browse_changes",
                return_value=[FileChange("src/New.ts", 1, 0)],
            ):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        stage.assert_called_once_with("src/Old.ts")
        self.assertEqual(state.changes, [FileChange("src/New.ts", 1, 0)])
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Staged src/Old.ts", output.getvalue())

    def test_browser_command_executor_stage_failure_does_not_refresh_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.git.stage_path",
            side_effect=git.GitError("cannot stage file"),
        ):
            with patch("cr.ui.browser._load_browse_changes") as load:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        load.assert_not_called()
        self.assertIn("Stage failed: cannot stage file", output.getvalue())

    def test_browser_command_executor_unstages_selected_file_and_refreshes_scope(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Staged.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.unstage_path", return_value=None) as unstage:
            with patch("cr.ui.browser._load_browse_changes", return_value=[]):
                with patch("cr.ui.browser._show_commits_when_empty"):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_called_once_with("src/Staged.ts")
        self.assertEqual(state.changes, [])
        self.assertIn("Unstaged src/Staged.ts", output.getvalue())

    def test_browser_command_executor_stage_reports_empty_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.stage_path") as stage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("stage"))

        self.assertTrue(result.handled)
        stage.assert_not_called()
        self.assertIn("No changed file to stage.", output.getvalue())

    def test_browser_command_executor_unstage_reports_empty_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.unstage_path") as unstage:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("unstage"))

        self.assertTrue(result.handled)
        unstage.assert_not_called()
        self.assertIn("No changed file to unstage.", output.getvalue())

    def test_browser_command_executor_shows_file_action_diagnostics(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            open_cmd="code -g {fileline}",
            copy_cmd="copy-tool {text}",
            reveal_cmd="reveal-tool {file}",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.repo_root", return_value=Path("/tmp/repo")):
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("file actions"))

        text = output.getvalue()
        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        self.assertIn("File actions:", text)
        self.assertIn("open: cli code -g", text)
        self.assertIn("copy: cli copy-tool", text)
        self.assertIn("reveal: cli reveal-tool", text)


    def test_browser_command_executor_steps_source_file_task_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("one\ntwo\nthree\n", encoding="utf-8")
            second.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:2:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                view_result = executor.execute(parse_browser_command("view problem"))
                next_result = executor.execute(parse_browser_command("next problem"))
                selected_after_next = state.problem_selected
                path_after_next = state.source_file_path
                line_after_next = state.source_file_line
                prev_result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(view_result.handled)
        self.assertTrue(next_result.handled)
        self.assertTrue(next_result.needs_redraw)
        self.assertEqual(selected_after_next, 1)
        self.assertEqual(path_after_next, "src/Two.ets")
        self.assertEqual(line_after_next, 2)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertTrue(prev_result.handled)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.source_file_path, "src/One.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)


    def test_browser_command_executor_does_not_use_stale_source_problem_for_context(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            other = repo / "src" / "Other.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 10)),
                encoding="utf-8",
            )
            other.write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 2, 1), FileChange("src/Other.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:2:1 error TS9: other bad"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy-tool"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"files": [{"path": "src/Foo.ets"}]},
                ):
                    with patch(
                        "cr.ui.browser.render_file_diff_snippet",
                        return_value="# File Diff: src/Foo.ets",
                    ):
                        with patch(
                            "cr.ui.browser.file_actions.copy_text",
                            return_value=None,
                        ) as copy_text:
                            result = executor.execute(
                                parse_browser_command("copy problem context")
                            )

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("# Problem Context: src/Foo.ets:5", copied)
        self.assertIn("## Source", copied)
        self.assertIn("## Diff", copied)
        self.assertNotIn("## Problem", copied)
        self.assertNotIn("## Task Output", copied)
        self.assertNotIn("src/Other.ets", copied)
        self.assertNotIn("other bad", copied)
        self.assertIn("# File Diff: src/Foo.ets", copied)


    def test_browser_command_executor_views_selected_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 error",
                        "src/Two.ets:2:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)


    def test_browser_command_executor_steps_file_detail_problem_to_visible_diff_line(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=0,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Other.ets:1:1 error",
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)

    def test_browser_command_executor_steps_file_detail_previous_problem(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                problem_selected=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/Foo.ets:2:1 error",
                        "src/Foo.ets:3:1 error",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,3 +1,4 @@",
                "     1    1 | one",
                "          2 | +two",
                "     2    3 | three",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("prev problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("已选择当前文件问题 1/2 src/Foo.ets:2。", state.status_message)

    def test_browser_command_executor_steps_file_detail_problem_without_visible_diff_line(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:3:1 error"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 1/1  src/Foo.ets",
                "  @@ -1,1 +1,2 @@",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn(
            "已选择当前文件问题 1/1 src/Foo.ets:3，但当前 diff 不显示该行。",
            state.status_message,
        )

    def test_browser_command_executor_reports_file_detail_without_file_problems(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "Foo.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Other.ets").write_text("one\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 0)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Other.ets:1:1 error"],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("next problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 1)
        self.assertIn("当前文件没有任务问题。", state.status_message)


    def test_browser_command_executor_views_source_file_diff(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 2/2  src/Two.ets",
                "  @@ -1,2 +1,3 @@",
                "     1    1 | one",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Opened source diff src/Two.ets:2.", state.status_message)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)

    def test_browser_command_executor_reports_source_file_diff_without_changed_file(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.selected, 0)
        self.assertIn(
            "No diff for source src/Two.ets:2 in current review scope.",
            state.status_message,
        )


    def test_browser_command_executor_views_sorted_task_problem_source(self):
        from cr.ui.browser import parse_browser_command

        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "One.ets"
            second = repo / "src" / "Two.ets"
            first.parent.mkdir(parents=True)
            first.write_text("sample", encoding="utf-8")
            second.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.TASK_PROBLEMS,
                problem_selected=0,
                problem_sort="severity",
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=[
                        "src/One.ets:1:1 warning W1: noisy",
                        "src/Two.ets:2:1 error E1: bad",
                    ],
                ),
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Two.ets")
        self.assertEqual(state.source_file_line, 2)

    def test_browser_command_executor_scrolls_and_opens_source_file_page(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 40)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=20,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                down = executor.execute(parse_browser_command("down", raw_keys=True))
                scroll_after_down = state.source_file_scroll
                end = executor.execute(parse_browser_command("end", raw_keys=True))
                scroll_after_end = state.source_file_scroll
                home = executor.execute(parse_browser_command("home", raw_keys=True))
                scroll_after_home = state.source_file_scroll
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    opened = executor.execute(parse_browser_command("open"))

        self.assertTrue(down.needs_redraw)
        self.assertTrue(end.needs_redraw)
        self.assertTrue(home.needs_redraw)
        self.assertGreater(scroll_after_down, 0)
        self.assertGreater(scroll_after_end, scroll_after_down)
        self.assertEqual(scroll_after_home, 0)
        self.assertTrue(opened.needs_redraw)
        open_path.assert_called_once_with(source, 20, "editor {fileline}")
        self.assertIn("Opened source src/Foo.ets:20", state.status_message)

    def test_browser_command_executor_copies_source_file_page_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=20,
            source_file_scroll=7,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with("src/Foo.ets:20", "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 20)
        self.assertEqual(state.source_file_scroll, 7)
        self.assertIn("Copied source line src/Foo.ets:20", state.status_message)

    def test_browser_command_executor_copies_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:5", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  8  line 8", copied)
        self.assertNotIn("line 1", copied)
        copy_text.assert_called_once_with(copied, "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 5)
        self.assertEqual(state.source_file_scroll, 2)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)

    def test_browser_command_executor_copies_source_file_context_with_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('hello')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("> 3  ", copied)
        self.assertIn("Copied source context src/Foo.ets:3", state.status_message)

    def test_browser_command_executor_saves_selected_source_context_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save source"))

            saved = repo / ".cr" / "handoff" / "source.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:3-6", text)
        self.assertIn("> 5  line 5", text)
        self.assertNotIn("line 2", text)
        self.assertNotIn("line 7", text)
        self.assertIn("Saved selected source to .cr/handoff/source.md.", state.status_message)

    def test_browser_command_executor_sets_source_context_lines(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_context = executor.execute(parse_browser_command("source context 8"))
        clamped_context = executor.execute(parse_browser_command("source context 999"))
        invalid_context = executor.execute(parse_browser_command("source context nope"))

        self.assertTrue(set_context.handled)
        self.assertTrue(set_context.needs_redraw)
        self.assertTrue(clamped_context.handled)
        self.assertTrue(invalid_context.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_context_lines, 50)
        self.assertIn("Source context must be a non-negative integer.", state.status_message)

    def test_browser_command_executor_sets_and_clears_source_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_selection = executor.execute(parse_browser_command("source select 8 3"))
        selection_after_set = (
            state.source_selection_start,
            state.source_selection_end,
        )
        invalid_selection = executor.execute(parse_browser_command("source select nope 3"))
        selection_after_invalid = (
            state.source_selection_start,
            state.source_selection_end,
        )
        clear_selection = executor.execute(parse_browser_command("source clear selection"))

        self.assertTrue(set_selection.handled)
        self.assertTrue(set_selection.needs_redraw)
        self.assertTrue(invalid_selection.handled)
        self.assertTrue(clear_selection.handled)
        self.assertEqual(selection_after_set, (3, 8))
        self.assertEqual(selection_after_invalid, (3, 8))
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertIn("Source selection cleared.", state.status_message)

    def test_browser_command_executor_selects_source_range_from_mark_to_current_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        mark_result = executor.execute(parse_browser_command("source mark"))
        state.source_file_line = 9
        select_result = executor.execute(parse_browser_command("source select to"))
        state.source_file_line = 3
        reverse_result = executor.execute(parse_browser_command("source select to"))
        clear_mark_result = executor.execute(parse_browser_command("source clear mark"))

        self.assertTrue(mark_result.needs_redraw)
        self.assertTrue(select_result.needs_redraw)
        self.assertTrue(reverse_result.needs_redraw)
        self.assertTrue(clear_mark_result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (3, 5))
        self.assertEqual(state.source_mark_line, 0)
        self.assertIn("Source mark cleared.", state.status_message)

    def test_browser_command_executor_reports_source_select_to_without_mark(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select to"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn("Set a source mark before selecting to it.", state.status_message)

    def test_browser_command_executor_selects_current_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (2, 5))
        self.assertIn(
            "Selected source symbol struct Foo > method build src/Foo.ets:2-5.",
            state.status_message,
        )

    def test_browser_command_executor_reports_source_symbol_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn(
            "Open a source file before selecting source symbol.",
            state.status_message,
        )

    def test_browser_command_executor_reports_source_symbol_selection_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                source_selection_start=7,
                source_selection_end=9,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 9))
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_source_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select 1 3"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_selection_start, 0)
        self.assertIn("Open a source file before selecting source.", state.status_message)

    def test_browser_command_executor_copies_selected_source_symbol_range(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    select_result = executor.execute(
                        parse_browser_command("source select symbol")
                    )
                    copy_result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(select_result.handled)
        self.assertTrue(copy_result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("const title = 'hi'", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied selected source src/Foo.ets:2-5.", state.status_message)

    def test_browser_command_executor_copies_source_file_symbol_directly(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_selection_start=7,
                source_selection_end=8,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertNotIn("other() {", copied)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 8))
        self.assertIn("Copied source symbol src/Foo.ets:2-5.", state.status_message)

    def test_browser_command_executor_saves_file_detail_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    return value",
                        "  }",
                        "  other() {",
                        "    return nope",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 1)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(False),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser._cached_file_lines",
                    return_value=[
                        "File 1/1  src/Sample.ts",
                        "  @@ -1 +3 @@",
                        "          3 | +    return value",
                    ],
                ):
                    result = executor.execute(
                        parse_browser_command("save source symbol tmp/render.md")
                    )

            saved = repo / "tmp" / "render.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Sample.ts:2-4", text)
        self.assertIn("Symbol: class Sample > method render", text)
        self.assertIn("return value", text)
        self.assertNotIn("other()", text)
        self.assertIn("Saved source symbol to tmp/render.md.", state.status_message)

    def test_browser_command_executor_copies_source_field_arrow_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  private onTap = () => {",
                        "    this.handleTap()",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: struct Foo > method onTap", copied)
        self.assertIn("private onTap = () => {", copied)
        self.assertIn("this.handleTap()", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_copies_source_accessor_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  get title(): string {",
                        "    return this.model.title",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method title", copied)
        self.assertIn("get title(): string", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_copies_source_generic_method_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  private createModel<T extends BaseModel>(value: T): T {",
                        "    return value",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method createModel", copied)
        self.assertIn("private createModel<T extends BaseModel>", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_reports_copy_source_symbol_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        self.assertTrue(result.handled)
        copy_text.assert_not_called()
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_source_context_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.CHANGED_FILES,
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source context 8"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_context_lines, 3)
        self.assertIn("Open a source file before setting source context.", state.status_message)

    def test_browser_command_executor_copies_configured_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("  4  line 4", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 3", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)

    def test_browser_command_executor_copies_selected_source_range(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied selected source src/Foo.ets:3-6", state.status_message)

    def test_browser_command_executor_reports_empty_source_context_copy(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file to copy.", state.status_message)

    def test_browser_command_executor_reports_missing_source_context_copy(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Missing.ets",
                source_file_line=5,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("Source file not found.", state.status_message)

    def test_browser_command_executor_reports_empty_source_file_line_copy(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file line to copy.", state.status_message)

    def test_browser_command_executor_finds_text_in_source_file_page(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nBeta target\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                file_find_text="file-query",
                task_find_text="task-query",
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("find TARGET", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertEqual(state.source_find_text, "TARGET")
        self.assertEqual(state.file_find_text, "file-query")
        self.assertEqual(state.task_find_text, "task-query")
        self.assertIn('Found "TARGET" at line 2.', state.status_message)

    def test_browser_command_executor_repeats_source_file_find_matches(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "target one\nmiddle\ntarget two\n",
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                find = executor.execute(parse_browser_command("find target", raw_keys=True))
                next_match = executor.execute(
                    parse_browser_command("next match", raw_keys=True)
                )
                line_after_next = state.source_file_line
                previous_match = executor.execute(
                    parse_browser_command("prev match", raw_keys=True)
                )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(line_after_next, 3)
        self.assertEqual(state.source_file_line, 1)
        self.assertEqual(state.source_find_text, "target")
        self.assertIn('Found "target" at line 1.', state.status_message)

    def test_browser_command_executor_jumps_source_file_symbols(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('first')",
                        "  }",
                        "  private onTap = () => {",
                        "    this.handleTap()",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_symbol = executor.execute(parse_browser_command("next symbol"))
                line_after_next = state.source_file_line
                scroll_after_next = state.source_file_scroll
                prev_symbol = executor.execute(parse_browser_command("prev symbol"))

        self.assertTrue(next_symbol.handled)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(line_after_next, 5)
        self.assertEqual(scroll_after_next, -1)
        self.assertTrue(prev_symbol.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertIn("已跳到源码符号 struct Foo > method build src/Foo.ets:2.", state.status_message)

    def test_browser_command_executor_reports_source_symbol_jump_empty_states(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                no_symbols = executor.execute(parse_browser_command("next symbol"))
                no_symbol_message = state.status_message
                state.source_file_path = "src/Missing.ets"
                missing = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(no_symbols.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(no_symbol_message, "没有可跳转的源码符号。")
        self.assertIn("Source file not found.", state.status_message)

    def test_browser_command_executor_reports_source_symbol_jump_boundaries(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('first')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                previous_symbol = executor.execute(parse_browser_command("prev symbol"))
                previous_message = state.status_message
                state.source_file_line = 4
                next_symbol = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(previous_symbol.needs_redraw)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(previous_message, "已经在第一个源码符号。")
        self.assertEqual(state.source_file_line, 4)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(state.status_message, "已经在最后一个源码符号。")

    def test_browser_command_executor_reports_source_file_find_empty_states(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                empty = executor.execute(parse_browser_command("find", raw_keys=True))
                missing = executor.execute(parse_browser_command("find owner", raw_keys=True))
                repeat = executor.execute(parse_browser_command("next match", raw_keys=True))
                state.source_file_path = "src/Missing.ets"
                unreadable = executor.execute(
                    parse_browser_command("find alpha", raw_keys=True)
                )

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertTrue(repeat.needs_redraw)
        self.assertTrue(unreadable.needs_redraw)
        self.assertEqual(state.source_find_text, "owner")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertIn("Source file not found.", state.status_message)

    def test_browser_command_executor_reports_no_task_problem_to_view(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("view problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertIn("No task problem to view.", state.status_message)

    def test_browser_command_executor_does_not_copy_empty_task_problems(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.TASK_PROBLEMS)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy problem"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No task problem to copy.", state.status_message)

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy problems"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No task problems to copy.", state.status_message)


    def test_browser_file_actions_report_when_no_changed_file_is_available(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with patch("cr.ui.browser.file_actions.reveal_path") as reveal:
                with redirect_stdout(output):
                    copy_result = executor.execute(parse_browser_command("copy path"))
                    reveal_result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(copy_result.handled)
        self.assertTrue(reveal_result.handled)
        copy.assert_not_called()
        reveal.assert_not_called()
        self.assertIn("No changed file to copy.", output.getvalue())
        self.assertIn("No changed file to reveal.", output.getvalue())

    def test_browser_command_executor_shows_task_diagnostics_without_starting_task(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.task_runtime.task_diagnostic_lines",
                    return_value=["Task commands:", "build: missing"],
                ) as diagnostics:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("tasks"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        diagnostics.assert_called_once_with(repo, args)
        self.assertIn("Task commands:", output.getvalue())
        self.assertIn("build: missing", output.getvalue())

    def test_browser_command_executor_shows_task_schema_help_without_starting_task(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.task_runtime.task_schema_help_lines",
            return_value=["Task preset file: .cr/tasks.json"],
        ) as help_lines:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("tasks help"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        help_lines.assert_called_once_with()
        self.assertIn("Task preset file: .cr/tasks.json", output.getvalue())


    def test_browser_command_executor_copies_visible_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool {text}",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=3,
            paths=[],
            code=False,
            untracked=True,
        )
        src_change = FileChange("src/Sample.ts", 2, 1)
        docs_change = FileChange("docs/Guide.md", 1, 0)
        state = BrowserState(
            [src_change, docs_change],
            selected=0,
            page=BrowserPage.FILE_DETAIL,
            filter_text="src",
            seen_paths={"src/Sample.ts"},
            review_notes={
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Sample.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Sample.ts",
            ) as render_prompt:
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 0},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.filter_text, "src")
        self.assertEqual(
            state.review_notes,
            {
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        self.assertIsNone(state.task)
        build_data.assert_called_once_with(
            [src_change],
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 0},
            context=3,
            seen_paths={"src/Sample.ts"},
            review_notes={"src/Sample.ts": "check lifecycle"},
        )
        render_prompt.assert_called_once()
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Sample.ts",
            "copy-tool {text}",
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())

    def test_browser_command_executor_saves_visible_scope_prompt_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=3,
                paths=[],
                code=False,
                untracked=True,
            )
            src_change = FileChange("src/Sample.ts", 2, 1)
            docs_change = FileChange("docs/Guide.md", 1, 0)
            state = BrowserState(
                [src_change, docs_change],
                selected=0,
                page=BrowserPage.FILE_DETAIL,
                filter_text="src",
                seen_paths={"src/Sample.ts"},
                review_notes={
                    "src/Sample.ts": "check lifecycle",
                    "docs/Guide.md": "outside filtered handoff",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Sample.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Sample.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                                with redirect_stdout(output):
                                    result = executor.execute(
                                        parse_browser_command("save prompt")
                                    )

            target = repo / ".cr" / "handoff" / "review-prompt.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Code Review Handoff\n\nsrc/Sample.ts")
            self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
            self.assertEqual(state.selected, 0)
            self.assertEqual(state.filter_text, "src")
            self.assertIsNone(state.task)
            build_data.assert_called_once_with(
                [src_change],
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 0},
                context=3,
                seen_paths={"src/Sample.ts"},
                review_notes={"src/Sample.ts": "check lifecycle"},
            )
            copy.assert_not_called()
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
                output.getvalue(),
            )

    def test_browser_command_executor_copies_selected_file_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=False,
        )
        first_change = FileChange("src/First.ts", 2, 0)
        second_change = FileChange("src/Second.ts", 1, 1)
        state = BrowserState(
            [first_change, second_change],
            selected=1,
            page=BrowserPage.CHANGED_FILES,
            review_notes={
                "src/First.ts": "not selected",
                "src/Second.ts": "selected note",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Second.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Second.ts",
            ):
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 3},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt file")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        build_data.assert_called_once_with(
            [second_change],
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 3},
            context=2,
            seen_paths=set(),
            review_notes={"src/Second.ts": "selected note"},
        )
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Second.ts",
            None,
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())

    def test_browser_command_executor_saves_selected_file_prompt_explicit_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=False,
            )
            first_change = FileChange("src/First.ts", 2, 0)
            second_change = FileChange("src/Second.ts", 1, 1)
            state = BrowserState(
                [first_change, second_change],
                selected=1,
                page=BrowserPage.CHANGED_FILES,
                review_notes={
                    "src/First.ts": "not selected",
                    "src/Second.ts": "selected note",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Second.ts"}],
                    },
                ) as build_data:
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 3},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command(
                                        "save prompt file tmp/second.md"
                                    )
                                )

            target = repo / "tmp" / "second.md"
            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
            self.assertEqual(state.selected, 1)
            build_data.assert_called_once_with(
                [second_change],
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                include_hunks=True,
                other_changes={"staged": 0, "unstaged": 3},
                context=2,
                seen_paths=set(),
                review_notes={"src/Second.ts": "selected note"},
            )
            self.assertIn(
                "Saved prompt for 1 file to tmp/second.md",
                output.getvalue(),
            )

    def test_browser_command_executor_saves_selected_file_prompt_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState(
                [FileChange("src/First.ts", 2, 0), FileChange("src/Second.ts", 1, 1)],
                selected=1,
                review_notes={"src/Second.ts": "selected note"},
            )
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={
                        "summary": {"files": 1},
                        "files": [{"path": "src/Second.ts"}],
                    },
                ):
                    with patch(
                        "cr.ui.browser.render_prompt_handoff",
                        return_value="# Code Review Handoff\n\nsrc/Second.ts",
                    ):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            with redirect_stdout(output):
                                result = executor.execute(
                                    parse_browser_command("save prompt file")
                                )

            target = repo / ".cr" / "handoff" / "review-prompt-file.md"
            self.assertTrue(result.handled)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# Code Review Handoff\n\nsrc/Second.ts",
            )
            self.assertIn(
                "Saved prompt for 1 file to .cr/handoff/review-prompt-file.md",
                output.getvalue(),
            )

    def test_browser_command_executor_does_not_copy_empty_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed files to copy prompt.", output.getvalue())

    def test_browser_command_executor_does_not_copy_missing_file_prompt(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt file"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed file to copy prompt.", output.getvalue())

    def test_browser_command_executor_does_not_save_empty_scope_prompt(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.build_review_data") as build_data:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("save prompt"))

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            build_data.assert_not_called()
            self.assertFalse((repo / ".cr" / "handoff" / "review-prompt.md").exists())
            self.assertIn("No changed files to save prompt.", output.getvalue())

    def test_browser_command_executor_surfaces_prompt_save_failure(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            blocker = repo / "blocker"
            blocker.write_text("not a directory", encoding="utf-8")
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=True,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("save prompt blocker/review.md")
                            )

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertIn(
                "Could not save prompt to blocker/review.md",
                output.getvalue(),
            )

    def test_browser_command_executor_surfaces_prompt_copy_failure(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool",
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value="Copy failed using CLI command: copy-tool",
                ):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Copy failed using CLI command: copy-tool", output.getvalue())

    def test_browser_command_executor_copies_prompt_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=True,
        )
        frame = BrowserFrame()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch("cr.ui.browser.file_actions.copy_text", return_value=None):
                    result = executor.execute(
                        parse_browser_command("copy prompt", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn("Copied prompt for 1 file", state.status_message)

    def test_browser_command_executor_saves_prompt_in_raw_status(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            frame = BrowserFrame()
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                frame,
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            result = executor.execute(
                                parse_browser_command("save prompt", raw_keys=True)
                            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn(
            "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
            state.status_message,
        )


    def test_browser_command_executor_runs_forward_navigation(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("forward"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)

    def test_browser_command_executor_opens_page_help(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE, source_file_path="src/Foo.ets")
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("help"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.SOURCE_FILE)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)

    def test_switch_review_scope_resets_page_history(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )

        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_resets_page_history_for_reloaded_changes(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState([FileChange("src/Old.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        self.assertTrue(state.page_forward_stack)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 1, 1)]):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_preserves_file_detail_when_selected_file_survives(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 1),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            page=BrowserPage.FILE_DETAIL,
            file_scroll=20,
        )
        state.file_line_cache["stale"] = ["old"]
        state.page_back_stack.append(
            browser_module.BrowserPageSnapshot(
                BrowserPage.CHANGED_FILES,
                0,
                0,
                0,
                0,
                0,
                0,
                "",
                None,
                0,
            )
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[
                FileChange("src/Second.ts", 3, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                with patch("cr.ui.browser._max_file_scroll", return_value=8):
                    result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.changes[0].path, "src/Second.ts")
        self.assertEqual(state.file_scroll, 8)
        self.assertEqual(state.file_line_cache, {})
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])

    def test_refresh_returns_to_changed_files_when_file_detail_disappears(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
        )
        state = BrowserState(
            [FileChange("src/Old.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=12,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/New.ts", 1, 0)],
        ):
            with patch("cr.ui.browser._show_commits_when_empty"):
                result = executor.execute(parse_browser_command("refresh"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.page_back_stack, [])
        self.assertEqual(state.page_forward_stack, [])
        self.assertIn("Current file no longer visible after refresh.", state.status_message)

    def test_browser_main_loop_delegates_action_execution(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")
        run_loop_source = source[source.index("def run_browser") : source.index("def _should_restore")]

        self.assertIn("BrowserCommandExecutor(", run_loop_source)
        self.assertIn(".execute(parsed_command)", run_loop_source)
        self.assertNotIn("BrowserCommandAction.RUN_BUILD", run_loop_source)
        self.assertNotIn("BrowserCommandAction.CHOOSE_NUMBER", run_loop_source)

    def test_review_workspace_loads_filters_and_switches_scope(self):
        loads: list[tuple[bool, bool, str | None, str | None, bool]] = []

        def loader(args):
            loads.append(
                (
                    args.staged,
                    args.all_changes,
                    args.base,
                    args.ref_range,
                    args.untracked,
                )
            )
            if args.staged:
                return [FileChange("src/Staged.ts", 3, 1)]
            return [
                FileChange("src/First.ts", 1, 0),
                FileChange("docs/Second.md", 2, 0),
            ]

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
            sort="git",
        )
        workspace = ReviewWorkspace.load(args, loader=loader)

        self.assertEqual(
            [change.path for change in workspace.changes],
            ["src/First.ts", "docs/Second.md"],
        )

        workspace.set_filter("src/")
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/First.ts"],
        )
        workspace.selected = 4
        workspace.list_scroll = 3
        workspace.previous_scope = ReviewScope(False, False, None, None, True)

        workspace.switch_scope(
            args,
            ReviewScope(True, False, None, None, False),
            loader=loader,
        )

        self.assertEqual(workspace.changes, [FileChange("src/Staged.ts", 3, 1)])
        self.assertEqual(workspace.filter_text, "")
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.list_scroll, 0)
        self.assertIsNone(workspace.previous_scope)
        self.assertEqual(loads[-1], (True, False, None, None, False))

    def test_review_workspace_reloads_changes_preserving_selected_path(self):
        args = argparse_namespace()
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 0),
            ],
            selected=1,
            filter_text="src/",
            list_scroll=5,
        )

        workspace.reload_changes(
            args,
            loader=lambda _args: [
                FileChange("src/Second.ts", 3, 1),
                FileChange("src/Third.ts", 1, 0),
            ],
            preserve_selected_path="src/Second.ts",
        )

        self.assertEqual(
            workspace.changes,
            [
                FileChange("src/Second.ts", 3, 1),
                FileChange("src/Third.ts", 1, 0),
            ],
        )
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.filter_text, "src/")
        self.assertEqual(workspace.list_scroll, 5)

    def test_review_workspace_is_used_by_main_browser_implementation(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("ReviewWorkspace", source)
        self.assertIn("load_workspace_changes", source)
        self.assertNotIn("selected_changes", source)
        self.assertNotIn("sort_changes", source)

    def test_browser_frame_module_owns_task_panel_presentation_implementation(self):
        browser_source = Path(browser_module.__file__).read_text(encoding="utf-8")
        frame_source = Path(frame_module.__file__).read_text(encoding="utf-8")

        self.assertIn("class BrowserFrame", frame_source)
        self.assertIn("class ScreenLayout", frame_source)
        self.assertIn("def task_panel_lines", frame_source)
        self.assertIn("def draw_task_panel_only", frame_source)
        self.assertIn("frame_module.task_panel_lines", browser_source)
        self.assertIn("frame_module.draw_task_panel_only", browser_source)
        self.assertNotIn("shlex.quote", browser_source)
        self.assertNotIn("def task_panel_lines", browser_source)
        self.assertNotIn("def draw_task_panel_only", browser_source)

    def test_review_workspace_selects_commit_scope_and_captures_previous_scope(self):
        loads: list[str | None] = []

        def loader(args):
            loads.append(args.ref_range)
            return [FileChange("src/Commit.ts", 4, 2)]

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
        )
        commit = CommitSummary(
            commit="abcdef1234567890",
            parent="1234567890abcdef",
            authored_at="2026-06-24",
            subject="Example",
        )
        workspace = ReviewWorkspace([FileChange("src/Old.ts", 1, 1)])
        workspace.filter_text = "Old"
        workspace.selected = 3
        workspace.list_scroll = 8

        workspace.select_commit(args, commit, loader=loader)

        self.assertEqual(
            workspace.previous_scope,
            ReviewScope(True, False, None, None, False),
        )
        self.assertIs(workspace.selected_commit, commit)
        self.assertEqual(args.ref_range, "1234567890abcdef..abcdef1234567890")
        self.assertFalse(args.staged)
        self.assertFalse(args.all_changes)
        self.assertFalse(args.untracked)
        self.assertEqual(workspace.changes, [FileChange("src/Commit.ts", 4, 2)])
        self.assertEqual(workspace.filter_text, "")
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(workspace.list_scroll, 0)
        self.assertEqual(loads[-1], "1234567890abcdef..abcdef1234567890")

    def test_review_workspace_serializes_and_restores_workspace_state_data(self):
        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
        )
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=0,
            filter_text="src/",
            seen_paths={"src/First.ts"},
            remaining_only=True,
            review_notes={"src/Second.ts": "check lifecycle edge case"},
        )

        data = workspace.state_data(args, mode=BrowserPage.FILE_DETAIL)

        self.assertEqual(data["scope"]["staged"], True)
        self.assertEqual(data["selected_path"], "src/Second.ts")
        self.assertEqual(data["selected_index"], 0)
        self.assertEqual(data["mode"], "file")
        self.assertEqual(data["seen_paths"], ["src/First.ts"])
        self.assertEqual(data["remaining_only"], True)
        self.assertEqual(
            data["review_notes"],
            {"src/Second.ts": "check lifecycle edge case"},
        )

        restored_args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=True,
        )
        restored = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ]
        )
        mode = restored.restore_state(restored_args, data)

        self.assertTrue(restored_args.staged)
        self.assertFalse(restored_args.untracked)
        self.assertEqual(restored.filter_text, "src/")
        self.assertEqual(restored.selected, 0)
        self.assertEqual(restored.seen_paths, {"src/First.ts"})
        self.assertTrue(restored.remaining_only)
        self.assertEqual(
            restored.review_notes,
            {"src/Second.ts": "check lifecycle edge case"},
        )
        self.assertEqual(mode, "file")

    def test_background_task_runtime_uses_task_state_names(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertTrue(hasattr(browser_module, "TaskState"))
        self.assertFalse(hasattr(browser_module, "BuildState"))
        self.assertIn('task: "TaskState | None"', source)
        self.assertNotIn('build: "BuildState | None"', source)
        self.assertIn("def _poll_task", source)
        self.assertNotIn("def _poll_build", source)
        self.assertIn("def _task_panel_lines", source)
        self.assertNotIn("def _build_panel_lines", source)

    def test_format_counts_handles_binary_stats(self):
        self.assertEqual(format_counts(FileChange("asset.bin", None, None)), "+? -?")

    def test_open_command_uses_configured_template(self):
        from cr.ui.file_actions import open_command

        command = open_command(
            Path("/tmp/space dir/Sample.ts"),
            12,
            "code -g {fileline}",
        )

        self.assertEqual(command, ["code", "-g", "/tmp/space dir/Sample.ts:12"])

    def test_open_command_source_reports_cli_env_platform_and_missing(self):
        from cr.ui.file_actions import open_command_source

        with patch.dict(os.environ, {"CR_OPEN_CMD": "env-open {fileline}"}, clear=True):
            env_source = open_command_source(Path("/tmp/Sample.ts"), 7)
            cli_source = open_command_source(
                Path("/tmp/Sample.ts"),
                7,
                "cli-open {file}",
            )
        with patch.dict(os.environ, {}, clear=True):
            with patch("cr.ui.file_actions.shutil.which", return_value=None):
                missing_source = open_command_source(Path("/tmp/Sample.ts"), 7)
            with patch("cr.ui.file_actions.shutil.which", return_value="/usr/local/bin/code"):
                platform_source = open_command_source(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(env_source.source, "env")
        self.assertEqual(env_source.command, ["env-open", "/tmp/Sample.ts:7"])
        self.assertEqual(cli_source.source, "cli")
        self.assertEqual(cli_source.command, ["cli-open", "/tmp/Sample.ts"])
        self.assertEqual(platform_source.source, "platform")
        self.assertEqual(platform_source.command, ["code", "-g", "/tmp/Sample.ts:7"])
        self.assertEqual(missing_source.source, "missing")
        self.assertIsNone(missing_source.command)

    def test_file_action_helpers_include_source_in_open_failures(self):
        from cr.ui.file_actions import open_path

        with patch(
            "cr.ui.file_actions.subprocess.Popen",
            side_effect=OSError("missing open"),
        ):
            message = open_path(Path("/tmp/Sample.ts"), 3, "missing-open {file}")

        self.assertIn("Open failed (cli missing-open /tmp/Sample.ts)", message)
        self.assertIn("missing open", message)

    def test_open_command_prefers_gui_editor_with_line(self):
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return f"/usr/local/bin/{name}" if name == "code" else None

        with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
            command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["code", "-g", "/tmp/Sample.ts:7"])

    def test_open_command_falls_back_to_macos_open(self):
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return "/usr/bin/open" if name == "open" else None

        with patch("cr.ui.file_actions.platform.system", return_value="Darwin"):
            with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
                command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["open", "/tmp/Sample.ts"])

    def test_browse_parser_accepts_file_action_command_configuration(self):
        from cr.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "browse",
                "--copy-cmd",
                "copy-tool",
                "--reveal-cmd",
                "reveal-tool --file {file}",
            ]
        )

        self.assertEqual(args.copy_cmd, "copy-tool")
        self.assertEqual(args.reveal_cmd, "reveal-tool --file {file}")

    def test_file_action_helpers_discover_macos_clipboard_and_reveal_commands(self):
        from cr.ui.file_actions import clipboard_command, reveal_command

        def fake_which(name):
            if name in {"pbcopy", "open"}:
                return f"/usr/bin/{name}"
            return None

        with patch("cr.ui.file_actions.platform.system", return_value="Darwin"):
            with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
                self.assertEqual(clipboard_command(), ["pbcopy"])
                self.assertEqual(
                    reveal_command(Path("/tmp/Sample.ts")),
                    ["open", "-R", "/tmp/Sample.ts"],
                )

    def test_file_action_helpers_report_missing_platform_commands(self):
        from cr.ui.file_actions import copy_text, open_path, reveal_path

        with patch("cr.ui.file_actions.open_command_source") as source:
            source.return_value.command = None
            self.assertEqual(
                open_path(Path("/tmp/Sample.ts"), 7),
                (
                    "No editor opener found (missing). Set --open-cmd or "
                    "CR_OPEN_CMD, for example: --open-cmd 'code -g {fileline}'"
                ),
            )
        with patch("cr.ui.file_actions.clipboard_command", return_value=None):
            self.assertEqual(
                copy_text("src/Sample.ts"),
                "No clipboard command found (missing).",
            )
        with patch("cr.ui.file_actions.reveal_command", return_value=None):
            self.assertEqual(
                reveal_path(Path("/tmp/Sample.ts")),
                "No file browser command found (missing).",
            )

    def test_file_action_helpers_use_configured_copy_command(self):
        from cr.ui.file_actions import copy_text

        with patch("cr.ui.file_actions.subprocess.run") as run:
            result = copy_text("src/Sample.ts", "copy-tool --label {text}")

        self.assertIsNone(result)
        run.assert_called_once_with(
            ["copy-tool", "--label", "src/Sample.ts"],
            input="src/Sample.ts",
            text=True,
            check=True,
        )

    def test_file_action_helpers_include_source_in_failures(self):
        from cr.ui.file_actions import copy_text, reveal_path

        with patch(
            "cr.ui.file_actions.subprocess.run",
            side_effect=OSError("missing copy"),
        ):
            copy_result = copy_text("src/Sample.ts", "copy-tool {text}")
        with patch(
            "cr.ui.file_actions.subprocess.Popen",
            side_effect=OSError("missing reveal"),
        ):
            reveal_result = reveal_path(
                Path("/tmp/repo/src/Sample.ts"),
                "reveal-tool {file}",
            )

        self.assertIn("Copy failed (cli copy-tool src/Sample.ts)", copy_result)
        self.assertIn("missing copy", copy_result)
        self.assertIn(
            "Reveal failed (cli reveal-tool /tmp/repo/src/Sample.ts)",
            reveal_result,
        )
        self.assertIn("missing reveal", reveal_result)

    def test_file_action_helpers_use_configured_reveal_command(self):
        from cr.ui.file_actions import reveal_path

        with patch("cr.ui.file_actions.subprocess.Popen") as popen:
            result = reveal_path(
                Path("/tmp/repo/src/Sample.ts"),
                "reveal-tool --file {file} --dir {dir}",
            )

        self.assertIsNone(result)
        popen.assert_called_once_with(
            [
                "reveal-tool",
                "--file",
                "/tmp/repo/src/Sample.ts",
                "--dir",
                "/tmp/repo/src",
            ]
        )

    def test_file_action_helpers_use_environment_configuration(self):
        from cr.ui.file_actions import (
            configured_copy_command,
            configured_reveal_command,
            copy_command_source,
            open_command,
            open_command_source,
            reveal_command_source,
        )

        with patch.dict(
            os.environ,
            {
                "CR_OPEN_CMD": "env-open {fileline}",
                "CR_COPY_CMD": "env-copy {text}",
                "CR_REVEAL_CMD": "env-reveal {file}",
            },
            clear=True,
        ):
            self.assertEqual(
                open_command(Path("/tmp/repo/src/Sample.ts"), 7),
                ["env-open", "/tmp/repo/src/Sample.ts:7"],
            )
            self.assertEqual(
                open_command(
                    Path("/tmp/repo/src/Sample.ts"),
                    7,
                    "cli-open {file}",
                ),
                ["cli-open", "/tmp/repo/src/Sample.ts"],
            )
            self.assertEqual(
                configured_copy_command("src/Sample.ts"),
                ["env-copy", "src/Sample.ts"],
            )
            self.assertEqual(
                configured_copy_command("src/Sample.ts", "cli-copy {text}"),
                ["cli-copy", "src/Sample.ts"],
            )
            self.assertEqual(
                configured_reveal_command(Path("/tmp/repo/src/Sample.ts")),
                ["env-reveal", "/tmp/repo/src/Sample.ts"],
            )
            self.assertEqual(
                configured_reveal_command(
                    Path("/tmp/repo/src/Sample.ts"),
                    "cli-reveal {dir}",
                ),
                ["cli-reveal", "/tmp/repo/src"],
            )
            copy_env = copy_command_source("src/Sample.ts")
            copy_cli = copy_command_source("src/Sample.ts", "cli-copy {text}")
            open_env = open_command_source(Path("/tmp/repo/src/Sample.ts"), 7)
            open_cli = open_command_source(
                Path("/tmp/repo/src/Sample.ts"),
                7,
                "cli-open {file}",
            )
            reveal_env = reveal_command_source(Path("/tmp/repo/src/Sample.ts"))
            reveal_cli = reveal_command_source(
                Path("/tmp/repo/src/Sample.ts"),
                "cli-reveal {dir}",
            )
        with patch.dict(os.environ, {}, clear=True):
            with patch("cr.ui.file_actions.clipboard_command", return_value=["pbcopy"]):
                copy_platform = copy_command_source("src/Sample.ts")
            with patch(
                "cr.ui.file_actions.reveal_command",
                return_value=["open", "-R", "/tmp/repo/src/Sample.ts"],
            ):
                reveal_platform = reveal_command_source(
                    Path("/tmp/repo/src/Sample.ts")
                )

        self.assertEqual(open_env.source, "env")
        self.assertEqual(open_env.command, ["env-open", "/tmp/repo/src/Sample.ts:7"])
        self.assertEqual(open_cli.source, "cli")
        self.assertEqual(open_cli.command, ["cli-open", "/tmp/repo/src/Sample.ts"])
        self.assertEqual(copy_env.source, "env")
        self.assertEqual(copy_env.command, ["env-copy", "src/Sample.ts"])
        self.assertEqual(copy_cli.source, "cli")
        self.assertEqual(copy_cli.command, ["cli-copy", "src/Sample.ts"])
        self.assertEqual(copy_platform.source, "platform")
        self.assertEqual(copy_platform.command, ["pbcopy"])
        self.assertEqual(reveal_env.source, "env")
        self.assertEqual(reveal_env.command, ["env-reveal", "/tmp/repo/src/Sample.ts"])
        self.assertEqual(reveal_cli.source, "cli")
        self.assertEqual(reveal_cli.command, ["cli-reveal", "/tmp/repo/src"])
        self.assertEqual(reveal_platform.source, "platform")
        self.assertEqual(
            reveal_platform.command,
            ["open", "-R", "/tmp/repo/src/Sample.ts"],
        )

    def test_build_command_detects_douyin_harmony_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")

            self.assertEqual(
                _build_command(repo),
                ["./remote", "buildEntry", "--app", "douyin"],
            )
            self.assertEqual(
                _build_command(repo, "./custom build"),
                ["./custom", "build"],
            )

    def test_task_command_resolves_configured_test_and_lint_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd="./build.sh",
                test_cmd="npm test -- --watch=false",
                lint_cmd="npm run lint",
            )

            self.assertEqual(_task_command(repo, args, "build"), ["./build.sh"])
            self.assertEqual(
                _task_command(repo, args, "test"),
                ["npm", "test", "--", "--watch=false"],
            )
            self.assertEqual(
                _task_command(repo, args, "lint"),
                ["npm", "run", "lint"],
            )

    def test_task_command_does_not_guess_test_or_lint_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(build_cmd=None, test_cmd=None, lint_cmd=None)

            self.assertIsNone(_task_command(repo, args, "test"))
            self.assertIsNone(_task_command(repo, args, "lint"))

    def test_task_panel_collects_background_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = (
                f"{sys.executable} -c "
                "\"print('compile line 1'); print('compile line 2')\""
            )
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task)
            if state.task.returncode is None:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            self.assertEqual(state.task.returncode, 0)
            _poll_task(state.task)
            lines = _task_panel_lines(state.task, TerminalStyle(False), 5)
            text = "\n".join(lines)
            self.assertIn("Build succeeded.", text)
            self.assertIn("compile line 1", text)
            self.assertIn("compile line 2", text)

    def test_test_task_collects_background_output_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"print('test line')\""
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=command,
                lint_cmd=None,
            )
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                from cr.ui.browser import _start_task

                _start_task(state, args, "test")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task)
            if state.task.returncode is None:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            self.assertEqual(state.task.returncode, 0)
            _poll_task(state.task)
            _record_completed_task(state)
            lines = _task_panel_lines(state.task, TerminalStyle(False), 5)
            text = "\n".join(lines)
            self.assertIn("Test succeeded.", text)
            self.assertIn("test line", text)
            self.assertEqual(state.task_history[0].kind, "test")

    def test_lint_task_without_command_shows_configuration_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=None,
                lint_cmd=None,
            )
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                from cr.ui.browser import _start_task

                _start_task(state, args, "lint")

            self.assertIsNotNone(state.task)
            self.assertEqual(state.task.kind, "lint")
            self.assertEqual(_task_status(state.task), "failed to start")
            self.assertIn(
                "No lint command configured. Set --lint-cmd or CR_LINT_CMD.",
                state.task.lines,
            )

    def test_task_panel_renders_recent_task_history(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        build = TaskState(
            ["./build.sh"],
            process,
            lines=["compile line"],
            returncode=0,
        )
        history = [
            TaskRecord(
                kind="build",
                status="failed (1)",
                command=["./build.sh"],
                returncode=1,
            )
        ]

        lines = _task_panel_lines(build, TerminalStyle(False), 6, history)
        text = "\n".join(lines)

        self.assertIn("Recent: build failed (1) ./build.sh", text)
        self.assertIn("compile line", text)

    def test_completed_build_records_task_history_once(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [],
            task=TaskState(
                ["./build.sh"],
                process,
                lines=["Build succeeded."],
                returncode=0,
            ),
        )

        _record_completed_task(state)
        _record_completed_task(state)

        self.assertEqual(len(state.task_history), 1)
        self.assertEqual(state.task_history[0].kind, "build")
        self.assertEqual(state.task_history[0].status, "succeeded")
        self.assertEqual(state.task_history[0].returncode, 0)

    def test_stop_without_running_build_does_not_record_task_history(self):
        state = BrowserState([])

        _stop_task(state)
        _record_completed_task(state)

        self.assertEqual(state.task_history, [])

    def test_browse_screen_task_panel_includes_task_history(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["./build.sh"], process, lines=["compile line"]),
            task_history=[
                TaskRecord(
                    kind="build",
                    status="succeeded",
                    command=["./old-build.sh"],
                    returncode=0,
                )
            ],
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Recent: build succeeded ./old-build.sh", text)


    def test_browse_screen_renders_task_problems_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("sample", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/Foo.ets", 1, 1)],
                page=BrowserPage.TASK_PROBLEMS,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    kind="build",
                    lines=["src/Foo.ets:12:3 error: bad call"],
                    returncode=1,
                ),
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.frame.shutil.get_terminal_size",
                    return_value=os.terminal_size((120, 12)),
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Task Problems", text)
        self.assertIn("Task problems", text)
        self.assertIn("src/Foo.ets:12:3", text)
        self.assertIn("bad call", text)
        self.assertIn("cr:problems> ", text)

    def test_browse_screen_renders_source_file_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_context_lines=8,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.frame.shutil.get_terminal_size",
                    return_value=os.terminal_size((120, 12)),
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Source > src/Foo.ets", text)
        self.assertIn("Source src/Foo.ets", text)
        self.assertIn("context: 8", text)
        self.assertIn("> 2  two", text)
        self.assertIn("cr:source> ", text)

    def test_build_start_records_process_group_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")

            self.assertIsNotNone(state.task)
            try:
                self.assertEqual(
                    state.task.process_group_id,
                    state.task.process.pid,
                )
            finally:
                if state.task.running:
                    state.task.process.terminate()
                    state.task.process.wait(timeout=1)
                if state.task.process.stdout is not None:
                    state.task.process.stdout.close()

    def test_build_stop_terminates_child_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            child_pid_file = repo / "child.pid"
            script.write_text(
                "from pathlib import Path\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
                "Path('child.pid').write_text(str(child.pid))\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])
            child_pid: int | None = None

            def pid_is_running(pid: int) -> bool:
                try:
                    os.kill(pid, 0)
                except OSError:
                    return False
                return True

            try:
                with patch("cr.ui.browser.git.repo_root", return_value=repo):
                    _start_task(state, args, "build")
                    self.assertIsNotNone(state.task)
                    for _ in range(100):
                        if child_pid_file.exists():
                            child_pid = int(child_pid_file.read_text(encoding="utf-8"))
                            break
                        time.sleep(0.01)
                    self.assertIsNotNone(child_pid)
                    self.assertTrue(pid_is_running(child_pid))

                    _stop_task(state)
                    for _ in range(100):
                        _poll_task(state.task)
                        if state.task.returncode is not None and not pid_is_running(child_pid):
                            break
                        time.sleep(0.01)

                self.assertFalse(pid_is_running(child_pid))
            finally:
                if child_pid is not None and pid_is_running(child_pid):
                    os.kill(child_pid, signal.SIGKILL)
                if state.task is not None and state.task.running:
                    state.task.process.terminate()
                    state.task.process.wait(timeout=1)

    def test_build_stop_falls_back_when_process_group_stop_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                with patch(
                    "cr.ui.tasks.os.killpg",
                    side_effect=OSError("pg gone"),
                ):
                    _stop_task(state)
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            try:
                self.assertIsNotNone(state.task.returncode)
                self.assertEqual(_task_status(state.task), "stopped")
                self.assertTrue(
                    any(
                        "Build process group stop failed: pg gone" in line
                        for line in state.task.lines
                    )
                )
            finally:
                if state.task is not None and state.task.running:
                    state.task.process.kill()

    def test_poll_escalates_stopped_build_to_process_group_kill(self):
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

            def kill(self):
                raise AssertionError("process.kill should not be used with a process group")

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_called_once_with(1234, signal.SIGKILL)
        self.assertTrue(build.stop_escalated)
        self.assertIn("Build did not stop; force killing process group.", build.lines)

    def test_poll_does_not_escalate_stopped_build_within_grace_period(self):
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

            def kill(self):
                raise AssertionError("process.kill should not run inside grace period")

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=9.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_not_called()
        self.assertFalse(build.stop_escalated)
        self.assertEqual(build.lines, [])

    def test_poll_escalates_stopped_build_only_once(self):
        class RunningProcess:
            stdout = None

            def poll(self):
                return None

        build = TaskState(
            ["fake-build"],
            RunningProcess(),
            process_group_id=1234,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)
                _poll_task(build)

        killpg.assert_called_once_with(1234, signal.SIGKILL)
        self.assertEqual(
            build.lines.count("Build did not stop; force killing process group."),
            1,
        )

    def test_poll_escalates_stopped_build_without_process_group_to_process_kill(self):
        class RunningProcess:
            stdout = None

            def __init__(self):
                self.kill_count = 0

            def poll(self):
                return None

            def kill(self):
                self.kill_count += 1

        process = RunningProcess()
        build = TaskState(
            ["fake-build"],
            process,
            process_group_id=None,
            stop_requested=True,
            stop_requested_at=0.0,
        )

        with patch("cr.ui.tasks.time.monotonic", return_value=10.0):
            with patch("cr.ui.tasks.os.killpg") as killpg:
                _poll_task(build)

        killpg.assert_not_called()
        self.assertEqual(process.kill_count, 1)
        self.assertTrue(build.stop_escalated)
        self.assertIn("Build did not stop; force killing build process.", build.lines)

    def test_build_stop_records_stop_request_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                before_stop = time.monotonic()
                _stop_task(state)
                after_stop = time.monotonic()

            try:
                self.assertGreaterEqual(state.task.stop_requested_at, before_stop)
                self.assertLessEqual(state.task.stop_requested_at, after_stop)
                self.assertFalse(state.task.stop_escalated)
            finally:
                if state.task is not None and state.task.running:
                    state.task.process.kill()
                    state.task.process.wait(timeout=1)
                if state.task.process.stdout is not None:
                    state.task.process.stdout.close()

    def test_build_stop_marks_stopped_not_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                self.assertTrue(state.task.running)

                _stop_task(state)
                self.assertTrue(state.task.stop_requested)
                self.assertEqual(_task_status(state.task), "stopping")
                self.assertIn("Stopping build...", state.task.lines)

                for _ in range(100):
                    _poll_task(state.task)
                    if state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.task.returncode)
            self.assertEqual(_task_status(state.task), "stopped")
            self.assertIn("Build stopped.", state.task.lines)

    def test_build_rerun_starts_new_process_after_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            output = repo / "build.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('build.out')\n"
                "path.write_text(path.read_text() + 'run\\n' if path.exists() else 'run\\n')\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)
                self.assertEqual(state.task.returncode, 0)

                _rerun_task(state, args)
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertEqual(state.task.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "run\nrun\n")

    def test_rerun_repeats_recent_test_task_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "test_task.py"
            output = repo / "test.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('test.out')\n"
                "path.write_text(path.read_text() + 'test\\n' if path.exists() else 'test\\n')\n",
                encoding="utf-8",
            )
            args = argparse_namespace(
                build_cmd=None,
                test_cmd=f"{sys.executable} {script}",
                lint_cmd=None,
            )
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                from cr.ui.browser import _start_task

                _start_task(state, args, "test")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)
                self.assertEqual(state.task.kind, "test")
                self.assertEqual(state.task.returncode, 0)

                _rerun_task(state, args)
                self.assertEqual(state.task.kind, "test")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertEqual(state.task.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "test\ntest\n")

    def test_build_rerun_keeps_previous_task_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "build.py"
            output = repo / "build.out"
            script.write_text(
                "from pathlib import Path\n"
                "path = Path('build.out')\n"
                "count = int(path.read_text()) if path.exists() else 0\n"
                "path.write_text(str(count + 1))\n",
                encoding="utf-8",
            )
            args = argparse_namespace(build_cmd=f"{sys.executable} {script}")
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                for _ in range(100):
                    _poll_task(state.task)
                    if state.task and state.task.returncode is not None:
                        break
                    time.sleep(0.01)
                _record_completed_task(state)

                self.assertEqual(len(state.task_history), 1)

                _rerun_task(state, args)

            self.assertEqual(len(state.task_history), 1)
            self.assertEqual(state.task_history[0].status, "succeeded")
            self.assertIsNotNone(state.task)
            self.assertIsNone(state.task.returncode)
            if state.task.running:
                state.task.process.terminate()
                state.task.process.wait(timeout=1)
            if state.task.process.stdout is not None:
                state.task.process.stdout.close()

    def test_build_rerun_while_running_does_not_start_second_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = f"{sys.executable} -c \"import time; time.sleep(10)\""
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_task(state, args, "build")
                self.assertIsNotNone(state.task)
                first_process = state.task.process

                _rerun_task(state, args)

            self.assertIs(state.task.process, first_process)
            self.assertIn("Build is already running. Stop it before rerun.", state.task.lines)
            _stop_task(state)
            for _ in range(100):
                _poll_task(state.task)
                if state.task.returncode is not None:
                    break
                time.sleep(0.01)

    def test_build_stop_without_running_build_shows_feedback(self):
        state = BrowserState([])

        _stop_task(state)

        self.assertIsNotNone(state.task)
        self.assertEqual(_task_status(state.task), "idle")
        self.assertIn("No build is running.", state.task.lines)

    def test_task_panel_partial_refresh_does_not_clear_screen(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["compile line"])
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                _draw_task_panel_only(build, TerminalStyle(False))

        text = output.getvalue()
        self.assertNotIn("\033[2J", text)
        self.assertIn("\0337", text)
        self.assertIn("\033[7;1H", text)
        self.assertIn("\0338", text)
        self.assertIn("compile line", text)

        output = StringIO()
        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                _draw_task_panel_only(build, TerminalStyle(False))

        self.assertEqual(output.getvalue(), "")
        process.wait(timeout=1)

    def test_full_browser_redraw_primes_task_panel_frame_cache(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        frame = BrowserFrame()
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False), frame)

                    output = StringIO()
                    with redirect_stdout(output):
                        refreshed = _draw_task_panel_only(
                            state.task,
                            TerminalStyle(False),
                            frame,
                        )

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        process.wait(timeout=1)

    def test_task_panel_partial_refresh_refuses_stale_frame_layout(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=False,
        )
        build.last_rendered_panel = ["old panel"]
        build.lines.append("new line")
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 30)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_task_panel_partial_refresh_refuses_dirty_frame(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=True,
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_browser_status_message_marks_frame_dirty_before_task_refresh(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["first line"])
        frame = BrowserFrame(
            layout=_screen_layout(build, rows=12),
            complete=True,
            task_panel=["old panel"],
            dirty=False,
        )
        state = BrowserState([], task=build)
        output = StringIO()

        _show_browser_message(state, "Opened src/Sample.ts:3", raw_keys=True, frame=frame)

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with redirect_stdout(output):
                refreshed = _draw_task_panel_only(build, TerminalStyle(False), frame)

        self.assertEqual(state.status_message, "Opened src/Sample.ts:3")
        self.assertFalse(refreshed)
        self.assertEqual(output.getvalue(), "")
        self.assertTrue(frame.dirty)
        process.wait(timeout=1)

    def test_command_prompt_cancel_forces_full_browser_redraw(self):
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
                                    side_effect=["command_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_command_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)

    def test_filter_prompt_cancel_forces_full_browser_redraw(self):
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
                                    side_effect=["filter_prompt", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._read_filter_query",
                                        return_value="__interrupt__",
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen"
                                        ) as draw:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(draw.call_count, 2)


    def test_task_problems_page_tick_redraws_main_content_not_panel_only(self):
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
        processes: list[subprocess.Popen[bytes]] = []

        def start_running_task(state, _args, _kind):
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            processes.append(process)
            state.task = TaskState(["sleep"], process, lines=["first line"])

        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                with patch("cr.ui.browser.git.repo_root", return_value=repo):
                    with patch(
                        "cr.ui.browser._should_restore_browser_workspace_state",
                        return_value=False,
                    ):
                        with patch(
                            "cr.ui.browser._load_browse_changes",
                            return_value=[FileChange("src/Sample.ts", 1, 1)],
                        ):
                            with patch("cr.ui.browser._show_commits_when_empty"):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "build",
                                            "problems",
                                            browser_input.TICK,
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._start_task",
                                            side_effect=start_running_task,
                                        ):
                                            with patch(
                                                "cr.ui.browser._draw_browse_screen"
                                            ) as draw:
                                                with patch(
                                                    "cr.ui.browser._draw_task_panel_only"
                                                ) as panel_only:
                                                    from cr.ui.browser import run_browser

                                                    result = run_browser(args)
        finally:
            for process in processes:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)

        self.assertEqual(result, 0)
        self.assertGreaterEqual(draw.call_count, 4)
        panel_only.assert_not_called()

    def test_screen_layout_reserves_prompt_and_task_panel_regions(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, lines=["compile line"])

        plain = _screen_layout(None, rows=12)
        with_task = _screen_layout(build, rows=12)

        self.assertEqual(plain.prompt_row, 12)
        self.assertEqual(plain.content_height, 11)
        self.assertEqual(plain.task_height, 0)
        self.assertIsNone(plain.task_start_row)
        self.assertEqual(with_task.prompt_row, 12)
        self.assertEqual(with_task.task_start_row, 7)
        self.assertEqual(with_task.task_height, 5)
        self.assertEqual(with_task.content_height, 6)
        process.wait(timeout=1)

    def test_browse_screen_redraws_in_place(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertTrue(text.startswith("\033[2J\033[H"))
        self.assertIn("Scope: worktree > Files", text)
        self.assertIn("> 1", text)
        self.assertIn("└─ src", text)
        self.assertIn("└─ Sample.ts", text)
        self.assertIn("操作：Enter 打开", text)

    def test_browse_screen_action_bar_coexists_with_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((80, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("操作：Enter 打开", text)
        self.assertIn("compile line", text)
        self.assertIn("Build running", text)

    def test_browse_screen_file_detail_shows_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
            context=2,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="file")
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with patch(
                    "cr.ui.browser.change_hunk_lines",
                    return_value=["changes:", "  3 + added"],
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Files > src/Sample.ts", text)
        self.assertIn("操作：]/[ 跳转 hunk", text)

    def test_browse_screen_recent_commits_stays_scope_picker(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                )
            ],
            page="commits",
        )
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: recent commits", text)
        self.assertNotIn("Scope: recent commits > Files", text)

    def test_commit_picker_rows_show_change_summary(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Example change",
                    files=2,
                    added=10,
                    deleted=3,
                )
            ],
            page=BrowserPage.COMMIT_PICKER,
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )

        self.assertIn("2 files, +10 -3", "\n".join(lines))
        self.assertIn("Example change", "\n".join(lines))

    def test_commit_picker_filter_matches_scope_summary_fields(self):
        commits = [
            CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-24",
                subject="Feature login",
                files=2,
                added=10,
                deleted=3,
            ),
            CommitSummary(
                commit="1111111122222222",
                parent="abcdef1234567890",
                authored_at="2026-06-25",
                subject="Docs only",
                files=1,
                added=1,
                deleted=0,
            ),
        ]

        self.assertEqual(commit_picker.filter_commits_by_query(commits, ""), commits)
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "ABCDEF"),
            [commits[0]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "2026-06-25"),
            [commits[1]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "login"),
            [commits[0]],
        )
        self.assertEqual(
            commit_picker.filter_commits_by_query(commits, "+10 -3"),
            [commits[0]],
        )

    def test_commit_picker_selected_commit_uses_filtered_results(self):
        commits = [
            CommitSummary(
                commit="1111111111111111",
                parent="0000000000000000",
                authored_at="2026-06-24",
                subject="Docs only",
            ),
            CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-25",
                subject="Feature login",
            ),
        ]

        self.assertIs(
            commit_picker.selected_commit(commits, selected=0, query="login"),
            commits[1],
        )
        self.assertIsNone(
            commit_picker.selected_commit(commits, selected=0, query="missing")
        )
        self.assertIsNone(commit_picker.selected_commit(commits, selected=9))

    def test_commit_picker_filter_shows_matches_and_count(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                    files=2,
                    added=10,
                    deleted=3,
                ),
                CommitSummary(
                    commit="1111111122222222",
                    parent="abcdef1234567890",
                    authored_at="2026-06-25",
                    subject="Docs only",
                    files=1,
                    added=1,
                    deleted=0,
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn('Filter: login (1/2 matches, c to clear)', text)
        self.assertIn("Feature login", text)
        self.assertNotIn("Docs only", text)

    def test_commit_picker_filter_empty_state(self):
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="missing",
        )

        lines = page_content.browse_commit_screen_lines(
            state,
            TerminalStyle(),
            max_lines=10,
        )
        text = "\n".join(lines)

        self.assertIn("No recent commits match filter: missing (1 total).", text)
        self.assertIn("Press c to clear the filter.", text)

    def test_commit_picker_filter_commands_are_isolated_from_file_filter(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-24",
                    subject="Feature login",
                )
            ],
            page=BrowserPage.COMMIT_PICKER,
            filter_text="src/",
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        set_result = executor.execute(parse_browser_command("/login"))
        clear_result = executor.execute(parse_browser_command("c"))

        self.assertTrue(set_result.handled)
        self.assertTrue(set_result.needs_redraw)
        self.assertTrue(clear_result.handled)
        self.assertEqual(state.page, BrowserPage.COMMIT_PICKER)
        self.assertEqual(state.filter_text, "src/")
        self.assertEqual(state.commit_filter_text, "")

    def test_commit_picker_number_selects_filtered_commit(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        state = BrowserState(
            [],
            commits=[
                CommitSummary(
                    commit="1111111111111111",
                    parent="0000000000000000",
                    authored_at="2026-06-24",
                    subject="Docs only",
                ),
                CommitSummary(
                    commit="abcdef1234567890",
                    parent="1234567890abcdef",
                    authored_at="2026-06-25",
                    subject="Feature login",
                ),
            ],
            page=BrowserPage.COMMIT_PICKER,
            commit_filter_text="login",
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch(
            "cr.ui.browser._load_browse_changes",
            return_value=[FileChange("src/Login.ts", 1, 0)],
        ):
            result = executor.execute(parse_browser_command("1"))

        self.assertTrue(result.handled)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected_commit.subject, "Feature login")
        self.assertEqual(args.ref_range, "1234567890abcdef..abcdef1234567890")

    def test_commit_picker_filter_prompt_does_not_change_file_filter(self):
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
            frames.append((state.mode, state.filter_text, state.commit_filter_text))

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch(
                            "cr.ui.browser._load_recent_commits",
                            return_value=[
                                CommitSummary(
                                    commit="abcdef1234567890",
                                    parent="1234567890abcdef",
                                    authored_at="2026-06-25",
                                    subject="Feature login",
                                )
                            ],
                        ):
                            with patch("cr.ui.browser._show_commits_when_empty"):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=["g", "filter_prompt", "q"],
                                    ):
                                        with patch(
                                            "cr.ui.browser._read_filter_query",
                                            return_value="login",
                                        ):
                                            with patch(
                                                "cr.ui.browser._draw_browse_screen",
                                                side_effect=capture_draw,
                                            ):
                                                from cr.ui.browser import run_browser

                                                result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn((BrowserPage.COMMIT_PICKER, "", "login"), frames)

    def test_browse_screen_selected_commit_files_show_product_breadcrumb(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range="abcdef1^..abcdef1",
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            selected_commit=CommitSummary(
                commit="abcdef1234567890",
                parent="1234567890abcdef",
                authored_at="2026-06-24",
                subject="Example change",
            ),
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        self.assertIn("Scope: commit abcdef12 > Files", output.getvalue())

    def test_browse_screen_scope_home_shows_review_scope_entries(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], page="scopes")
        output = StringIO()

        with redirect_stdout(output):
            _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: scope home", text)
        self.assertNotIn("Scope: scope home > Files", text)
        self.assertIn("Review scopes", text)
        self.assertIn("Worktree", text)
        self.assertIn("Staged", text)
        self.assertIn("All local changes", text)
        self.assertIn("Recent commits", text)
        self.assertIn("Base ref", text)
        self.assertIn(": base REF", text)
        self.assertIn("Explicit range", text)
        self.assertIn(": range OLD..NEW", text)

    def test_scope_home_screen_shows_live_scope_counts(self):
        state = BrowserState(
            [],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={
                "worktree": 2,
                "staged": 1,
                "all": 3,
                "commits": 4,
            },
        )

        lines = page_content.browse_scope_home_screen_lines(
            state,
            TerminalStyle(),
            max_lines=20,
        )
        text = "\n".join(lines)

        self.assertIn("Worktree (2 files)", text)
        self.assertIn("Staged (1 file)", text)
        self.assertIn("All local changes (3 files)", text)
        self.assertIn("Recent commits (4 commits)", text)
        self.assertNotIn("Base ref (", text)
        self.assertNotIn("Explicit range (", text)

    def test_scope_home_command_opens_scope_home(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.mode)

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
                                    side_effect=["scopes", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("scopes", frames)

    def test_scope_home_command_loads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 2, "staged": 1, "all": 3, "commits": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("scopes", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 2)
        load_counts.assert_called_once_with(args)

    def test_scope_home_refresh_reloads_scope_counts(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.SCOPE_HOME,
            scope_counts={"worktree": 1},
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._load_scope_home_counts",
            return_value={"worktree": 4},
        ) as load_counts:
            result = executor.execute(parse_browser_command("r", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_counts["worktree"], 4)
        load_counts.assert_called_once_with(args)

    def test_scope_home_count_loader_counts_review_scope_candidates(self):
        args = argparse_namespace(paths=["src"], code=True, untracked=True)

        def changed_files(paths, staged=False, all_changes=False, include_untracked=False):
            self.assertEqual(paths, ["src"])
            if staged:
                self.assertFalse(include_untracked)
                return [FileChange("src/Staged.ts", 1, 0)]
            if all_changes:
                self.assertTrue(include_untracked)
                return [
                    FileChange("src/Staged.ts", 1, 0),
                    FileChange("src/Unstaged.ts", 1, 0),
                    FileChange("README.md", 1, 0),
                ]
            self.assertTrue(include_untracked)
            return [
                FileChange("src/Unstaged.ts", 1, 0),
                FileChange("README.md", 1, 0),
            ]

        with patch("cr.ui.browser.git.changed_files", side_effect=changed_files):
            with patch(
                "cr.ui.browser.git.recent_commits",
                return_value=[
                    CommitSummary(
                        commit="abcdef1234567890",
                        parent=None,
                        authored_at="2026-06-24",
                        subject="Example",
                    )
                ],
            ):
                counts = browser_module._load_scope_home_counts(args)

        self.assertEqual(
            counts,
            {"worktree": 1, "staged": 1, "all": 2, "commits": 1},
        )

    def test_scope_home_enter_switches_to_staged_scope(self):
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
        frames: list[tuple[str, bool, bool]] = []

        def capture_draw(state, args, style, frame=None):
            frames.append((state.mode, args.staged, args.all_changes))

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
                                    side_effect=["scopes", "down", "enter", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", True, False), frames)

    def test_scope_home_enter_opens_recent_commits(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.mode)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._should_restore_browser_workspace_state", return_value=False):
                    with patch(
                        "cr.ui.browser._load_browse_changes",
                        return_value=[FileChange("src/Sample.ts", 1, 1)],
                    ):
                        with patch("cr.ui.browser._show_commits_when_empty"):
                            with patch(
                                "cr.ui.browser._load_recent_commits",
                                return_value=[
                                    CommitSummary(
                                        commit="abcdef1234567890",
                                        parent="1234567890abcdef",
                                        authored_at="2026-06-24",
                                        subject="Example change",
                                    )
                                ],
                            ):
                                with patch("cr.ui.browser._use_raw_keys", return_value=True):
                                    with patch(
                                        "cr.ui.browser._read_browse_command",
                                        side_effect=[
                                            "scopes",
                                            "down",
                                            "down",
                                            "down",
                                            "enter",
                                            "q",
                                        ],
                                    ):
                                        with patch(
                                            "cr.ui.browser._draw_browse_screen",
                                            side_effect=capture_draw,
                                        ):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn("commits", frames)

    def test_home_key_still_jumps_to_first_file_instead_of_opening_scope_home(self):
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
                                    side_effect=["down", "home", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        from cr.ui.browser import run_browser

                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertIn(("list", 1), frames)
        self.assertEqual(frames[-1], ("list", 0))

    def test_browse_screen_places_task_panel_above_prompt(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("compile line", text)
        self.assertIn("\033[12;1H\033[2Kcr:list> ", text)
        process.wait(timeout=1)

    def test_browse_context_line_shows_status_message(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            status_message="Opened src/Sample.ts:3",
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        self.assertIn(
            "Scope: worktree > Files  |  Opened src/Sample.ts:3",
            output.getvalue(),
        )

    def test_raw_key_open_feedback_stays_inside_browser_frame(self):
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
            open_cmd="echo {fileline}",
        )
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir()
            sample.write_text("sample\n", encoding="utf-8")
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
                                    side_effect=["open", "q"],
                                ):
                                    with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                                        with patch(
                                            "cr.ui.browser.git.repo_path",
                                            return_value=sample,
                                        ):
                                            with patch("cr.ui.file_actions.subprocess.Popen"):
                                                with patch(
                                                    "cr.ui.browser._draw_browse_screen",
                                                    side_effect=capture_draw,
                                                ):
                                                    output = StringIO()
                                                    with redirect_stdout(output):
                                                        from cr.ui.browser import run_browser

                                                        result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Opened", output.getvalue())
        self.assertIn("Opened src/Sample.ts:3", frames)

    def test_raw_key_invalid_selection_feedback_stays_inside_browser_frame(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

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
                                    side_effect=["99", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        output = StringIO()
                                        with redirect_stdout(output):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Choose 1-1.", output.getvalue())
        self.assertIn("Choose 1-1.", frames)

    def test_raw_key_unknown_command_feedback_stays_inside_browser_frame(self):
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
        frames: list[str] = []

        def capture_draw(state, args, style, frame=None):
            frames.append(state.status_message)

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
                                    side_effect=["wat", "q"],
                                ):
                                    with patch(
                                        "cr.ui.browser._draw_browse_screen",
                                        side_effect=capture_draw,
                                    ):
                                        output = StringIO()
                                        with redirect_stdout(output):
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertNotIn("Unknown command.", output.getvalue())
        self.assertTrue(any(message.startswith("Unknown command.") for message in frames))

    def test_browse_screen_pads_short_content_before_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 30)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=3):
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        before_panel = text.split("Build running", 1)[0]
        process.wait(timeout=1)
        self.assertEqual(before_panel.count("\n"), 23)

    def test_browse_screen_shows_command_list_with_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            task=TaskState(["true"], process, lines=["compile line"]),
            page="commands",
        )
        output = StringIO()

        with patch(
            "cr.ui.frame.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 40)),
        ):
            with redirect_stdout(output):
                _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        process.wait(timeout=1)
        self.assertIn("命令面板", text)
        self.assertIn("Enter：执行选中命令", text)
        self.assertIn("审查范围", text)
        self.assertIn("compile line", text)
        self.assertIn("\033[40;1H\033[2Kcr:commands> ", text)

    def test_raw_key_command_read_does_not_print_newline(self):
        output = StringIO()

        with patch("cr.ui.browser._read_raw_key", return_value="down"):
            with redirect_stdout(output):
                command = _read_browse_command("cr:list> ", raw_keys=True)

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_raw_key_reader_does_not_print_newline(self):
        output = StringIO()

        with redirect_stdout(output):
            command = browser_input.read_browse_command(
                "cr:list> ",
                raw_keys=True,
                raw_key_reader=lambda timeout=None: "down",
            )

        self.assertEqual(command, "down")
        self.assertEqual(output.getvalue(), "")

    def test_browser_input_line_mode_returns_eof_and_interrupt_sentinels(self):
        eof_output = StringIO()
        interrupt_output = StringIO()

        with patch("builtins.input", side_effect=EOFError):
            with redirect_stdout(eof_output):
                eof_command = browser_input.read_browse_command("cr:list> ", raw_keys=False)
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(interrupt_output):
                interrupt_command = browser_input.read_browse_command(
                    "cr:list> ",
                    raw_keys=False,
                )

        self.assertEqual(eof_command, browser_input.EOF_COMMAND)
        self.assertEqual(interrupt_command, browser_input.INTERRUPT)
        self.assertEqual(eof_output.getvalue(), "\n")
        self.assertEqual(interrupt_output.getvalue(), "\n")

    def test_browser_input_idle_tick_uses_raw_idle_timeout(self):
        seen_timeouts = []

        command = browser_input.read_browse_command(
            "cr:list> ",
            raw_keys=True,
            tick_when_idle=True,
            raw_key_reader=lambda timeout=None: seen_timeouts.append(timeout)
            or browser_input.TICK,
        )

        self.assertEqual(command, browser_input.TICK)
        self.assertEqual(seen_timeouts, [browser_input.RAW_IDLE_TIMEOUT_SECONDS])

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

    def test_browser_remaining_only_filters_seen_paths(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            seen_paths={"src/First.ts", "src/Third.ts"},
            remaining_only=True,
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )

    def test_review_workspace_source_filter_combines_with_path_and_remaining_filters(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 2, 1, source="unstaged"),
                FileChange("docs/Third.md", 1, 0, source="staged"),
            ],
            filter_text="src",
            source_filter="staged",
            seen_paths={"src/First.ts"},
            remaining_only=True,
        )

        self.assertEqual(workspace.visible_changes, [])
        workspace.remaining_only = False
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/First.ts"],
        )

    def test_review_workspace_marks_selected_file_seen(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        self.assertTrue(workspace.mark_selected_seen())
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

        self.assertTrue(workspace.unmark_selected_seen())
        self.assertEqual(workspace.seen_paths, set())

    def test_review_workspace_mark_seen_and_advance_uses_remaining_index(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
                FileChange("src/Third.ts", 3, 0),
            ],
            selected=0,
            remaining_only=True,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/First.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertTrue(result.had_next_before)
        self.assertEqual(workspace.seen_paths, {"src/First.ts"})
        self.assertEqual(workspace.selected, 0)
        self.assertEqual(
            [change.path for change in workspace.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )

    def test_review_workspace_mark_seen_and_advance_reports_last_file(self):
        workspace = ReviewWorkspace(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
        )

        result = workspace.mark_selected_seen_and_advance()

        self.assertEqual(result.marked_path, "src/Second.ts")
        self.assertEqual(result.target_path, "src/Second.ts")
        self.assertFalse(result.had_next_before)
        self.assertEqual(workspace.selected, 1)
        self.assertEqual(workspace.seen_paths, {"src/Second.ts"})

    def test_browser_state_syncs_source_filter_with_workspace(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0, source="staged"),
                FileChange("src/Second.ts", 1, 0, source="unstaged"),
            ],
            source_filter="staged",
        )

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/First.ts"],
        )

        state.source_filter = "unstaged"
        state._sync_to_workspace()
        state._sync_from_workspace()

        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts"],
        )

    def test_review_workspace_persists_source_filter(self):
        args = argparse_namespace(
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            untracked=False,
        )
        workspace = ReviewWorkspace(
            [FileChange("src/First.ts", 1, 0, source="staged")],
            source_filter="staged",
        )

        data = workspace.state_data(args, mode=BrowserPage.CHANGED_FILES)
        restored = ReviewWorkspace([FileChange("src/First.ts", 1, 0, source="staged")])
        restored.restore_state(args, data)

        self.assertEqual(data["source_filter"], "staged")
        self.assertEqual(restored.source_filter, "staged")

    def test_review_workspace_scope_switch_clears_source_filter(self):
        args = argparse_namespace(
            staged=False,
            all_changes=True,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        workspace = ReviewWorkspace(
            [FileChange("src/Old.ts", 1, 0, source="staged")],
            source_filter="staged",
        )

        workspace.switch_scope(
            args,
            ReviewScope(False, False, None, None, False),
            loader=lambda _args: [FileChange("src/New.ts", 1, 0, source="unstaged")],
        )

        self.assertEqual(workspace.source_filter, "")

    def test_switch_review_scope_resets_view_state_but_keeps_task_panel(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            sort="git",
            paths=[],
            code=False,
        )
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = TaskState(["true"], process, returncode=0)
        state = BrowserState(
            [FileChange("src/Old.ts", 1, 1)],
            task=build,
            selected=3,
            list_scroll=4,
            commit_scroll=2,
            file_scroll=9,
            page="file",
            filter_text="Old",
        )
        state.first_line_cache["src/Old.ts"] = 1
        state.file_line_cache["src/Old.ts"] = ["cached"]

        with patch("cr.ui.browser._load_browse_changes", return_value=[FileChange("src/New.ts", 2, 0)]):
            _switch_review_scope(
                state,
                args,
                ReviewScope(True, False, None, None, False),
            )

        self.assertTrue(args.staged)
        self.assertEqual(state.changes, [FileChange("src/New.ts", 2, 0)])
        self.assertIs(state.task, build)
        self.assertEqual(state.mode, "list")
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.list_scroll, 0)
        self.assertEqual(state.commit_scroll, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.filter_text, "")
        self.assertEqual(state.first_line_cache, {})
        self.assertEqual(state.file_line_cache, {})
        process.wait(timeout=1)

    def test_command_query_empty_or_question_mark_opens_command_list(self):
        self.assertEqual(_normalize_command_query(""), "commands")
        self.assertEqual(_normalize_command_query("?"), "commands")
        self.assertEqual(_normalize_command_query(" build "), "build")

    def test_command_list_lines_group_commands_by_purpose(self):
        lines = _browse_command_lines(TerminalStyle(False), max_lines=120)
        text = "\n".join(lines)

        self.assertIn("命令", text)
        self.assertIn("导航", text)
        self.assertIn("审查范围", text)
        self.assertIn("任务", text)
        self.assertIn("文件", text)
        self.assertIn("会话", text)
        self.assertIn("staged", text)
        self.assertIn("build", text)
        self.assertIn("done next", text)
        self.assertIn("note TEXT", text)
        self.assertIn("note change TEXT", text)
        self.assertIn("notes QUERY", text)
        self.assertIn("copy notes QUERY", text)
        self.assertIn("save notes", text)
        self.assertIn("copy prompt", text)
        self.assertIn("copy prompt file", text)
        self.assertIn("open hunk", text)
        self.assertIn("open line", text)
        self.assertIn("copy hunk", text)
        self.assertIn("copy line", text)
        self.assertIn("copy change", text)
        self.assertIn("find TEXT", text)
        self.assertIn("next match", text)
        self.assertIn("prev match", text)
        self.assertIn("next change", text)
        self.assertIn("prev change", text)
        self.assertIn("save diff", text)
        self.assertIn("next hunk", text)
        self.assertIn("prev hunk", text)
        self.assertIn("save prompt", text)
        self.assertIn("save prompt file", text)

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

    def test_browser_test_command_starts_background_test_task(self):
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
            build_cmd=None,
            test_cmd="echo test",
            lint_cmd=None,
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
                                    side_effect=["test", "q"],
                                ):
                                    with patch("cr.ui.browser._draw_browse_screen"):
                                        with patch("cr.ui.browser._start_task") as start_task:
                                            from cr.ui.browser import run_browser

                                            result = run_browser(args)

        self.assertEqual(result, 0)
        self.assertEqual(start_task.call_args.args[2], "test")

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

    def test_browse_file_screen_scrolls_long_content(self):
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


    def test_browser_workspace_state_saves_under_git_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                selected=0,
                page="file",
                filter_text="Second",
            )
            args = argparse_namespace(
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)

            path = _browser_workspace_state_path(repo)
            self.assertEqual(path, repo / ".git" / "cr" / "browse-state.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["version"], 1)
            self.assertEqual(data["scope"]["staged"], True)
            self.assertEqual(data["scope"]["all_changes"], False)
            self.assertEqual(data["filter_text"], "Second")
            self.assertEqual(data["selected_path"], "src/Second.ts")
            self.assertEqual(data["selected_index"], 0)
            self.assertEqual(data["mode"], "file")
            self.assertNotIn("task_history", data)

    def test_browser_workspace_state_does_not_persist_task_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [FileChange("src/First.ts", 1, 0)],
                task_history=[
                    TaskRecord(
                        kind="build",
                        status="succeeded",
                        command=["./build.sh"],
                        returncode=0,
                    )
                ],
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)

            data = json.loads(
                _browser_workspace_state_path(repo).read_text(encoding="utf-8")
            )
            self.assertNotIn("task_history", data)

    def test_browser_workspace_state_saves_and_restores_progress_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                seen_paths={"src/First.ts"},
                remaining_only=True,
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)
            workspace_state = _load_browser_workspace_state(repo)
            restored = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )
            _restore_browser_workspace_state(restored, args, workspace_state)

            self.assertEqual(restored.seen_paths, {"src/First.ts"})
            self.assertTrue(restored.remaining_only)
            self.assertEqual(
                [change.path for change in restored.visible_changes],
                ["src/Second.ts"],
            )

    def test_browser_workspace_state_saves_and_restores_review_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                review_notes={"src/Second.ts": "check lifecycle edge case"},
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            _save_browser_workspace_state(state, args, repo)
            workspace_state = _load_browser_workspace_state(repo)
            restored = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )
            _restore_browser_workspace_state(restored, args, workspace_state)

            self.assertEqual(
                restored.review_notes,
                {"src/Second.ts": "check lifecycle edge case"},
            )

    def test_browser_workspace_state_restores_scope_filter_and_selected_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_path = _browser_workspace_state_path(repo)
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": True,
                            "all_changes": False,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "Second",
                        "selected_path": "src/Second.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )
            args = argparse_namespace(
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )
            state = BrowserState(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ]
            )

            workspace_state = _load_browser_workspace_state(repo)
            self.assertIsNotNone(workspace_state)
            _restore_browser_workspace_state(state, args, workspace_state)

            self.assertTrue(args.staged)
            self.assertFalse(args.all_changes)
            self.assertEqual(state.filter_text, "Second")
            self.assertEqual(state.selected, 0)
            self.assertEqual(state.visible_changes[0].path, "src/Second.ts")
            self.assertEqual(state.mode, "file")

    def test_browser_workspace_state_falls_back_to_index_when_path_is_missing(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            paths=[],
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ]
        )
        workspace_state = {
            "version": 1,
            "scope": {
                "staged": False,
                "all_changes": False,
                "base": None,
                "ref_range": None,
                "untracked": False,
            },
            "filter_text": "",
            "selected_path": "src/Missing.ts",
            "selected_index": 9,
            "mode": "file",
        }

        _restore_browser_workspace_state(state, args, workspace_state)

        self.assertEqual(state.selected, 1)
        self.assertEqual(state.visible_changes[state.selected].path, "src/Second.ts")
        self.assertEqual(state.mode, "file")

    def test_cli_diff_outline_and_review_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            diff = self._cr(repo, "diff")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Changed file tree:", diff.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            outline = self._cr(repo, "outline", "Sample.ets")
            self.assertEqual(outline.returncode, 0, outline.stderr)
            self.assertIn("purpose: ArkTS page/component SamplePage", outline.stdout)
            self.assertIn("struct SamplePage", outline.stdout)
            self.assertIn("method build", outline.stdout)

            review = self._cr(repo, "review")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("Summary:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("focus", review.stdout)
            self.assertIn("Changed file tree:", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("modified: build", review.stdout)
            self.assertIn("method build *", review.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-    Text('hello')", review.stdout)
            self.assertIn("+    Text('hello world')", review.stdout)

            summary = self._cr(repo, "review", "--summary")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("Summary:", summary.stdout)
            self.assertIn("Changed file tree:", summary.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", summary.stdout)
            self.assertNotIn("\n  changes:", summary.stdout)
            self.assertNotIn("purpose:", summary.stdout)
            self.assertNotIn("outline:", summary.stdout)

            no_hunks = self._cr(repo, "review", "--no-hunks")
            self.assertEqual(no_hunks.returncode, 0, no_hunks.stderr)
            self.assertIn("Summary:", no_hunks.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", no_hunks.stdout)
            self.assertIn("modified: build", no_hunks.stdout)
            self.assertIn("outline:", no_hunks.stdout)
            self.assertNotIn("\n  changes:", no_hunks.stdout)
            self.assertNotIn("-    Text('hello')", no_hunks.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 1)
            self.assertEqual(data["summary"]["added"], 1)
            self.assertEqual(data["summary"]["deleted"], 1)
            self.assertEqual(data["files"][0]["path"], "Sample.ets")
            self.assertEqual(data["files"][0]["status"], "modified")
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertIn("ArkTS page/component SamplePage", data["files"][0]["purpose"])
            self.assertTrue(any("+    Text('hello world')" in line for line in data["files"][0]["hunks"]))
            self.assertNotIn("Review changes:", json_review.stdout)

            json_summary = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_summary.returncode, 0, json_summary.stderr)
            summary_data = json.loads(json_summary.stdout)
            self.assertEqual(summary_data["files"][0]["hunks"], [])

    def test_cli_defaults_to_interactive_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "pages" / "Sample.ets"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('old')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            session = self._cr_input(repo, "q\n")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Enter", session.stdout)
            self.assertIn("j/k", session.stdout)
            self.assertIn("Sample.ets", session.stdout)
            self.assertIn("cr:list>", session.stdout)

    def test_cli_defaults_to_browser_when_options_are_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "--context", "0", "--sort", "path")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("交互式代码审查", session.stdout)
            self.assertIn("Sample.ts", session.stdout)

    def test_cli_interactive_browser_opens_file_and_navigates(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\nn\nb\nr\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("File 1/2", session.stdout)
            self.assertIn("File 2/2", session.stdout)
            self.assertIn("-export const first = 'old'", session.stdout)
            self.assertIn("+export const first = 'new'", session.stdout)
            self.assertIn("Changed files", session.stdout)

    def test_cli_browser_shows_recent_commits_when_no_worktree_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'from commit'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change sample")

            sample.write_text("export const sample = 'staged only'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")

            session = self._cr_input(
                repo,
                "1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("change sample", session.stdout)
            self.assertIn("1 file, +1 -1", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'from commit'", session.stdout)

    def test_cli_browser_can_switch_from_worktree_to_recent_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\nw\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("Scope: recent commits", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("committed sample", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)
            self.assertIn("-export const sample = 'committed'", session.stdout)
            self.assertIn("+export const sample = 'working tree'", session.stdout)

    def test_cli_browser_filters_recent_commits_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'docs'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "docs update")

            sample.write_text("export const sample = 'login'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "login flow")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n/login\n1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: login (1/", session.stdout)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("login flow", session.stdout)
            self.assertIn("+export const sample = 'login'", session.stdout)

    def test_cli_browser_can_open_scope_home_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(repo, "scopes\nq\n", "browse")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: scope home", session.stdout)
            self.assertIn("Review scopes", session.stdout)
            self.assertIn("Worktree", session.stdout)
            self.assertIn("Staged", session.stdout)
            self.assertIn("cr:scopes>", session.stdout)

    def test_cli_browser_back_from_commit_file_returns_to_commit_file_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            alpha = repo / "src" / "Alpha.ts"
            beta = repo / "src" / "Beta.ts"
            alpha.parent.mkdir(parents=True)
            alpha.write_text("export const alpha = 'old'\n", encoding="utf-8")
            beta.write_text("export const beta = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            alpha.write_text("export const alpha = 'committed'\n", encoding="utf-8")
            beta.write_text("export const beta = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change both files")

            session = self._cr_input(
                repo,
                "g\n1\n1\nb\n2\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: commit", session.stdout)
            self.assertIn("+export const alpha = 'committed'", session.stdout)
            self.assertIn("+export const beta = 'committed'", session.stdout)

    def test_cli_browser_can_switch_review_scopes_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'staged'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "staged\n1\nb\nall\n1\nb\nworktree\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertIn("Scope: all local changes", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: worktree", session.stdout)
            self.assertIn("-export const sample = 'staged'", session.stdout)

    def test_cli_browser_can_switch_to_base_and_range_scopes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "base HEAD~1\n1\nb\nrange HEAD~1..HEAD\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: base HEAD~1", session.stdout)
            self.assertIn("+export const sample = 'worktree'", session.stdout)
            self.assertIn("Scope: range HEAD~1..HEAD", session.stdout)
            self.assertIn("+export const sample = 'committed'", session.stdout)

    def test_cli_browser_command_list_is_discoverable_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "commands\nb\ncmds\nb\nhelp commands\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertGreaterEqual(session.stdout.count("命令"), 3)
            self.assertIn("审查范围", session.stdout)
            self.assertIn("任务", session.stdout)
            self.assertIn("cr:commands>", session.stdout)
            self.assertIn("Changed files", session.stdout)

    def test_cli_interactive_browser_filters_files_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "filter First\nc\n/Second\nr\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: First (1/2 matches, c to clear)", session.stdout)
            self.assertIn("Filter: Second (1/2 matches, c to clear)", session.stdout)
            self.assertIn("File 1/1", session.stdout)
            self.assertIn("Second.ts", session.stdout)
            self.assertIn("-export const second = 'old'", session.stdout)
            self.assertIn("+export const second = 'new'", session.stdout)

    def test_cli_browser_restores_saved_workspace_filter_and_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            first_session = self._cr_input(
                repo,
                "filter Second\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(first_session.returncode, 0, first_session.stderr)
            self.assertTrue((repo / ".git" / "cr" / "browse-state.json").exists())

            second_session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(second_session.returncode, 0, second_session.stderr)
            self.assertIn("File 1/1", second_session.stdout)
            self.assertIn("Second.ts", second_session.stdout)
            self.assertNotIn("First.ts", second_session.stdout)

    def test_cli_browser_explicit_scope_ignores_saved_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'staged'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            sample.write_text("export const sample = 'worktree'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": True,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "",
                        "selected_path": "src/Sample.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "1\nq\n",
                "browse",
                "--staged",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Scope: staged", session.stdout)
            self.assertIn("+export const sample = 'staged'", session.stdout)
            self.assertNotIn("+export const sample = 'worktree'", session.stdout)

    def test_cli_browser_ignores_malformed_saved_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            sample.write_text("export const sample = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text("{not json", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "browse", "--context", "0")

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)

    def test_cli_browser_pathspec_ignores_saved_workspace_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")
            state_path = repo / ".git" / "cr" / "browse-state.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "scope": {
                            "staged": False,
                            "all_changes": False,
                            "base": None,
                            "ref_range": None,
                            "untracked": False,
                        },
                        "filter_text": "Second",
                        "selected_path": "src/Second.ts",
                        "selected_index": 0,
                        "mode": "file",
                    }
                ),
                encoding="utf-8",
            )

            session = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--context",
                "0",
                "src/First.ts",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertNotIn("Second.ts", session.stdout)
            self.assertNotIn("Filter: Second", session.stdout)

    def test_cli_browser_can_mark_seen_and_show_remaining_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen", session.stdout)
            self.assertIn("remaining only", session.stdout)
            self.assertIn("[x]", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("[ ]", session.stdout)
            self.assertIn("Second.ts", session.stdout)

    def test_cli_browser_can_unmark_seen_and_return_to_all_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "m\nremaining\nallfiles\ntodo\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Progress: 1/2 seen remaining only", session.stdout)
            self.assertIn("Progress: 0/2 seen", session.stdout)
            self.assertIn("First.ts", session.stdout)
            self.assertIn("Second.ts", session.stdout)

    def test_cli_interactive_browser_can_open_current_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\no\nq\n",
                "browse",
                "--context",
                "0",
                "--open-cmd",
                "true",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Opened src/Sample.ts:1", session.stdout)

    def test_cli_interactive_browser_can_run_build_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            build_script = repo / "build.sh"
            build_script.write_text(
                "#!/bin/sh\npwd > build.out\n",
                encoding="utf-8",
            )
            os.chmod(build_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            subdir = repo / "src"
            session = self._cr_input(
                subdir,
                "build\nq\n",
                "browse",
                "--build-cmd",
                "./build.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Build: ./build.sh", session.stdout)
            self.assertIn("Build succeeded.", session.stdout)
            self.assertEqual(
                Path((repo / "build.out").read_text(encoding="utf-8").strip()).resolve(),
                repo.resolve(),
            )

    def test_cli_interactive_browser_can_run_test_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            test_script = repo / "test.sh"
            test_script.write_text(
                "#!/bin/sh\necho test ran > test.out\n",
                encoding="utf-8",
            )
            os.chmod(test_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            session = self._cr_input(
                repo,
                "test\nq\n",
                "browse",
                "--test-cmd",
                "./test.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Test: ./test.sh", session.stdout)
            self.assertIn("Test succeeded.", session.stdout)
            self.assertEqual(
                (repo / "test.out").read_text(encoding="utf-8").strip(),
                "test ran",
            )

    def test_cli_can_emit_clickable_file_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const value = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const value = 'new'\n", encoding="utf-8")

            default_review = self._cr(repo, "review", "--summary")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033]8;;", default_review.stdout)

            linked_review = self._cr(
                repo,
                "review",
                "--summary",
                "--links",
                "always",
            )
            self.assertEqual(linked_review.returncode, 0, linked_review.stderr)
            self.assertIn("\033]8;;file://", linked_review.stdout)
            self.assertIn("#L1", linked_review.stdout)
            self.assertIn("\033]8;;\033\\", linked_review.stdout)

            vscode_browse = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--links",
                "always",
                "--link-scheme",
                "vscode",
            )
            self.assertEqual(vscode_browse.returncode, 0, vscode_browse.stderr)
            self.assertNotIn("\033]8;;", vscode_browse.stdout)
            self.assertIn("Sample.ts", vscode_browse.stdout)

    def test_cli_review_accepts_configurable_hunk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )

            no_context = self._cr(repo, "review", "--json", "--context", "0")
            self.assertEqual(no_context.returncode, 0, no_context.stderr)
            no_context_hunks = "\n".join(json.loads(no_context.stdout)["files"][0]["hunks"])
            self.assertIn("-    Text('hello')", no_context_hunks)
            self.assertIn("+    Text('hello world')", no_context_hunks)
            self.assertNotIn("  build() {", no_context_hunks)

            wider_context = self._cr(repo, "review", "--json", "--context", "3")
            self.assertEqual(wider_context.returncode, 0, wider_context.stderr)
            wider_hunks = "\n".join(json.loads(wider_context.stdout)["files"][0]["hunks"])
            self.assertIn("  build() {", wider_hunks)

            bad_context = self._cr(repo, "review", "--context", "-1")
            self.assertEqual(bad_context.returncode, 2)
            self.assertIn("context must be >= 0", bad_context.stderr)

    def test_cli_compacts_deep_paths_and_can_color_diff_hunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "a" / "b" / "c" / "d" / "e" / "f" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "export function sample(): string {\n  return 'old'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "export function sample(): string {\n  return 'new'\n}\n",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--color", "always")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn(".../d/e/f", review.stdout)
            self.assertIn(".../d/e/f/Sample.ts", review.stdout)
            self.assertNotIn("a/b/c/d/e/f/Sample.ts", review.stdout)
            self.assertIn("\033[32m", review.stdout)
            self.assertIn("\033[31m", review.stdout)

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033[", default_review.stdout)

    def test_cli_review_compares_against_named_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from head')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "head")

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertIn("No working tree changes.", default_review.stdout)

            review = self._cr(repo, "review", "--base", "HEAD~1", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("Sample.ets:3", review.stdout)

            diff = self._cr(repo, "diff", "--base", "HEAD~1", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            json_review = self._cr(repo, "review", "--base", "HEAD~1", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 1, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

    def test_cli_review_compares_explicit_ref_range_without_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")
            self._run(repo, "git", "branch", "-M", "main")
            self._run(repo, "git", "branch", "feature")
            self._run(repo, "git", "checkout", "feature")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from feature')
  }

  helper() {
    return 'feature only'
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "feature")
            self._run(repo, "git", "checkout", "main")

            review = self._cr(repo, "review", "--range", "main..feature", "--no-hunks")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +5 -1", review.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", review.stdout)
            self.assertIn(
                "purpose: ArkTS page/component SamplePage with methods build, helper",
                review.stdout,
            )
            self.assertIn("method helper", review.stdout)

            diff = self._cr(repo, "diff", "--range", "main..feature", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", diff.stdout)

            json_review = self._cr(repo, "review", "--range", "main..feature", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build", "helper"])
            self.assertIn("build, helper", data["files"][0]["purpose"])

    def test_cli_review_shows_first_changed_line_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("anchor", review.stdout)
            self.assertIn("Sample.ets:7", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build line 7", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["first_changed_line"], 7)
            self.assertEqual(data["files"][0]["anchor"], "Sample.ets:7")

    def test_cli_includes_untracked_files_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tracked = repo / "README.md"
            new_page = repo / "src" / "pages" / "NewPage.ets"
            tracked.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            new_page.parent.mkdir(parents=True)
            new_page.write_text(
                "struct NewPage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            default_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(default_diff.returncode, 0, default_diff.stderr)
            self.assertIn("No working tree changes.", default_diff.stdout)
            self.assertNotIn("NewPage.ets", default_diff.stdout)

            diff = self._cr(repo, "diff", "--untracked", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("NewPage.ets +5 -0 untracked", diff.stdout)
            self.assertIn("modified: build", diff.stdout)
            self.assertNotIn("No working tree changes.", diff.stdout)

            review = self._cr(repo, "review", "--untracked", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/NewPage.ets", review.stdout)
            self.assertIn("+5 -0 untracked", review.stdout)
            self.assertIn("src/pages/NewPage.ets:1", review.stdout)
            self.assertIn("+struct NewPage", review.stdout)
            self.assertIn("purpose: ArkTS page/component NewPage", review.stdout)
            self.assertIn("method build *", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 0})
            self.assertEqual(data["files"][0]["status"], "untracked")
            self.assertEqual(data["files"][0]["first_changed_line"], 1)
            self.assertEqual(data["files"][0]["anchor"], "src/pages/NewPage.ets:1")
            self.assertTrue(any("+struct NewPage" in line for line in data["files"][0]["hunks"]))

            staged = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertIn("No staged changes.", staged.stdout)
            self.assertNotIn("NewPage.ets", staged.stdout)

            all_changes = self._cr(repo, "review", "--all", "--untracked", "--code")
            self.assertEqual(all_changes.returncode, 0, all_changes.stderr)
            self.assertIn("src/pages/NewPage.ets", all_changes.stdout)

    def test_git_stage_and_unstage_path_update_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "init")
            sample.write_text("new\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                git.stage_path("Sample.ts")
                staged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(staged.returncode, 0, staged.stderr)
                self.assertIn("Sample.ts", staged.stdout)
                git.unstage_path("Sample.ts")
                unstaged = subprocess.run(
                    ["git", "diff", "--cached", "--name-only"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
                self.assertNotIn("Sample.ts", unstaged.stdout)
            finally:
                os.chdir(previous_cwd)

    def test_git_all_changes_marks_mixed_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("one\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("two\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            sample.write_text("three\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(all_changes=True)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].path, "Sample.ts")
        self.assertEqual(changes[0].source, "mixed")

    def test_git_local_scopes_mark_staged_and_unstaged_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged_file = repo / "staged.ts"
            unstaged_file = repo / "unstaged.ts"
            staged_file.write_text("old staged\n", encoding="utf-8")
            unstaged_file.write_text("old unstaged\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")
            staged_file.write_text("new staged\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged_file.write_text("new unstaged\n", encoding="utf-8")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                staged_changes = git.changed_files(staged=True)
                unstaged_changes = git.changed_files()
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(
            {change.path: change.source for change in staged_changes},
            {"staged.ts": "staged"},
        )
        self.assertEqual(
            {change.path: change.source for change in unstaged_changes},
            {"unstaged.ts": "unstaged"},
        )

    def test_git_recent_commits_include_change_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "first.ts"
            second = repo / "second.ts"
            first.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("new\n", encoding="utf-8")
            second.write_text("one\ntwo\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change summary")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                commits = git.recent_commits(limit=1)
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].subject, "change summary")
        self.assertEqual(commits[0].files, 2)
        self.assertEqual(commits[0].added, 3)
        self.assertEqual(commits[0].deleted, 1)

    def test_git_comparison_scopes_do_not_mark_local_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ts"
            sample.write_text("old\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "base")
            sample.write_text("new\n", encoding="utf-8")
            self._run(repo, "git", "add", "Sample.ts")
            self._run(repo, "git", "commit", "-m", "head")

            previous_cwd = Path.cwd()
            try:
                os.chdir(repo)
                changes = git.changed_files(base="HEAD~1")
            finally:
                os.chdir(previous_cwd)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].source, "")

    def test_cli_omits_untracked_binary_and_large_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            binary = repo / "asset.bin"
            large = repo / "large.txt"
            readme.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            binary.write_bytes(b"\x00\xff\x00\xff")
            large.write_text("x" * 210_000, encoding="utf-8")

            review = self._cr(repo, "review", "--untracked")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("asset.bin +? -0 untracked", review.stdout)
            self.assertIn("large.txt +? -0 untracked", review.stdout)
            self.assertIn("asset.bin: binary or non-UTF-8 file; content omitted", review.stdout)
            self.assertIn("large.txt: file is too large for inline diff", review.stdout)
            self.assertNotIn("+" + ("x" * 200), review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            files = {item["path"]: item for item in data["files"]}
            self.assertIsNone(files["asset.bin"]["added"])
            self.assertIsNone(files["large.txt"]["added"])
            self.assertIn("content omitted", "\n".join(files["asset.bin"]["hunks"]))
            self.assertIn("too large for inline diff", "\n".join(files["large.txt"]["hunks"]))

    def test_cli_flags_lockfile_config_and_generated_risks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            lockfile = repo / "package-lock.json"
            config = repo / "tsconfig.json"
            generated = repo / "src" / "generated" / "client.ts"
            generated.parent.mkdir(parents=True)
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v1'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {"strict": true}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v2'\n}\n", encoding="utf-8")

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("risk", review.stdout)
            self.assertIn("package-lock.json", review.stdout)
            self.assertIn("lockfile", review.stdout)
            self.assertIn("tsconfig.json", review.stdout)
            self.assertIn("config", review.stdout)
            self.assertIn("src/generated/client.ts", review.stdout)
            self.assertIn("generated", review.stdout)
            self.assertIn("risk: lockfile", review.stdout)
            self.assertIn("risk: config", review.stdout)
            self.assertIn("risk: generated", review.stdout)

            full_review = self._cr(repo, "review", "package-lock.json")
            self.assertEqual(full_review.returncode, 0, full_review.stderr)
            self.assertIn("  risk: lockfile", full_review.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            risks = {item["path"]: item["risk_hints"] for item in data["files"]}
            self.assertEqual(risks["package-lock.json"], ["lockfile"])
            self.assertEqual(risks["tsconfig.json"], ["config"])
            self.assertEqual(risks["src/generated/client.ts"], ["generated"])

    def test_cli_review_sorts_large_reviews_by_risk_or_churn(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            risk_sorted = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(risk_sorted.returncode, 0, risk_sorted.stderr)
            self.assertLess(
                risk_sorted.stdout.index("package-lock.json"),
                risk_sorted.stdout.index("README.md"),
            )

            churn_sorted = self._cr(repo, "review", "--summary", "--sort", "churn")
            self.assertEqual(churn_sorted.returncode, 0, churn_sorted.stderr)
            self.assertLess(
                churn_sorted.stdout.index("src/app.ts"),
                churn_sorted.stdout.index("package-lock.json"),
            )

            json_review = self._cr(repo, "review", "--json", "--summary", "--sort", "risk")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["path"], "package-lock.json")

    def test_cli_review_picks_one_file_by_summary_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("idx", summary.stdout)
            self.assertLess(
                summary.stdout.index("1  package-lock.json"),
                summary.stdout.index("2  src/app.ts"),
            )

            picked = self._cr(repo, "review", "--sort", "risk", "--pick", "2")
            self.assertEqual(picked.returncode, 0, picked.stderr)
            self.assertIn("1 files", picked.stdout)
            self.assertIn("src/app.ts", picked.stdout)
            self.assertIn("+  const value = 'v2'", picked.stdout)
            self.assertNotIn("package-lock.json", picked.stdout)
            self.assertNotIn("README.md", picked.stdout)

            bad_pick = self._cr(repo, "review", "--pick", "9")
            self.assertEqual(bad_pick.returncode, 2)
            self.assertIn("--pick must be between 1 and 3", bad_pick.stderr)

    def test_cli_review_tracks_seen_files_and_filters_remaining(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v2'\n}\n",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--seen", "README.md")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("seen", summary.stdout)
            self.assertIn("README.md", summary.stdout)
            self.assertIn("yes", summary.stdout)
            self.assertIn("src/app.ts", summary.stdout)
            self.assertIn("no", summary.stdout)

            remaining = self._cr(
                repo,
                "review",
                "--summary",
                "--seen",
                "README.md",
                "--remaining",
            )
            self.assertEqual(remaining.returncode, 0, remaining.stderr)
            self.assertIn("src/app.ts", remaining.stdout)
            self.assertNotIn("README.md", remaining.stdout)

            no_remaining = self._cr(
                repo,
                "review",
                "--seen",
                "README.md,src/app.ts",
                "--remaining",
            )
            self.assertEqual(no_remaining.returncode, 0, no_remaining.stderr)
            self.assertIn("No remaining changes.", no_remaining.stdout)

            json_review = self._cr(repo, "review", "--json", "--seen", "README.md")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            seen_by_path = {item["path"]: item["seen"] for item in data["files"]}
            self.assertTrue(seen_by_path["README.md"])
            self.assertFalse(seen_by_path["src/app.ts"])

            prompt = self._cr(repo, "review", "--prompt", "--seen", "README.md")
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("state: seen", prompt.stdout)

    def test_cli_review_emits_prompt_ready_markdown_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            lockfile = repo / "package-lock.json"
            page.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello prompt')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")

            prompt = self._cr(
                repo,
                "review",
                "--prompt",
                "--sort",
                "risk",
                "--context",
                "0",
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("# Code Review Handoff", prompt.stdout)
            self.assertIn("Please review these changes.", prompt.stdout)
            self.assertIn("## Summary", prompt.stdout)
            self.assertIn("- Files: 2", prompt.stdout)
            self.assertIn("## Files", prompt.stdout)
            self.assertLess(
                prompt.stdout.index("package-lock.json"),
                prompt.stdout.index("src/pages/Sample.ets"),
            )
            self.assertIn("risk: lockfile", prompt.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", prompt.stdout)
            self.assertIn("focus: build", prompt.stdout)
            self.assertIn("```diff", prompt.stdout)
            self.assertIn("+    Text('hello prompt')", prompt.stdout)
            self.assertNotIn("Review changes:", prompt.stdout)
            self.assertNotIn('"summary"', prompt.stdout)

    def test_cli_filters_to_code_files_and_path_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            helper = repo / "src" / "utils" / "helper.ts"
            readme = repo / "README.md"
            page.parent.mkdir(parents=True)
            helper.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello page')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'b'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello docs\n", encoding="utf-8")

            review = self._cr(repo, "review", "--code", "src/pages")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/Sample.ets +1 -1", review.stdout)
            self.assertNotIn("src/utils/helper.ts", review.stdout)
            self.assertNotIn("README.md", review.stdout)

            diff = self._cr(repo, "diff", "--code", "src/pages")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("src/pages", diff.stdout)
            self.assertNotIn("src/utils", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

            code_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(code_diff.returncode, 0, code_diff.stderr)
            self.assertIn("src/pages/Sample.ets", code_diff.stdout)
            self.assertIn("src/utils/helper.ts", code_diff.stdout)
            self.assertNotIn("README.md", code_diff.stdout)

    def test_code_filter_does_not_show_doc_only_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("No working tree changes.", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

    def test_cli_marks_deleted_code_files_without_fake_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "src" / "utils" / "helper.ts"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("helper.ts +0 -3 deleted", diff.stdout)
            self.assertNotIn("modified: unknown", diff.stdout)

            review = self._cr(repo, "review", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/utils/helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_can_review_staged_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello staged')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")

            unstaged = self._cr(repo, "diff")
            self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
            self.assertIn("No working tree changes.", unstaged.stdout)

            staged_diff = self._cr(repo, "diff", "--staged")
            self.assertEqual(staged_diff.returncode, 0, staged_diff.stderr)
            self.assertIn("Sample.ets +1 -1 modified: build", staged_diff.stdout)

            staged_review = self._cr(repo, "review", "--staged")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn("Sample.ets +1 -1", staged_review.stdout)
            self.assertIn("+    Text('hello staged')", staged_review.stdout)
            self.assertIn("modified: build", staged_review.stdout)

    def test_cli_can_review_staged_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "helper.ts"
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "helper.ts")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()
            self._run(repo, "git", "add", "helper.ts")

            review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_notes_when_the_other_git_side_has_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'b'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'b'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Note: staged changes also exist; use --staged to review them.", diff.stdout)
            self.assertIn("unstaged.ts", diff.stdout)
            self.assertNotIn("  └─ staged.ts +1 -1", diff.stdout)

            staged_review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn(
                "Note: unstaged changes also exist; omit --staged to review them.",
                staged_review.stdout,
            )
            self.assertIn("staged.ts", staged_review.stdout)
            self.assertNotIn("  └─ unstaged.ts +1 -1", staged_review.stdout)

            json_review = self._cr(repo, "review", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["other_changes"], {"staged": 1, "unstaged": 0})

    def test_cli_can_review_all_staged_and_unstaged_changes_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'staged'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'unstaged'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--all", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", diff.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", diff.stdout)
            self.assertNotIn("also exist", diff.stdout)

            review = self._cr(repo, "review", "--all", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", review.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", review.stdout)
            self.assertIn("+  return 'staged'", review.stdout)
            self.assertIn("+  return 'unstaged'", review.stdout)
            self.assertNotIn("also exist", review.stdout)

            json_review = self._cr(repo, "review", "--all", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 2)
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

            bad_scope = self._cr(repo, "review", "--all", "--staged")
            self.assertEqual(bad_scope.returncode, 2)
            self.assertIn("not allowed with argument", bad_scope.stderr)

    def _cr(self, cwd, *args):
        return self._cr_input(cwd, None, *args)

    def _cr_input(self, cwd, input_text, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "cr", *args],
            cwd=cwd,
            text=True,
            input=input_text,
            capture_output=True,
            env=env,
            check=False,
        )

    def _run(self, cwd, *args):
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
