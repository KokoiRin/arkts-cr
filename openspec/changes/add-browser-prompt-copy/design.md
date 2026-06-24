## Design

`copy prompt` is an in-browser handoff command, not a new prompt renderer. It composes existing modules:

- `ReviewWorkspace`: owns the current Review Scope and visible/selected changed files.
- `cr.review.data.build_review_data`: turns changed files into structured review facts.
- `cr.review.prompt.render_prompt_handoff`: renders the canonical Markdown handoff.
- `cr.ui.file_actions.copy_text`: copies text through `--copy-cmd`, `CR_COPY_CMD`, or platform fallback.

## Command Behavior

- `copy prompt`: copy prompt-ready Markdown for the current visible changed files.
- `copy prompt file`: copy prompt-ready Markdown for the selected visible changed file only.

Both commands should:

- preserve page, selection, review scope, file filter, progress state, notes, and task state
- respect current scope flags (`staged`, `all`, `base`, `range`) and hunk context
- include current seen markers in prompt metadata
- use the same copy action configuration as `copy path`, `copy anchor`, and `copy notes`
- surface copy failures through the existing file action failure message

## Empty States

- If `copy prompt` has no visible changed files: `No changed files to copy prompt.`
- If `copy prompt file` has no selected changed file: `No changed file to copy prompt.`

Neither empty state should launch a clipboard command.

## Scope

This change deliberately does not add:

- custom prompt templates
- prompt preview pages
- exporting prompt text to files
- including review notes inside the generated prompt
- fuzzy prompt selection

Those can be considered after the basic in-browser handoff proves useful.
