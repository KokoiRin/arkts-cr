import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.review.prompt import render_prompt_handoff
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
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


class PromptHandoffSaveFeedbackTests(unittest.TestCase):

    def test_browser_command_executor_surfaces_prompt_save_failure(self):
        # Behavior: 当用户在Prompt Handoff中保存「BrowserCommandExecutor 暴露 提示词 保存 失败」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            blocker = repo / "blocker"
            blocker.write_text("not a directory", encoding="utf-8")
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=True,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=False,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("save prompt blocker/review.md")
                            )

            self.assertTrue(result.handled)
            self.assertFalse(result.needs_redraw)
            self.assertIn(
                "Could not save prompt to blocker/review.md",
                output.getvalue(),
            )
    def test_browser_command_executor_saves_prompt_in_raw_status(self):
        # Behavior: 当用户在Prompt Handoff中保存「BrowserCommandExecutor 保存 提示词 in raw status」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            args = argparse_namespace(
                copy_cmd=None,
                staged=False,
                all_changes=False,
                base=None,
                ref_range=None,
                context=2,
                paths=[],
                code=False,
                untracked=True,
            )
            frame = BrowserFrame()
            state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
            executor = BrowserCommandExecutor(
                state,
                args,
                TerminalStyle(),
                frame,
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.build_review_data",
                    return_value={"summary": {"files": 1}, "files": []},
                ):
                    with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                        with patch(
                            "cr.ui.browser.other_change_counts",
                            return_value={"staged": 0, "unstaged": 0},
                        ):
                            result = executor.execute(
                                parse_browser_command("save prompt", raw_keys=True)
                            )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn(
            "Saved prompt for 1 file to .cr/handoff/review-prompt.md",
            state.status_message,
        )

if __name__ == "__main__":
    unittest.main()
