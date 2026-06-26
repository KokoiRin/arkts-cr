import unittest
from pathlib import Path

import cr.ui.browser as browser_module
from cr.ui.commands import BrowserCommandAction, parse_browser_command


class BrowserCommandParserTests(unittest.TestCase):
    def test_command_aliases_and_parameters_map_to_stable_actions(self):
        # Behavior: 当用户在产品通用行为中执行操作「命令 别名 and 参数 映射 to 稳定 动作」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        cases = [
            ("q", BrowserCommandAction.QUIT, ""),
            ("quit", BrowserCommandAction.QUIT, ""),
            ("build", BrowserCommandAction.RUN_BUILD, ""),
            ("compile", BrowserCommandAction.RUN_BUILD, ""),
            ("done next", BrowserCommandAction.MARK_SEEN_AND_NEXT, ""),
            ("seen next", BrowserCommandAction.MARK_SEEN_AND_NEXT, ""),
            ("copy path", BrowserCommandAction.COPY_PATH, ""),
            ("copy anchor", BrowserCommandAction.COPY_ANCHOR, ""),
            ("copy diff", BrowserCommandAction.COPY_DIFF, ""),
            ("copy hunk", BrowserCommandAction.COPY_HUNK, ""),
            ("copy line", BrowserCommandAction.COPY_LINE, ""),
            ("copy source", BrowserCommandAction.COPY_SOURCE_CONTEXT, ""),
            ("copy source symbol", BrowserCommandAction.COPY_SOURCE_SYMBOL, ""),
            ("copy symbol", BrowserCommandAction.COPY_SOURCE_SYMBOL, ""),
            ("copy current symbol", BrowserCommandAction.COPY_SOURCE_SYMBOL, ""),
            ("save source", BrowserCommandAction.SAVE_SOURCE_CONTEXT, ""),
            ("save source tmp/source.md", BrowserCommandAction.SAVE_SOURCE_CONTEXT, "tmp/source.md"),
            ("save source symbol", BrowserCommandAction.SAVE_SOURCE_SYMBOL, ""),
            ("save source symbol tmp/symbol.md", BrowserCommandAction.SAVE_SOURCE_SYMBOL, "tmp/symbol.md"),
            ("next symbol", BrowserCommandAction.NEXT_SOURCE_SYMBOL, ""),
            ("prev symbol", BrowserCommandAction.PREVIOUS_SOURCE_SYMBOL, ""),
            ("copy change", BrowserCommandAction.COPY_CHANGE, ""),
            ("open hunk", BrowserCommandAction.OPEN_HUNK, ""),
            ("open line", BrowserCommandAction.OPEN_LINE, ""),
            ("view source", BrowserCommandAction.VIEW_SOURCE, ""),
            ("view source symbol", BrowserCommandAction.VIEW_SOURCE_SYMBOL, ""),
            ("source view", BrowserCommandAction.VIEW_SOURCE, ""),
            ("view current source", BrowserCommandAction.VIEW_SOURCE, ""),
            ("find TargetValue", BrowserCommandAction.FIND_IN_FILE, "TargetValue"),
            ("next match", BrowserCommandAction.NEXT_MATCH, ""),
            ("prev match", BrowserCommandAction.PREVIOUS_MATCH, ""),
            ("next change", BrowserCommandAction.NEXT_CHANGE, ""),
            ("prev change", BrowserCommandAction.PREVIOUS_CHANGE, ""),
            ("save diff", BrowserCommandAction.SAVE_DIFF, ""),
            ("save diff tmp/diff.md", BrowserCommandAction.SAVE_DIFF, "tmp/diff.md"),
            ("next hunk", BrowserCommandAction.NEXT_HUNK, ""),
            ("]", BrowserCommandAction.NEXT_HUNK, ""),
            ("prev hunk", BrowserCommandAction.PREVIOUS_HUNK, ""),
            ("[", BrowserCommandAction.PREVIOUS_HUNK, ""),
            ("reveal", BrowserCommandAction.REVEAL_FILE, ""),
            ("file actions", BrowserCommandAction.SHOW_FILE_ACTION_DIAGNOSTICS, ""),
            ("note check lifecycle edge case", BrowserCommandAction.SET_REVIEW_NOTE, "check lifecycle edge case"),
            ("note change check lifecycle edge case", BrowserCommandAction.SET_CHANGE_REVIEW_NOTE, "check lifecycle edge case"),
            ("note change", BrowserCommandAction.SET_REVIEW_NOTE, "change"),
            ("note", BrowserCommandAction.SET_REVIEW_NOTE, ""),
            ("notes", BrowserCommandAction.SHOW_REVIEW_NOTES, ""),
            ("review notes", BrowserCommandAction.SHOW_REVIEW_NOTES, ""),
            ("notes lifecycle", BrowserCommandAction.SHOW_REVIEW_NOTES, "lifecycle"),
            ("copy notes", BrowserCommandAction.COPY_REVIEW_NOTES, ""),
            ("copy notes lifecycle", BrowserCommandAction.COPY_REVIEW_NOTES, "lifecycle"),
            ("notes copy", BrowserCommandAction.COPY_REVIEW_NOTES, ""),
            ("save notes", BrowserCommandAction.SAVE_REVIEW_NOTES, ""),
            ("save notes tmp/notes.md", BrowserCommandAction.SAVE_REVIEW_NOTES, "tmp/notes.md"),
            ("copy prompt", BrowserCommandAction.COPY_PROMPT, ""),
            ("copy prompt file", BrowserCommandAction.COPY_FILE_PROMPT, ""),
            ("copy task", BrowserCommandAction.COPY_TASK_OUTPUT, ""),
            ("copy task tail", BrowserCommandAction.COPY_TASK_OUTPUT_TAIL, ""),
            ("copy task tail 5", BrowserCommandAction.COPY_TASK_OUTPUT_TAIL, "5"),
            ("copy task match", BrowserCommandAction.COPY_TASK_OUTPUT_MATCH, ""),
            ("task output", BrowserCommandAction.SHOW_TASK_OUTPUT, ""),
            ("output", BrowserCommandAction.SHOW_TASK_OUTPUT, ""),
            ("problems", BrowserCommandAction.SHOW_TASK_PROBLEMS, ""),
            ("task problems", BrowserCommandAction.SHOW_TASK_PROBLEMS, ""),
            ("copy problem", BrowserCommandAction.COPY_TASK_PROBLEM, ""),
            ("save problem", BrowserCommandAction.SAVE_TASK_PROBLEM, ""),
            ("save problem tmp/problem.md", BrowserCommandAction.SAVE_TASK_PROBLEM, "tmp/problem.md"),
            ("copy problems", BrowserCommandAction.COPY_TASK_PROBLEMS, ""),
            ("copy file problems", BrowserCommandAction.COPY_FILE_TASK_PROBLEMS, ""),
            ("save problems", BrowserCommandAction.SAVE_TASK_PROBLEMS, ""),
            ("save problems tmp/problems.md", BrowserCommandAction.SAVE_TASK_PROBLEMS, "tmp/problems.md"),
            ("save file problems", BrowserCommandAction.SAVE_FILE_TASK_PROBLEMS, ""),
            ("save file problems tmp/file-problems.md", BrowserCommandAction.SAVE_FILE_TASK_PROBLEMS, "tmp/file-problems.md"),
            ("next problem file", BrowserCommandAction.NEXT_TASK_PROBLEM_FILE, ""),
            ("prev problem file", BrowserCommandAction.PREVIOUS_TASK_PROBLEM_FILE, ""),
            ("next problem", BrowserCommandAction.NEXT_TASK_PROBLEM, ""),
            ("prev problem", BrowserCommandAction.PREVIOUS_TASK_PROBLEM, ""),
            ("copy problem context", BrowserCommandAction.COPY_PROBLEM_CONTEXT, ""),
            ("save problem context", BrowserCommandAction.SAVE_PROBLEM_CONTEXT, ""),
            ("save problem context tmp/problem.md", BrowserCommandAction.SAVE_PROBLEM_CONTEXT, "tmp/problem.md"),
            ("problems find Foo", BrowserCommandAction.SET_TASK_PROBLEM_QUERY, "Foo"),
            ("problems clear find", BrowserCommandAction.CLEAR_TASK_PROBLEM_QUERY, ""),
            ("source select 2 5", BrowserCommandAction.SET_SOURCE_SELECTION, "2 5"),
            ("source mark", BrowserCommandAction.SET_SOURCE_MARK, ""),
            ("source select to", BrowserCommandAction.SELECT_SOURCE_TO_MARK, ""),
            ("source select symbol", BrowserCommandAction.SELECT_SOURCE_SYMBOL, ""),
            ("select source symbol", BrowserCommandAction.SELECT_SOURCE_SYMBOL, ""),
            ("source symbol", BrowserCommandAction.SELECT_SOURCE_SYMBOL, ""),
            ("source clear mark", BrowserCommandAction.CLEAR_SOURCE_MARK, ""),
            ("source clear selection", BrowserCommandAction.CLEAR_SOURCE_SELECTION, ""),
            ("problems errors", BrowserCommandAction.SET_TASK_PROBLEM_FILTER, "error"),
            ("warnings", BrowserCommandAction.SET_TASK_PROBLEM_FILTER, "warning"),
            ("problems all", BrowserCommandAction.CLEAR_TASK_PROBLEM_FILTER, ""),
            ("problems sort severity", BrowserCommandAction.SET_TASK_PROBLEM_SORT, "severity"),
            ("problems sort output", BrowserCommandAction.SET_TASK_PROBLEM_SORT, "output"),
            ("problems group file", BrowserCommandAction.SET_TASK_PROBLEM_GROUP, "file"),
            ("problems group none", BrowserCommandAction.SET_TASK_PROBLEM_GROUP, "none"),
            ("view problem", BrowserCommandAction.VIEW_TASK_PROBLEM, ""),
            ("view problem diff", BrowserCommandAction.VIEW_TASK_PROBLEM_DIFF, ""),
            ("copy problem diff", BrowserCommandAction.COPY_PROBLEM_DIFF, ""),
            ("save problem diff", BrowserCommandAction.SAVE_PROBLEM_DIFF, ""),
            ("save problem diff tmp/problem-diff.md", BrowserCommandAction.SAVE_PROBLEM_DIFF, "tmp/problem-diff.md"),
            ("view diff", BrowserCommandAction.VIEW_TASK_PROBLEM_DIFF, ""),
            ("save prompt", BrowserCommandAction.SAVE_PROMPT, ""),
            ("save prompt tmp/review.md", BrowserCommandAction.SAVE_PROMPT, "tmp/review.md"),
            ("save prompt file", BrowserCommandAction.SAVE_FILE_PROMPT, ""),
            ("save prompt file tmp/file.md", BrowserCommandAction.SAVE_FILE_PROMPT, "tmp/file.md"),
            ("save task", BrowserCommandAction.SAVE_TASK_OUTPUT, ""),
            ("save task tmp/task.md", BrowserCommandAction.SAVE_TASK_OUTPUT, "tmp/task.md"),
            ("save task tail", BrowserCommandAction.SAVE_TASK_OUTPUT_TAIL, ""),
            ("save task tail tmp/tail.md", BrowserCommandAction.SAVE_TASK_OUTPUT_TAIL, "tmp/tail.md"),
            ("save task match", BrowserCommandAction.SAVE_TASK_OUTPUT_MATCH, ""),
            ("save task match tmp/match.md", BrowserCommandAction.SAVE_TASK_OUTPUT_MATCH, "tmp/match.md"),
            ("tasks", BrowserCommandAction.SHOW_TASK_DIAGNOSTICS, ""),
            ("tasks help", BrowserCommandAction.SHOW_TASK_SCHEMA_HELP, ""),
            ("task help", BrowserCommandAction.SHOW_TASK_SCHEMA_HELP, ""),
            ("forward", BrowserCommandAction.FORWARD, ""),
            ("stage", BrowserCommandAction.STAGE_FILE, ""),
            ("unstage", BrowserCommandAction.UNSTAGE_FILE, ""),
            ("source staged", BrowserCommandAction.SET_SOURCE_FILTER, "staged"),
            ("source clear", BrowserCommandAction.CLEAR_SOURCE_FILTER, ""),
            ("source context 1", BrowserCommandAction.SET_SOURCE_CONTEXT_LINES, "1"),
            ("base main", BrowserCommandAction.SWITCH_BASE, "main"),
            ("range main..feature", BrowserCommandAction.SWITCH_RANGE, "main..feature"),
            ("/src/ui", BrowserCommandAction.SET_FILE_FILTER, "src/ui"),
            ("12", BrowserCommandAction.CHOOSE_NUMBER, "12"),
            ("wat", BrowserCommandAction.UNKNOWN, "wat"),
        ]

        for command, expected_action, expected_value in cases:
            with self.subTest(command=command):
                parsed = parse_browser_command(command)

                self.assertEqual(parsed.action, expected_action)
                self.assertEqual(parsed.value, expected_value)

    def test_raw_slash_is_not_a_filter_command(self):
        # Behavior: 当用户在产品通用行为中过滤「raw slash is 不 a 过滤 命令」时，系统应只呈现符合条件的结果，并保持相关选择规则稳定 [Requirement: TODO]
        parsed = parse_browser_command("/src/ui", raw_keys=True)

        self.assertEqual(parsed.action, BrowserCommandAction.UNKNOWN)
        self.assertEqual(parsed.value, "/src/ui")

    def test_browser_main_loop_delegates_to_command_parser(self):
        # Behavior: 当用户在产品通用行为中解析「browser main loop delegates to 命令 parser」时，系统应产出正确的结构化结果 [Requirement: TODO]
        source = Path(browser_module.__file__).read_text(encoding="utf-8")

        self.assertIn("parse_browser_command(command, raw_keys=raw_keys)", source)
        self.assertNotIn('command.startswith("base ")', source)
        self.assertNotIn('command in {"build", "compile"}', source)


if __name__ == "__main__":
    unittest.main()
