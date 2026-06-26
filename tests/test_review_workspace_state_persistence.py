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


class ReviewWorkspaceStatePersistenceTests(unittest.TestCase):

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

if __name__ == "__main__":
    unittest.main()
