import unittest

from cr.outline import parse_outline
from cr.purpose import describe_file


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
        text = describe_file("src/pages/Home.ets", parse_outline(SAMPLE_PAGE))

        self.assertEqual(
            text,
            "ArkTS page/component HomePage with methods aboutToAppear, build",
        )

    def test_describes_function_module(self):
        text = describe_file("src/utils/user.ts", parse_outline(SAMPLE_UTILS))

        self.assertEqual(
            text,
            "TypeScript utility module with functions formatName, parseAge",
        )

    def test_falls_back_to_path_when_no_symbols_are_found(self):
        text = describe_file("README.md", [])

        self.assertEqual(text, "Markdown document README.md")


if __name__ == "__main__":
    unittest.main()
