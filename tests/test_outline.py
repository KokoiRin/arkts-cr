import unittest

from cr.outline import modified_symbols, parse_outline, render_outline


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


if __name__ == "__main__":
    unittest.main()
