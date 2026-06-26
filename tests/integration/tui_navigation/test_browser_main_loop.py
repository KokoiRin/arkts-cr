import unittest
from pathlib import Path

import cr.ui.browser as browser_module


class BrowserMainLoopTests(unittest.TestCase):
    def test_browser_main_loop_delegates_action_execution(self):
        # Behavior: 当用户在TUI 导航中执行操作「browser main loop delegates action execution」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        source = Path(browser_module.__file__).read_text(encoding="utf-8")
        run_loop_source = source[source.index("def run_browser") : source.index("def _should_restore")]

        self.assertIn("BrowserCommandExecutor(", run_loop_source)
        self.assertIn(".execute(parsed_command)", run_loop_source)
        self.assertNotIn("BrowserCommandAction.RUN_BUILD", run_loop_source)
        self.assertNotIn("BrowserCommandAction.CHOOSE_NUMBER", run_loop_source)


if __name__ == "__main__":
    unittest.main()
