import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cr.ui.browser import BrowserCommandExecutor, BrowserFrame, BrowserState
from cr.ui.terminal import TerminalStyle
from cr.vcs.git import FileChange


def argparse_namespace(**kwargs):
    class Namespace:
        pass

    namespace = Namespace()
    for key, value in kwargs.items():
        setattr(namespace, key, value)
    return namespace


class FileActionCommandTests(unittest.TestCase):
    def test_browser_command_executor_copies_selected_path(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(copy_cmd="copy-tool"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("copy path"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        copy.assert_called_once_with("src/Sample.ts", "copy-tool")
        self.assertIn("Copied src/Sample.ts", output.getvalue())

    def test_browser_command_executor_copies_selected_anchor(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        copy.assert_called_once_with("src/Sample.ts:12", None)
        self.assertIn("Copied src/Sample.ts:12", output.getvalue())

    def test_browser_command_executor_anchor_falls_back_to_path_without_line(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=False,
            all_changes=False,
            base=None,
            ref_range=None,
            copy_cmd=None,
        )
        state = BrowserState([FileChange("asset.bin", None, None)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )

        with patch("cr.ui.browser.git.first_changed_line", return_value=None):
            with patch("cr.ui.browser.file_actions.copy_text", return_value=None) as copy:
                with redirect_stdout(StringIO()):
                    result = executor.execute(parse_browser_command("copy anchor"))

        self.assertTrue(result.handled)
        copy.assert_called_once_with("asset.bin", None)

    def test_browser_command_executor_opens_selected_file(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
            open_cmd="code -g {fileline}",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.first_changed_line", return_value=12) as first_line:
            with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
                with patch("cr.ui.browser.file_actions.open_path", return_value=None) as open_path:
                    with redirect_stdout(output):
                        result = executor.execute(parse_browser_command("open"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        first_line.assert_called_once_with(
            "src/Sample.ts",
            staged=True,
            all_changes=False,
            base=None,
            ref_range=None,
        )
        open_path.assert_called_once_with(repo_file, 12, "code -g {fileline}")
        self.assertIn("Opened src/Sample.ts:12", output.getvalue())

    def test_browser_command_executor_reveals_selected_file(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(reveal_cmd="reveal-tool --file {file}"),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()
        repo_file = Path("/tmp/repo/src/Sample.ts")

        with patch("cr.ui.browser.git.repo_path", return_value=repo_file):
            with patch("cr.ui.browser.file_actions.reveal_path", return_value=None) as reveal:
                with redirect_stdout(output):
                    result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        reveal.assert_called_once_with(repo_file, "reveal-tool --file {file}")
        self.assertIn("Revealed src/Sample.ts", output.getvalue())

    def test_browser_command_executor_shows_file_action_diagnostics(self):
        from cr.ui.browser import parse_browser_command

        args = argparse_namespace(
            open_cmd="code -g {fileline}",
            copy_cmd="copy-tool {text}",
            reveal_cmd="reveal-tool {file}",
        )
        state = BrowserState([FileChange("src/Sample.ts", 1, 1)])
        executor = BrowserCommandExecutor(
            state,
            args,
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.git.repo_root", return_value=Path("/tmp/repo")):
            with redirect_stdout(output):
                result = executor.execute(parse_browser_command("file actions"))

        text = output.getvalue()
        self.assertTrue(result.handled)
        self.assertFalse(result.needs_redraw)
        self.assertIsNone(state.task)
        self.assertIn("File actions:", text)
        self.assertIn("open: cli code -g", text)
        self.assertIn("copy: cli copy-tool", text)
        self.assertIn("reveal: cli reveal-tool", text)

    def test_browser_file_actions_report_when_no_changed_file_is_available(self):
        from cr.ui.browser import parse_browser_command

        state = BrowserState([])
        executor = BrowserCommandExecutor(
            state,
            argparse_namespace(),
            TerminalStyle(),
            BrowserFrame(),
            raw_keys=False,
        )
        output = StringIO()

        with patch("cr.ui.browser.file_actions.copy_text") as copy:
            with patch("cr.ui.browser.file_actions.reveal_path") as reveal:
                with redirect_stdout(output):
                    copy_result = executor.execute(parse_browser_command("copy path"))
                    reveal_result = executor.execute(parse_browser_command("reveal"))

        self.assertTrue(copy_result.handled)
        self.assertTrue(reveal_result.handled)
        copy.assert_not_called()
        reveal.assert_not_called()
        self.assertIn("No changed file to copy.", output.getvalue())
        self.assertIn("No changed file to reveal.", output.getvalue())

    def test_open_command_uses_configured_template(self):
        from cr.ui.file_actions import open_command

        command = open_command(
            Path("/tmp/space dir/Sample.ts"),
            12,
            "code -g {fileline}",
        )

        self.assertEqual(command, ["code", "-g", "/tmp/space dir/Sample.ts:12"])

    def test_open_command_source_reports_cli_env_platform_and_missing(self):
        from cr.ui.file_actions import open_command_source

        with patch.dict(os.environ, {"CR_OPEN_CMD": "env-open {fileline}"}, clear=True):
            env_source = open_command_source(Path("/tmp/Sample.ts"), 7)
            cli_source = open_command_source(
                Path("/tmp/Sample.ts"),
                7,
                "cli-open {file}",
            )
        with patch.dict(os.environ, {}, clear=True):
            with patch("cr.ui.file_actions.shutil.which", return_value=None):
                missing_source = open_command_source(Path("/tmp/Sample.ts"), 7)
            with patch("cr.ui.file_actions.shutil.which", return_value="/usr/local/bin/code"):
                platform_source = open_command_source(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(env_source.source, "env")
        self.assertEqual(env_source.command, ["env-open", "/tmp/Sample.ts:7"])
        self.assertEqual(cli_source.source, "cli")
        self.assertEqual(cli_source.command, ["cli-open", "/tmp/Sample.ts"])
        self.assertEqual(platform_source.source, "platform")
        self.assertEqual(platform_source.command, ["code", "-g", "/tmp/Sample.ts:7"])
        self.assertEqual(missing_source.source, "missing")
        self.assertIsNone(missing_source.command)

    def test_file_action_helpers_include_source_in_open_failures(self):
        from cr.ui.file_actions import open_path

        with patch(
            "cr.ui.file_actions.subprocess.Popen",
            side_effect=OSError("missing open"),
        ):
            message = open_path(Path("/tmp/Sample.ts"), 3, "missing-open {file}")

        self.assertIn("Open failed (cli missing-open /tmp/Sample.ts)", message)
        self.assertIn("missing open", message)

    def test_open_command_prefers_gui_editor_with_line(self):
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return f"/usr/local/bin/{name}" if name == "code" else None

        with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
            command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["code", "-g", "/tmp/Sample.ts:7"])

    def test_open_command_falls_back_to_macos_open(self):
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return "/usr/bin/open" if name == "open" else None

        with patch("cr.ui.file_actions.platform.system", return_value="Darwin"):
            with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
                command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["open", "/tmp/Sample.ts"])

    def test_browse_parser_accepts_file_action_command_configuration(self):
        from cr.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(
            [
                "browse",
                "--copy-cmd",
                "copy-tool",
                "--reveal-cmd",
                "reveal-tool --file {file}",
            ]
        )

        self.assertEqual(args.copy_cmd, "copy-tool")
        self.assertEqual(args.reveal_cmd, "reveal-tool --file {file}")

    def test_file_action_helpers_discover_macos_clipboard_and_reveal_commands(self):
        from cr.ui.file_actions import clipboard_command, reveal_command

        def fake_which(name):
            if name in {"pbcopy", "open"}:
                return f"/usr/bin/{name}"
            return None

        with patch("cr.ui.file_actions.platform.system", return_value="Darwin"):
            with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
                self.assertEqual(clipboard_command(), ["pbcopy"])
                self.assertEqual(
                    reveal_command(Path("/tmp/Sample.ts")),
                    ["open", "-R", "/tmp/Sample.ts"],
                )

    def test_file_action_helpers_report_missing_platform_commands(self):
        from cr.ui.file_actions import copy_text, open_path, reveal_path

        with patch("cr.ui.file_actions.open_command_source") as source:
            source.return_value.command = None
            self.assertEqual(
                open_path(Path("/tmp/Sample.ts"), 7),
                (
                    "No editor opener found (missing). Set --open-cmd or "
                    "CR_OPEN_CMD, for example: --open-cmd 'code -g {fileline}'"
                ),
            )
        with patch("cr.ui.file_actions.clipboard_command", return_value=None):
            self.assertEqual(
                copy_text("src/Sample.ts"),
                "No clipboard command found (missing).",
            )
        with patch("cr.ui.file_actions.reveal_command", return_value=None):
            self.assertEqual(
                reveal_path(Path("/tmp/Sample.ts")),
                "No file browser command found (missing).",
            )

    def test_file_action_helpers_use_configured_copy_command(self):
        from cr.ui.file_actions import copy_text

        with patch("cr.ui.file_actions.subprocess.run") as run:
            result = copy_text("src/Sample.ts", "copy-tool --label {text}")

        self.assertIsNone(result)
        run.assert_called_once_with(
            ["copy-tool", "--label", "src/Sample.ts"],
            input="src/Sample.ts",
            text=True,
            check=True,
        )

    def test_file_action_helpers_include_source_in_failures(self):
        from cr.ui.file_actions import copy_text, reveal_path

        with patch(
            "cr.ui.file_actions.subprocess.run",
            side_effect=OSError("missing copy"),
        ):
            copy_result = copy_text("src/Sample.ts", "copy-tool {text}")
        with patch(
            "cr.ui.file_actions.subprocess.Popen",
            side_effect=OSError("missing reveal"),
        ):
            reveal_result = reveal_path(
                Path("/tmp/repo/src/Sample.ts"),
                "reveal-tool {file}",
            )

        self.assertIn("Copy failed (cli copy-tool src/Sample.ts)", copy_result)
        self.assertIn("missing copy", copy_result)
        self.assertIn(
            "Reveal failed (cli reveal-tool /tmp/repo/src/Sample.ts)",
            reveal_result,
        )
        self.assertIn("missing reveal", reveal_result)

    def test_file_action_helpers_use_configured_reveal_command(self):
        from cr.ui.file_actions import reveal_path

        with patch("cr.ui.file_actions.subprocess.Popen") as popen:
            result = reveal_path(
                Path("/tmp/repo/src/Sample.ts"),
                "reveal-tool --file {file} --dir {dir}",
            )

        self.assertIsNone(result)
        popen.assert_called_once_with(
            [
                "reveal-tool",
                "--file",
                "/tmp/repo/src/Sample.ts",
                "--dir",
                "/tmp/repo/src",
            ]
        )

    def test_file_action_helpers_use_environment_configuration(self):
        from cr.ui.file_actions import (
            configured_copy_command,
            configured_reveal_command,
            copy_command_source,
            open_command,
            open_command_source,
            reveal_command_source,
        )

        with patch.dict(
            os.environ,
            {
                "CR_OPEN_CMD": "env-open {fileline}",
                "CR_COPY_CMD": "env-copy {text}",
                "CR_REVEAL_CMD": "env-reveal {file}",
            },
            clear=True,
        ):
            self.assertEqual(
                open_command(Path("/tmp/repo/src/Sample.ts"), 7),
                ["env-open", "/tmp/repo/src/Sample.ts:7"],
            )
            self.assertEqual(
                open_command(
                    Path("/tmp/repo/src/Sample.ts"),
                    7,
                    "cli-open {file}",
                ),
                ["cli-open", "/tmp/repo/src/Sample.ts"],
            )
            self.assertEqual(
                configured_copy_command("src/Sample.ts"),
                ["env-copy", "src/Sample.ts"],
            )
            self.assertEqual(
                configured_copy_command("src/Sample.ts", "cli-copy {text}"),
                ["cli-copy", "src/Sample.ts"],
            )
            self.assertEqual(
                configured_reveal_command(Path("/tmp/repo/src/Sample.ts")),
                ["env-reveal", "/tmp/repo/src/Sample.ts"],
            )
            self.assertEqual(
                configured_reveal_command(
                    Path("/tmp/repo/src/Sample.ts"),
                    "cli-reveal {dir}",
                ),
                ["cli-reveal", "/tmp/repo/src"],
            )
            copy_env = copy_command_source("src/Sample.ts")
            copy_cli = copy_command_source("src/Sample.ts", "cli-copy {text}")
            open_env = open_command_source(Path("/tmp/repo/src/Sample.ts"), 7)
            open_cli = open_command_source(
                Path("/tmp/repo/src/Sample.ts"),
                7,
                "cli-open {file}",
            )
            reveal_env = reveal_command_source(Path("/tmp/repo/src/Sample.ts"))
            reveal_cli = reveal_command_source(
                Path("/tmp/repo/src/Sample.ts"),
                "cli-reveal {dir}",
            )
        with patch.dict(os.environ, {}, clear=True):
            with patch("cr.ui.file_actions.clipboard_command", return_value=["pbcopy"]):
                copy_platform = copy_command_source("src/Sample.ts")
            with patch(
                "cr.ui.file_actions.reveal_command",
                return_value=["open", "-R", "/tmp/repo/src/Sample.ts"],
            ):
                reveal_platform = reveal_command_source(
                    Path("/tmp/repo/src/Sample.ts")
                )

        self.assertEqual(open_env.source, "env")
        self.assertEqual(open_env.command, ["env-open", "/tmp/repo/src/Sample.ts:7"])
        self.assertEqual(open_cli.source, "cli")
        self.assertEqual(open_cli.command, ["cli-open", "/tmp/repo/src/Sample.ts"])
        self.assertEqual(copy_env.source, "env")
        self.assertEqual(copy_env.command, ["env-copy", "src/Sample.ts"])
        self.assertEqual(copy_cli.source, "cli")
        self.assertEqual(copy_cli.command, ["cli-copy", "src/Sample.ts"])
        self.assertEqual(copy_platform.source, "platform")
        self.assertEqual(copy_platform.command, ["pbcopy"])
        self.assertEqual(reveal_env.source, "env")
        self.assertEqual(reveal_env.command, ["env-reveal", "/tmp/repo/src/Sample.ts"])
        self.assertEqual(reveal_cli.source, "cli")
        self.assertEqual(reveal_cli.command, ["cli-reveal", "/tmp/repo/src"])
        self.assertEqual(reveal_platform.source, "platform")
        self.assertEqual(
            reveal_platform.command,
            ["open", "-R", "/tmp/repo/src/Sample.ts"],
        )
