import json
import tempfile
import unittest
from pathlib import Path

from cr.ui import workspace_persistence
from cr.ui.browser import (
    BrowserPage,
    BrowserState,
    ReviewWorkspace,
    TaskRecord,
    _browser_workspace_state_path,
    _load_browser_workspace_state,
    _restore_browser_workspace_state,
    _save_browser_workspace_state,
)
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class WorkspacePersistenceTests(unittest.TestCase):
    def test_workspace_state_uses_git_cr_path_and_skips_explicit_scopes(self):
        # Behavior: 当用户在Review Scope 与工作区中执行操作「工作区状态 使用 Git cr 路径 and skips explicit 范围」时，系统应保存、恢复或重置预期状态 [Requirement: TODO]
        repo = Path("/tmp/sample-repo")
        default_args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            paths=[],
        )
        path_args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            untracked=False,
            paths=["src"],
        )

        self.assertEqual(
            workspace_persistence.workspace_state_path(repo),
            repo / ".git" / "cr" / "browse-state.json",
        )
        self.assertTrue(workspace_persistence.should_restore_workspace_state(default_args))
        self.assertTrue(workspace_persistence.should_save_workspace_state(default_args))
        self.assertFalse(workspace_persistence.should_restore_workspace_state(path_args))
        self.assertFalse(workspace_persistence.should_save_workspace_state(path_args))

    def test_workspace_state_persists_review_progress_filter_and_notes(self):
        # Behavior: 当用户在Review Scope 与工作区中打开或定位「工作区状态 persists review progress 过滤 and notes」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            workspace = ReviewWorkspace(
                [
                    FileChange("src/First.ts", 1, 0),
                    FileChange("src/Second.ts", 2, 1),
                ],
                selected=0,
                filter_text="Second",
                seen_paths={"src/First.ts"},
                review_notes={"src/Second.ts": "check lifecycle"},
            )
            args = argparse_namespace(
                staged=True,
                all_changes=False,
                base=None,
                ref_range=None,
                untracked=False,
                paths=[],
            )

            workspace_persistence.save_workspace_state(
                workspace,
                args,
                repo,
                mode=BrowserPage.FILE_DETAIL,
            )
            loaded = workspace_persistence.load_workspace_state(repo)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["version"], 1)
        self.assertEqual(loaded["scope"]["staged"], True)
        self.assertEqual(loaded["filter_text"], "Second")
        self.assertEqual(loaded["selected_path"], "src/Second.ts")
        self.assertEqual(loaded["mode"], BrowserPage.FILE_DETAIL)
        self.assertEqual(loaded["seen_paths"], ["src/First.ts"])
        self.assertEqual(loaded["review_notes"], {"src/Second.ts": "check lifecycle"})
        self.assertNotIn("task_history", loaded)
        self.assertNotIn("action_bar", loaded)

    def test_workspace_state_ignores_invalid_json_version_or_schema(self):
        # Behavior: 当用户在Review Scope 与工作区中处理异常「工作区状态 忽略 非法 JSON version or schema」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / ".git" / "cr" / "browse-state.json"
            path.parent.mkdir(parents=True)

            path.write_text("{not-json", encoding="utf-8")
            self.assertIsNone(workspace_persistence.load_workspace_state(repo))

            path.write_text(
                json.dumps({"version": 999, "scope": {}}),
                encoding="utf-8",
            )
            self.assertIsNone(workspace_persistence.load_workspace_state(repo))

            path.write_text(json.dumps({"version": 1}), encoding="utf-8")
            self.assertIsNone(workspace_persistence.load_workspace_state(repo))

    def test_browser_workspace_state_saves_under_git_dir(self):
        # Behavior: 当用户在Review Scope 与工作区中保存「browser 工作区状态 保存 under Git dir」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中执行操作「browser 工作区状态 不会 persist task 历史」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中保存「browser 工作区状态 保存 and 恢复 progress markers」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中保存「browser 工作区状态 保存 and 恢复 review notes」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中过滤「browser 工作区状态 恢复 范围 过滤 and 选中 路径」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
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
        # Behavior: 当用户在Review Scope 与工作区中处理异常「browser 工作区状态 回退 返回 to index when 路径 is 缺失」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
