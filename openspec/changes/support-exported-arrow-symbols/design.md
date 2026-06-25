# Design

The smallest correct change is in `src/cr/source/outline.py`.

`ARROW_FUNCTION_RE` already recognizes top-level `const|let|var` arrow functions, including generic arrows and async arrow values. This P0 only permits an optional leading `export` before the declaration keyword:

```text
export const load = async <T>(value: T) => { ... }
```

No UI state or command parser changes are needed. Existing Source File and File Detail commands benefit because they already call `source_outline.parse_outline`.
