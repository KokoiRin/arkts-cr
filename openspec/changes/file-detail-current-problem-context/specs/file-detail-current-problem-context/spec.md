# file-detail-current-problem-context Specification

## ADDED Requirements

### Requirement: Enrich File Detail problem context with current-row task problem

The browser SHALL include problem text and nearby task output in File Detail problem context handoff when the current rendered new-file line exactly matches a parsed task problem.

#### Scenario: Current File Detail row matches a task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section for `src/One.ets:4`
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Current File Detail row has no matching task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include any globally selected task problem.

#### Scenario: Save enriched File Detail problem context

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem context tmp/context.md`
- **THEN** the saved context includes the current problem, task output excerpt, source, and diff.
