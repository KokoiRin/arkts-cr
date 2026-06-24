## Why

Recent commits are a Review Scope entry point, but the Commit Picker currently
shows only hash, date, and subject. Users need a quick sense of each commit's
size before entering it and drilling into Changed Files.

## What Changes

- Add changed-file count and added/deleted line totals to recent commit facts.
- Render those totals on Commit Picker rows.
- Preserve existing commit selection, paging, scope switching, and selected
  commit diff behavior.
- Keep the summary as Git fact metadata; do not add persisted browser state.

## Capabilities

### New Capabilities
- `browser-commit-picker-change-summary`: displays per-commit change size in the
  Commit Picker.

### Modified Capabilities
- None.

## Impact

- Touches `cr.vcs.git.CommitSummary` and `recent_commits()` for commit metadata.
- Touches `cr.ui.page_content` for Commit Picker row rendering.
- Adds focused rendering and Git parsing tests.
- Updates product and architecture docs for Commit Picker summaries.
