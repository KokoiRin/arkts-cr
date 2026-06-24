## Design

`Command Catalog` is an in-process UI module. It has no Git, filesystem, subprocess, or terminal input dependencies. Its interface should hide the knowledge currently scattered through `browser.py`:

- which commands are displayed in each group
- which displayed commands are executable from the command palette
- how palette filtering ranks command, label, group, and description matches
- how command list and command palette rows are rendered

`browser.py` should continue to own:

- `BrowserState.command_filter_text`, `command_selected`, and `command_scroll`
- page transitions and action execution
- drawing the returned lines into the Browser Frame

## Module Interface

The new module should expose small functions with stable behavior:

- `command_catalog() -> tuple[CommandGroup, ...]`
- `command_palette_entries() -> list[PaletteCommand]`
- `filtered_command_palette_entries(query: str) -> list[PaletteCommand]`
- `selected_palette_command(query: str, selected: int) -> PaletteCommand | None`
- `command_list_lines(style, max_lines) -> list[str]`
- `command_palette_screen_lines(query, selected, scroll, style, max_lines) -> CommandPaletteScreen`

The screen helper may return both rendered lines and normalized scroll so the browser keeps owning mutable state.

## Behavior Preservation

This is an extraction, not a product change. It should preserve:

- command group names and order
- command labels, descriptions, and executable command strings
- non-executable placeholder entries such as `base REF`, `note TEXT`, and `copy notes QUERY`
- match count text
- ranking order: exact, prefix, command/label contains, group, description
- clipped command-list behavior
- command palette scroll-window behavior

## Non-Goals

- Do not add new commands.
- Do not change command names or aliases.
- Do not change command dispatch parsing.
- Do not introduce fuzzy matching.
- Do not split browser rendering or task panel rendering in this change.
