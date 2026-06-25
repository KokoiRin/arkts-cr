# Design

## Behavior

The regex-based outline will recognize enum declarations as container-like symbols:

- `enum Status { ... }`
- `export enum Status { ... }`
- `export const enum Status { ... }`

The enum body is treated as one selectable symbol range. Enum members are not separate symbols because the first release needs reliable block-level handoff, not semantic TypeScript parsing.

## Boundaries

Only `src/cr/source/outline.py` changes in behavior. Browser commands continue to use the existing outline APIs and source-range Markdown rendering.

## Validation

- Outline tests verify enum labels and modified-symbol names.
- Browser tests verify `copy source symbol` copies only the enum range and includes `Symbol: enum ...` metadata.
