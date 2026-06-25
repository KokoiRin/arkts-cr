# Support Default Export Symbols

## Why

Source File and File Detail use the lightweight outline to choose focused source ranges for `copy source symbol`, `source select symbol`, symbol navigation, and problem-context handoff. TS/ArkTS modules often use `export default class Foo` or `export default function createFoo()`. Today those declarations are treated as no symbol, so handoff falls back to coarser context.

## What Changes

- Recognize `export default class|struct|interface Name` as the same container symbols as non-default exports.
- Recognize `export default function Name(...)` as a function symbol.
- Keep the current regex-based outline and existing symbol labels.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No anonymous `export default function (...)` support in this slice.
- No default-export arrow expression support in this slice.
- No export graph resolution, source editing, quick fixes, or language-server integration.
