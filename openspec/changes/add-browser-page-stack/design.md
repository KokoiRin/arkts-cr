## Context

`BrowserNavigation` currently owns page transition intent and small local resets, but it explicitly does not keep a real history stack. `ReviewWorkspace` owns active review scope and changed-file data. The page stack should sit with navigation, not with workspace loading or rendering.

## Goals / Non-Goals

**Goals:**

- Track in-session page history for browser page transitions.
- Preserve local page state needed for useful back/forward: page, selected file, list scroll, file scroll, command selection/filter/scroll, scope selection, and commit selection/scroll.
- Make `back` pop history and `forward` restore the page just left.
- Clear forward history after a new normal navigation branch.

**Non-Goals:**

- Do not persist the full page stack to `.git/cr/browse-state.json`.
- Do not move Review Scope loading out of `ReviewWorkspace`.
- Do not implement browser tabs, multi-window navigation, or route URLs.
- Do not change task panel behavior.

## Decisions

### 1. Stack entries are navigation snapshots

Each entry stores lightweight UI navigation state, not Git data. The changed-file list and selected commit objects remain owned by `BrowserState` / `ReviewWorkspace`.

### 2. Navigation module owns stack operations

`BrowserNavigation` records snapshots on page-changing operations. The browser executor should call navigation methods, not manually push history.

### 3. Back and forward are explicit

`back` pops from the back stack into the current state and pushes the previous current snapshot to the forward stack. `forward` does the reverse. New navigation clears the forward stack.

### 4. Scope switching resets history

Changing Review Scope is a higher-level workspace change. The page stack belongs inside a scope; scope switching should reset it to avoid returning to stale pages from another scope.

## Risks / Trade-offs

- [Risk] Recording too much state can duplicate workspace ownership. -> Mitigation: store only page-local UI fields, not changes or scope data.
- [Risk] Existing hierarchy-aware back behavior may change. -> Mitigation: keep fallback behavior when the stack is empty.
- [Risk] More navigation state increases test surface. -> Mitigation: test through `BrowserNavigation` and `BrowserCommandExecutor` behavior, not implementation internals.
