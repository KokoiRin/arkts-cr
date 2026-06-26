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


class SelectedFileDiffActionTests(unittest.TestCase):

    def test_copy_diff_handoff_contains_only_the_selected_file(self):
        # Behavior: 当用户在Changed Files中复制「复制 diff handoff contains 只读 the 选中文件」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
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
        # Behavior: 当用户在Changed Files中复制「复制 选中 diff snippet 提示 空态 选择」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        args = argparse_namespace(copy_cmd="copy-tool")
        state = BrowserState([])

        with patch("cr.ui.selected_file_actions.file_actions.copy_text") as copy:
            message = selected_file_actions.copy_selected_diff_snippet(state, args)

        self.assertEqual(message, "No changed file to copy diff.")
        copy.assert_not_called()
    def test_save_selected_diff_snippet_writes_default_handoff_file(self):
        # Behavior: 当用户在Changed Files中保存「保存 选中 diff snippet 写入 默认 handoff 文件」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
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
        # Behavior: 当用户在Changed Files中保存「保存 选中 diff snippet 提示 空态 选择」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
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
        # Behavior: 当用户在Changed Files中保存「保存 选中 diff snippet 提示 写入 失败」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
