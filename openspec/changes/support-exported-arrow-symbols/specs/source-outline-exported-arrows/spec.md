# source-outline-exported-arrows Specification

## ADDED Requirements

### Requirement: Recognize exported arrow function declarations

The lightweight source outline SHALL recognize top-level exported `const`, `let`, and `var` arrow declarations as function symbols.

#### Scenario: Exported const arrow

- **GIVEN** a source file contains `export const loadModel = async <T>(value: T) => { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function loadModel`.

#### Scenario: Exported let arrow

- **GIVEN** a source file contains `export let normalize = (value: string) => { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function normalize`.
