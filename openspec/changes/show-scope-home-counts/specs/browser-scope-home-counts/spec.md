## ADDED Requirements

### Requirement: Scope Home displays count overview
The browser SHALL show overview counts for directly countable Scope Home entries.

#### Scenario: Render changed-file scope counts
- **WHEN** Scope Home renders counts for Worktree, Staged, and All local changes
- **THEN** those entries SHALL include changed-file counts

#### Scenario: Render recent commit count
- **WHEN** Scope Home renders a count for Recent commits
- **THEN** the Recent commits entry SHALL include a commit count

### Requirement: Scope Home count loading is temporary UI state
The browser SHALL load Scope Home counts as temporary UI state without persisting them.

#### Scenario: Open Scope Home loads counts
- **WHEN** the user opens Scope Home
- **THEN** the browser SHALL sample scope counts before rendering the page

#### Scenario: Refresh Scope Home reloads counts
- **WHEN** the user refreshes while Scope Home is active
- **THEN** the browser SHALL reload the Scope Home counts

#### Scenario: Parameterized scopes stay count-free
- **WHEN** Scope Home renders Base ref or Explicit range entries
- **THEN** those entries SHALL remain parameterized command hints without live counts
