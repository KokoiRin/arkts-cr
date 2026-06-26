from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui.browser import (
    BrowserPage,
    BrowserState,
    ReviewScope,
    ReviewWorkspace,
    TaskState,
    _switch_review_scope,
)
from cr.vcs.git import CommitSummary, FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class ReviewWorkspaceScopeLifecycleTests(unittest.TestCase):

    def test_review_workspace_loads_filters_and_switches_scope(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace loads 过滤 and 切换 范围」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace reloads changes preserving 选中 路径」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace is used by main browser implementation」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("ReviewWorkspace", source)
        self.assertIn("load_workspace_changes", source)
        self.assertNotIn("selected_changes", source)
        self.assertNotIn("sort_changes", source)
    def test_review_workspace_selects_commit_scope_and_captures_previous_scope(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「ReviewWorkspace 选择 commit 范围 and captures previous 范围」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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
    def test_switch_review_scope_resets_view_state_but_keeps_task_panel(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「切换 review 范围 重置 查看 状态 but keeps Task Panel」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
