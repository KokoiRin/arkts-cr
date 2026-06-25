# Change: Source File problem header

## Why

Source File can now step through task problems directly, but the page header only shows source context such as selection, mark, and symbol. When scanning several build/test/lint failures, users need to know which diagnostic the current source line represents without jumping back to Task Problems.

## What Changes

- Show a compact current-problem label in the Source File header when the selected parsed task problem matches the current source path and line.
- Keep the label hidden when Source File is opened from non-problem navigation or when the user moves the source target to another line.
- Preserve existing copy/save/handoff behavior.

## Non-Goals

- No diagnostics persistence.
- No language-service lookup.
- No multi-problem source panel.
- No quick fixes or source editing.
