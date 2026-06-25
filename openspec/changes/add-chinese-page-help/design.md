## Page Model
Help is a first-class browser page named `help`. The navigation state records
`help_topic_page`, which is the page being explained. Opening Help pushes the
current page snapshot onto the existing back stack and switches to `help`.

## Rendering
`page_content` owns the Chinese help copy. Help content is data driven by topic
page so the same command can explain changed files, file detail, task output,
task problems, source files, scope selection, commits, and command palette.

## Localization Scope
Command words stay in English because they are executable input. User-facing
descriptions, headers, action bars, and help copy on the affected TUI surfaces
are Chinese.

## Non-goals
- No keybinding changes.
- No terminal mouse/click support changes.
- No full localization pass over CLI argparse help or README prose.
