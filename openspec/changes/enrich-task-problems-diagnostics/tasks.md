## 1. Tests

- [x] 1.1 Add parser coverage for severity, code, and cleaned message.
- [x] 1.2 Add fallback coverage for anchor-only unknown diagnostics.
- [x] 1.3 Add rendering coverage for compact diagnostic labels.
- [x] 1.4 Add handoff coverage for copied diagnostic facts.

## 2. Implementation

- [x] 2.1 Extend `TaskProblem` with optional diagnostic facts.
- [x] 2.2 Add generic severity/code/message extraction in `cr.ui.task_problems`.
- [x] 2.3 Render compact diagnostic labels in Task Problems page.
- [x] 2.4 Include diagnostic facts in selected/all problem handoff text.

## 3. Docs And Validation

- [x] 3.1 Update README, design, navigation, and P0 docs.
- [x] 3.2 Run OpenSpec validation, focused tests, full tests, compile, and diff check.
- [x] 3.3 Run Warden scope review.
