# Add File Detail Problem Context

## Why

File Detail is where users spend most of their review time reading a changed file. Today it can copy source context, copy a source symbol, copy a hunk, or copy a change, but packaging the current line as a handoff bundle with both source and diff context still requires navigating to Source File first.

This adds the missing direct handoff path for the core review flow: while reading a diff row, copy or save the current source line plus the same-file diff for AI/reviewer follow-up.

## What Changes

- File Detail `copy problem context` resolves the current rendered new-file line and copies Source File-style source context plus the current file diff.
- File Detail `save problem context [PATH]` saves the same bundle.
- Deleted-only rows or pages without a current new-file line report the existing File Detail source-line error.

## Non-Goals

- No language server, quick fix, or code editing.
- No automatic symbol-range selection from File Detail.
- No multi-file dependency collection.
- No new persistent state or page navigation.
