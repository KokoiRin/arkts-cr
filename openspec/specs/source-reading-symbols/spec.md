# Source Reading and Symbols Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Read-only source preview, source selection, source context, and lightweight symbol recognition.

## Requirements
### Requirement: Include current source symbol in source handoff

The browser SHALL include the current symbol label in copied source Markdown when a label is available.

#### Scenario: Copy source context with symbol
- **GIVEN** Source File Page target line belongs to a parsed symbol
- **WHEN** the user runs `copy source` without a selected range
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the existing source context line window unchanged

#### Scenario: Copy selected source range with symbol
- **GIVEN** Source File Page has an active source selection
- **AND** the target line belongs to a parsed symbol
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include the current symbol label
- **AND** it SHALL keep the selected line range unchanged

### Requirement: Browser renders source file page

Source File Page SHALL render source text with line numbers.

#### Scenario: Render target line

- **GIVEN** Source File Page has a readable repo-local text file and target line
- **WHEN** the page renders
- **THEN** it SHALL show the repo-relative path
- **AND** it SHALL show line-numbered source rows
- **AND** it SHALL mark the target line

#### Scenario: Scroll source file

- **GIVEN** Source File Page is visible
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update source scroll within valid bounds

#### Scenario: Render unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the page renders
- **THEN** it SHALL show a clear source-file empty/error state

### Requirement: Browser searches Source File Page

The browser SHALL search text within the current Source File Page.

#### Scenario: Find source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL search source lines case-insensitively
- **AND** it SHALL move the Source File Page target line to the first matching source line
- **AND** it SHALL keep Review Scope, task state, and page history unchanged

#### Scenario: Missing source text

- **GIVEN** Source File Page is visible with a readable source file
- **WHEN** the user runs `find TEXT` with no matches
- **THEN** the browser SHALL report no matches
- **AND** it SHALL keep the current source target line and scroll unchanged

### Requirement: Browser repeats Source File Page search

The browser SHALL repeat Source File Page searches using page-local query state.

#### Scenario: Next source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL move to the next matching source line with wraparound

#### Scenario: Previous source match

- **GIVEN** Source File Page has a previous non-empty source find query
- **WHEN** the user runs `prev match`
- **THEN** the browser SHALL move to the previous matching source line with wraparound

#### Scenario: No source query

- **GIVEN** Source File Page has no previous source find query
- **WHEN** the user runs `next match`
- **THEN** the browser SHALL ask the user to enter text to find

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

### Requirement: Browser copies Source File Page source context

The browser SHALL copy a compact source context snippet for the current Source File Page target line.

#### Scenario: Copy source context

- **GIVEN** Source File Page is visible for `src/Foo.ets`
- **AND** its target line is `20`
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL copy Markdown headed by `src/Foo.ets:20`
- **AND** the copied code block SHALL include nearby source lines with line numbers
- **AND** the target line SHALL be marked.

#### Scenario: Empty source state

- **GIVEN** Source File Page is visible without a source path
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL report that there is no source file to copy
- **AND** it SHALL not call the clipboard command.

### Requirement: Browser advertises source context copy

The browser SHALL expose `copy source` in command help and Source File Page actions.

#### Scenario: Source File Page action bar

- **GIVEN** Source File Page is visible
- **WHEN** the contextual action bar renders
- **THEN** it SHALL include `copy source`.

### Requirement: Source File Page copies configurable source context

The browser SHALL let users configure how many source lines around the current Source File Page target line are included by `copy source`.

#### Scenario: Default context remains unchanged

- **GIVEN** the user has not changed Source File Page context
- **WHEN** the user runs `copy source`
- **THEN** the copied snippet SHALL include up to three lines before and after the target line.

#### Scenario: User sets source context radius

- **GIVEN** the user is on Source File Page
- **WHEN** the user runs `source context 1`
- **THEN** future `copy source` output SHALL include up to one line before and after the target line.

#### Scenario: Source context is visible

- **GIVEN** Source File Page is rendered
- **WHEN** the source context radius is active
- **THEN** the page SHALL display the current context radius.

