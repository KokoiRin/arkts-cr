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


class SourceFileSymbolSaveCommandTests(unittest.TestCase):

    def test_browser_command_executor_saves_file_detail_source_symbol(self):
        # Behavior: 当用户在File Detail中保存「BrowserCommandExecutor 保存 File Detail 源码 符号」时，系统应生成正确的上下文内容，并交给复制或保存动作 [Requirement: TODO]
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Sample.ts"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Sample {",
                        "  render() {",
                        "    return value",
                        "  }",
                        "  other() {",
                        "    return nope",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [FileChange("src/Sample.ts", 1, 1)],
                page=BrowserPage.FILE_DETAIL,
                selected=0,
                file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(False),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser._cached_file_lines",
                    return_value=[
                        "File 1/1  src/Sample.ts",
                        "  @@ -1 +3 @@",
                        "          3 | +    return value",
                    ],
                ):
                    result = executor.execute(
                        parse_browser_command("save source symbol tmp/render.md")
                    )

            saved = repo / "tmp" / "render.md"
            text = saved.read_text(encoding="utf-8")

        self.assertTrue(result.handled)
        self.assertIn("src/Sample.ts:2-4", text)
        self.assertIn("Symbol: class Sample > method render", text)
        self.assertIn("return value", text)
        self.assertNotIn("other()", text)
        self.assertIn("Saved source symbol to tmp/render.md.", state.status_message)

if __name__ == "__main__":
    unittest.main()
