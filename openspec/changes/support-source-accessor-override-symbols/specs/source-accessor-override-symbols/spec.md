# source-accessor-override-symbols Specification

## ADDED Requirements

### Requirement: Accessor and Override Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS override and accessor member declarations as method-like symbols.

#### Scenario: Override method label

- **GIVEN** a class or struct contains `override name(...) { ... }`
- **WHEN** cr asks for the symbol label at a line inside that method
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Getter and setter labels

- **GIVEN** a class or struct contains `get name() { ... }` or `set name(value) { ... }`
- **WHEN** cr asks for the symbol label at a line inside the accessor
- **THEN** the label includes the containing class/struct and `method name`

#### Scenario: Copy source symbol uses accessor range

- **GIVEN** Source File is focused on a line inside an accessor
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that accessor block
- **AND** it does not include adjacent methods outside the accessor
