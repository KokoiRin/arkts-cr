import unittest
from contextlib import redirect_stdout
from io import StringIO

from cr.ui.browser import (
    BrowserActionResult,
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
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


class BrowserCommandExecutorTests(unittest.TestCase):
    def test_browser_command_executor_reports_quit_intent(self):
        # Behavior: 当用户在产品通用行为中处理异常「BrowserCommandExecutor 提示 quit intent」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("q"))

        self.assertEqual(result, BrowserActionResult(exit_code=0))

    def test_browser_command_executor_changes_page_and_requests_redraw(self):
        # Behavior: 当用户在产品通用行为中执行操作「BrowserCommandExecutor changes page and requests 重绘」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        result = executor.execute(parse_browser_command("commands"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.COMMAND_PALETTE)

    def test_browser_command_executor_reports_unknown_command_feedback(self):
        # Behavior: 当用户在产品通用行为中处理异常「BrowserCommandExecutor 提示 unknown 命令 feedback」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("wat"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIn("Unknown command.", output.getvalue())

    def test_browser_command_executor_runs_forward_navigation(self):
        # Behavior: 当用户在产品通用行为中导航「BrowserCommandExecutor runs 前进 导航」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("forward"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)

    def test_browser_command_executor_opens_page_help(self):
        # Behavior: 当用户在产品通用行为中打开或定位「BrowserCommandExecutor 打开 page 帮助」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE, source_file_path="src/Foo.ets")
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("help"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.SOURCE_FILE)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)

    def test_browser_command_executor_applies_source_filter(self):
        # Behavior: 当用户在产品通用行为中过滤「BrowserCommandExecutor applies 源码 过滤」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [
                FileChange("src/Staged.ts", 1, 0, source="staged"),
                FileChange("src/Unstaged.ts", 1, 0, source="unstaged"),
            ],
            selected=1,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source staged", raw_keys=True))

        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.source_filter, "staged")
        self.assertEqual(state.selected, 0)
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/Staged.ts"],
        )

    def test_browser_command_executor_rejects_unknown_source_filter(self):
        # Behavior: 当用户在产品通用行为中过滤「BrowserCommandExecutor rejects unknown 源码 过滤」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 0, source="staged")])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with redirect_stdout(output):
            result = executor.execute(parse_browser_command("source generated"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")
        self.assertIn("Unknown source filter", output.getvalue())

    def test_browser_command_executor_clears_source_filter(self):
        # Behavior: 当用户在产品通用行为中过滤「BrowserCommandExecutor clears 源码 过滤」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 0, source="staged")],
            source_filter="staged",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with redirect_stdout(StringIO()):
            result = executor.execute(parse_browser_command("source all"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_filter, "")
