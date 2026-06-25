## Why

`copy source symbol` is useful when handing a failing source block back to AI,
but the current lightweight outline misses a common ArkTS/TS shape: class or
struct fields that hold arrow-function callbacks, such as
`private onTap = () => { ... }`. When a changed line is inside that callback,
users fall back to manual range selection.

## What Changes

- Recognize class/struct/interface field arrow functions as method-like symbols.
- Include optional access modifiers, `static`, `readonly`, and type annotations.
- Let existing Source File and File Detail `copy source symbol` commands reuse
  the improved outline without new UI commands.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No language-server dependency.
- No cross-file symbol resolution.
- No automatic semantic rename or edit support.
- No new persisted state.
