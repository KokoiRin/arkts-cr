## Design

Review notes are browser workspace state, but prompt Markdown is a `cr.review` output format. The browser should only choose which notes are relevant and pass them to review data assembly; it should not concatenate Markdown.

The data flow becomes:

```text
BrowserState.review_notes
  -> build_review_data(..., review_notes=...)
  -> render_prompt_handoff(data)
  -> file_actions.copy_text(...)
```

## Behavior

- `copy prompt` includes review notes for files in the current visible changed files.
- `copy prompt file` includes the selected file note if present.
- Persisted notes for files outside the copied prompt file set are ignored.
- Empty or whitespace-only notes are ignored by existing workspace note cleanup and should not render.
- Prompt output without notes should be unchanged.

## Prompt Format

Use a compact stable label:

```markdown
- review note: check lifecycle edge case
```

The line appears in both:

- the file summary block under `## Files`
- the file detail block under `## Details`

This mirrors existing labels such as `risk`, `state`, `purpose`, and `focus`.

## Non-Goals

- Do not add a new command.
- Do not read `.git/cr/browse-state.json` from `cr review --prompt`.
- Do not include notes outside the copied file set.
- Do not add prompt templates or note export files.
