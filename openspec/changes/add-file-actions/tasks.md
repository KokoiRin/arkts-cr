## 1. Command Model

- [x] 1.1 Add parser actions for `copy path`, `copy anchor`, and `reveal`
- [x] 1.2 Add executable command palette entries in the Files group

## 2. File Action Helpers

- [x] 2.1 Add clipboard helper with common platform command discovery
- [x] 2.2 Add reveal helper with common platform command discovery
- [x] 2.3 Return user-facing success/failure messages without raising into the browser loop

## 3. Browser Execution

- [x] 3.1 Execute copy path against the selected visible changed file
- [x] 3.2 Execute copy anchor using the current review scope's first changed line
- [x] 3.3 Execute reveal against the selected repo file
- [x] 3.4 Preserve existing `open` behavior

## 4. Documentation

- [x] 4.1 Update README command usage
- [x] 4.2 Update navigation/P0 docs and CONTEXT terms

## 5. Verification

- [x] 5.1 Run focused tests, full tests, compile check, OpenSpec strict validation, and diff check
- [x] 5.2 Run Warden scope review
