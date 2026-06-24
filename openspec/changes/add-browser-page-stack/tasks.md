## 1. Navigation Stack Model

- [x] 1.1 Add lightweight page snapshot state to `BrowserState`
- [x] 1.2 Teach `BrowserNavigation` to push current snapshots on page transitions
- [x] 1.3 Implement `back` and `forward` stack operations with existing fallback behavior

## 2. Browser Command

- [x] 2.1 Add parser action and command palette entry for `forward`
- [x] 2.2 Execute `forward` through `BrowserCommandExecutor`
- [x] 2.3 Clear page history on Review Scope switches and refreshes that reload the changed-file set

## 3. Documentation

- [x] 3.1 Update README command usage
- [x] 3.2 Update CONTEXT, design, navigation roadmap, and P0 docs

## 4. Verification

- [x] 4.1 Run focused tests, full tests, compile check, OpenSpec strict validation, and diff check
- [x] 4.2 Run Warden scope review
