# Support Exported Arrow Symbols

## Why

Source File and File Detail handoff rely on the lightweight outline to choose the smallest useful source range. TS/ArkTS modules commonly expose helper logic as `export const name = (...) => {}` or `export let name = (...) => {}`. Today those exported arrow functions are treated as no symbol, so `copy source symbol` and symbol-based context fall back to coarse snippets.

## What Changes

- Recognize top-level exported `const` / `let` / `var` arrow functions as function symbols.
- Keep existing non-exported arrow function behavior unchanged.
- Reuse the current regex-based outline and brace end-line estimation.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No cross-file export resolution.
- No default export handling in this slice.
- No source editing, quick fixes, or language-server integration.
