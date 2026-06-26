import json
import tempfile
import unittest
from pathlib import Path

from cr.ui import workspace_persistence
from cr.ui.browser import BrowserPage, ReviewWorkspace
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


if __name__ == "__main__":
    unittest.main()
