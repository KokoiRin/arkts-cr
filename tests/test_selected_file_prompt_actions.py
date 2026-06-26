import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cr.ui import handoff as handoff_module
from cr.ui import selected_file_actions
from cr.ui.browser import BrowserState
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class SelectedFilePromptActionTests(unittest.TestCase):

    def test_prompt_handoff_text_uses_selected_file_only(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            context=0,
            paths=[],
            code=False,
            untracked=False,
        )
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 2, 1),
            ],
            selected=1,
            review_notes={
                "src/First.ts": "not selected",
                "src/Second.ts": "selected note",
            },
        )

        with patch(
            "cr.ui.selected_file_actions.build_review_data",
            return_value={"files": [{"path": "src/Second.ts"}]},
        ) as build_data:
            with patch(
                "cr.ui.selected_file_actions.render_prompt_handoff",
                return_value="prompt text",
            ):
                with patch(
                    "cr.ui.selected_file_actions.other_change_counts",
                    return_value={"staged": 0, "unstaged": 0},
                ):
                    result = selected_file_actions.prompt_handoff_text(
                        state,
                        args,
                        selected_only=True,
                    )

        self.assertEqual(result, ("prompt text", 1))
        build_data.assert_called_once_with(
            [state.changes[1]],
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            include_hunks=True,
            other_changes={"staged": 0, "unstaged": 0},
            context=0,
            seen_paths=set(),
            review_notes={"src/Second.ts": "selected note"},
        )

if __name__ == "__main__":
    unittest.main()
