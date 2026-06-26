from pathlib import Path
import unittest

import cr.ui.browser as browser_module
from cr.ui.browser import BrowserPage, BrowserState, ReviewScope, ReviewWorkspace
from cr.vcs.git import CommitSummary, FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class ReviewWorkspaceTests(unittest.TestCase):
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
