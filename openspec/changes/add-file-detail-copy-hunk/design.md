## Context

`copy diff` copies a selected file's full compact diff snippet. File Detail now
also supports hunk navigation and `open hunk`, so the user can focus on one
changed block. Copying only that active hunk is the smallest next handoff
surface.

## Goals / Non-Goals

**Goals:**

- Add `copy hunk` for File Detail.
- Use the current File Detail scroll to choose the active hunk.
- Copy Markdown that includes the selected path, an anchor using the hunk's
  new-file start line, and the active rendered hunk block.
- Reuse the existing copy command configuration.
- Keep Review Scope, selected file, filters, notes, progress, and task state
  unchanged.

**Non-Goals:**

- No raw apply-able patch guarantee.
- No hunk picker.
- No hunk save command in this slice.
- No changes to `copy diff`; it continues to copy the whole selected file
  snippet.

## Decisions

### Decision 1: Reuse rendered File Detail hunk rules

`cr.ui.file_detail_navigation` already owns rendered hunk header detection and
active hunk line resolution. It will also return the active rendered hunk block
as plain text lines with ANSI codes stripped. Browser execution stays
responsible for copying and status feedback.

### Decision 2: Copy review text, not a patch

The copied hunk uses a Markdown `text` fence because File Detail hunks are
line-numbered review output, not raw patch hunks. This avoids implying that the
snippet can be applied directly.

### Decision 3: Keep command explicit

The command is `copy hunk`. `copy diff` keeps copying the whole selected file
diff snippet.

## Risks / Trade-offs

- The hunk block is derived from rendered File Detail text. This is acceptable
  for a review handoff command and keeps all rendered hunk assumptions in one
  module.
