import unittest

from cr.source.outline import (
    modified_symbols,
    parse_outline,
    render_outline,
    symbol_label_at_line,
)


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


class OutlineSymbolLabelTests(unittest.TestCase):

    def test_symbol_label_identifies_current_nested_or_top_level_symbol(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies 当前 nested or top level 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "struct FeedCard {",
                    "  build() {",
                    "    Text('hello')",
                    "  }",
                    "}",
                    "function helper() {",
                    "  return 1",
                    "}",
                    "const loose = 1",
                ]
            )
        )

        method = symbol_label_at_line(symbols, 3)
        function = symbol_label_at_line(symbols, 7)
        outside = symbol_label_at_line(symbols, 9)

        self.assertEqual(method, "struct FeedCard > method build")
        self.assertEqual(function, "function helper")
        self.assertEqual(outside, "")
    def test_symbol_label_identifies_field_arrow_function_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies field arrow function 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "struct FeedCard {",
                    "  private onTap = () => {",
                    "    this.handleTap()",
                    "  }",
                    "  public static readonly makeModel: () => Model = () => {",
                    "    return new Model()",
                    "  }",
                    "}",
                    "const load = () => {",
                    "  return 1",
                    "}",
                ]
            )
        )

        field_arrow = symbol_label_at_line(symbols, 3)
        typed_field_arrow = symbol_label_at_line(symbols, 6)
        top_level_arrow = symbol_label_at_line(symbols, 10)

        self.assertEqual(field_arrow, "struct FeedCard > method onTap")
        self.assertEqual(typed_field_arrow, "struct FeedCard > method makeModel")
        self.assertEqual(top_level_arrow, "function load")
    def test_symbol_label_identifies_override_and_accessor_members(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies override and accessor members」时，系统应产出正确的结构化结果 [Requirement: TODO]
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

        override_method = symbol_label_at_line(symbols, 3)
        getter = symbol_label_at_line(symbols, 6)
        setter = symbol_label_at_line(symbols, 9)

        self.assertEqual(override_method, "class FeedCard > method aboutToAppear")
        self.assertEqual(getter, "class FeedCard > method title")
        self.assertEqual(setter, "class FeedCard > method title")
    def test_symbol_label_identifies_generic_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies generic 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "class Store {",
                    "  private createModel<T extends BaseModel>(value: T): T {",
                    "    return value",
                    "  }",
                    "  private makeModel = <T>(value: T) => {",
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

        generic_method = symbol_label_at_line(symbols, 3)
        field_arrow = symbol_label_at_line(symbols, 6)
        generic_function = symbol_label_at_line(symbols, 10)
        top_level_arrow = symbol_label_at_line(symbols, 13)

        self.assertEqual(generic_method, "class Store > method createModel")
        self.assertEqual(field_arrow, "class Store > method makeModel")
        self.assertEqual(generic_function, "function parseModel")
        self.assertEqual(top_level_arrow, "function loadModel")
    def test_symbol_label_identifies_declaration_only_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies declaration 只读 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "abstract class BaseCard {",
                    "  abstract load(): Promise<void>;",
                    "  protected abstract render(): void;",
                    "  abstract get title(): string;",
                    "  hydrate() {",
                    "    this.render()",
                    "  }",
                    "}",
                    "interface Renderer {",
                    "  mount(): void;",
                    "  unmount(): void;",
                    "}",
                ]
            )
        )

        abstract_method = symbol_label_at_line(symbols, 2)
        protected_abstract = symbol_label_at_line(symbols, 3)
        abstract_getter = symbol_label_at_line(symbols, 4)
        concrete_method = symbol_label_at_line(symbols, 6)
        first_interface_method = symbol_label_at_line(symbols, 10)
        second_interface_method = symbol_label_at_line(symbols, 11)

        self.assertEqual(abstract_method, "class BaseCard > method load")
        self.assertEqual(protected_abstract, "class BaseCard > method render")
        self.assertEqual(abstract_getter, "class BaseCard > method title")
        self.assertEqual(concrete_method, "class BaseCard > method hydrate")
        self.assertEqual(first_interface_method, "interface Renderer > method mount")
        self.assertEqual(second_interface_method, "interface Renderer > method unmount")
    def test_symbol_label_identifies_exported_arrow_function_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies exported arrow function 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "export const loadModel = async <T>(value: T) => {",
                    "  return value",
                    "}",
                    "export let normalize = (value: string) => {",
                    "  return value.trim()",
                    "}",
                ]
            )
        )

        exported_const = symbol_label_at_line(symbols, 2)
        exported_let = symbol_label_at_line(symbols, 5)

        self.assertEqual(exported_const, "function loadModel")
        self.assertEqual(exported_let, "function normalize")
    def test_symbol_label_identifies_default_export_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies 默认 export 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "export default class FeedStore {",
                    "  hydrate() {",
                    "    this.ready = true",
                    "  }",
                    "}",
                    "export default function createStore() {",
                    "  return new FeedStore()",
                    "}",
                ]
            )
        )

        method = symbol_label_at_line(symbols, 3)
        default_function = symbol_label_at_line(symbols, 7)

        self.assertEqual(method, "class FeedStore > method hydrate")
        self.assertEqual(default_function, "function createStore")
    def test_symbol_label_identifies_enum_symbols(self):
        # Behavior: 当用户在Source File中解析「符号 label identifies enum 符号」时，系统应产出正确的结构化结果 [Requirement: TODO]
        symbols = parse_outline(
            "\n".join(
                [
                    "export const enum FeedStatus {",
                    "  Loading = 'loading',",
                    "  Ready = 'ready',",
                    "}",
                    "export enum LoadState {",
                    "  Idle,",
                    "  Done,",
                    "}",
                    "enum CardKind {",
                    "  Video,",
                    "  Image,",
                    "}",
                ]
            )
        )

        exported_const_enum = symbol_label_at_line(symbols, 2)
        exported_enum = symbol_label_at_line(symbols, 6)
        plain_enum = symbol_label_at_line(symbols, 10)

        self.assertEqual(exported_const_enum, "enum FeedStatus")
        self.assertEqual(exported_enum, "enum LoadState")
        self.assertEqual(plain_enum, "enum CardKind")

if __name__ == "__main__":
    unittest.main()
