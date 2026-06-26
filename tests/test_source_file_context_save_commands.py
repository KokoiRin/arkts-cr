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


class SourceFileContextSaveCommandsTest(unittest.TestCase):

    def test_browser_command_executor_saves_selected_source_context_default_path(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 9)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("save source"))

            saved = repo / ".cr" / "handoff" / "source.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:3-6", text)
        self.assertIn("> 5  line 5", text)
        self.assertNotIn("line 2", text)
        self.assertNotIn("line 7", text)
        self.assertIn("Saved selected source to .cr/handoff/source.md.", state.status_message)

if __name__ == "__main__":
    unittest.main()