### Requirement: Source context radius is page-local browser state

The browser SHALL keep Source File Page context radius in page-local browser state.

#### Scenario: Page history restores source context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the user navigates away and then returns through page history
- **THEN** Source File Page SHALL restore source context radius 8.

#### Scenario: Opening a new source file resets context

- **GIVEN** Source File Page has source context radius 8
- **WHEN** the browser opens a different Source File Page from Task Problems
- **THEN** the new Source File Page SHALL use the default radius.

### Requirement: Source File Page selects a source range

The browser SHALL support a page-local line range selection in Source File Page.

#### Scenario: Select range

- **GIVEN** Source File Page is open for a repo-local source file
- **WHEN** the user runs `source select 4 8`
- **THEN** the page SHALL record the selected range `4-8`
- **AND** render the active selection in the Source File Page header and rows.

#### Scenario: Normalize reversed range

- **GIVEN** Source File Page is open
- **WHEN** the user runs `source select 8 4`
- **THEN** the page SHALL record the selected range `4-8`.

#### Scenario: Clear range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user runs `source clear selection`
- **THEN** the page SHALL clear the selected range.

### Requirement: Source File Page mark-based range selection
The browser SHALL let users select a Source File Page range by marking the
current source target line and selecting to the later current target line.

#### Scenario: Mark current line and select to another current line
- **GIVEN** the browser is on Source File Page at line 5
- **WHEN** the user runs `source mark`
- **AND** the current source target line later becomes 9
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 5 through 9
- **AND** `copy source` SHALL keep using the selected range behavior

#### Scenario: Selection works regardless of direction
- **GIVEN** the browser is on Source File Page at line 9 with an active mark
  from line 5
- **WHEN** the current source target line later becomes 3
- **AND** the user runs `source select to`
- **THEN** the Source File Page selection SHALL be lines 3 through 5

#### Scenario: Mark is page-local
- **GIVEN** the browser has a source mark in Source File Page
- **WHEN** the user navigates away and returns through page history
- **THEN** the source mark SHALL be restored
- **WHEN** the user opens a different source file
- **THEN** the source mark SHALL be cleared

### Requirement: Show current source symbol in Source File Page

The browser SHALL show a best-effort current symbol label in Source File Page when the target line belongs to a parsed source symbol.

#### Scenario: Show enclosing method label
- **GIVEN** Source File Page is showing a repo-local source file
- **AND** the target line is inside a parsed class method
- **WHEN** the page renders
- **THEN** the header SHALL include a readable symbol label for the enclosing method and container

#### Scenario: Omit missing symbol label
- **GIVEN** Source File Page is showing a source line outside parsed symbols
- **WHEN** the page renders
- **THEN** the header SHALL omit the symbol label rather than showing an unknown placeholder

### Requirement: Keep source symbol hints lightweight

Current source symbol hints MUST NOT introduce language-server dependencies, syntax-aware range expansion, source editing, workspace persistence, or Source File Page state fields.

#### Scenario: Symbol lookup is informational
- **GIVEN** source symbol parsing fails to identify an enclosing symbol
- **WHEN** Source File Page renders or copies source
- **THEN** source preview and copy behavior SHALL continue without a symbol label

### Requirement: Source File can select the current symbol

The Source File page SHALL provide a command that selects the innermost
best-effort outline symbol containing the current source line.

#### Scenario: Select current method symbol

- **GIVEN** the browser is on Source File for a repo-local ArkTS/ETS/TS file
- **AND** the current line is inside a method parsed by the existing outline module
- **WHEN** the user runs `source select symbol`
- **THEN** the source selection SHALL become that method's start and end line
- **AND** the page SHALL redraw with the selected range visible
- **AND** the status SHALL include the selected symbol label and range

#### Scenario: No source page is open

- **GIVEN** the browser is not on Source File
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL tell the user to open a source file first

#### Scenario: No symbol contains the current line

- **GIVEN** the browser is on Source File
- **AND** no outline symbol contains the current source line
- **WHEN** the user runs `source select symbol`
- **THEN** no source selection SHALL be changed
- **AND** the status SHALL say no source symbol exists at the current line

