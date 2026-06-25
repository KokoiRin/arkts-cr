## ADDED Requirements

### Requirement: Browser copies Source File Page line anchors

The browser SHALL copy the current Source File Page target line as a repo-relative `path:line` anchor.

#### Scenario: Copy target source line

- **GIVEN** Source File Page is visible for `src/Foo.ets`
- **AND** its target line is `20`
- **WHEN** the user runs `copy line`
- **THEN** the browser SHALL copy `src/Foo.ets:20`
- **AND** it SHALL stay on Source File Page
- **AND** it SHALL preserve the source scroll and target line.

#### Scenario: Empty source state

- **GIVEN** Source File Page is visible without a source path
- **WHEN** the user runs `copy line`
- **THEN** the browser SHALL report that there is no source file line to copy
- **AND** it SHALL not call the clipboard command.

### Requirement: Browser advertises Source File Page copy line

The browser SHALL expose the Source File Page copy-line action in its contextual action bar.

#### Scenario: Source File Page action bar

- **GIVEN** Source File Page is visible
- **WHEN** the browser renders the contextual action bar
- **THEN** the bar SHALL include `copy line`.
