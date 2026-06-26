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


class SelectedFileLineChangeActionTests(unittest.TestCase):

    def test_open_hunk_targets_the_active_hunk_line(self):
        # Behavior: 当用户在file detail中打开line、change、actions、open时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
    def test_open_line_targets_the_current_added_line(self):
        # Behavior: 当用户在file action中打开line、change、actions、open时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file detail中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
