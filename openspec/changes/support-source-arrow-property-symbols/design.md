## Design

The existing `cr.source.outline` module is intentionally regex-based and already
owns best-effort ArkTS/ETS/TS symbol detection. This change adds one local
symbol matcher for class/struct/interface field arrow functions:

```ts
private onTap = () => {
  ...
}

readonly buildModel: () => Model = () => {
  ...
}
```

The matcher returns `kind="method"` so existing container validation keeps it
inside class/struct/interface symbols. Existing callers then automatically
benefit:

- Source File current-symbol hint.
- `source select symbol`.
- `copy source symbol`.
- File Detail direct `copy source symbol`.
- Review outline modified-symbol summaries.

## Boundaries

- The matcher stays best-effort and line-based.
- It only recognizes arrow fields with assignment on the declaration line.
- It does not evaluate nested generics or multiline type declarations beyond the
  existing brace-balance end-line estimate.

## Validation

- Unit tests cover symbol labels and ranges for class field arrow functions.
- BrowserCommandExecutor tests cover copying the selected source symbol from
  Source File.
- Existing outline and browser tests guard non-regression for normal methods and
  top-level arrow functions.
