# Support Declaration Source Symbols

## Why

Source/File Detail handoff now depends on the lightweight outline for symbol selection and context packaging. ArkTS/TS files often contain declaration-only members in interfaces or abstract classes, such as `abstract load(): Promise<void>;` or `render(): void;`. Today those shapes are either missed or can be treated as an open-ended range, making nearby `copy source symbol`, `view source symbol`, and problem-context handoff less precise.

## What Changes

- Recognize `abstract` methods and abstract accessors as method-like symbols.
- Treat declaration-only signatures without a body as one-line symbols instead of ranges that extend to the end of the file.
- Keep existing best-effort outline APIs and labels.

## Non-Goals

- No full TypeScript/ArkTS parser.
- No type resolution, inheritance analysis, or interface implementation lookup.
- No source editing, quick fixes, outline panel, language server, or cross-file dependency expansion.
