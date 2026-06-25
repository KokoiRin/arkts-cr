## Context

Source File Page is a read-only source preview over repo-local files. `cr.ui.source_file` already owns UTF-8 reads and target-line windowing, while Browser Action Execution owns clipboard/editor side effects. The snippet formatting should stay with the source model so it remains testable and reusable if the UI implementation changes later.

## Decisions

1. Add `copy source`.
   - Reason: `copy line` already means anchor-only. A separate command keeps semantics clear.
2. Use a fixed target context of three lines before and after the target.
   - Reason: it is compact enough for chat handoff and useful enough for most compile/problem loops.
3. Copy Markdown text with line numbers.
   - Reason: it is readable in AI/chat tools and preserves the exact target line.
4. Keep this Source File Page only.
   - Reason: File Detail already has diff-oriented `copy hunk` and `copy change`; this feature is for source preview, not changed-file diffs.

## Behavior

- On Source File Page for `src/Foo.ets` target line 20, `copy source` copies a Markdown block headed by `src/Foo.ets:20`.
- The code block includes up to lines 17-23 with `>` marking line 20.
- If the source file is unreadable or no source path is active, the command reports a clear empty/error state without copying.

## Boundaries

- Do not add BrowserState fields.
- Do not change Source File Page navigation, search, or editor open behavior.
- Do not change File Detail copy commands.
