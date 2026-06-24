import unittest

from cr.git import FileChange
from cr.tree import format_change_summary, render_change_tree


class ChangeTreeTests(unittest.TestCase):
    def test_renders_changed_files_as_directory_tree(self):
        changes = [
            FileChange("src/pages/Home.ets", 5, 2),
            FileChange("src/components/Button.ts", 1, 0),
            FileChange("README.md", 2, 1),
        ]

        text = render_change_tree(changes)

        self.assertIn("├─ README.md +2 -1", text)
        self.assertIn("└─ src", text)
        self.assertIn("   ├─ components", text)
        self.assertIn("   │  └─ Button.ts +1 -0", text)
        self.assertIn("   └─ pages", text)
        self.assertIn("      └─ Home.ets +5 -2", text)

    def test_compacts_deep_tree_to_nearby_changed_directory(self):
        changes = [
            FileChange(
                "business_modules/CreativeTools/Camp/camera_kmp_impl/src/"
                "ohosArm64Main/kotlin/com/ss/kmp/ugc/aweme/edit/main/"
                "sticker/hashtag/gesture/HashtagDragBoundaryHelper.ohos.kt",
                2,
                11,
            )
        ]

        text = render_change_tree(changes)

        self.assertIn("└─ .../sticker/hashtag/gesture", text)
        self.assertIn("   └─ HashtagDragBoundaryHelper.ohos.kt +2 -11", text)
        self.assertNotIn("business_modules", text)

    def test_uses_common_directory_for_multiple_deep_changes(self):
        changes = [
            FileChange("a/b/c/d/e/src/pages/Home.ets", 5, 2),
            FileChange("a/b/c/d/e/src/components/Button.ts", 1, 0),
        ]

        text = render_change_tree(changes)

        self.assertIn("└─ .../d/e/src", text)
        self.assertIn("   ├─ components", text)
        self.assertIn("   └─ pages", text)
        self.assertNotIn("└─ a", text)

    def test_formats_renamed_files_for_humans(self):
        change = FileChange("src/newName.ts", 0, 0, status="renamed", old_path="src/oldName.ts")

        self.assertEqual(
            format_change_summary(change),
            "+0 -0 renamed from src/oldName.ts",
        )


if __name__ == "__main__":
    unittest.main()
