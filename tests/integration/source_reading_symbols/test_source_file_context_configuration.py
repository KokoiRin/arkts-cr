import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cr.ui.browser as browser_module
from cr.ui.browser import (
    BrowserCommandExecutor,
    BrowserFrame,
    BrowserNavigation,
    BrowserPage,
    BrowserState,
    TaskState,
    _draw_browse_screen,
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


class SourceFileContextConfigurationTest(unittest.TestCase):

    def test_browser_command_executor_sets_source_context_lines(self):
        # Behavior: 当用户在Source File中查看「BrowserCommandExecutor sets 源码 上下文 行」时，系统应展示正确内容、层级和状态提示 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_context = executor.execute(parse_browser_command("source context 8"))
        clamped_context = executor.execute(parse_browser_command("source context 999"))
        invalid_context = executor.execute(parse_browser_command("source context nope"))

        self.assertTrue(set_context.handled)
        self.assertTrue(set_context.needs_redraw)
        self.assertTrue(clamped_context.handled)
        self.assertTrue(invalid_context.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_context_lines, 50)
        self.assertIn("Source context must be a non-negative integer.", state.status_message)

if __name__ == "__main__":
    unittest.main()
