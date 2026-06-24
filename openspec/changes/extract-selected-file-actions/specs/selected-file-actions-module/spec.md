## ADDED Requirements

### Requirement: Selected File Actions Module Ownership

`cr browse` selected-file action workflow MUST be owned by a dedicated UI module rather than browser command execution.

#### Scenario: Browser executes selected-file workflow through a module

- **GIVEN** a parsed browser action such as open, copy path, copy anchor, reveal, note, copy prompt file, or save prompt file
- **WHEN** the action depends on the current selected changed file or current visible changed-file set
- **THEN** selected-file path/line/note/prompt workflow is performed by the Selected File Actions module
- **AND** BrowserCommandExecutor remains responsible for routing parsed commands and placing returned messages into the browser UI
- **AND** platform subprocess details remain owned by `cr.ui.file_actions`
- **AND** prompt Markdown rendering remains owned by `cr.review.prompt`

### Requirement: Selected File Actions Behavior Preservation

Extracting Selected File Actions MUST preserve existing user-visible behavior.

#### Scenario: Existing selected-file actions keep messages and side effects

- **GIVEN** the same browser state, args, selected file, configured open/copy/reveal commands, review notes, and prompt save path as before extraction
- **WHEN** open, copy path, copy anchor, reveal, note set/clear, copy prompt, copy prompt file, save prompt, or save prompt file is executed
- **THEN** user-facing messages, clipboard/editor/reveal invocation, first-line anchor calculation, review-note filtering, workspace sync, file cache invalidation, prompt save path behavior, and empty-state messages remain behaviorally equivalent
- **AND** raw-key redraw/status behavior remains owned by BrowserCommandExecutor and is unchanged
