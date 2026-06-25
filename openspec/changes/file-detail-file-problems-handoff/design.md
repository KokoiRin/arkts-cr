# Design

## Behavior

Add a small helper that resolves the target path for file-problem handoff:

- If `state.page == BrowserPage.FILE_DETAIL`, use `state.visible_changes[state.selected].path`.
- Otherwise, keep using the currently selected parsed task problem path.

The copy/save commands then filter parsed task problems by that path.

## Boundaries

- Command parsing remains unchanged.
- Behavior lives in `src/cr/ui/browser.py` near existing task problem copy/save helpers.
- Output format remains the existing `task_problems_module.problems_handoff_text`.
- Save behavior continues to use `handoff_module.save_task_problems_text(..., selected_file=True)`.

## Validation

- Add a File Detail test showing `copy file problems` uses the current changed file even when `problem_selected` points at another file.
- Add a File Detail test showing `save file problems [PATH]` writes the current changed file's problems.
- Add a no-current-file-problems test.
- Run focused tests, OpenSpec validation, and full test discovery.
