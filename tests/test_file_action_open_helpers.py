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


class FileActionOpenHelperTests(unittest.TestCase):
    def test_open_command_uses_configured_template(self):
        # Behavior: 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.file_actions import open_command

        command = open_command(
            Path("/tmp/space dir/Sample.ts"),
            12,
            "code -g {fileline}",
        )

        self.assertEqual(command, ["code", "-g", "/tmp/space dir/Sample.ts:12"])
    def test_open_command_source_reports_cli_env_platform_and_missing(self):
        # Behavior: 当用户在file action遇到缺失状态时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
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
        # Behavior: 当用户在file action遇到失败反馈时，系统应给出正确反馈或保持安全状态 [Requirement: TODO]
        from cr.ui.file_actions import open_path

        with patch(
            "cr.ui.file_actions.subprocess.Popen",
            side_effect=OSError("missing open"),
        ):
            message = open_path(Path("/tmp/Sample.ts"), 3, "missing-open {file}")

        self.assertIn("Open failed (cli missing-open /tmp/Sample.ts)", message)
        self.assertIn("missing open", message)
    def test_open_command_prefers_gui_editor_with_line(self):
        # Behavior: 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return f"/usr/local/bin/{name}" if name == "code" else None

        with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
            command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["code", "-g", "/tmp/Sample.ts:7"])
    def test_open_command_falls_back_to_macos_open(self):
        # Behavior: 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        from cr.ui.file_actions import open_command

        def fake_which(name):
            return "/usr/bin/open" if name == "open" else None

        with patch("cr.ui.file_actions.platform.system", return_value="Darwin"):
            with patch("cr.ui.file_actions.shutil.which", side_effect=fake_which):
                command = open_command(Path("/tmp/Sample.ts"), 7)

        self.assertEqual(command, ["open", "/tmp/Sample.ts"])

if __name__ == "__main__":
    unittest.main()
