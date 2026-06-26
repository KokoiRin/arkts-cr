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


class PromptHandoffCopyCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_visible_scope_prompt(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 复制 可见 范围 提示词」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool {text}",
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=3,
            paths=[],
            code=False,
            untracked=True,
        )
        src_change = FileChange("src/Sample.ts", 2, 1)
        docs_change = FileChange("docs/Guide.md", 1, 0)
        state = BrowserState(
            [src_change, docs_change],
            selected=0,
            page=BrowserPage.FILE_DETAIL,
            filter_text="src",
            seen_paths={"src/Sample.ts"},
            review_notes={
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Sample.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Sample.ts",
            ) as render_prompt:
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 0},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.filter_text, "src")
        self.assertEqual(
            state.review_notes,
            {
                "src/Sample.ts": "check lifecycle",
                "docs/Guide.md": "outside filtered handoff",
            },
        )
        self.assertIsNone(state.task)
        build_data.assert_called_once_with(
            [src_change],
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 0},
            context=3,
            seen_paths={"src/Sample.ts"},
            review_notes={"src/Sample.ts": "check lifecycle"},
        )
        render_prompt.assert_called_once()
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Sample.ts",
            "copy-tool {text}",
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())
    def test_browser_command_executor_copies_selected_file_prompt(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 复制 选中文件 提示词」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd=None,
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            context=2,
            paths=[],
            code=False,
            untracked=False,
        )
        first_change = FileChange("src/First.ts", 2, 0)
        second_change = FileChange("src/Second.ts", 1, 1)
        state = BrowserState(
            [first_change, second_change],
            selected=1,
            page=BrowserPage.CHANGED_FILES,
            review_notes={
                "src/First.ts": "not selected",
                "src/Second.ts": "selected note",
            },
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": [{"path": "src/Second.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.browser.render_prompt_handoff",
                return_value="# Code Review Handoff\n\nsrc/Second.ts",
            ):
                with patch(
                    "cr.ui.browser.other_change_counts",
                    return_value={"staged": 0, "unstaged": 3},
                ):
                    with patch(
                        "cr.ui.browser.file_actions.copy_text", return_value=None
                    ) as copy:
                        with redirect_stdout(output):
                            result = executor.execute(
                                parse_browser_command("copy prompt file")
                            )

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        build_data.assert_called_once_with(
            [second_change],
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 3},
            context=2,
            seen_paths=set(),
            review_notes={"src/Second.ts": "selected note"},
        )
        copy.assert_called_once_with(
            "# Code Review Handoff\n\nsrc/Second.ts",
            None,
        )
        self.assertIn("Copied prompt for 1 file", output.getvalue())
    def test_browser_command_executor_does_not_copy_empty_scope_prompt(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 不会 复制 空态 范围 提示词」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

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
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed files to copy prompt.", output.getvalue())
    def test_browser_command_executor_does_not_copy_missing_file_prompt(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 不会 复制 缺失 文件 提示词」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

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
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.build_review_data") as build_data:
            with patch("cr.ui.browser.file_actions.copy_text") as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy prompt file"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        build_data.assert_not_called()
        copy.assert_not_called()
        self.assertIn("No changed file to copy prompt.", output.getvalue())
    def test_browser_command_executor_surfaces_prompt_copy_failure(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 暴露 提示词 复制 失败」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            copy_cmd="copy-tool",
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

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value="Copy failed using CLI command: copy-tool",
                ):
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("copy prompt"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Copy failed using CLI command: copy-tool", output.getvalue())
    def test_browser_command_executor_copies_prompt_in_raw_status(self):
        # Behavior: 当用户在Prompt Handoff中复制「BrowserCommandExecutor 复制 提示词 in raw status」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

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
        frame = BrowserFrame()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            frame,
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser.build_review_data",
            return_value={"summary": {"files": 1}, "files": []},
        ):
            with patch("cr.ui.browser.render_prompt_handoff", return_value="prompt"):
                with patch("cr.ui.browser.file_actions.copy_text", return_value=None):
                    result = executor.execute(
                        parse_browser_command("copy prompt", raw_keys=True)
                    )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertTrue(frame.dirty)
        self.assertIn("Copied prompt for 1 file", state.status_message)

if __name__ == "__main__":
    unittest.main()
