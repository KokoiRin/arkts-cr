## Context

The product hierarchy treats a selected commit as a Review Scope:

```text
Commit Picker
  -> commit <sha> Review Scope
    -> Changed Files
      -> File Detail
```

Commit Picker currently helps users find a commit by date and subject, but not
by size. A compact file/churn summary makes the first layer more useful without
changing the lower Changed Files and File Detail layers.

## Goals / Non-Goals

**Goals:**
- Add `files`, `added`, and `deleted` metadata to recent commit summaries.
- Render a compact summary on Commit Picker rows.
- Keep row selection and commit diff behavior unchanged.
- Keep summary collection inside the Git adapter.

**Non-Goals:**
- No commit search or filtering.
- No per-file preview in the Commit Picker.
- No background loading or persisted commit metadata cache.
- No change to `cr review`, `cr diff`, or selected commit Changed Files output.

## Decisions

1. Extend `CommitSummary` with defaulted metadata fields.

   Existing tests and callers construct `CommitSummary` directly. Defaulting
   `files`, `added`, and `deleted` preserves those call sites while allowing
   `recent_commits()` to enrich real Git results.

2. Parse commit stats in `cr.vcs.git.recent_commits()`.

   The Git adapter already owns commit discovery and subprocess calls. It can
   ask Git for numstat data while returning plain Python facts to the UI.

   Alternative considered: load stats lazily during rendering. That would make
   Page Content call Git or require browser orchestration to do per-frame work,
   which violates existing boundaries.

3. Render summary in Page Content.

   Commit Picker row text belongs to `cr.ui.page_content`; it should format the
   metadata without knowing how the facts were collected.

## Risks / Trade-offs

- **Risk:** `git log --numstat` is heavier than the current recent commit log.
  **Mitigation:** the limit remains small, and the query runs only when recent
  commits are loaded or refreshed, not on every frame.

- **Risk:** binary file stats have unknown line counts.
  **Mitigation:** count the changed file but ignore unknown line counts in the
  added/deleted totals, matching existing binary count conventions.
