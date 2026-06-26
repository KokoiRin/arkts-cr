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


class SelectedFileReferenceActionTests(unittest.TestCase):

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
    def test_copy_anchor_points_to_the_first_changed_line(self):
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

if __name__ == "__main__":
    unittest.main()
