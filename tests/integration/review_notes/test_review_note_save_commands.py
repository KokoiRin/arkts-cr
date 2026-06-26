import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
from cr.ui import review_notes
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    _review_note_lines,
)
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class ReviewNoteSaveCommandTests(unittest.TestCase):
    def test_browser_command_executor_saves_review_notes_default_path(self):
        # Behavior: 当用户在Review Notes中保存「BrowserCommandExecutor 保存 review notes 默认 路径」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [
                    FileChange("src/Second.ts", 2, 1),
                    FileChange("src/First.ts", 1, 0),
                ],
                selected=1,
                page=BrowserPage.FILE_DETAIL,
                review_notes={
                    "src/First.ts": "first current note",
                    "src/Second.ts": "second current note",
                    "docs/Old.md": "stale follow-up",
                },
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save notes"))

            saved = repo / ".cr" / "handoff" / "review-notes.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(
            text,
            "\n".join(
                [
                    "Review notes:",
                    "1. src/Second.ts: second current note",
                    "2. src/First.ts: first current note",
                    "3. docs/Old.md: stale follow-up",
                ]
            ),
        )
        self.assertIn(
            "Saved 3 review notes to .cr/handoff/review-notes.md.",
            state.status_message,
        )
    def test_browser_command_executor_saves_review_notes_requested_path(self):
        # Behavior: 当用户在Review Notes中保存「BrowserCommandExecutor 保存 review notes requested 路径」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 0)],
                review_notes={"src/Sample.ts": "check lifecycle edge case"},
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(
                    parse_browser_command("save notes tmp/review-notes.md")
                )

            saved = repo / "tmp" / "review-notes.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(
            text,
            "Review notes:\n1. src/Sample.ts: check lifecycle edge case",
        )
        self.assertIn(
            "Saved 1 review notes to tmp/review-notes.md.",
            state.status_message,
        )
    def test_browser_command_executor_does_not_save_empty_review_notes(self):
        # Behavior: 当用户在Review Notes中保存「BrowserCommandExecutor 不会 保存 空态 review notes」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save notes"))

            target = repo / ".cr" / "handoff" / "review-notes.md"

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertFalse(target.exists())
        self.assertIn("No review notes to save.", state.status_message)
    def test_browser_command_executor_reports_save_review_notes_failures(self):
        # Behavior: 当用户在Review Notes中保存「BrowserCommandExecutor 提示 保存 review notes failures」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            review_notes={"src/Sample.ts": "check lifecycle edge case"},
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.git.repo_root", return_value=Path("/repo")):
            with patch(
                "cr.ui.browser.handoff_module.save_review_notes_text",
                return_value=handoff_module.HandoffSaveResult(
                    Path("/repo/blocked/notes.md"),
                    "blocked/notes.md",
                    "Could not save review notes to blocked/notes.md: denied",
                ),
            ):
                result = executor.execute(
                    parse_browser_command("save notes blocked/notes.md")
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertIn(
            "Could not save review notes to blocked/notes.md: denied",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
