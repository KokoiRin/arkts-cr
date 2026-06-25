# source-outline-default-exports Specification

## ADDED Requirements

### Requirement: Recognize named default-exported containers

The lightweight source outline SHALL recognize named `export default class`, `export default struct`, and `export default interface` declarations as container symbols.

#### Scenario: Default-exported class

- **GIVEN** a source file contains `export default class FeedStore { hydrate() { ... } }`
- **WHEN** the outline is queried for a line inside `hydrate`
- **THEN** the symbol label is `class FeedStore > method hydrate`.

### Requirement: Recognize named default-exported functions

The lightweight source outline SHALL recognize named `export default function` declarations as function symbols.

#### Scenario: Default-exported function

- **GIVEN** a source file contains `export default function createStore() { ... }`
- **WHEN** the outline is queried for a line inside that function body
- **THEN** the symbol label is `function createStore`.
