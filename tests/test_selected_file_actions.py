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


class SelectedFileActionsTests(unittest.TestCase):
    def test_copy_selected_path_returns_status_message(self):
        with patch(
            "cr.ui.selected_file_actions.file_actions.copy_text",
            return_value=None,
        ) as copy:
            message = selected_file_actions.copy_selected_path(
                "src/Sample.ts",
                copy_cmd="copy-tool",
            )

        self.assertEqual(message, "Copied src/Sample.ts")
        copy.assert_called_once_with("src/Sample.ts", "copy-tool")

    def test_copy_selected_anchor_uses_first_changed_line(self):
        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )

        with patch(
            "cr.ui.selected_file_actions.git.first_changed_line",
            return_value=12,
        ) as first_line:
            with patch(
                "cr.ui.selected_file_actions.file_actions.copy_text",
                return_value=None,
            ) as copy:
                message = selected_file_actions.copy_selected_anchor(
                    "src/Sample.ts",
                    args,
                    copy_cmd=None,
                )

        self.assertEqual(message, "Copied src/Sample.ts:12")
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        copy.assert_called_once_with("src/Sample.ts:12", None)

    def test_copy_selected_diff_snippet_uses_selected_file_only(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            copy_cmd="copy-tool",
        )
        state = BrowserState(
            [
                FileChange("src/First.md", 1, 0),
                FileChange("docs/Second.md", 2, 1),
            ],
            selected=1,
            seen_paths={"docs/Second.md"},
            review_notes={"docs/Second.md": "check wording"},
        )

        with patch("cr.review.data.git.first_changed_line", return_value=7):
            with patch(
                "cr.review.data.git.file_diff",
                return_value="@@ -1 +1 @@\n-old\n+new\n",
            ):
                with patch(
                    "cr.ui.selected_file_actions.file_actions.copy_text",
                    return_value=None,
                ) as copy:
                    message = selected_file_actions.copy_selected_diff_snippet(
                        state,
                        args,
                        other_counts=lambda _args: {"staged": 0, "unstaged": 0},
                    )

        copied_text = copy.call_args.args[0]
        self.assertEqual(message, "Copied diff for docs/Second.md")
        self.assertNotIn("src/First.md", copied_text)
        self.assertIn("# File Diff: docs/Second.md", copied_text)
        self.assertIn("- anchor: docs/Second.md:7", copied_text)
        self.assertIn("- state: seen", copied_text)
        self.assertIn("- review note: check wording", copied_text)
        self.assertIn("+new", copied_text)
        copy.assert_called_once_with(copied_text, "copy-tool")

    def test_copy_selected_diff_snippet_reports_empty_selection(self):
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])

        with patch("cr.ui.selected_file_actions.file_actions.copy_text") as copy:
            message = selected_file_actions.copy_selected_diff_snippet(state, args)

        self.assertEqual(message, "No changed file to copy diff.")
        copy.assert_not_called()

    def test_open_selected_hunk_uses_active_hunk_line(self):
        args = argparse_namespace(open_cmd="editor {fileline}")
        change = FileChange("src/Sample.ts", 1, 0)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  @@ -20,2 +31,3 @@",
            "  +second",
        ]

        with patch(
            "cr.ui.selected_file_actions.git.repo_path",
            return_value=Path("/repo/src/Sample.ts"),
        ):
            with patch(
                "cr.ui.selected_file_actions.file_actions.open_path",
                return_value=None,
            ) as open_path:
                message = selected_file_actions.open_selected_hunk(
                    change,
                    lines,
                    3,
                    args,
                )

        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            31,
            "editor {fileline}",
        )
        self.assertEqual(message, "Opened hunk src/Sample.ts:31")

    def test_open_selected_line_uses_current_new_file_line(self):
        args = argparse_namespace(open_cmd="editor {fileline}")
        change = FileChange("src/Sample.ts", 1, 0)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch(
            "cr.ui.selected_file_actions.git.repo_path",
            return_value=Path("/repo/src/Sample.ts"),
        ):
            with patch(
                "cr.ui.selected_file_actions.file_actions.open_path",
                return_value=None,
            ) as open_path:
                message = selected_file_actions.open_selected_line(
                    change,
                    lines,
                    2,
                    args,
                )

        open_path.assert_called_once_with(
            Path("/repo/src/Sample.ts"),
            32,
            "editor {fileline}",
        )
        self.assertEqual(message, "Opened line src/Sample.ts:32")

    def test_copy_selected_line_copies_current_new_file_anchor(self):
        args = argparse_namespace(copy_cmd="copy-tool")
        change = FileChange("src/Sample.ts", 1, 0)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch(
            "cr.ui.selected_file_actions.file_actions.copy_text",
            return_value=None,
        ) as copy_text:
            message = selected_file_actions.copy_selected_line(
                change,
                lines,
                2,
                args,
            )

        copy_text.assert_called_once_with("src/Sample.ts:32", "copy-tool")
        self.assertEqual(message, "Copied line src/Sample.ts:32")

    def test_copy_selected_change_renders_current_added_row(self):
        args = argparse_namespace(copy_cmd="copy-tool")
        change = FileChange("src/Sample.ts", 1, 0)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch(
            "cr.ui.selected_file_actions.file_actions.copy_text",
            return_value=None,
        ) as copy_text:
            message = selected_file_actions.copy_selected_change(
                change,
                lines,
                2,
                args,
            )

        copied = copy_text.call_args.args[0]
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(message, "Copied change for src/Sample.ts:32")
        self.assertIn("# Changed Row: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:32", copied)
        self.assertIn("- kind: added", copied)
        self.assertIn("        32 | +second", copied)

    def test_copy_selected_change_renders_current_deleted_row(self):
        args = argparse_namespace(copy_cmd="copy-tool")
        change = FileChange("src/Sample.ts", 0, 1)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -20,2 +31,0 @@",
            "    20      | -gone",
        ]

        with patch(
            "cr.ui.selected_file_actions.file_actions.copy_text",
            return_value=None,
        ) as copy_text:
            message = selected_file_actions.copy_selected_change(
                change,
                lines,
                1,
                args,
            )

        copied = copy_text.call_args.args[0]
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(message, "Copied deleted change for src/Sample.ts:20")
        self.assertIn("# Changed Row: src/Sample.ts", copied)
        self.assertIn("- old line: 20", copied)
        self.assertIn("- kind: deleted", copied)
        self.assertIn("  20      | -gone", copied)
        self.assertNotIn("- anchor:", copied)

    def test_copy_selected_hunk_renders_only_active_hunk(self):
        args = argparse_namespace(copy_cmd="copy-tool")
        change = FileChange("src/Sample.ts", 1, 0)
        lines = [
            "File 1/1  src/Sample.ts",
            "  @@ -1 +3 @@",
            "  +first",
            "  @@ -20,2 +31,3 @@",
            "    20   31 | context",
            "          32 | +second",
        ]

        with patch(
            "cr.ui.selected_file_actions.file_actions.copy_text",
            return_value=None,
        ) as copy_text:
            message = selected_file_actions.copy_selected_hunk(
                change,
                lines,
                3,
                args,
            )

        copied = copy_text.call_args.args[0]
        copy_text.assert_called_once_with(copied, "copy-tool")
        self.assertEqual(message, "Copied hunk 2/2 for src/Sample.ts:31")
        self.assertIn("# Hunk Diff: src/Sample.ts", copied)
        self.assertIn("- anchor: src/Sample.ts:31", copied)
        self.assertIn("- hunk: 2/2", copied)
        self.assertIn("```text", copied)
        self.assertIn("@@ -20,2 +31,3 @@", copied)
        self.assertIn("  20   31 | context", copied)
        self.assertIn("        32 | +second", copied)
        self.assertNotIn("+first", copied)

    def test_save_selected_diff_snippet_writes_default_handoff_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace()
            state = BrowserState([FileChange("docs/Second.md", 2, 1)])

            message = selected_file_actions.save_selected_diff_snippet(
                state,
                args,
                repo_root=lambda: repo,
                snippet_text=lambda _state, _args: (
                    "# File Diff: docs/Second.md\n\n```diff\n+new\n```",
                    "docs/Second.md",
                ),
            )

            target = repo / ".cr" / "handoff" / "review-diff.md"
            self.assertEqual(
                message,
                "Saved diff for docs/Second.md to .cr/handoff/review-diff.md",
            )
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "# File Diff: docs/Second.md\n\n```diff\n+new\n```",
            )

    def test_save_selected_diff_snippet_reports_empty_selection(self):
        args = argparse_namespace()
        state = BrowserState([])

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            message = selected_file_actions.save_selected_diff_snippet(
                state,
                args,
                repo_root=lambda: repo,
            )

            self.assertEqual(message, "No changed file to save diff.")
            self.assertFalse((repo / ".cr").exists())

    def test_save_selected_diff_snippet_reports_write_failure(self):
        args = argparse_namespace()
        state = BrowserState([FileChange("docs/Second.md", 2, 1)])

        message = selected_file_actions.save_selected_diff_snippet(
            state,
            args,
            "blocked/diff.md",
            repo_root=lambda: Path("/repo"),
            snippet_text=lambda _state, _args: (
                "# File Diff: docs/Second.md",
                "docs/Second.md",
            ),
            save_diff_text=lambda _text, _repo, _path: handoff_module.HandoffSaveResult(
                Path("/repo/blocked/diff.md"),
                "blocked/diff.md",
                "Could not save diff to blocked/diff.md: denied",
            ),
        )

        self.assertEqual(message, "Could not save diff to blocked/diff.md: denied")

    def test_stage_selected_path_is_available_for_local_scopes(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
        )

        with patch(
            "cr.ui.selected_file_actions.git.stage_path",
            return_value=None,
        ) as stage:
            message = selected_file_actions.stage_selected_path("src/Sample.ts", args)

        self.assertEqual(message, "Staged src/Sample.ts")
        stage.assert_called_once_with("src/Sample.ts")

    def test_stage_selected_path_rejects_read_only_scopes(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base="main",
            ref_range=None,
        )

        with patch("cr.ui.selected_file_actions.git.stage_path") as stage:
            message = selected_file_actions.stage_selected_path("src/Sample.ts", args)

        self.assertEqual(
            message,
            "Index actions are only available for local worktree/index scopes.",
        )
        stage.assert_not_called()

    def test_unstage_selected_path_is_available_for_local_scopes(self):
        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )

        with patch(
            "cr.ui.selected_file_actions.git.unstage_path",
            return_value=None,
        ) as unstage:
            message = selected_file_actions.unstage_selected_path("src/Sample.ts", args)

        self.assertEqual(message, "Unstaged src/Sample.ts")
        unstage.assert_called_once_with("src/Sample.ts")

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

    def test_append_selected_change_review_note_uses_current_added_row(self):
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

    def test_append_selected_change_review_note_uses_current_deleted_row(self):
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

    def test_prompt_handoff_text_uses_selected_file_only(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=0,
            paths=[],
            code=False,
            untracked=False,
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            review_notes={
                "src/First.ts": "not selected",
                "src/Second.ts": "selected note",
            },
        )

        with patch(
            "cr.ui.selected_file_actions.build_review_data",
            return_value={"files": [{"path": "src/Second.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.selected_file_actions.render_prompt_handoff",
                return_value="prompt text",
            ):
                with patch(
                    "cr.ui.selected_file_actions.other_change_counts",
                    return_value={"staged": 0, "unstaged": 0},
                ):
                    result = selected_file_actions.prompt_handoff_text(
                        state,
                        args,
                        selected_only=True,
                    )

        self.assertEqual(result, ("prompt text", 1))
        build_data.assert_called_once_with(
            [state.changes[1]],
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 0},
            context=0,
            seen_paths=set(),
            review_notes={"src/Second.ts": "selected note"},
        )


if __name__ == "__main__":
    unittest.main()
