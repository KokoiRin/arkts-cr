## 1. Tests

- [x] 1.1 Add outline coverage for class/struct field arrow-function symbols.
- [x] 1.2 Add Source File `copy source symbol` coverage for field arrow functions.
- [x] 1.3 Confirm existing method/function outline behavior still passes.

## 2. Implementation

- [x] 2.1 Add a best-effort field-arrow matcher to `cr.source.outline`.
- [x] 2.2 Return field arrow functions as method-like symbols inside containers.
- [x] 2.3 Reuse existing source-symbol copy/select paths without new UI state.

## 3. Docs And Validation

- [x] 3.1 Update README or docs/p0.md with the delivered slice.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, and diff check.
- [x] 3.3 Run Warden scope review.
