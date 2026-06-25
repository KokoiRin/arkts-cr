# Design

This P0 mirrors existing source copy behavior:

- `source_file.py` remains the Markdown renderer.
- `browser.py` chooses Source File vs File Detail target and reports status.
- `handoff.py` owns path defaults and write errors.
- `commands.py`, the command catalog, README, and page help expose the commands.

Default paths:

```text
.cr/handoff/source.md
.cr/handoff/source-symbol.md
```

`save source` preserves Source File selection semantics: if a source selection exists, save that selected range; otherwise save the current context window. In File Detail it saves source context around the current rendered new-file line, matching `copy source`.

`save source symbol` saves the current symbol range from Source File or File Detail, matching `copy source symbol`, and does not mutate Source File selection.
