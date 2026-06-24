## Context

`copy diff` already renders a compact selected-file review snippet through
`cr.review.snippet` and chooses the current visible file through
`cr.ui.selected_file_actions`. Prompt handoff already has copy/save pairs:
`copy prompt` / `save prompt` and `copy prompt file` / `save prompt file`.

The missing pair is `save diff`: the same lightweight selected-file context
without depending on a clipboard command.

## Goals / Non-Goals

**Goals:**

- Add `save diff [PATH]` as the selected-file save counterpart to `copy diff`.
- Save exactly the selected visible file's compact diff snippet.
- Reuse `cr.review.snippet` for text and `cr.ui.handoff` for path resolution,
  directory creation, UTF-8 writes, and write-error messages.
- Keep the current page and workspace state unchanged.

**Non-Goals:**

- No multi-file diff export.
- No raw patch/apply format.
- No new browser page or persisted state.
- No changes to `copy diff` snippet text.

## Decisions

### Decision 1: Handoff owns file writes

`cr.ui.handoff` gains a diff-specific default path and save helper. This keeps
path handling and write-error messages in the same UI-side module that already
owns saved prompt handoff files.

### Decision 2: Selected File Actions owns selected-file save workflow

`cr.ui.selected_file_actions` already chooses the selected file and builds the
one-file diff snippet for `copy diff`. `save diff` reuses that same public
workflow and only swaps clipboard output for file output.

### Decision 3: Command stays small

The command is `save diff [PATH]`. Without a path it writes to
`.cr/handoff/review-diff.md`; with a path it follows existing handoff path
semantics: absolute paths are used directly and relative paths are repo-root
relative.

## Risks / Trade-offs

- This creates another handoff file under `.cr/handoff`. The trade-off is
  acceptable because it mirrors existing saved prompt behavior and avoids adding
  clipboard-specific workarounds to the main browser loop.
