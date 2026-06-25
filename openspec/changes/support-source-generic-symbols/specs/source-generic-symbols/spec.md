# source-generic-symbols Specification

## ADDED Requirements

### Requirement: Generic Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS generic function-like declarations as symbols.

#### Scenario: Generic method label

- **GIVEN** a class or struct contains `name<T>(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that method
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Generic function label

- **GIVEN** a source file contains `function name<T>(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that function
- **THEN** the label is `function name`

#### Scenario: Generic arrow function label

- **GIVEN** a source file contains `const name = <T>(...) => { ... }`
- **WHEN** cr asks for the symbol label at a line inside that arrow function
- **THEN** the label is `function name`

#### Scenario: Copy source symbol uses generic method range

- **GIVEN** Source File is focused on a line inside a generic method
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that generic method block
- **AND** it does not include adjacent methods outside the generic method
