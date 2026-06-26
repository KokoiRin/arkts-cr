import tempfile
import unittest
from pathlib import Path

from cr.ui import handoff as handoff_module


class HandoffSaveBehaviorTests(unittest.TestCase):
    def test_prompt_handoff_saves_scope_and_file_prompts_to_repo_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            relative = handoff_module.save_prompt_text(
                "scope prompt",
                repo,
                selected_only=False,
            )
            absolute_path = repo / "tmp" / "absolute.md"
            absolute = handoff_module.save_prompt_text(
                "file prompt",
                repo,
                str(absolute_path),
                selected_only=True,
            )

            self.assertIsNone(relative.error)
            self.assertEqual(relative.display_path, ".cr/handoff/review-prompt.md")
            self.assertEqual(relative.path.read_text(encoding="utf-8"), "scope prompt")
            self.assertIsNone(absolute.error)
            self.assertEqual(absolute.display_path, "tmp/absolute.md")
            self.assertEqual(absolute.path.read_text(encoding="utf-8"), "file prompt")

    def test_diff_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_diff_text("default diff", repo)
            requested = handoff_module.save_diff_text(
                "requested diff",
                repo,
                "tmp/current-file.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/review-diff.md")
            self.assertEqual(default.path.read_text(encoding="utf-8"), "default diff")
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/current-file.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested diff",
            )

    def test_task_output_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_task_output_text("default task", repo)
            requested = handoff_module.save_task_output_text(
                "requested task",
                repo,
                "tmp/task.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/task-output.md")
            self.assertEqual(default.path.read_text(encoding="utf-8"), "default task")
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/task.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested task",
            )

    def test_problem_context_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_problem_context_text(
                "default problem context",
                repo,
            )
            requested = handoff_module.save_problem_context_text(
                "requested problem context",
                repo,
                "tmp/problem.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/problem-context.md")
            self.assertEqual(
                default.path.read_text(encoding="utf-8"),
                "default problem context",
            )
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/problem.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested problem context",
            )

    def test_task_problem_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_task_problem_text(
                "default task problem",
                repo,
            )
            requested = handoff_module.save_task_problem_text(
                "requested task problem",
                repo,
                "tmp/problem.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/task-problem.md")
            self.assertEqual(
                default.path.read_text(encoding="utf-8"),
                "default task problem",
            )
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/problem.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested task problem",
            )

    def test_problem_diff_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_problem_diff_text(
                "default problem diff",
                repo,
            )
            requested = handoff_module.save_problem_diff_text(
                "requested problem diff",
                repo,
                "tmp/problem-diff.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/problem-diff.md")
            self.assertEqual(
                default.path.read_text(encoding="utf-8"),
                "default problem diff",
            )
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/problem-diff.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested problem diff",
            )

    def test_review_notes_handoff_saves_default_and_requested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            default = handoff_module.save_review_notes_text(
                "default review notes",
                repo,
            )
            requested = handoff_module.save_review_notes_text(
                "requested review notes",
                repo,
                "tmp/notes.md",
            )

            self.assertIsNone(default.error)
            self.assertEqual(default.display_path, ".cr/handoff/review-notes.md")
            self.assertEqual(
                default.path.read_text(encoding="utf-8"),
                "default review notes",
            )
            self.assertIsNone(requested.error)
            self.assertEqual(requested.display_path, "tmp/notes.md")
            self.assertEqual(
                requested.path.read_text(encoding="utf-8"),
                "requested review notes",
            )


if __name__ == "__main__":
    unittest.main()