### Requirement: File Detail can open Source File at current new line

The File Detail page SHALL provide a command that opens the Source File page at
the current rendered new-file line.

#### Scenario: View source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL open Source File for the current changed file
- **AND** the Source File target line SHALL be the mapped new-file line
- **AND** Back SHALL return to the same File Detail scroll

#### Scenario: Current row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row is a deleted-only row or another row without a new-file line
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL remain on File Detail
- **AND** the status SHALL say there is no current new-file line

#### Scenario: Not on File Detail

- **GIVEN** the browser is not on File Detail
- **WHEN** the user runs `view source`
- **THEN** the browser SHALL stay on the current page
- **AND** the status SHALL tell the user to open a file detail first

### Requirement: File Detail can copy source context

The File Detail page SHALL allow `copy source` to copy Source File-style
Markdown for the current rendered new-file line.

#### Scenario: Copy source from current diff row

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row maps to a new-file line
- **WHEN** the user runs `copy source`
- **THEN** copied Markdown SHALL be anchored to the current changed file and mapped line
- **AND** it SHALL include source context around that line
- **AND** it SHALL include best-effort symbol metadata when available
- **AND** the browser SHALL remain on File Detail

#### Scenario: Current diff row has no new-file line

- **GIVEN** the browser is on File Detail
- **AND** the current rendered row has no new-file line
- **WHEN** the user runs `copy source`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say there is no current new-file line

### Requirement: Source File copy source remains unchanged

The existing Source File `copy source` behavior SHALL continue to copy selected
ranges or target-line context as before.

#### Scenario: Copy source from Source File

- **GIVEN** the browser is on Source File
- **WHEN** the user runs `copy source`
- **THEN** the existing Source File copy behavior SHALL be preserved

### Requirement: Source File can copy current symbol

Source File SHALL provide `copy source symbol` to copy the innermost best-effort
symbol range containing the current source line.

#### Scenario: Copy current Source File method

- **GIVEN** the browser is on Source File
- **AND** the current line is inside a parsed method
- **WHEN** the user runs `copy source symbol`
- **THEN** copied Markdown SHALL contain that method's source range
- **AND** it SHALL include `Symbol: ...` metadata
- **AND** it SHALL not change the current source selection

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

### Requirement: Source File supports adjacent symbol navigation

The browser SHALL support jumping to adjacent recognized source symbols from
Source File Page.

#### Scenario: Jump to next symbol

- **GIVEN** Source File Page is open on a line before another recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the current source line SHALL move to the next symbol start line
- **AND** the page SHALL remain Source File Page.

#### Scenario: Jump to previous symbol

- **GIVEN** Source File Page is open on a line after a recognized symbol
- **WHEN** the user runs `prev symbol`
- **THEN** the current source line SHALL move to the previous symbol start line
- **AND** the page SHALL remain Source File Page.

### Requirement: Source symbol navigation handles empty and boundary states

The browser SHALL report clear status messages without changing the current
source line when adjacent source-symbol navigation cannot move.

#### Scenario: No next symbol

- **GIVEN** Source File Page is open at or after the final recognized symbol
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that it is already at the last symbol
- **AND** preserve the current source line.

#### Scenario: No source symbols

- **GIVEN** Source File Page is open for a readable file with no recognized
  symbols
- **WHEN** the user runs `next symbol`
- **THEN** the browser SHALL report that no source symbols were found
- **AND** preserve the current source line.

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

### Requirement: Save current source context

The browser SHALL support saving the same Markdown handoff produced by `copy source`.

#### Scenario: Save selected Source File range

- **GIVEN** Source File has an active selected range
- **WHEN** the user runs `save source`
- **THEN** the selected source range is saved to `.cr/handoff/source.md`
- **AND** the current target line remains marked in the saved Markdown.

### Requirement: Save current source symbol

The browser SHALL support saving the same Markdown handoff produced by `copy source symbol`.

#### Scenario: Save File Detail source symbol

