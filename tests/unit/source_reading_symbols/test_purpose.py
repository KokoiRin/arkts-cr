import unittest

from cr.source.outline import parse_outline
from cr.source.purpose import describe_file


SAMPLE_PAGE = """\
struct HomePage {
  aboutToAppear() {
  }

  build() {
  }
}
"""


SAMPLE_UTILS = """\
export function formatName(name: string): string {
  return name.trim()
}

export function parseAge(raw: string): number {
  return Number(raw)
}
"""


class PurposeTests(unittest.TestCase):
    def test_describes_arkts_page_component_from_path_and_symbols(self):
        # Behavior: 当用户在Source File中执行操作「describes arkts page component from 路径 and 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        text = describe_file("src/pages/Home.ets", parse_outline(SAMPLE_PAGE))

        self.assertEqual(
            text,
            "ArkTS page/component HomePage with methods aboutToAppear, build",
        )

    def test_describes_function_module(self):
        # Behavior: 当用户在Source File中执行操作「describes function module」时，系统应完成对应产品行为，并保持页面状态正确 [Requirement: TODO]
        text = describe_file("src/utils/user.ts", parse_outline(SAMPLE_UTILS))

        self.assertEqual(
            text,
            "TypeScript utility module with functions formatName, parseAge",
        )

    def test_falls_back_to_path_when_no_symbols_are_found(self):
        # Behavior: 当用户在Source File中执行操作「回退 返回 to 路径 when 无 符号 are found」时，系统应进入正确页面或位置，并维护可预期的返回关系 [Requirement: TODO]
        text = describe_file("README.md", [])

        self.assertEqual(text, "Markdown document README.md")


if __name__ == "__main__":
    unittest.main()
