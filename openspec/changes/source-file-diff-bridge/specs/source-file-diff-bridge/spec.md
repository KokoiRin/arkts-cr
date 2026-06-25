# source-file-diff-bridge Specification

## ADDED Requirements

### Requirement: Open current Source File diff

The browser SHALL let Source File users open the current source path in File Detail for the active review scope.

#### Scenario: Source File current line exists in diff

- **GIVEN** Source File is open for `src/Foo.ets` at line 12
- **AND** `src/Foo.ets` is present in the current changed-file list
- **WHEN** the user runs `view diff`
- **THEN** the browser opens File Detail for `src/Foo.ets`
- **AND** scrolls to the rendered diff row for line 12 when visible.

#### Scenario: Source File path is not changed

- **GIVEN** Source File is open for `src/Unchanged.ets`
- **AND** `src/Unchanged.ets` is not present in the current changed-file list
- **WHEN** the user runs `view diff`
- **THEN** the browser stays on Source File
- **AND** reports that no diff is available in the current review scope.
