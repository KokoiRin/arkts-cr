# Support Source Enum Symbols

## Why

Source/File Detail navigation and handoff use the lightweight source outline to select readable code ranges. The outline recognizes classes, structs, interfaces, functions, methods, accessors, and arrow callbacks, but TS/ArkTS enum blocks still appear as no current symbol.

When a change or task problem lands inside an enum, `copy source symbol`, symbol navigation, and modified-symbol summaries lose the nearest useful block and fall back to manual line ranges or `unknown`.

## What Changes

- Recognize `enum` and `export const enum` declarations as block-level source symbols.
- Reuse existing current-symbol labels, symbol range selection, copy/save, and symbol navigation behavior.
- Treat enum changes as named modified symbols instead of `unknown`.

## Non-Goals

- No enum member parsing.
- No enum value evaluation.
- No complete TypeScript/ArkTS parser.
- No language-server integration, source editing, quick fixes, or cross-file resolution.
