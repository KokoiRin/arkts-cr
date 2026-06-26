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


class SelectedFileStageActionTests(unittest.TestCase):

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

if __name__ == "__main__":
    unittest.main()
