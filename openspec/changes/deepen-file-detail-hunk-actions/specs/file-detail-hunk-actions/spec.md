## ADDED Requirements

### Requirement: File Detail hunk workflows are selected-file actions
The browser SHALL route selected File Detail hunk open/copy workflows through
the selected-file action module while preserving current behavior.

#### Scenario: Open selected hunk through selected-file action
- **WHEN** the browser opens the active File Detail hunk
- **THEN** the selected-file action module SHALL resolve the hunk line from the
  rendered File Detail lines
- **AND** it SHALL invoke the configured editor action for that file and line
- **AND** it SHALL return the same success and failure messages as before

#### Scenario: Copy selected hunk through selected-file action
- **WHEN** the browser copies the active File Detail hunk
- **THEN** the selected-file action module SHALL resolve the active rendered
  hunk block from the rendered File Detail lines
- **AND** it SHALL copy the same Markdown hunk text as before
- **AND** it SHALL return the same success and failure messages as before

#### Scenario: Browser keeps page ownership
- **WHEN** `open hunk` or `copy hunk` is executed outside File Detail or without
  a visible selected file
- **THEN** the browser SHALL keep those page/selection checks in browser command
  execution
- **AND** it SHALL NOT ask the selected-file action module to load browser
  state or render file content
