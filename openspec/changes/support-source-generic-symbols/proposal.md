# Support Source Generic Symbols

## Why

Source/File Detail handoff uses the lightweight source outline to select and copy useful code ranges. The outline recognizes many ArkTS/TS function shapes, but it misses generic methods and functions such as `createModel<T>()`, `function parse<T>()`, and generic arrow callbacks like `const map = <T>(value: T) =>`.

When a problem lands inside those blocks, cr can fall back to the outer class or no symbol, which makes `copy source symbol` and problem-context handoff less precise.

## What Changes

- Recognize generic class/struct/interface methods.
- Recognize generic top-level functions.
- Recognize generic top-level and field arrow functions.
- Reuse existing labels and copy/select behavior.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No semantic generic type resolution.
- No cross-file dependency collection.
- No source editing, quick fixes, or language-server integration.
