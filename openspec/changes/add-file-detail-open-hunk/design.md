## Context

`open` already opens the selected file at the first changed line. After File
Detail hunk navigation, users can position the File Detail view on a specific
hunk, but there is no editor handoff for that hunk.

## Goals / Non-Goals

**Goals:**

- Add `open hunk` for File Detail.
- Use the current File Detail scroll to choose the nearest active hunk.
- Open the selected file at the hunk's new-file start line through the existing
  configured editor handoff.
- Keep Review Scope, selected file, filters, notes, progress, and task state
  unchanged.

**Non-Goals:**

- No hunk picker.
- No hunk staging.
- No new editor command configuration.
- No changes to normal `open`; it continues to open the first changed line.

## Decisions

### Decision 1: Reuse File Detail navigation hunk parsing

`cr.ui.file_detail_navigation` already owns rendered hunk header discovery. It
will also parse the new-file start line from the active rendered hunk header.
Browser execution stays responsible only for applying the editor handoff.

### Decision 2: Current hunk follows scroll

The active hunk is the latest hunk header at or before the current File Detail
scroll. If the scroll is before the first hunk, the first hunk is used. This
matches what a user sees after opening a file detail before scrolling.

### Decision 3: Keep command explicit

The command is `open hunk`. The existing `open` command keeps its current
first-changed-line behavior, which is still useful from Changed Files and from
the top of File Detail.

## Risks / Trade-offs

- The hunk line is derived from rendered hunk header text. This follows the
  existing File Detail hunk navigation model and keeps the behavior local to the
  UI layer. If hunk rendering changes later, `cr.ui.file_detail_navigation` is
  the single update point.
