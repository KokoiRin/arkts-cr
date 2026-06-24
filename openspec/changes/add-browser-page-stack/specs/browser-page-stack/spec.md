## ADDED Requirements

### Requirement: Browser records page history
The browser SHALL record in-session page transitions as navigation history.

#### Scenario: Open file detail then go back
- **WHEN** the user opens File Detail from Changed Files
- **AND** then runs `back`
- **THEN** the browser SHALL return to the prior Changed Files state including selected file and list scroll

#### Scenario: Open command palette then go back
- **WHEN** the user opens Command Palette from another browser page
- **AND** then runs `back`
- **THEN** the browser SHALL return to the page that opened Command Palette

### Requirement: Browser supports forward navigation
The browser SHALL provide a `forward` command that restores the page most recently left by `back`.

#### Scenario: Back then forward
- **WHEN** the user opens File Detail, runs `back`, and then runs `forward`
- **THEN** the browser SHALL return to File Detail with its local scroll state restored

#### Scenario: New branch clears forward history
- **WHEN** the user goes back and then opens a different page
- **THEN** the browser SHALL clear forward history

### Requirement: Scope switching resets page history
The browser SHALL treat page history as scoped to the current Review Scope.

#### Scenario: Switch review scope
- **WHEN** the user switches Review Scope
- **THEN** the browser SHALL reset back/forward page history

### Requirement: Existing fallback back behavior remains
The browser SHALL keep the existing hierarchy-aware fallback when no page history is available.

#### Scenario: Back with no history
- **WHEN** no page history is available
- **THEN** `back` SHALL preserve the existing fallback behavior for File Detail, Command Palette, Scope Home, selected commit scopes, and Changed Files
