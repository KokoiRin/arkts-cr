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


class PromptHandoffRenderingTests(unittest.TestCase):
    def test_prompt_handoff_renders_review_notes_in_summary_and_detail(self):
        prompt = render_prompt_handoff(
            {
                "summary": {"files": 1, "added": 2, "deleted": 1},
                "other_changes": {"staged": 0, "unstaged": 0},
                "files": [
                    {
                        "path": "src/Sample.ts",
                        "summary": "+2 -1",
                        "status": "modified",
                        "anchor": "src/Sample.ts:3",
                        "risk_hints": [],
                        "seen": False,
                        "purpose": None,
                        "modified_symbols": [],
                        "review_note": "check lifecycle edge case",
                        "hunks": ["@@ -1 +1 @@", "-old", "+new"],
                    }
                ],
            }
        )

        self.assertEqual(prompt.count("review note: check lifecycle edge case"), 2)
        self.assertIn("   - review note: check lifecycle edge case", prompt)
        self.assertIn("- review note: check lifecycle edge case", prompt)

if __name__ == "__main__":
    unittest.main()
