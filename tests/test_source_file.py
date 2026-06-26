import tempfile
import unittest
from pathlib import Path

from cr.ui import source_file


class SourceFileBehaviorTests(unittest.TestCase):
    def test_source_view_windows_the_target_line_inside_repo_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text(
                "\n".join(f"line {index}" for index in range(1, 21)),
                encoding="utf-8",
            )

            view = source_file.load_source_file_view(
                repo,
                "src/Foo.ets",
                target_line=10,
                scroll=-1,
                capacity=5,
            )

        self.assertIsNone(view.error)
        self.assertEqual(view.path, "src/Foo.ets")
        self.assertEqual(view.target_line, 10)
        self.assertEqual(view.scroll, 7)
        self.assertEqual([row.line_number for row in view.rows], [8, 9, 10, 11, 12])
        self.assertEqual(view.rows[2].text, "line 10")
        self.assertTrue(view.rows[2].is_target)

    def test_source_view_clamps_line_and_reports_missing_or_non_utf8_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("only one line\n", encoding="utf-8")
            binary = repo / "src" / "Blob.bin"
            binary.write_bytes(b"\xff\xfe\x00")

            clamped = source_file.load_source_file_view(
                repo,
                "src/Foo.ets",
                target_line=99,
                scroll=0,
                capacity=5,
            )
            missing = source_file.load_source_file_view(
                repo,
                "src/Missing.ets",
                target_line=1,
                scroll=0,
                capacity=5,
            )
            non_utf8 = source_file.load_source_file_view(
                repo,
                "src/Blob.bin",
                target_line=1,
                scroll=0,
                capacity=5,
            )

        self.assertEqual(clamped.target_line, 1)
        self.assertEqual(clamped.rows[0].line_number, 1)
        self.assertIsNone(clamped.error)
        self.assertEqual(missing.error, "Source file not found.")
        self.assertEqual(non_utf8.error, "Source file is not UTF-8 text.")

    def test_source_content_reads_lines_and_reports_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("one\ntwo\n", encoding="utf-8")

            content = source_file.load_source_file_content(repo, "src/Foo.ets")
            missing = source_file.load_source_file_content(repo, "src/Missing.ets")

        self.assertEqual(content.lines, ["one", "two"])
        self.assertIsNone(content.error)
        self.assertEqual(missing.error, "Source file not found.")

    def test_source_context_markdown_centers_target_and_can_include_symbol_label(self):
        content = source_file.SourceFileContent(
            "src/Foo.ets",
            [f"line {index}" for index in range(1, 11)],
        )

        snippet = source_file.source_context_markdown(
            content,
            target_line=5,
            context_lines=2,
        )

        self.assertIn("src/Foo.ets:5", snippet)
        self.assertIn("```text", snippet)
        self.assertIn("  3  line 3", snippet)
        self.assertIn("> 5  line 5", snippet)
        self.assertIn("  7  line 7", snippet)
        self.assertNotIn("line 2", snippet)
        self.assertNotIn("line 8", snippet)

        labeled = source_file.source_context_markdown(
            content,
            target_line=5,
            context_lines=1,
            symbol_label="struct Foo > method build",
        )

        self.assertIn("Symbol: struct Foo > method build", labeled)
        self.assertIn("> 5  line 5", labeled)
        self.assertNotIn("line 3", labeled)

    def test_source_range_selection_marks_rows_and_renders_ordered_markdown(self):
        content = source_file.SourceFileContent(
            "src/Foo.ets",
            [f"line {index}" for index in range(1, 8)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            source = repo / "src" / "Foo.ets"
            source.parent.mkdir(parents=True)
            source.write_text("\n".join(content.lines), encoding="utf-8")

            view = source_file.load_source_file_view(
                repo,
                "src/Foo.ets",
                target_line=3,
                scroll=0,
                capacity=5,
                selection_start=2,
                selection_end=4,
            )

        selected = [
            row.line_number
            for row in view.rows
            if row.is_selected
        ]
        snippet = source_file.source_range_markdown(
            content,
            start_line=4,
            end_line=2,
            target_line=3,
        )

        self.assertEqual(selected, [2, 3, 4])
        self.assertIn("src/Foo.ets:2-4", snippet)
        self.assertIn("  2  line 2", snippet)
        self.assertIn("> 3  line 3", snippet)
        self.assertIn("  4  line 4", snippet)
        self.assertNotIn("line 1", snippet)
        self.assertNotIn("line 5", snippet)

        labeled = source_file.source_range_markdown(
            content,
            start_line=2,
            end_line=4,
            target_line=3,
            symbol_label="struct Foo > method build",
        )

        self.assertIn("Symbol: struct Foo > method build", labeled)
        self.assertIn("src/Foo.ets:2-4", labeled)
        self.assertNotIn("line 5", labeled)


if __name__ == "__main__":
    unittest.main()
