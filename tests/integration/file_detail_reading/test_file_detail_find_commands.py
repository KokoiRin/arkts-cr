import subprocess
import unittest
from unittest.mock import patch

from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserPage,
    BrowserState,
    TaskState,
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


class FileDetailFindCommandTests(unittest.TestCase):

    def test_browser_command_executor_finds_text_in_file_detail(self):
        # Behavior: 当用户在File Detail中执行操作「BrowserCommandExecutor finds text in File Detail」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  purpose: sample",
            "  @@ -1 +1 @@",
            "       1 | context",
            "       2 | +TargetValue",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                result = executor.execute(
                    parse_browser_command("find targetvalue", raw_keys=True)
                )

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 3)
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertEqual(state.file_find_text, "targetvalue")
        self.assertIn('Found "targetvalue" at line 4.', state.status_message)

    def test_browser_command_executor_repeats_file_detail_find_matches(self):
        # Behavior: 当用户在File Detail中执行操作「BrowserCommandExecutor repeats File Detail find 匹配」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=0,
            review_notes={"src/Sample.ts": "keep note"},
        )
        state.task = TaskState(["build"], subprocess.Popen(["true"]))
        state.task.process.wait(timeout=1)
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )
        lines = [
            "File 1/1  src/Sample.ts",
            "  target first",
            "  context",
            "  Target second",
            "  context",
            "  target third",
        ]

        with patch("cr.ui.browser._cached_file_lines", return_value=lines):
            with patch("cr.ui.browser._max_file_scroll", return_value=10):
                find = executor.execute(
                    parse_browser_command("find target", raw_keys=True)
                )
                next_match = executor.execute(
                    parse_browser_command("next match", raw_keys=True)
                )
                previous_match = executor.execute(
                    parse_browser_command("prev match", raw_keys=True)
                )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(state.file_find_text, "target")
        self.assertEqual(state.review_notes["src/Sample.ts"], "keep note")
        self.assertIsNotNone(state.task)
        self.assertIn('Found "target" at line 1.', state.status_message)

    def test_browser_command_executor_reports_repeat_find_without_query(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 repeat find 不包含 查询」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Run find TEXT first.", state.status_message)

    def test_browser_command_executor_reports_repeat_find_without_matches(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 repeat find 不包含 匹配」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        state.file_find_text = "owner"
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1  src/Sample.ts", "  context"],
        ):
            result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn('No matches for "owner".', state.status_message)

    def test_browser_command_executor_reports_find_outside_file_detail(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 find outside File Detail」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("find target", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to find text.", state.status_message)

    def test_browser_command_executor_reports_repeat_find_outside_file_detail(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 repeat find outside File Detail」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([FileChange("src/Sample.ts", 1, 0)])
        state.file_find_text = "target"
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("next match", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertIn("Open a file detail to find text.", state.status_message)

    def test_browser_command_executor_reports_empty_and_missing_find(self):
        # Behavior: 当用户在File Detail中处理异常「BrowserCommandExecutor 提示 空态 and 缺失 find」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=2,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch(
            "cr.ui.browser._cached_file_lines",
            return_value=["File 1/1  src/Sample.ts", "  context"],
        ):
            empty = executor.execute(parse_browser_command("find", raw_keys=True))
            missing = executor.execute(parse_browser_command("find owner", raw_keys=True))

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 2)
        self.assertEqual(state.file_find_text, "owner")
        self.assertIn('No matches for "owner".', state.status_message)
