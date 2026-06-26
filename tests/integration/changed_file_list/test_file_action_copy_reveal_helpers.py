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


class FileActionCopyRevealHelperTests(unittest.TestCase):
    def test_file_action_helpers_discover_macos_clipboard_and_reveal_commands(self):
        # Behavior: 当用户在file action中验证action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action遇到缺失状态时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file action中复制action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action遇到失败反馈时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file action中验证action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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
        # Behavior: 当用户在file action中验证配置时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
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

if __name__ == "__main__":
    unittest.main()
