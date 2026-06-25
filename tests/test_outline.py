import unittest

from cr.source.outline import modified_symbols, parse_outline, render_outline


SAMPLE = """\
struct Page {
  aboutToAppear() {
    this.load()
  }

  private helper(value: string): string {
    return value.trim()
  }

  build() {
    Column() {
      Text(this.helper('x'))
    }
  }
}

export function formatName(name: string): string {
  return name.trim()
}

interface Store {
  load(id: string): Promise<string>;
}
"""


class OutlineTests(unittest.TestCase):
    def test_parses_arkts_structure(self):
        symbols = parse_outline(SAMPLE)

        self.assertEqual(symbols[0].kind, "struct")
        self.assertEqual(symbols[0].name, "Page")
        self.assertEqual([child.name for child in symbols[0].children], [
            "aboutToAppear",
            "helper",
            "build",
        ])
        self.assertEqual(symbols[1].kind, "function")
        self.assertEqual(symbols[1].name, "formatName")
        self.assertEqual(symbols[2].kind, "interface")
        self.assertEqual(symbols[2].children[0].name, "load")

    def test_renders_tree(self):
        text = render_outline("Sample.ets", parse_outline(SAMPLE), {"build"})

        self.assertIn("struct Page", text)
        self.assertIn("method build *", text)
        self.assertIn("function formatName", text)

    def test_maps_changed_lines_to_methods(self):
        symbols = parse_outline(SAMPLE)

        self.assertEqual(modified_symbols(symbols, {11}), ["build"])
        self.assertEqual(modified_symbols(symbols, {17}), ["formatName"])
        self.assertEqual(modified_symbols(symbols, set()), ["unknown"])

    def test_parses_override_and_accessor_members(self):
        symbols = parse_outline(
            "\n".join(
                [
                    "class FeedCard extends BaseCard {",
                    "  override aboutToAppear() {",
                    "    this.load()",
                    "  }",
                    "  get title(): string {",
                    "    return this.model.title",
                    "  }",
                    "  set title(value: string) {",
                    "    this.model.title = value",
                    "  }",
                    "}",
                ]
            )
        )

        self.assertEqual(
            [child.name for child in symbols[0].children],
            ["aboutToAppear", "title", "title"],
        )
        self.assertEqual(modified_symbols(symbols, {3}), ["aboutToAppear"])
        self.assertEqual(modified_symbols(symbols, {6}), ["title"])

    def test_parses_generic_function_like_symbols(self):
        symbols = parse_outline(
            "\n".join(
                [
                    "class Store {",
                    "  createModel<T extends BaseModel>(value: T): T {",
                    "    return value",
                    "  }",
                    "  makeModel = <T>(value: T) => {",
                    "    return value",
                    "  }",
                    "}",
                    "function parseModel<T>(value: T): T {",
                    "  return value",
                    "}",
                    "const loadModel = <T>(value: T) => {",
                    "  return value",
                    "}",
                ]
            )
        )

        self.assertEqual(
            [child.name for child in symbols[0].children],
            ["createModel", "makeModel"],
        )
        self.assertEqual(symbols[1].name, "parseModel")
        self.assertEqual(symbols[2].name, "loadModel")
        self.assertEqual(modified_symbols(symbols, {3}), ["createModel"])
        self.assertEqual(modified_symbols(symbols, {10}), ["parseModel"])


if __name__ == "__main__":
    unittest.main()
