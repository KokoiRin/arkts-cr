## Context

The product hierarchy defines recent commits as a first-layer Review Scope
selector. Users can filter that selector before entering a selected commit
scope. The current implementation already behaves correctly, but its rules are
split across layers:

- `page_content.py` owns commit search text and filtering.
- `BrowserState.visible_commits` delegates to page rendering code.
- `browser.py` uses the filtered list for numeric and Enter selection.

Page Content should render rows and empty states; it should not be the source of
truth for Commit Picker model rules.

## Goals / Non-Goals

**Goals:**

- Add `cr.ui.commit_picker` as the owner of Commit Picker filtering and
  filtered selection helpers.
- Keep filtering case-insensitive and based on commit hash, date, subject, and
  displayed change summary text.
- Let Browser State and Page Content share the same module-owned filtered list.
- Preserve existing command behavior and output text.

**Non-Goals:**

- No new user commands.
- No persistence of commit filter state.
- No Git subprocess calls in `cr.ui.commit_picker`.
- No movement of row formatting or terminal styling out of Page Content.

## Decisions

### Decision 1: Keep the module pure

`cr.ui.commit_picker` accepts `CommitSummary` values and strings, then returns
lists or selected items. It does not know about terminal style, browser pages,
Git subprocesses, frame layout, or command parsing.

### Decision 2: Rendering remains Page Content

Commit row text, filter count lines, and empty-state lines stay in
`cr.ui.page_content`, because they are main-content rendering rules. Page
Content calls the Commit Picker module for the filtered list instead of
re-owning matching.

### Decision 3: Browser owns state, not rules

`BrowserState` still owns the current `commit_filter_text`, `selected`, and
`commit_scroll` values. It delegates filtered list and filtered selection rules
to the Commit Picker module.

## Risks / Trade-offs

- This is mostly an architecture change, so the main risk is accidental behavior
  drift. Focused module tests plus existing Commit Picker integration tests cover
  matching, empty state, clearing, and numeric selection.
- A tiny module may look premature, but Commit Picker is already a named
  product surface. Keeping its rules out of rendering preserves the three-layer
  navigation model as more scope selectors are added.
