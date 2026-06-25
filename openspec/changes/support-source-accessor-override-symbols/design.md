# Design

## Behavior

The regex-based outline keeps its current best-effort model. It will treat:

- `override aboutToAppear() { ... }`
- `public override aboutToAppear() { ... }`
- `get title(): string { ... }`
- `set title(value: string) { ... }`

as method-like symbols inside class/struct/interface containers.

Accessors are labeled as `method title` so existing UI wording and copy/select behavior remain stable. The getter/setter distinction is deliberately not exposed in the label because the current symbol taxonomy only has containers, functions, and methods.

## Boundaries

Only `src/cr/source/outline.py` changes in core behavior. Browser commands and source rendering should continue to call the same outline APIs.

## Validation

- Outline unit tests verify labels for override and accessor methods.
- Browser command tests verify `copy source symbol` copies an accessor range without copying adjacent methods.
