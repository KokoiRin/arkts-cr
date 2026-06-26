import unittest

from cr.ui.browser import BrowserCommandExecutor, BrowserFrame, BrowserPage, BrowserState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class DoneNextCommandTests(unittest.TestCase):

    def test_browser_command_executor_marks_done_and_moves_next_in_changed_files(self):
        # Behavior: 当用户在产品通用行为中导航「BrowserCommandExecutor 标记 done and 移动 next in changed 文件」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_does_not_skip_remaining_file(self):
        # Behavior: 当用户在产品通用行为中执行操作「BrowserCommandExecutor done next 不会 skip 剩余 文件」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
                FileChange("src/Third.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=0,
            remaining_only=True,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, {"src/First.ts"})
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Second.ts", "src/Third.ts"],
        )
        self.assertEqual(state.selected, 0)
        self.assertIn("Moved to src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_last_visible_file(self):
        # Behavior: 当用户在产品通用行为中处理异常「BrowserCommandExecutor done next 提示 last 可见 文件」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            page=BrowserPage.CHANGED_FILES,
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.seen_paths, {"src/Second.ts"})
        self.assertIn("No next file after src/Second.ts", state.status_message)

    def test_browser_command_executor_done_next_reports_empty_visible_files(self):
        # Behavior: 当用户在产品通用行为中处理异常「BrowserCommandExecutor done next 提示 空态 可见 文件」时，系统应给出明确反馈，并保持当前状态安全可恢复 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace()
        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("done next", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.seen_paths, set())
        self.assertIn("No changed file to mark seen.", state.status_message)
