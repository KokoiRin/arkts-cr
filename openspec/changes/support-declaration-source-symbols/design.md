# Design

## Behavior

The regex-based outline will accept `abstract` as a method/accessor modifier in the same lightweight modifier list that already handles visibility, `static`, `async`, and `override`.

Declaration-only signatures that do not contain `{` on their estimated body range will end on their own line. This prevents an interface or abstract method declaration from swallowing following methods when `symbol_path_at_line` resolves the current line.

Examples:

- `abstract load(): Promise<void>;`
- `protected abstract render(): void;`
- `abstract get title(): string;`
- `render(): void;` inside an interface

## Boundaries

- Behavior changes only in `src/cr/source/outline.py`.
- Browser commands keep using existing outline APIs.
- Tests exercise public outline behavior through `parse_outline` and `symbol_label_at_line`.

## Validation

- Add outline tests for abstract method/accessor labels.
- Add outline tests proving declaration-only signatures do not capture following concrete methods.
- Run focused tests, OpenSpec validation, and full test discovery.
