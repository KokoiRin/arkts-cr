import unittest
from pathlib import Path

import cr.ui.browser as browser_module
from cr.ui.browser import BrowserState
from cr.ui.navigation import BrowserNavigation, BrowserPage, BrowserPageSnapshot
from cr.vcs.git import CommitSummary, FileChange


class BrowserNavigationTests(unittest.TestCase):
    def test_page_model_names_current_pages(self):
        self.assertEqual(BrowserPage.SCOPE_HOME, "scopes")
        self.assertEqual(BrowserPage.COMMIT_PICKER, "commits")
        self.assertEqual(BrowserPage.CHANGED_FILES, "list")
        self.assertEqual(BrowserPage.FILE_DETAIL, "file")
        self.assertEqual(BrowserPage.COMMAND_PALETTE, "commands")
        self.assertEqual(BrowserPage.HELP, "help")
        self.assertEqual(BrowserPage.TASK_OUTPUT, "task-output")
        self.assertEqual(BrowserPage.TASK_PROBLEMS, "problems")
        self.assertEqual(BrowserPage.SOURCE_FILE, "source")

        state = BrowserState([])
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.mode, BrowserPage.CHANGED_FILES)

        state.mode = BrowserPage.FILE_DETAIL
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)

        state.page = BrowserPage.COMMAND_PALETTE
        self.assertEqual(state.mode, BrowserPage.COMMAND_PALETTE)

    def test_browser_implementation_uses_page_model_and_navigation(self):
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("BrowserPage.CHANGED_FILES", source)
        self.assertIn("BrowserPage.FILE_DETAIL", source)
        self.assertIn("BrowserPage.COMMIT_PICKER", source)
        self.assertIn("BrowserPage.SCOPE_HOME", source)
        self.assertIn("BrowserPage.COMMAND_PALETTE", source)
        self.assertIn("BrowserPage.HELP", source)
        self.assertIn("BrowserPage.TASK_OUTPUT", source)
        self.assertIn("BrowserPage.TASK_PROBLEMS", source)
        self.assertIn("BrowserPage.SOURCE_FILE", source)
        self.assertIn("BrowserNavigation.", source)
        self.assertNotIn('mode: str = "list"', source)
        self.assertNotIn("state.mode", source)
        self.assertNotIn("state.page = BrowserPage", source)

    def test_opening_pages_resets_local_page_state(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            selected=3,
            list_scroll=4,
            commit_scroll=5,
            command_scroll=6,
            file_scroll=7,
            task_scroll=8,
            problem_filter="warning",
            problem_sort="severity",
            problem_query="Foo",
            problem_group="file",
            source_context_lines=8,
            source_selection_start=4,
            source_selection_end=7,
            scope_selected=2,
            command_selected=3,
            page=BrowserPage.FILE_DETAIL,
        )

        BrowserNavigation.show_scope_home(state)
        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)
        self.assertEqual(state.scope_selected, 0)

        BrowserNavigation.show_command_palette(state)
        self.assertEqual(state.page, BrowserPage.COMMAND_PALETTE)
        self.assertEqual(state.command_selected, 0)
        self.assertEqual(state.command_scroll, 0)

        BrowserNavigation.show_commit_picker(state, clear_selected_commit=True)
        self.assertEqual(state.page, BrowserPage.COMMIT_PICKER)
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.commit_scroll, 0)

        BrowserNavigation.show_changed_files(state)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.file_scroll, 0)

        state.file_scroll = 9
        BrowserNavigation.open_file_detail(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 0)

        state.task_scroll = 11
        BrowserNavigation.show_task_output(state)
        self.assertEqual(state.page, BrowserPage.TASK_OUTPUT)
        self.assertEqual(state.task_scroll, 0)

        state.problem_selected = 3
        state.problem_scroll = 4
        state.source_find_text = "old-source-query"
        BrowserNavigation.show_task_problems(state)
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_selected, 0)
        self.assertEqual(state.problem_scroll, 0)
        self.assertEqual(state.problem_filter, "")
        self.assertEqual(state.problem_sort, "output")
        self.assertEqual(state.problem_query, "")
        self.assertEqual(state.problem_group, "none")

        BrowserNavigation.show_task_problems(
            state,
            problem_filter="error",
            problem_sort="severity",
            problem_query="Foo",
            problem_group="file",
        )
        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_filter, "error")
        self.assertEqual(state.problem_sort, "severity")
        self.assertEqual(state.problem_query, "Foo")
        self.assertEqual(state.problem_group, "file")

        BrowserNavigation.show_source_file(state, "src/Foo.ets", 12)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/Foo.ets")
        self.assertEqual(state.source_file_line, 12)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertEqual(state.source_find_text, "")
        self.assertEqual(state.source_context_lines, 3)
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertEqual(state.source_mark_line, 0)

        BrowserNavigation.show_page_help(state)
        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.SOURCE_FILE)

    def test_replace_pages_does_not_modify_history(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            file_scroll=7,
        )
        state.page_back_stack.append(
            BrowserPageSnapshot(
                BrowserPage.CHANGED_FILES,
                0,
                0,
                0,
                0,
                0,
                0,
                "",
                None,
                0,
            )
        )

        BrowserNavigation.replace_with_file_detail(state)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 7)
        self.assertEqual(len(state.page_back_stack), 1)

        BrowserNavigation.replace_with_changed_files(state)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.file_scroll, 0)
        self.assertEqual(len(state.page_back_stack), 1)

    def test_back_preserves_existing_hierarchy_fallbacks(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.COMMAND_PALETTE,
            file_scroll=7,
        )

        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.file_scroll, 0)

        state.page = BrowserPage.SCOPE_HOME
        state.file_scroll = 8
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.file_scroll, 0)

        state.page = BrowserPage.FILE_DETAIL
        state.file_scroll = 9
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.file_scroll, 0)

        commit = CommitSummary(
            commit="abcdef1234567890",
            parent=None,
            authored_at="2026-06-24",
            subject="Example",
        )
        state.selected_commit = commit
        state.page = BrowserPage.CHANGED_FILES
        state.file_scroll = 10
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.COMMIT_PICKER)
        self.assertIs(state.selected_commit, commit)
        self.assertEqual(state.file_scroll, 0)

    def test_back_and_forward_restore_page_snapshots(self):
        state = BrowserState(
            [
                FileChange("src/First.ts", 1, 0),
                FileChange("src/Second.ts", 1, 0),
            ],
            selected=1,
            list_scroll=4,
            page=BrowserPage.CHANGED_FILES,
        )

        BrowserNavigation.open_file_detail(state)
        state.file_scroll = 9
        BrowserNavigation.go_back(state)

        self.assertEqual(state.page, BrowserPage.CHANGED_FILES)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.list_scroll, 4)

        BrowserNavigation.go_forward(state)

        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 9)

        BrowserNavigation.show_source_file(state, "src/First.ts", 3)
        state.source_find_text = "needle"
        state.source_file_scroll = 2
        state.source_context_lines = 8
        state.source_selection_start = 2
        state.source_selection_end = 5
        state.source_mark_line = 4
        BrowserNavigation.go_back(state)
        BrowserNavigation.go_forward(state)

        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_path, "src/First.ts")
        self.assertEqual(state.source_file_line, 3)
        self.assertEqual(state.source_file_scroll, 2)
        self.assertEqual(state.source_find_text, "needle")
        self.assertEqual(state.source_context_lines, 8)
        self.assertEqual(state.source_selection_start, 2)
        self.assertEqual(state.source_selection_end, 5)
        self.assertEqual(state.source_mark_line, 4)

        BrowserNavigation.show_task_problems(
            state,
            problem_filter="warning",
            problem_sort="severity",
            problem_query="Foo",
            problem_group="file",
        )
        state.problem_selected = 2
        state.problem_scroll = 1
        BrowserNavigation.go_back(state)
        BrowserNavigation.go_forward(state)

        self.assertEqual(state.page, BrowserPage.TASK_PROBLEMS)
        self.assertEqual(state.problem_filter, "warning")
        self.assertEqual(state.problem_sort, "severity")
        self.assertEqual(state.problem_query, "Foo")
        self.assertEqual(state.problem_group, "file")
        self.assertEqual(state.problem_selected, 2)
        self.assertEqual(state.problem_scroll, 1)

        BrowserNavigation.show_page_help(state)
        BrowserNavigation.go_back(state)
        BrowserNavigation.go_forward(state)

        self.assertEqual(state.page, BrowserPage.HELP)
        self.assertEqual(state.help_topic_page, BrowserPage.TASK_PROBLEMS)

    def test_back_returns_to_page_that_opened_command_palette(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=12,
        )

        BrowserNavigation.show_command_palette(state)
        BrowserNavigation.go_back(state)

        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 12)

    def test_back_returns_to_page_that_opened_help(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.FILE_DETAIL,
            selected=0,
            file_scroll=12,
        )

        BrowserNavigation.show_page_help(state)
        BrowserNavigation.go_back(state)

        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.file_scroll, 12)

    def test_new_branch_clears_forward_stack(self):
        state = BrowserState(
            [FileChange("src/Sample.ts", 1, 1)],
            page=BrowserPage.CHANGED_FILES,
        )

        BrowserNavigation.open_file_detail(state)
        BrowserNavigation.go_back(state)
        BrowserNavigation.show_scope_home(state)
        BrowserNavigation.go_forward(state)

        self.assertEqual(state.page, BrowserPage.SCOPE_HOME)


if __name__ == "__main__":
    unittest.main()
