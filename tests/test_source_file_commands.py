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


class SourceFileCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_source_enum_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".git").mkdir()
            source = repo / "src" / "Status.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "export const enum FeedStatus {",
                        "  Loading = 'loading',",
                        "  Ready = 'ready',",
                        "}",
                        "function after() {",
                        "  return FeedStatus.Ready",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            change = FileChange("src/Status.ets", 1, 0)
            copied: list[str] = []
            state = browser_module.BrowserState(
                [change],
                page=browser_module.BrowserPage.SOURCE_FILE,
                source_file_path="src/Status.ets",
                source_file_line=2,
                selected=0,
            )
            executor = browser_module.BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    side_effect=lambda text, _cmd: copied.append(text),
                ):
                    result = executor.execute(parse_browser_command("copy source symbol"))

        self.assertTrue(result.handled)
        self.assertIn("Copied source symbol src/Status.ets:1-4.", state.status_message)
        self.assertEqual(len(copied), 1)
        self.assertIn("Symbol: enum FeedStatus", copied[0])
        self.assertIn("  Loading = 'loading',", copied[0])
        self.assertNotIn("function after", copied[0])

    def test_browse_source_file_screen_lines_show_current_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('hello')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("symbol: struct Foo > method build", text)
        self.assertIn("> 3", text)

    def test_browse_source_file_screen_lines_show_matching_task_problem(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertIn("problem: 1/1 ERROR TS123", text)
        self.assertIn("bad value", text)

    def test_browse_source_file_screen_lines_hides_stale_task_problem(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        process.wait(timeout=1)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                task=TaskState(
                    ["./build.sh"],
                    process,
                    lines=["src/Foo.ets:2:1 error TS123: bad value"],
                ),
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                lines = browser_module._browse_source_file_screen_lines(
                    state,
                    TerminalStyle(False),
                    max_lines=8,
                )

        text = "\n".join(lines)
        self.assertNotIn("problem:", text)
        self.assertNotIn("bad value", text)

    def test_browser_command_executor_views_source_file_diff(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0), FileChange("src/Two.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )
            lines = [
                "File 2/2  src/Two.ets",
                "  @@ -1,2 +1,3 @@",
                "     1    1 | one",
                "          2 | +two",
            ]

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser._cached_file_lines", return_value=lines):
                    with patch("cr.ui.browser._max_file_scroll", return_value=10):
                        result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.FILE_DETAIL)
        self.assertEqual(state.selected, 1)
        self.assertEqual(state.file_scroll, 2)
        self.assertIn("Opened source diff src/Two.ets:2.", state.status_message)
        BrowserNavigation.go_back(state)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)

    def test_browser_command_executor_reports_source_file_diff_without_changed_file(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source_dir = repo / "src"
            source_dir.mkdir(parents=True)
            (source_dir / "One.ets").write_text("one\n", encoding="utf-8")
            (source_dir / "Two.ets").write_text("one\ntwo\n", encoding="utf-8")
            state = BrowserState(
                [FileChange("src/One.ets", 1, 0)],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Two.ets",
                source_file_line=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("view diff"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.selected, 0)
        self.assertIn(
            "No diff for source src/Two.ets:2 in current review scope.",
            state.status_message,
        )

    def test_browser_command_executor_scrolls_and_opens_source_file_page(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 40)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=20,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(open_cmd="editor {fileline}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                down = executor.execute(parse_browser_command("down", raw_keys=True))
                scroll_after_down = state.source_file_scroll
                end = executor.execute(parse_browser_command("end", raw_keys=True))
                scroll_after_end = state.source_file_scroll
                home = executor.execute(parse_browser_command("home", raw_keys=True))
                scroll_after_home = state.source_file_scroll
                with patch(
                    "cr.ui.browser.file_actions.open_path",
                    return_value=None,
                ) as open_path:
                    opened = executor.execute(parse_browser_command("open"))

        self.assertTrue(down.needs_redraw)
        self.assertTrue(end.needs_redraw)
        self.assertTrue(home.needs_redraw)
        self.assertGreater(scroll_after_down, 0)
        self.assertGreater(scroll_after_end, scroll_after_down)
        self.assertEqual(scroll_after_home, 0)
        self.assertTrue(opened.needs_redraw)
        open_path.assert_called_once_with(source, 20, "editor {fileline}")
        self.assertIn("Opened source src/Foo.ets:20", state.status_message)

    def test_browser_command_executor_copies_source_file_page_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=20,
            source_file_scroll=7,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_called_once_with("src/Foo.ets:20", "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 20)
        self.assertEqual(state.source_file_scroll, 7)
        self.assertIn("Copied source line src/Foo.ets:20", state.status_message)

    def test_browser_command_executor_copies_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:5", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  8  line 8", copied)
        self.assertNotIn("line 1", copied)
        copy_text.assert_called_once_with(copied, "copy {text}")
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 5)
        self.assertEqual(state.source_file_scroll, 2)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)

    def test_browser_command_executor_copies_source_file_context_with_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('hello')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("> 3  ", copied)
        self.assertIn("Copied source context src/Foo.ets:3", state.status_message)

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

    def test_browser_command_executor_sets_source_context_lines(self):
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

    def test_browser_command_executor_sets_and_clears_source_selection(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        set_selection = executor.execute(parse_browser_command("source select 8 3"))
        selection_after_set = (
            state.source_selection_start,
            state.source_selection_end,
        )
        invalid_selection = executor.execute(parse_browser_command("source select nope 3"))
        selection_after_invalid = (
            state.source_selection_start,
            state.source_selection_end,
        )
        clear_selection = executor.execute(parse_browser_command("source clear selection"))

        self.assertTrue(set_selection.handled)
        self.assertTrue(set_selection.needs_redraw)
        self.assertTrue(invalid_selection.handled)
        self.assertTrue(clear_selection.handled)
        self.assertEqual(selection_after_set, (3, 8))
        self.assertEqual(selection_after_invalid, (3, 8))
        self.assertEqual(state.source_selection_start, 0)
        self.assertEqual(state.source_selection_end, 0)
        self.assertIn("Source selection cleared.", state.status_message)

    def test_browser_command_executor_selects_source_range_from_mark_to_current_line(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        mark_result = executor.execute(parse_browser_command("source mark"))
        state.source_file_line = 9
        select_result = executor.execute(parse_browser_command("source select to"))
        state.source_file_line = 3
        reverse_result = executor.execute(parse_browser_command("source select to"))
        clear_mark_result = executor.execute(parse_browser_command("source clear mark"))

        self.assertTrue(mark_result.needs_redraw)
        self.assertTrue(select_result.needs_redraw)
        self.assertTrue(reverse_result.needs_redraw)
        self.assertTrue(clear_mark_result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (3, 5))
        self.assertEqual(state.source_mark_line, 0)
        self.assertIn("Source mark cleared.", state.status_message)

    def test_browser_command_executor_reports_source_select_to_without_mark(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.SOURCE_FILE,
            source_file_path="src/Foo.ets",
            source_file_line=5,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select to"))

        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn("Set a source mark before selecting to it.", state.status_message)

    def test_browser_command_executor_selects_current_source_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (2, 5))
        self.assertIn(
            "Selected source symbol struct Foo > method build src/Foo.ets:2-5.",
            state.status_message,
        )

    def test_browser_command_executor_reports_source_symbol_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (0, 0))
        self.assertIn(
            "Open a source file before selecting source symbol.",
            state.status_message,
        )

    def test_browser_command_executor_reports_source_symbol_selection_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                source_selection_start=7,
                source_selection_end=9,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("source select symbol"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 9))
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_source_selection_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.CHANGED_FILES)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source select 1 3"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_selection_start, 0)
        self.assertIn("Open a source file before selecting source.", state.status_message)

    def test_browser_command_executor_copies_selected_source_symbol_range(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    select_result = executor.execute(
                        parse_browser_command("source select symbol")
                    )
                    copy_result = executor.execute(parse_browser_command("copy source"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(select_result.handled)
        self.assertTrue(copy_result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertIn("const title = 'hi'", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied selected source src/Foo.ets:2-5.", state.status_message)

    def test_browser_command_executor_copies_source_file_symbol_directly(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    const title = 'hi'",
                        "    Text(title)",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_selection_start=7,
                source_selection_end=8,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-5", copied)
        self.assertIn("Symbol: struct Foo > method build", copied)
        self.assertNotIn("other() {", copied)
        self.assertEqual((state.source_selection_start, state.source_selection_end), (7, 8))
        self.assertIn("Copied source symbol src/Foo.ets:2-5.", state.status_message)

    def test_browser_command_executor_saves_file_detail_source_symbol(self):
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

    def test_browser_command_executor_copies_source_field_arrow_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  private onTap = () => {",
                        "    this.handleTap()",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: struct Foo > method onTap", copied)
        self.assertIn("private onTap = () => {", copied)
        self.assertIn("this.handleTap()", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_copies_source_accessor_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  get title(): string {",
                        "    return this.model.title",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method title", copied)
        self.assertIn("get title(): string", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_copies_source_generic_method_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "class Foo {",
                        "  private createModel<T extends BaseModel>(value: T): T {",
                        "    return value",
                        "  }",
                        "  other() {",
                        "    Text('nope')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        copied = copy_text.call_args.args[0]
        self.assertTrue(result.handled)
        self.assertIn("src/Foo.ets:2-4", copied)
        self.assertIn("Symbol: class Foo > method createModel", copied)
        self.assertIn("private createModel<T extends BaseModel>", copied)
        self.assertNotIn("other() {", copied)
        self.assertIn("Copied source symbol src/Foo.ets:2-4.", state.status_message)

    def test_browser_command_executor_reports_copy_source_symbol_without_symbol(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy source symbol"))

        self.assertTrue(result.handled)
        copy_text.assert_not_called()
        self.assertIn("No source symbol at current line.", state.status_message)

    def test_browser_command_executor_reports_source_context_without_source_page(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState(
            [],
            page=BrowserPage.CHANGED_FILES,
            source_context_lines=3,
        )
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        result = executor.execute(parse_browser_command("source context 8"))

        self.assertTrue(result.handled)
        self.assertEqual(state.source_context_lines, 3)
        self.assertIn("Open a source file before setting source context.", state.status_message)

    def test_browser_command_executor_copies_configured_source_file_context(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("  4  line 4", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 3", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied source context src/Foo.ets:5", state.status_message)

    def test_browser_command_executor_copies_selected_source_range(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 11)),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=5,
                source_context_lines=1,
                source_selection_start=3,
                source_selection_end=6,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.browser.file_actions.copy_text",
                    return_value=None,
                ) as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        copied = copy_text.call_args.args[0]
        self.assertIn("src/Foo.ets:3-6", copied)
        self.assertIn("  3  line 3", copied)
        self.assertIn("> 5  line 5", copied)
        self.assertIn("  6  line 6", copied)
        self.assertNotIn("line 2", copied)
        self.assertNotIn("line 7", copied)
        self.assertIn("Copied selected source src/Foo.ets:3-6", state.status_message)

    def test_browser_command_executor_reports_empty_source_context_copy(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file to copy.", state.status_message)

    def test_browser_command_executor_reports_missing_source_context_copy(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Missing.ets",
                source_file_line=5,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(copy_cmd="copy {text}"),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
                    result = executor.execute(parse_browser_command("copy source"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("Source file not found.", state.status_message)

    def test_browser_command_executor_reports_empty_source_file_line_copy(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([], page=BrowserPage.SOURCE_FILE)
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy {text}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=True,
        )

        with patch("cr.ui.browser.file_actions.copy_text") as copy_text:
            result = executor.execute(parse_browser_command("copy line"))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        copy_text.assert_not_called()
        self.assertIn("No source file line to copy.", state.status_message)

    def test_browser_command_executor_finds_text_in_source_file_page(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nBeta target\ngamma\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                file_find_text="file-query",
                task_find_text="task-query",
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                result = executor.execute(parse_browser_command("find TARGET", raw_keys=True))

        self.assertTrue(result.handled)
        self.assertTrue(result.needs_redraw)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertEqual(state.source_find_text, "TARGET")
        self.assertEqual(state.file_find_text, "file-query")
        self.assertEqual(state.task_find_text, "task-query")
        self.assertIn('Found "TARGET" at line 2.', state.status_message)

    def test_browser_command_executor_repeats_source_file_find_matches(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "target one\nmiddle\ntarget two\n",
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                find = executor.execute(parse_browser_command("find target", raw_keys=True))
                next_match = executor.execute(
                    parse_browser_command("next match", raw_keys=True)
                )
                line_after_next = state.source_file_line
                previous_match = executor.execute(
                    parse_browser_command("prev match", raw_keys=True)
                )

        self.assertTrue(find.needs_redraw)
        self.assertTrue(next_match.needs_redraw)
        self.assertTrue(previous_match.needs_redraw)
        self.assertEqual(line_after_next, 3)
        self.assertEqual(state.source_file_line, 1)
        self.assertEqual(state.source_find_text, "target")
        self.assertIn('Found "target" at line 1.', state.status_message)

    def test_browser_command_executor_jumps_source_file_symbols(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('first')",
                        "  }",
                        "  private onTap = () => {",
                        "    this.handleTap()",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=3,
                source_file_scroll=2,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                next_symbol = executor.execute(parse_browser_command("next symbol"))
                line_after_next = state.source_file_line
                scroll_after_next = state.source_file_scroll
                prev_symbol = executor.execute(parse_browser_command("prev symbol"))

        self.assertTrue(next_symbol.handled)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(line_after_next, 5)
        self.assertEqual(scroll_after_next, -1)
        self.assertTrue(prev_symbol.handled)
        self.assertEqual(state.page, BrowserPage.SOURCE_FILE)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, -1)
        self.assertIn("已跳到源码符号 struct Foo > method build src/Foo.ets:2.", state.status_message)

    def test_browser_command_executor_reports_source_symbol_jump_empty_states(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("const title = 'hi'\nText(title)\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                no_symbols = executor.execute(parse_browser_command("next symbol"))
                no_symbol_message = state.status_message
                state.source_file_path = "src/Missing.ets"
                missing = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(no_symbols.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(no_symbol_message, "没有可跳转的源码符号。")
        self.assertIn("Source file not found.", state.status_message)

    def test_browser_command_executor_reports_source_symbol_jump_boundaries(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(
                    [
                        "struct Foo {",
                        "  build() {",
                        "    Text('first')",
                        "  }",
                        "}",
                    ]
                ),
                encoding="utf-8",
            )
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=1,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                previous_symbol = executor.execute(parse_browser_command("prev symbol"))
                previous_message = state.status_message
                state.source_file_line = 4
                next_symbol = executor.execute(parse_browser_command("next symbol"))

        self.assertTrue(previous_symbol.needs_redraw)
        self.assertTrue(next_symbol.needs_redraw)
        self.assertEqual(previous_message, "已经在第一个源码符号。")
        self.assertEqual(state.source_file_line, 4)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertEqual(state.status_message, "已经在最后一个源码符号。")

    def test_browser_command_executor_reports_source_file_find_empty_states(self):
        from cr.ui.browser import parse_browser_command

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("alpha\nbeta\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_file_scroll=1,
            )
            executor = BrowserCommandExecutor(
                state,
                argparse_namespace(),
                TerminalStyle(),
                BrowserFrame(),
                raw_keys=True,
            )

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                empty = executor.execute(parse_browser_command("find", raw_keys=True))
                missing = executor.execute(parse_browser_command("find owner", raw_keys=True))
                repeat = executor.execute(parse_browser_command("next match", raw_keys=True))
                state.source_file_path = "src/Missing.ets"
                unreadable = executor.execute(
                    parse_browser_command("find alpha", raw_keys=True)
                )

        self.assertTrue(empty.needs_redraw)
        self.assertTrue(missing.needs_redraw)
        self.assertTrue(repeat.needs_redraw)
        self.assertTrue(unreadable.needs_redraw)
        self.assertEqual(state.source_find_text, "owner")
        self.assertEqual(state.source_file_line, 2)
        self.assertEqual(state.source_file_scroll, 1)
        self.assertIn("Source file not found.", state.status_message)

    def test_browse_screen_renders_source_file_page(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\nthree\n", encoding="utf-8")
            state = BrowserState(
                [],
                page=BrowserPage.SOURCE_FILE,
                source_file_path="src/Foo.ets",
                source_file_line=2,
                source_context_lines=8,
            )
            output = StringIO()

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                with patch(
                    "cr.ui.frame.shutil.get_terminal_size",
                    return_value=os.terminal_size((120, 12)),
                ):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertIn("Scope: worktree > Source > src/Foo.ets", text)
        self.assertIn("Source src/Foo.ets", text)
        self.assertIn("context: 8", text)
        self.assertIn("> 2  two", text)
        self.assertIn("cr:source> ", text)


if __name__ == "__main__":
    unittest.main()
