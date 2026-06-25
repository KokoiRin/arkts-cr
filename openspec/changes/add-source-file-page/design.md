## Context

File Detail is for changed-file diffs inside the active Review Scope. Task Problems may point at any repo-local file, including files outside the current changes. Source File Page is therefore a cross-layer read-only page, not a new Review Scope layer and not a replacement for File Detail.

## Goals / Non-Goals

**Goals:**

- `view problem` from Task Problems opens the selected repo-local problem file in Source File Page.
- The page shows source lines with line numbers and marks the problem line.
- The initial window keeps the problem line visible and preferably near the middle.
- Existing movement keys scroll the source file.
- Back/forward returns through normal page history.
- Missing or unreadable files produce a clear empty/error state without crashing.

**Non-Goals:**

- No editing or writing source files.
- No syntax highlighting or language parser.
- No diagnostics severity/category/error-code parsing.
- No task history search or persisted source-file state.
- No change to `Enter` on Task Problems; it remains external editor handoff.

## Decisions

1. **Source File Page is a cross-layer page.**
   - Choice: add `BrowserPage.SOURCE_FILE = "source"` with `source_file_path`, `source_file_line`, and `source_file_scroll`.
   - Reason: it is not part of the Review Scope -> Changed Files -> File Detail hierarchy; it is an IDE-like read-only utility page.

2. **Source reading gets a small model module.**
   - Choice: add `cr.ui.source_file` for repo-local path normalization, UTF-8 text reading, and visible-window calculation.
   - Reason: Page Content should render already prepared source facts instead of owning filesystem rules.

3. **Problem viewing is explicit.**
   - Choice: use `view problem` rather than changing Enter.
   - Reason: Enter already has a stable external-editor meaning on Task Problems, and preserving that avoids surprising users.

## Risks / Trade-offs

- **Large files**: the first slice reads UTF-8 text into memory like existing file-detail helpers. If real usage hits huge files, add a streaming/windowed reader later.
- **Binary or non-UTF-8 files**: this page reports an unreadable state instead of guessing encodings.
- **Not persisted**: source preview is session navigation state only; persistence can wait until real usage proves it matters.
