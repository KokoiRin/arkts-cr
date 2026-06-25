# source-declaration-symbols Specification

## ADDED Requirements

### Requirement: Declaration Source Symbol Recognition

The lightweight source outline SHALL recognize common ArkTS/TS declaration-only function-like members without letting them capture unrelated following code.

#### Scenario: Abstract method label

- **GIVEN** a class contains `abstract load(): Promise<void>;`
- **WHEN** cr asks for the symbol label at that declaration line
- **THEN** the label includes the containing class and `method load`.

#### Scenario: Abstract accessor label

- **GIVEN** a class contains `abstract get title(): string;`
- **WHEN** cr asks for the symbol label at that declaration line
- **THEN** the label includes the containing class and `method title`.

#### Scenario: Declaration-only member does not capture following method

- **GIVEN** a class contains a declaration-only member followed by a concrete method
- **WHEN** cr asks for the symbol label inside the concrete method
- **THEN** the label resolves to the concrete method, not the earlier declaration-only member.

#### Scenario: Interface method declarations remain one-line symbols

- **GIVEN** an interface contains multiple method declarations
- **WHEN** cr asks for the symbol label at the second declaration
- **THEN** the label resolves to the second declaration, not the first one.
