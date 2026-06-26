from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]


class PackagingTests(unittest.TestCase):
    def test_setup_py_exposes_cr_console_script(self):
        # Behavior: 当用户在Task Panel / Task Output中执行操作「setup py exposes cr console script」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        text = (ROOT / "setup.py").read_text(encoding="utf-8")

        self.assertIn('python_requires=">=3.9"', text)
        self.assertIn('"cr=cr.cli:main"', text)

    def test_project_avoids_isolated_build_for_offline_editable_install(self):
        # Behavior: 当用户在Task Panel / Task Output中运行任务「project avoids isolated build for offline editable install」时，系统应正确更新任务状态、输出、问题和历史记录 [Requirement: TODO]
        self.assertFalse((ROOT / "pyproject.toml").exists())


if __name__ == "__main__":
    unittest.main()
