## ADDED Requirements

### Requirement: Source outline recognizes field arrow-function symbols

The source outline SHALL recognize class, struct, and interface field
arrow-function declarations as method-like symbols when they appear inside a
container.

#### Scenario: Label line inside a field arrow function

- **GIVEN** an ArkTS source file with `private onTap = () => { ... }` inside a
  struct
- **WHEN** the current line is inside the arrow-function body
- **THEN** the symbol label SHALL include `struct ... > method onTap`.

#### Scenario: Copy field arrow function source symbol

- **GIVEN** Source File Page is open on a line inside a field arrow function
- **WHEN** the user runs `copy source symbol`
- **THEN** the copied Markdown SHALL include the full field arrow-function range
- **AND** the symbol metadata SHALL name the field arrow function.

### Requirement: Top-level arrow functions remain function symbols

The source outline SHALL continue to recognize top-level `const name = () =>`
declarations as function symbols.

#### Scenario: Label line inside a top-level arrow function

- **GIVEN** a top-level `const load = () => { ... }` declaration
- **WHEN** the current line is inside the arrow-function body
- **THEN** the symbol label SHALL include `function load`.