- **GIVEN** File Detail is focused on a changed source line inside a recognized symbol
- **WHEN** the user runs `save source symbol tmp/render.md`
- **THEN** the current symbol range is saved to `tmp/render.md`
- **AND** the browser remains on File Detail without mutating Source File selection.

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

### Requirement: Open current File Detail source symbol

The browser SHALL let File Detail users open the current new-file source line in Source File and select the enclosing lightweight source symbol.

#### Scenario: Current diff row is inside a source symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to new-file line 12
- **AND** line 12 is inside a recognized function or method
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File for `src/Foo.ets` at line 12
- **AND** selects the recognized enclosing symbol range.

#### Scenario: Current diff row has no new-file line

- **GIVEN** File Detail is open for a deleted-only or metadata row
- **WHEN** the user runs `view source symbol`
- **THEN** the browser stays on File Detail
- **AND** reports that there is no current new-file line.

#### Scenario: Current source line has no recognized symbol

- **GIVEN** File Detail is open for `src/Foo.ets`
- **AND** the current rendered row maps to a new-file line
- **AND** that source line is not inside a recognized lightweight source symbol
- **WHEN** the user runs `view source symbol`
- **THEN** the browser opens Source File at that line
- **AND** reports that no source symbol is available without creating a fake selection.

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

### Requirement: Browser handles unreadable source find

The browser SHALL handle find on unreadable Source File Page state.

#### Scenario: Find unreadable source

- **GIVEN** Source File Page references a missing or unreadable file
- **WHEN** the user runs `find TEXT`
- **THEN** the browser SHALL report the source-file error without crashing

### Requirement: Browser copies source page context

The browser SHALL copy a focused Markdown context package from Source File Page.

#### Scenario: Copy context from Source File Page

- **GIVEN** Source File Page is open on a repo-local source file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the source target anchor
- **AND** it SHALL include source context using the active source context radius
- **AND** it SHALL include same-file diff context when available.

### Requirement: Source range composes with source copy

The browser SHALL make `copy source` copy the active selected source range when
a Source File Page selection exists.

#### Scenario: Copy selected range

- **GIVEN** Source File Page has selected range `4-8`
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL include only source lines 4 through 8
- **AND** report that the selected source range was copied.

#### Scenario: Copy source context without selection

- **GIVEN** Source File Page has no selected range
- **WHEN** the user runs `copy source`
- **THEN** the browser SHALL keep the existing context-radius copy behavior.

### Requirement: Source range follows source page lifecycle

The browser SHALL treat range selection as Source File Page local state.

#### Scenario: New source file clears range

- **GIVEN** Source File Page has an active selected range
- **WHEN** another Source File Page is opened
- **THEN** the active selected range SHALL be cleared.

#### Scenario: Page history restores range

- **GIVEN** Source File Page has an active selected range
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active selected range SHALL be restored.

### Requirement: Selected symbol range composes with copy source

The command SHALL reuse the existing Source File selection behavior so that a
subsequent `copy source` copies the selected symbol range with symbol metadata.

#### Scenario: Copy selected symbol

- **GIVEN** `source select symbol` selected the current method range
- **WHEN** the user runs `copy source`
- **THEN** the copied Markdown SHALL contain the selected range header
- **AND** it SHALL include the existing `Symbol: ...` metadata
- **AND** it SHALL not include lines outside the selected symbol range

### Requirement: Missing symbol is reported

When no best-effort source symbol contains the target line, the command SHALL
not copy text and SHALL tell the user no source symbol exists at the current line.

#### Scenario: Copy symbol outside any parsed symbol

- **GIVEN** the browser is on Source File
- **AND** the current line is not inside any parsed symbol
- **WHEN** the user runs `copy source symbol`
- **THEN** no text SHALL be copied
- **AND** the status SHALL say no source symbol exists at the current line

### Requirement: Source page context remains source focused

The browser SHALL NOT add a Task Output excerpt to Problem Context Markdown
generated directly from Source File Page unless an active task problem target is
used.

#### Scenario: Copy source page problem context

- **GIVEN** Source File Page is open for a source file and line
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include source and diff context
- **AND** it SHALL NOT include a Task Output section.
