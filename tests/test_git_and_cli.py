import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

from cr.ui.browser import (
    BuildState,
    BrowserState,
    _build_command,
    _build_panel_lines,
    _browse_file_screen_lines,
    _draw_build_panel_only,
    _draw_browse_screen,
    _open_command,
    _poll_build,
    _start_build,
    filter_changes_by_query,
)
from cr.review.changes import format_counts
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


ROOT = Path(__file__).resolve().parents[1]


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class CliTests(unittest.TestCase):
    def test_format_counts_handles_binary_stats(self):
        self.assertEqual(format_counts(FileChange("asset.bin", None, None)), "+? -?")

    def test_open_command_uses_configured_template(self):
        command = _open_command(
            Path("/tmp/space dir/Sample.ts"),
            12,
            "code -g {fileline}",
        )

        self.assertEqual(command, ["code", "-g", "/tmp/space dir/Sample.ts:12"])

    def test_open_command_prefers_gui_editor_with_line(self):
        def fake_which(name):
            return f"/usr/local/bin/{name}" if name == "code" else None

        with patch("cr.ui.browser.shutil.which", side_effect=fake_which):
            command = _open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["code", "-g", "/tmp/Sample.ts:7"])

    def test_open_command_falls_back_to_macos_open(self):
        def fake_which(name):
            return "/usr/bin/open" if name == "open" else None

        with patch("cr.ui.browser.platform.system", return_value="Darwin"):
            with patch("cr.ui.browser.shutil.which", side_effect=fake_which):
                command = _open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["open", "/tmp/Sample.ts"])

    def test_build_command_detects_douyin_harmony_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "DouyinHarmony"
            repo.mkdir()
            (repo / "remote").write_text("#!/bin/sh\n", encoding="utf-8")

            self.assertEqual(
                _build_command(repo),
                ["./remote", "buildEntry", "--app", "douyin"],
            )
            self.assertEqual(
                _build_command(repo, "./custom build"),
                ["./custom", "build"],
            )

    def test_build_panel_collects_background_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            command = (
                f"{sys.executable} -c "
                "\"print('compile line 1'); print('compile line 2')\""
            )
            args = argparse_namespace(build_cmd=command)
            state = BrowserState([])

            with patch("cr.ui.browser.git.repo_root", return_value=repo):
                _start_build(state, args)
                for _ in range(100):
                    _poll_build(state.build)
                    if state.build and state.build.returncode is not None:
                        break
                    time.sleep(0.01)

            self.assertIsNotNone(state.build)
            if state.build.returncode is None:
                state.build.process.terminate()
                state.build.process.wait(timeout=1)
            self.assertEqual(state.build.returncode, 0)
            _poll_build(state.build)
            lines = _build_panel_lines(state.build, TerminalStyle(False), 5)
            text = "\n".join(lines)
            self.assertIn("Build succeeded.", text)
            self.assertIn("compile line 1", text)
            self.assertIn("compile line 2", text)

    def test_build_panel_partial_refresh_does_not_clear_screen(self):
        process = subprocess.Popen(["true"], stdout=subprocess.DEVNULL)
        build = BuildState(["true"], process, lines=["compile line"])
        output = StringIO()

        with redirect_stdout(output):
            _draw_build_panel_only(build, TerminalStyle(False))

        text = output.getvalue()
        self.assertNotIn("\033[2J", text)
        self.assertIn("\0337", text)
        self.assertIn("compile line", text)

        output = StringIO()
        with redirect_stdout(output):
            _draw_build_panel_only(build, TerminalStyle(False))

        self.assertEqual(output.getvalue(), "")
        process.wait(timeout=1)

    def test_browse_screen_redraws_in_place(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertTrue(text.startswith("\033[2J\033[H"))
        self.assertIn("> 1", text)
        self.assertIn("└─ src", text)
        self.assertIn("└─ Sample.ts", text)

    def test_browse_tree_highlights_guides_and_uses_plain_white_file_names(self):
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/pages/Sample.ts", 1, 1)])
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=3):
            with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/pages/Sample.ts")):
                with redirect_stdout(output):
                    _draw_browse_screen(state, args, TerminalStyle(True, True))

        text = output.getvalue()
        self.assertIn("\033[36m└─ src/pages\033[0m", text)
        self.assertIn("\033[36m   └─ \033[0m", text)
        self.assertIn("\033[37mSample.ts", text)
        self.assertNotIn("\033[36mSample.ts", text)
        self.assertNotIn("\033]8;;", text)

    def test_browse_filter_matches_paths_and_clamps_selection(self):
        changes = [
            FileChange("src/pages/Home.ets", 1, 1),
            FileChange("src/components/Button.ts", 2, 0),
            FileChange("README.md", 1, 0),
        ]
        self.assertEqual(
            [change.path for change in filter_changes_by_query(changes, "BUTTON")],
            ["src/components/Button.ts"],
        )

        state = BrowserState(changes, selected=2)
        state.set_filter("src/")
        self.assertEqual(
            [change.path for change in state.visible_changes],
            ["src/pages/Home.ets", "src/components/Button.ts"],
        )
        self.assertEqual(state.selected, 0)

        state.selected = 99
        state.clamp_selection()
        self.assertEqual(state.selected, 1)

        state.set_filter("missing")
        self.assertEqual(state.visible_changes, [])
        self.assertEqual(state.selected, 0)
        self.assertEqual(state.mode, "list")

    def test_browse_screen_only_measures_visible_list_rows(self):
        changes = [FileChange(f"src/File{index}.ts", 1, 0) for index in range(30)]
        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState(changes)
        output = StringIO()

        with patch(
            "cr.ui.browser.shutil.get_terminal_size",
            return_value=os.terminal_size((100, 12)),
        ):
            with patch("cr.ui.browser.git.first_changed_line", return_value=1) as first_line:
                with patch("cr.ui.browser.git.repo_path", return_value=Path("/tmp/src/File0.ts")):
                    with redirect_stdout(output):
                        _draw_browse_screen(state, args, TerminalStyle(False))

        text = output.getvalue()
        self.assertLess(first_line.call_count, len(changes))
        self.assertIn("showing rows", text)
        self.assertIn("File0.ts", text)
        self.assertNotIn("File29.ts", text)

    def test_browse_file_screen_scrolls_long_content(self):
        args = argparse_namespace(
            context=0,
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            link_scheme="file",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)], mode="file")
        full_lines = ["File 1/1  src/Sample.ts"] + [
            f"line {index}" for index in range(1, 21)
        ]

        with patch("cr.ui.browser._browse_file_lines", return_value=full_lines):
            top = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )
            state.file_scroll = 10
            lower = _browse_file_screen_lines(
                state,
                state.changes[0],
                0,
                1,
                args,
                TerminalStyle(False),
                max_lines=6,
            )

        self.assertEqual(top[:2], ["File 1/1  src/Sample.ts", "line 1"])
        self.assertIn("showing 1-4/20", top[-1])
        self.assertIn("line 11", lower)
        self.assertIn("showing 11-14/20", lower[-1])

    def test_cli_diff_outline_and_review_in_temp_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            diff = self._cr(repo, "diff")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Changed file tree:", diff.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            outline = self._cr(repo, "outline", "Sample.ets")
            self.assertEqual(outline.returncode, 0, outline.stderr)
            self.assertIn("purpose: ArkTS page/component SamplePage", outline.stdout)
            self.assertIn("struct SamplePage", outline.stdout)
            self.assertIn("method build", outline.stdout)

            review = self._cr(repo, "review")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("Summary:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("focus", review.stdout)
            self.assertIn("Changed file tree:", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("modified: build", review.stdout)
            self.assertIn("method build *", review.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-    Text('hello')", review.stdout)
            self.assertIn("+    Text('hello world')", review.stdout)

            summary = self._cr(repo, "review", "--summary")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("Summary:", summary.stdout)
            self.assertIn("Changed file tree:", summary.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", summary.stdout)
            self.assertNotIn("\n  changes:", summary.stdout)
            self.assertNotIn("purpose:", summary.stdout)
            self.assertNotIn("outline:", summary.stdout)

            no_hunks = self._cr(repo, "review", "--no-hunks")
            self.assertEqual(no_hunks.returncode, 0, no_hunks.stderr)
            self.assertIn("Summary:", no_hunks.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", no_hunks.stdout)
            self.assertIn("modified: build", no_hunks.stdout)
            self.assertIn("outline:", no_hunks.stdout)
            self.assertNotIn("\n  changes:", no_hunks.stdout)
            self.assertNotIn("-    Text('hello')", no_hunks.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 1)
            self.assertEqual(data["summary"]["added"], 1)
            self.assertEqual(data["summary"]["deleted"], 1)
            self.assertEqual(data["files"][0]["path"], "Sample.ets")
            self.assertEqual(data["files"][0]["status"], "modified")
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertIn("ArkTS page/component SamplePage", data["files"][0]["purpose"])
            self.assertTrue(any("+    Text('hello world')" in line for line in data["files"][0]["hunks"]))
            self.assertNotIn("Review changes:", json_review.stdout)

            json_summary = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_summary.returncode, 0, json_summary.stderr)
            summary_data = json.loads(json_summary.stdout)
            self.assertEqual(summary_data["files"][0]["hunks"], [])

    def test_cli_defaults_to_interactive_browser(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "pages" / "Sample.ets"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('old')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            session = self._cr_input(repo, "q\n")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Interactive review", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Enter", session.stdout)
            self.assertIn("j/k", session.stdout)
            self.assertIn("Sample.ets", session.stdout)
            self.assertIn("cr:list>", session.stdout)

    def test_cli_defaults_to_browser_when_options_are_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(repo, "q\n", "--context", "0", "--sort", "path")
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Interactive review", session.stdout)
            self.assertIn("Sample.ts", session.stdout)

    def test_cli_interactive_browser_opens_file_and_navigates(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\nn\nb\nr\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )
            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("File 1/2", session.stdout)
            self.assertIn("File 2/2", session.stdout)
            self.assertIn("-export const first = 'old'", session.stdout)
            self.assertIn("+export const first = 'new'", session.stdout)
            self.assertIn("Changed files", session.stdout)

    def test_cli_browser_shows_recent_commits_when_no_worktree_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'from commit'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "change sample")

            sample.write_text("export const sample = 'staged only'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")

            session = self._cr_input(
                repo,
                "1\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("change sample", session.stdout)
            self.assertIn("cr:commits>", session.stdout)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Sample.ts", session.stdout)
            self.assertIn("-export const sample = 'old'", session.stdout)
            self.assertIn("+export const sample = 'from commit'", session.stdout)

    def test_cli_browser_can_switch_from_worktree_to_recent_commits(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'committed'\n", encoding="utf-8")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "committed sample")

            sample.write_text("export const sample = 'working tree'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "g\n1\nq\n",
                "browse",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Changed files", session.stdout)
            self.assertIn("Recent commits", session.stdout)
            self.assertIn("committed sample", session.stdout)
            self.assertIn("cr:commits>", session.stdout)

    def test_cli_interactive_browser_filters_files_in_line_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = repo / "src" / "First.ts"
            second = repo / "src" / "Second.ts"
            first.parent.mkdir(parents=True)
            first.write_text("export const first = 'old'\n", encoding="utf-8")
            second.write_text("export const second = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            first.write_text("export const first = 'new'\n", encoding="utf-8")
            second.write_text("export const second = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "filter First\nc\n/Second\nr\n1\nq\n",
                "browse",
                "--sort",
                "path",
                "--context",
                "0",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Filter: First (1/2 matches, c to clear)", session.stdout)
            self.assertIn("Filter: Second (1/2 matches, c to clear)", session.stdout)
            self.assertIn("File 1/1", session.stdout)
            self.assertIn("Second.ts", session.stdout)
            self.assertIn("-export const second = 'old'", session.stdout)
            self.assertIn("+export const second = 'new'", session.stdout)

    def test_cli_interactive_browser_can_open_current_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const sample = 'new'\n", encoding="utf-8")

            session = self._cr_input(
                repo,
                "1\no\nq\n",
                "browse",
                "--context",
                "0",
                "--open-cmd",
                "true",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Opened src/Sample.ts:1", session.stdout)

    def test_cli_interactive_browser_can_run_build_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const sample = 'old'\n", encoding="utf-8")
            build_script = repo / "build.sh"
            build_script.write_text(
                "#!/bin/sh\npwd > build.out\n",
                encoding="utf-8",
            )
            os.chmod(build_script, 0o755)
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            subdir = repo / "src"
            session = self._cr_input(
                subdir,
                "build\nq\n",
                "browse",
                "--build-cmd",
                "./build.sh",
            )

            self.assertEqual(session.returncode, 0, session.stderr)
            self.assertIn("Build: ./build.sh", session.stdout)
            self.assertIn("Build succeeded.", session.stdout)
            self.assertEqual(
                Path((repo / "build.out").read_text(encoding="utf-8").strip()).resolve(),
                repo.resolve(),
            )

    def test_cli_can_emit_clickable_file_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "src" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text("export const value = 'old'\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text("export const value = 'new'\n", encoding="utf-8")

            default_review = self._cr(repo, "review", "--summary")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033]8;;", default_review.stdout)

            linked_review = self._cr(
                repo,
                "review",
                "--summary",
                "--links",
                "always",
            )
            self.assertEqual(linked_review.returncode, 0, linked_review.stderr)
            self.assertIn("\033]8;;file://", linked_review.stdout)
            self.assertIn("#L1", linked_review.stdout)
            self.assertIn("\033]8;;\033\\", linked_review.stdout)

            vscode_browse = self._cr_input(
                repo,
                "q\n",
                "browse",
                "--links",
                "always",
                "--link-scheme",
                "vscode",
            )
            self.assertEqual(vscode_browse.returncode, 0, vscode_browse.stderr)
            self.assertNotIn("\033]8;;", vscode_browse.stdout)
            self.assertIn("Sample.ts", vscode_browse.stdout)

    def test_cli_review_accepts_configurable_hunk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }

  helper() {
    return this.title
  }
}
""",
                encoding="utf-8",
            )

            no_context = self._cr(repo, "review", "--json", "--context", "0")
            self.assertEqual(no_context.returncode, 0, no_context.stderr)
            no_context_hunks = "\n".join(json.loads(no_context.stdout)["files"][0]["hunks"])
            self.assertIn("-    Text('hello')", no_context_hunks)
            self.assertIn("+    Text('hello world')", no_context_hunks)
            self.assertNotIn("  build() {", no_context_hunks)

            wider_context = self._cr(repo, "review", "--json", "--context", "3")
            self.assertEqual(wider_context.returncode, 0, wider_context.stderr)
            wider_hunks = "\n".join(json.loads(wider_context.stdout)["files"][0]["hunks"])
            self.assertIn("  build() {", wider_hunks)

            bad_context = self._cr(repo, "review", "--context", "-1")
            self.assertEqual(bad_context.returncode, 2)
            self.assertIn("context must be >= 0", bad_context.stderr)

    def test_cli_compacts_deep_paths_and_can_color_diff_hunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "a" / "b" / "c" / "d" / "e" / "f" / "Sample.ts"
            sample.parent.mkdir(parents=True)
            sample.write_text(
                "export function sample(): string {\n  return 'old'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "export function sample(): string {\n  return 'new'\n}\n",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--color", "always")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn(".../d/e/f", review.stdout)
            self.assertIn(".../d/e/f/Sample.ts", review.stdout)
            self.assertNotIn("a/b/c/d/e/f/Sample.ts", review.stdout)
            self.assertIn("\033[32m", review.stdout)
            self.assertIn("\033[31m", review.stdout)

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertNotIn("\033[", default_review.stdout)

    def test_cli_review_compares_against_named_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from head')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "head")

            default_review = self._cr(repo, "review")
            self.assertEqual(default_review.returncode, 0, default_review.stderr)
            self.assertIn("No working tree changes.", default_review.stdout)

            review = self._cr(repo, "review", "--base", "HEAD~1", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +1 -1", review.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", review.stdout)
            self.assertIn("Sample.ets:3", review.stdout)

            diff = self._cr(repo, "diff", "--base", "HEAD~1", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +1 -1 modified: build", diff.stdout)

            json_review = self._cr(repo, "review", "--base", "HEAD~1", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 1, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build"])
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

    def test_cli_review_compares_explicit_ref_range_without_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "base")
            self._run(repo, "git", "branch", "-M", "main")
            self._run(repo, "git", "branch", "feature")
            self._run(repo, "git", "checkout", "feature")

            sample.write_text(
                """\
struct SamplePage {
  build() {
    Text('hello from feature')
  }

  helper() {
    return 'feature only'
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "feature")
            self._run(repo, "git", "checkout", "main")

            review = self._cr(repo, "review", "--range", "main..feature", "--no-hunks")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("Review changes:", review.stdout)
            self.assertIn("1 files, +5 -1", review.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", review.stdout)
            self.assertIn(
                "purpose: ArkTS page/component SamplePage with methods build, helper",
                review.stdout,
            )
            self.assertIn("method helper", review.stdout)

            diff = self._cr(repo, "diff", "--range", "main..feature", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Git diff stat:", diff.stdout)
            self.assertIn("Sample.ets +5 -1 modified: build, helper", diff.stdout)

            json_review = self._cr(repo, "review", "--range", "main..feature", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 1})
            self.assertEqual(data["files"][0]["modified_symbols"], ["build", "helper"])
            self.assertIn("build, helper", data["files"][0]["purpose"])

    def test_cli_review_shows_first_changed_line_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello')
  }
}
""",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                """\
struct SamplePage {
  aboutToAppear() {
    this.title = 'Ready'
  }

  build() {
    Text('hello world')
  }
}
""",
                encoding="utf-8",
            )

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("anchor", review.stdout)
            self.assertIn("Sample.ets:7", review.stdout)
            self.assertIn("└─ Sample.ets +1 -1 modified: build line 7", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--summary")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["first_changed_line"], 7)
            self.assertEqual(data["files"][0]["anchor"], "Sample.ets:7")

    def test_cli_includes_untracked_files_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tracked = repo / "README.md"
            new_page = repo / "src" / "pages" / "NewPage.ets"
            tracked.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            new_page.parent.mkdir(parents=True)
            new_page.write_text(
                "struct NewPage {\n  build() {\n    Text('new')\n  }\n}\n",
                encoding="utf-8",
            )

            default_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(default_diff.returncode, 0, default_diff.stderr)
            self.assertIn("No working tree changes.", default_diff.stdout)
            self.assertNotIn("NewPage.ets", default_diff.stdout)

            diff = self._cr(repo, "diff", "--untracked", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("NewPage.ets +5 -0 untracked", diff.stdout)
            self.assertIn("modified: build", diff.stdout)
            self.assertNotIn("No working tree changes.", diff.stdout)

            review = self._cr(repo, "review", "--untracked", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/NewPage.ets", review.stdout)
            self.assertIn("+5 -0 untracked", review.stdout)
            self.assertIn("src/pages/NewPage.ets:1", review.stdout)
            self.assertIn("+struct NewPage", review.stdout)
            self.assertIn("purpose: ArkTS page/component NewPage", review.stdout)
            self.assertIn("method build *", review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"], {"files": 1, "added": 5, "deleted": 0})
            self.assertEqual(data["files"][0]["status"], "untracked")
            self.assertEqual(data["files"][0]["first_changed_line"], 1)
            self.assertEqual(data["files"][0]["anchor"], "src/pages/NewPage.ets:1")
            self.assertTrue(any("+struct NewPage" in line for line in data["files"][0]["hunks"]))

            staged = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertIn("No staged changes.", staged.stdout)
            self.assertNotIn("NewPage.ets", staged.stdout)

            all_changes = self._cr(repo, "review", "--all", "--untracked", "--code")
            self.assertEqual(all_changes.returncode, 0, all_changes.stderr)
            self.assertIn("src/pages/NewPage.ets", all_changes.stdout)

    def test_cli_omits_untracked_binary_and_large_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            binary = repo / "asset.bin"
            large = repo / "large.txt"
            readme.write_text("hello\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "README.md")
            self._run(repo, "git", "commit", "-m", "init")

            binary.write_bytes(b"\x00\xff\x00\xff")
            large.write_text("x" * 210_000, encoding="utf-8")

            review = self._cr(repo, "review", "--untracked")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("asset.bin +? -0 untracked", review.stdout)
            self.assertIn("large.txt +? -0 untracked", review.stdout)
            self.assertIn("asset.bin: binary or non-UTF-8 file; content omitted", review.stdout)
            self.assertIn("large.txt: file is too large for inline diff", review.stdout)
            self.assertNotIn("+" + ("x" * 200), review.stdout)

            json_review = self._cr(repo, "review", "--json", "--untracked")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            files = {item["path"]: item for item in data["files"]}
            self.assertIsNone(files["asset.bin"]["added"])
            self.assertIsNone(files["large.txt"]["added"])
            self.assertIn("content omitted", "\n".join(files["asset.bin"]["hunks"]))
            self.assertIn("too large for inline diff", "\n".join(files["large.txt"]["hunks"]))

    def test_cli_flags_lockfile_config_and_generated_risks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            lockfile = repo / "package-lock.json"
            config = repo / "tsconfig.json"
            generated = repo / "src" / "generated" / "client.ts"
            generated.parent.mkdir(parents=True)
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v1'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            config.write_text('{"compilerOptions": {"strict": true}}\n', encoding="utf-8")
            generated.write_text("export function client(): string {\n  return 'v2'\n}\n", encoding="utf-8")

            review = self._cr(repo, "review", "--summary")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("risk", review.stdout)
            self.assertIn("package-lock.json", review.stdout)
            self.assertIn("lockfile", review.stdout)
            self.assertIn("tsconfig.json", review.stdout)
            self.assertIn("config", review.stdout)
            self.assertIn("src/generated/client.ts", review.stdout)
            self.assertIn("generated", review.stdout)
            self.assertIn("risk: lockfile", review.stdout)
            self.assertIn("risk: config", review.stdout)
            self.assertIn("risk: generated", review.stdout)

            full_review = self._cr(repo, "review", "package-lock.json")
            self.assertEqual(full_review.returncode, 0, full_review.stderr)
            self.assertIn("  risk: lockfile", full_review.stdout)

            json_review = self._cr(repo, "review", "--json")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            risks = {item["path"]: item["risk_hints"] for item in data["files"]}
            self.assertEqual(risks["package-lock.json"], ["lockfile"])
            self.assertEqual(risks["tsconfig.json"], ["config"])
            self.assertEqual(risks["src/generated/client.ts"], ["generated"])

    def test_cli_review_sorts_large_reviews_by_risk_or_churn(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            risk_sorted = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(risk_sorted.returncode, 0, risk_sorted.stderr)
            self.assertLess(
                risk_sorted.stdout.index("package-lock.json"),
                risk_sorted.stdout.index("README.md"),
            )

            churn_sorted = self._cr(repo, "review", "--summary", "--sort", "churn")
            self.assertEqual(churn_sorted.returncode, 0, churn_sorted.stderr)
            self.assertLess(
                churn_sorted.stdout.index("src/app.ts"),
                churn_sorted.stdout.index("package-lock.json"),
            )

            json_review = self._cr(repo, "review", "--json", "--summary", "--sort", "risk")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["files"][0]["path"], "package-lock.json")

    def test_cli_review_picks_one_file_by_summary_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            lockfile = repo / "package-lock.json"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello world\n", encoding="utf-8")
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")
            app.write_text(
                """\
export function app(): string {
  const value = 'v2'
  const suffix = 'large'
  return `${value}-${suffix}`
}
""",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--sort", "risk")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("idx", summary.stdout)
            self.assertLess(
                summary.stdout.index("1  package-lock.json"),
                summary.stdout.index("2  src/app.ts"),
            )

            picked = self._cr(repo, "review", "--sort", "risk", "--pick", "2")
            self.assertEqual(picked.returncode, 0, picked.stderr)
            self.assertIn("1 files", picked.stdout)
            self.assertIn("src/app.ts", picked.stdout)
            self.assertIn("+  const value = 'v2'", picked.stdout)
            self.assertNotIn("package-lock.json", picked.stdout)
            self.assertNotIn("README.md", picked.stdout)

            bad_pick = self._cr(repo, "review", "--pick", "9")
            self.assertEqual(bad_pick.returncode, 2)
            self.assertIn("--pick must be between 1 and 3", bad_pick.stderr)

    def test_cli_review_tracks_seen_files_and_filters_remaining(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            app = repo / "src" / "app.ts"
            app.parent.mkdir(parents=True)
            readme.write_text("hello\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v1'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")
            app.write_text(
                "export function app(): string {\n  return 'v2'\n}\n",
                encoding="utf-8",
            )

            summary = self._cr(repo, "review", "--summary", "--seen", "README.md")
            self.assertEqual(summary.returncode, 0, summary.stderr)
            self.assertIn("seen", summary.stdout)
            self.assertIn("README.md", summary.stdout)
            self.assertIn("yes", summary.stdout)
            self.assertIn("src/app.ts", summary.stdout)
            self.assertIn("no", summary.stdout)

            remaining = self._cr(
                repo,
                "review",
                "--summary",
                "--seen",
                "README.md",
                "--remaining",
            )
            self.assertEqual(remaining.returncode, 0, remaining.stderr)
            self.assertIn("src/app.ts", remaining.stdout)
            self.assertNotIn("README.md", remaining.stdout)

            no_remaining = self._cr(
                repo,
                "review",
                "--seen",
                "README.md,src/app.ts",
                "--remaining",
            )
            self.assertEqual(no_remaining.returncode, 0, no_remaining.stderr)
            self.assertIn("No remaining changes.", no_remaining.stdout)

            json_review = self._cr(repo, "review", "--json", "--seen", "README.md")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            seen_by_path = {item["path"]: item["seen"] for item in data["files"]}
            self.assertTrue(seen_by_path["README.md"])
            self.assertFalse(seen_by_path["src/app.ts"])

            prompt = self._cr(repo, "review", "--prompt", "--seen", "README.md")
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("state: seen", prompt.stdout)

    def test_cli_review_emits_prompt_ready_markdown_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            lockfile = repo / "package-lock.json"
            page.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 1}\n', encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello prompt')\n  }\n}\n",
                encoding="utf-8",
            )
            lockfile.write_text('{"lockfileVersion": 2}\n', encoding="utf-8")

            prompt = self._cr(
                repo,
                "review",
                "--prompt",
                "--sort",
                "risk",
                "--context",
                "0",
            )
            self.assertEqual(prompt.returncode, 0, prompt.stderr)
            self.assertIn("# Code Review Handoff", prompt.stdout)
            self.assertIn("Please review these changes.", prompt.stdout)
            self.assertIn("## Summary", prompt.stdout)
            self.assertIn("- Files: 2", prompt.stdout)
            self.assertIn("## Files", prompt.stdout)
            self.assertLess(
                prompt.stdout.index("package-lock.json"),
                prompt.stdout.index("src/pages/Sample.ets"),
            )
            self.assertIn("risk: lockfile", prompt.stdout)
            self.assertIn("purpose: ArkTS page/component SamplePage", prompt.stdout)
            self.assertIn("focus: build", prompt.stdout)
            self.assertIn("```diff", prompt.stdout)
            self.assertIn("+    Text('hello prompt')", prompt.stdout)
            self.assertNotIn("Review changes:", prompt.stdout)
            self.assertNotIn('"summary"', prompt.stdout)

    def test_cli_filters_to_code_files_and_path_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            page = repo / "src" / "pages" / "Sample.ets"
            helper = repo / "src" / "utils" / "helper.ts"
            readme = repo / "README.md"
            page.parent.mkdir(parents=True)
            helper.parent.mkdir(parents=True)
            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            page.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello page')\n  }\n}\n",
                encoding="utf-8",
            )
            helper.write_text(
                "export function helper(): string {\n  return 'b'\n}\n",
                encoding="utf-8",
            )
            readme.write_text("hello docs\n", encoding="utf-8")

            review = self._cr(repo, "review", "--code", "src/pages")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/pages/Sample.ets +1 -1", review.stdout)
            self.assertNotIn("src/utils/helper.ts", review.stdout)
            self.assertNotIn("README.md", review.stdout)

            diff = self._cr(repo, "diff", "--code", "src/pages")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("src/pages", diff.stdout)
            self.assertNotIn("src/utils", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

            code_diff = self._cr(repo, "diff", "--code")
            self.assertEqual(code_diff.returncode, 0, code_diff.stderr)
            self.assertIn("src/pages/Sample.ets", code_diff.stdout)
            self.assertIn("src/utils/helper.ts", code_diff.stdout)
            self.assertNotIn("README.md", code_diff.stdout)

    def test_code_filter_does_not_show_doc_only_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            readme = repo / "README.md"
            readme.write_text("hello\n", encoding="utf-8")

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            readme.write_text("hello docs\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("No working tree changes.", diff.stdout)
            self.assertNotIn("README.md", diff.stdout)

    def test_cli_marks_deleted_code_files_without_fake_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "src" / "utils" / "helper.ts"
            helper.parent.mkdir(parents=True)
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )

            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("helper.ts +0 -3 deleted", diff.stdout)
            self.assertNotIn("modified: unknown", diff.stdout)

            review = self._cr(repo, "review", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("src/utils/helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("changes:", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_can_review_staged_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            sample = repo / "Sample.ets"
            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "Sample.ets")
            self._run(repo, "git", "commit", "-m", "init")

            sample.write_text(
                "struct SamplePage {\n  build() {\n    Text('hello staged')\n  }\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "add", "Sample.ets")

            unstaged = self._cr(repo, "diff")
            self.assertEqual(unstaged.returncode, 0, unstaged.stderr)
            self.assertIn("No working tree changes.", unstaged.stdout)

            staged_diff = self._cr(repo, "diff", "--staged")
            self.assertEqual(staged_diff.returncode, 0, staged_diff.stderr)
            self.assertIn("Sample.ets +1 -1 modified: build", staged_diff.stdout)

            staged_review = self._cr(repo, "review", "--staged")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn("Sample.ets +1 -1", staged_review.stdout)
            self.assertIn("+    Text('hello staged')", staged_review.stdout)
            self.assertIn("modified: build", staged_review.stdout)

    def test_cli_can_review_staged_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            helper = repo / "helper.ts"
            helper.write_text(
                "export function helper(): string {\n  return 'a'\n}\n",
                encoding="utf-8",
            )
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", "helper.ts")
            self._run(repo, "git", "commit", "-m", "init")

            helper.unlink()
            self._run(repo, "git", "add", "helper.ts")

            review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("helper.ts +0 -3 deleted", review.stdout)
            self.assertIn("-export function helper()", review.stdout)
            self.assertNotIn("purpose:", review.stdout)

    def test_cli_notes_when_the_other_git_side_has_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'b'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'b'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("Note: staged changes also exist; use --staged to review them.", diff.stdout)
            self.assertIn("unstaged.ts", diff.stdout)
            self.assertNotIn("  └─ staged.ts +1 -1", diff.stdout)

            staged_review = self._cr(repo, "review", "--staged", "--code")
            self.assertEqual(staged_review.returncode, 0, staged_review.stderr)
            self.assertIn(
                "Note: unstaged changes also exist; omit --staged to review them.",
                staged_review.stdout,
            )
            self.assertIn("staged.ts", staged_review.stdout)
            self.assertNotIn("  └─ unstaged.ts +1 -1", staged_review.stdout)

            json_review = self._cr(repo, "review", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["other_changes"], {"staged": 1, "unstaged": 0})

    def test_cli_can_review_all_staged_and_unstaged_changes_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            staged = repo / "staged.ts"
            unstaged = repo / "unstaged.ts"
            staged.write_text("export function staged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            unstaged.write_text("export function unstaged(): string {\n  return 'a'\n}\n", encoding="utf-8")
            self._run(repo, "git", "init")
            self._run(repo, "git", "config", "user.email", "cr@example.invalid")
            self._run(repo, "git", "config", "user.name", "cr")
            self._run(repo, "git", "add", ".")
            self._run(repo, "git", "commit", "-m", "init")

            staged.write_text("export function staged(): string {\n  return 'staged'\n}\n", encoding="utf-8")
            self._run(repo, "git", "add", "staged.ts")
            unstaged.write_text("export function unstaged(): string {\n  return 'unstaged'\n}\n", encoding="utf-8")

            diff = self._cr(repo, "diff", "--all", "--code")
            self.assertEqual(diff.returncode, 0, diff.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", diff.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", diff.stdout)
            self.assertNotIn("also exist", diff.stdout)

            review = self._cr(repo, "review", "--all", "--code")
            self.assertEqual(review.returncode, 0, review.stderr)
            self.assertIn("staged.ts +1 -1 modified: staged", review.stdout)
            self.assertIn("unstaged.ts +1 -1 modified: unstaged", review.stdout)
            self.assertIn("+  return 'staged'", review.stdout)
            self.assertIn("+  return 'unstaged'", review.stdout)
            self.assertNotIn("also exist", review.stdout)

            json_review = self._cr(repo, "review", "--all", "--json", "--code")
            self.assertEqual(json_review.returncode, 0, json_review.stderr)
            data = json.loads(json_review.stdout)
            self.assertEqual(data["summary"]["files"], 2)
            self.assertEqual(data["other_changes"], {"staged": 0, "unstaged": 0})

            bad_scope = self._cr(repo, "review", "--all", "--staged")
            self.assertEqual(bad_scope.returncode, 2)
            self.assertIn("not allowed with argument", bad_scope.stderr)

    def _cr(self, cwd, *args):
        return self._cr_input(cwd, None, *args)

    def _cr_input(self, cwd, input_text, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "cr", *args],
            cwd=cwd,
            text=True,
            input=input_text,
            capture_output=True,
            env=env,
            check=False,
        )

    def _run(self, cwd, *args):
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
