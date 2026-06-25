## Why

Review Notes already let users mark files and changed rows while reading AI-written code, then inspect or copy the notes summary. Clipboard-only notes handoff is brittle for longer sessions and remote terminals, and README already frames Handoff as copy/save oriented.

## What Changes

- Add `save notes [PATH]` to write the current Review Notes summary to disk.
- Default to `.cr/handoff/review-notes.md`.
- Reuse the existing Review Notes ordering and text format.
- Report empty note sets and write failures without changing page, selection, task state, filters, or review progress.
- Update Chinese help, command discovery, README, and P0 history.

## Non-Goals

- No filtered save syntax; `copy notes QUERY` continues to cover filtered clipboard handoff.
- No note editing changes.
- No workspace persistence changes.
- No new note file format, note metadata, or export schema.
