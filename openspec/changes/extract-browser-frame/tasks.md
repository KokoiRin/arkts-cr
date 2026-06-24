## 1. Frame Module

- [x] 1.1 Add `cr.ui.frame` with `ScreenLayout`, `BrowserFrame`, terminal height/fit helpers, layout calculation, Task Panel lines, and partial-refresh output.
- [x] 1.2 Keep the frame module independent of `BrowserState`, ReviewWorkspace, navigation, command parsing, and Git review data.

## 2. Browser Delegation

- [x] 2.1 Delegate existing browser frame/task-panel helper names to `cr.ui.frame` while preserving current private entry points.
- [x] 2.2 Keep `_draw_browse_screen` in `browser.py`, but use the frame module for layout, task panel lines, prompt row, terminal line fitting, and frame cache state.

## 3. Tests And Documentation

- [x] 3.1 Add focused module-level tests for frame layout, Task Panel lines, history rendering, line fitting, and partial-refresh refusal/output behavior.
- [x] 3.2 Keep existing browser frame/task-panel tests passing without user-visible behavior changes.
- [x] 3.3 Update `CONTEXT.md`, `docs/design.md`, `docs/workbench-navigation.md`, and `docs/p0.md` to name Browser Frame as the screen-layer owner.

## 4. Verification

- [x] 4.1 Run OpenSpec validation, targeted frame/browser tests, full unit tests, compile checks, diff checks, and Warden review.
