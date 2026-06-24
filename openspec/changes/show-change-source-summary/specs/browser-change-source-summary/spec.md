## ADDED Requirements

### Requirement: Browser displays local source counts
The browser SHALL display a Changed Files source summary when the rendered changes include local source facts.

#### Scenario: Show source summary for local changes
- **WHEN** Changed Files renders visible changes with `FileChange.source` values of `staged`, `unstaged`, or `mixed`
- **THEN** Changed Files output SHALL include counts for the present local source values

#### Scenario: Omit absent source values
- **WHEN** Changed Files renders local changes with only one or two present source values
- **THEN** the source summary SHALL omit zero-count source values

### Requirement: Browser omits source summary without local source facts
The browser SHALL omit the Changed Files source summary when rendered changes do not include local source facts.

#### Scenario: Comparison scope without source facts
- **WHEN** Changed Files renders changes whose `FileChange.source` values are empty
- **THEN** Changed Files output SHALL NOT include a source summary
