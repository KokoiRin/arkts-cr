from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_setup_py_exposes_cr_console_script(self):
        # Behavior: 当用户在产品行为中验证packaging、setup、py、exposes时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        text = (ROOT / "setup.py").read_text(encoding="utf-8")

        self.assertIn('python_requires=">=3.9"', text)
        self.assertIn('"cr=cr.cli:main"', text)

    def test_project_avoids_isolated_build_for_offline_editable_install(self):
        # Behavior: 当用户在task output中验证packaging、project、avoids、isolated时，系统应完成对应行为并保持页面状态正确 [Requirement: TODO]
        self.assertFalse((ROOT / "pyproject.toml").exists())


if __name__ == "__main__":
    unittest.main()
