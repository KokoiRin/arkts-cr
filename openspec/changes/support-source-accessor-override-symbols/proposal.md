# Support Source Accessor and Override Symbols

## Why

Source File and File Detail handoff now depend heavily on the lightweight source outline: current-symbol hints, `source select symbol`, `copy source symbol`, and problem-context handoff all use it. The outline already recognizes common ArkTS/TS structs, classes, functions, methods, arrow functions, and field arrow methods, but it misses common class-member shapes such as `override aboutToAppear()` and `get title()`.

When a build problem lands inside one of those blocks, cr falls back to line-level context and users have to manually select the useful range.

## What Changes

- Recognize class/struct/interface methods with `override` modifiers.
- Recognize class/struct accessors declared with `get name()` or `set name(value)`.
- Reuse existing symbol labels and range selection behavior.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No semantic resolution across files.
- No decorator interpretation.
- No source editing, quick fixes, or language-server integration.
