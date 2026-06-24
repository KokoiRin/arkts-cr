## Context

The product hierarchy is already explicit:

```text
Review Scope -> Changed Files -> File Detail
```

File Detail currently supports line scrolling and page scrolling, but hunk
boundaries are only visible text. Users reviewing a large file need to jump
between changed blocks without scanning every context line.

## Goals / Non-Goals

**Goals:**

- Add `next hunk` and `prev hunk` commands for File Detail.
- Keep hunk navigation within the current selected file.
- Preserve current Review Scope, selected file, filters, notes, progress, and
  background task state.
- Keep hunk detection independent of browser command execution so it can be
  tested and moved later if the UI/runtime changes.

**Non-Goals:**

- No hunk picker page.
- No intra-hunk line selection or staging individual hunks.
- No persisted hunk position across sessions beyond the existing file scroll.
- No changes to diff rendering format.

## Decisions

### Decision 1: Hunk navigation is a File Detail rule

The hunk search and target-scroll calculation live in
`cr.ui.file_detail_navigation`, not in `browser.py`. The module receives
rendered File Detail lines and the current scroll position, then returns a
small result. Browser execution only applies the result and displays messages.

### Decision 2: Recognize rendered diff hunk headers conservatively

Rendered hunk headers are lines whose ANSI-stripped, left-trimmed text starts
with `@@`. This matches current `cr.review.hunks` output after browser
indentation without depending on Git subprocess calls or raw diff parsing.

### Decision 3: Do not wrap at file edges

`next hunk` at the last hunk and `prev hunk` at the first hunk keep the current
scroll and show a status message. This avoids surprising jumps in long files.

## Risks / Trade-offs

- The feature depends on rendered hunk header text. This is acceptable because
  it is explicitly File Detail navigation, and tests cover ANSI-stripped hunk
  recognition. If diff rendering changes later, this module is the one place to
  update.
