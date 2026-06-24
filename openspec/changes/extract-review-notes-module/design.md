## Context

`ReviewWorkspace` owns the note data itself, while `Page Content` marks noted
files and shows a selected file's note. The remaining rules are still in
`browser.py`:

- Clean note text before display.
- Order current changed-file notes before persisted extra notes.
- Filter by path or note text.
- Render empty and filtered-empty states.
- Copy the exact rendered summary and produce copy status messages.

Those are stable Review Notes rules, not browser run-loop behavior.

## Goals / Non-Goals

**Goals:**

- Add a pure-ish `cr.ui.review_notes` module for summary/search/copy rules.
- Keep platform copy execution delegated to `cr.ui.file_actions.copy_text`.
- Preserve all current command output and browser state behavior.
- Keep browser wrappers for compatibility with existing tests and private
  callers during incremental extraction.

**Non-Goals:**

- No new note commands.
- No note persistence schema changes.
- No note editing changes.
- No PR-comment or todo workflow expansion in this change.

## Decisions

### Decision 1: UI module, not review package

Review Notes are browser workspace UI state. They can feed review prompt data,
but the ordering/search/copy command behavior is UI-level, so the module lives
under `cr.ui`.

### Decision 2: Data in, lines out

`review_note_lines(changes, notes, query)` accepts explicit changed-file data
and note data instead of reading browser state. This keeps the module easy to
test and language-migration friendly.

### Decision 3: Copy helper returns status text

`copy_review_notes(...)` reuses the same rendered lines and returns the same
messages as the browser currently does. The module may accept a copy adapter for
tests, but `cr.ui.file_actions` remains the owner of clipboard subprocess
details.

## Risks / Trade-offs

- This extraction adds a small module. It earns its seam because the same rules
  are already used by show/copy/filter commands and will likely feed richer
  review workflows later.
- Browser compatibility wrappers remain temporarily. They keep the change small
  and can be removed after tests migrate fully to module-level surfaces.
