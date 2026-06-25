## Behavior

`save notes [PATH]` saves the same ordered summary produced by `notes` and `copy notes`.

When no path is supplied, the command writes `.cr/handoff/review-notes.md`.

If there are no notes, it reports `No review notes to save.` and does not create a file. If writing fails, it reports the existing handoff write error.

## Boundaries

`cr.ui.review_notes` owns the note summary text and empty-state rules. `browser.py` routes the command and places feedback. `handoff.py` owns the default path and UTF-8 write. The command parser only maps command text to stable browser actions.

The change deliberately does not add filtered-save parsing because `save notes path.md` would otherwise be ambiguous with note text queries.
