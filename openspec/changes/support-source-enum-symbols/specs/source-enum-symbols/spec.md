# source-enum-symbols Specification

## ADDED Requirements

### Requirement: Enum Symbol Recognition

The lightweight source outline SHALL recognize common TS/ArkTS enum declarations as block-level source symbols.

#### Scenario: Exported const enum label

- **GIVEN** a source file contains `export const enum FeedStatus { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum FeedStatus`

#### Scenario: Exported enum label

- **GIVEN** a source file contains `export enum LoadState { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum LoadState`

#### Scenario: Plain enum label

- **GIVEN** a source file contains `enum CardKind { ... }`
- **WHEN** cr asks for the symbol label at a line inside that enum body
- **THEN** the label is `enum CardKind`

#### Scenario: Modified enum name

- **GIVEN** a changed line belongs to an enum body
- **WHEN** cr maps changed lines to modified source symbols
- **THEN** the enum name is returned instead of `unknown`

#### Scenario: Copy source symbol uses enum range

- **GIVEN** Source File is focused on a line inside an enum body
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied source range contains that enum block
- **AND** it does not include the following top-level symbol
