# Task Problems Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Problems extracted from task output, problem navigation, filtering, grouping, and problem handoff.

## Requirements
### Requirement: Browser surfaces diagnostics facts in Problems UI and handoff

The browser SHALL surface extracted diagnostics facts in the Problems page and copy handoff text.

#### Scenario: Render compact diagnostic label

- **GIVEN** Task Problems page has a problem with severity `error` and code `TS2322`
- **WHEN** the page renders rows
- **THEN** the row SHALL include a compact `ERROR TS2322` label.

#### Scenario: Copy diagnostic facts

- **GIVEN** a task problem has severity, code, and message
- **WHEN** the user copies that problem
- **THEN** the copied handoff text SHALL include the location plus severity, code, and message facts.

### Requirement: Browser shows Task Problems page

The browser SHALL provide a Task Problems page for the current task output.

#### Scenario: Open Task Problems page

- **WHEN** the user runs `problems` or `task problems`
- **THEN** the browser SHALL enter Task Problems page
- **AND** the page SHALL participate in browser back/forward page history
- **AND** selection and scroll SHALL reset when the page opens

#### Scenario: Render Task Problems

- **GIVEN** current task output has extracted problems
- **WHEN** Task Problems page renders
- **THEN** it SHALL show each problem's path, line, optional column, and source output summary

#### Scenario: Render empty state

- **GIVEN** no current task exists or no problem anchors are extracted
- **WHEN** Task Problems page renders
- **THEN** it SHALL show an empty Task Problems state

### Requirement: Browser opens selected task problem

Task Problems page SHALL let users open the selected problem in their editor.

#### Scenario: Open selected problem

- **GIVEN** Task Problems page is visible with at least one problem selected
- **WHEN** the user presses Enter
- **THEN** the browser SHALL open the problem path at its line through the existing editor open action
- **AND** it SHALL keep Task Problems page visible

#### Scenario: Navigate task problems

- **GIVEN** Task Problems page is visible with multiple problems
- **WHEN** the user presses movement, paging, home, or end keys
- **THEN** the browser SHALL update problem selection and scroll within valid bounds

### Requirement: Browser copies selected task problem

The browser SHALL copy the selected Task Problems entry.

#### Scenario: Copy selected problem

- **GIVEN** Task Problems Page is visible with at least one problem selected
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL copy text containing the selected problem location and output summary
- **AND** the browser SHALL keep the current page, selection, scroll, Review Scope, and task state unchanged

#### Scenario: Copy selected problem empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problem`
- **THEN** the browser SHALL report that no task problem can be copied
- **AND** it SHALL NOT launch the clipboard command

### Requirement: Browser copies all task problems

The browser SHALL copy every current Task Problems entry.

#### Scenario: Copy all problems

- **GIVEN** current task output has extracted problems
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL copy a compact list containing every problem location and output summary in current output order

#### Scenario: Copy all problems empty state

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `copy problems`
- **THEN** the browser SHALL report that no task problems can be copied
- **AND** it SHALL NOT launch the clipboard command

### Requirement: Browser opens source preview from task problem

The browser SHALL provide a read-only Source File Page for the selected Task Problems entry.

#### Scenario: View selected problem source

- **GIVEN** Task Problems Page is visible with a selected problem
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL enter Source File Page for that problem's repo-local path
- **AND** it SHALL mark the problem line
- **AND** the previous Task Problems Page SHALL be reachable through browser back history

#### Scenario: Preserve external editor enter behavior

- **GIVEN** Task Problems Page is visible
- **WHEN** the user presses Enter
- **THEN** the browser SHALL continue to open the selected problem through the existing external editor action

#### Scenario: No selected problem

- **GIVEN** no current Task Problems are available
- **WHEN** the user runs `view problem`
- **THEN** the browser SHALL report that no task problem can be viewed
- **AND** it SHALL keep the current page visible

### Requirement: Browser enriches task problems with diagnostics facts

The browser SHALL enrich extracted task problems with optional severity, code, and message facts when common task-output text contains them.

#### Scenario: Extract severity code and message after anchor

- **GIVEN** current task output contains `src/Foo.ets:12:3 error TS2322: bad call`
- **AND** `src/Foo.ets` exists inside the repo
- **WHEN** task problems are extracted
- **THEN** the extracted problem SHALL have severity `error`
- **AND** code `TS2322`
- **AND** message `bad call`.

#### Scenario: Preserve unknown diagnostics

- **GIVEN** current task output contains a repo-local `path:line[:column]` anchor but no recognized severity or code
- **WHEN** task problems are extracted
- **THEN** the problem SHALL still be returned
- **AND** its diagnostic facts SHALL be empty
- **AND** its raw summary SHALL be preserved.

### Requirement: Browser filters Task Problems by severity

The browser SHALL filter current Task Problems by extracted severity without reordering them.

#### Scenario: Show error problems only

- **GIVEN** current task output has error and warning problems
- **WHEN** the user runs `problems errors`
- **THEN** the browser SHALL enter Task Problems page
- **AND** it SHALL show only problems whose severity is `error`
- **AND** it SHALL preserve task-output order among visible error problems.

#### Scenario: Clear severity filter

- **GIVEN** Task Problems page is filtered to warnings
- **WHEN** the user runs `problems all`
- **THEN** the browser SHALL show all current task problems.

### Requirement: Browser applies the visible problem filter to actions

The browser SHALL apply the active severity filter to selection, open, source preview, and copy actions.

#### Scenario: Copy visible filtered problems

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL include only visible error problems.

#### Scenario: Empty filtered state

- **GIVEN** current task output has problems but none match the active severity filter
- **WHEN** Task Problems page renders
- **THEN** it SHALL show a filter-specific empty state.

### Requirement: Browser shows Task Problems severity counts

The browser SHALL show compact severity counts for the currently visible Task Problems list.

#### Scenario: Render mixed severity counts

- **GIVEN** Task Problems page has visible errors, warnings, and unknown-severity problems
- **WHEN** the page renders
- **THEN** the header SHALL include counts for each visible severity bucket
- **AND** unknown-severity problems SHALL be counted as `unknown`.

#### Scenario: Filtered counts are visible counts

- **GIVEN** Task Problems page is filtered to errors
- **WHEN** the page renders
- **THEN** the header SHALL show the visible error count
- **AND** it SHALL not imply hidden warning or info totals.

### Requirement: Browser optionally sorts Task Problems by severity

The browser SHALL support an explicit severity sort mode for current Task Problems while keeping output order as the default.

#### Scenario: Sort by severity

- **GIVEN** Task Problems include warnings, errors, notes, and unknown-severity anchors
- **WHEN** the user runs `problems sort severity`
- **THEN** the browser SHALL show errors before warnings, info, notes, and unknown anchors
- **AND** it SHALL preserve task-output order within each severity bucket.

#### Scenario: Restore output order

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `problems sort output`
- **THEN** the browser SHALL show problems in task-output order.

### Requirement: Browser applies sort mode to visible problem actions

The browser SHALL apply the active sort mode to selection, open, source preview, and copy actions.

#### Scenario: Copy sorted visible problems

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the user runs `copy problems`
- **THEN** the copied handoff SHALL follow the sorted visible order.

#### Scenario: Header shows active sort

- **GIVEN** Task Problems page is sorted by severity
- **WHEN** the page renders
- **THEN** the header SHALL show that severity sort is active.

### Requirement: Browser copies selected problem context

The browser SHALL copy a focused Markdown context package for the currently selected task problem.

#### Scenario: Copy context from Task Problems

- **GIVEN** Task Problems has a selected problem whose source file can be read
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include the selected problem facts
- **AND** it SHALL include source context around the problem line
- **AND** it SHALL include same-file diff context when the file is changed in the current Review Scope.

#### Scenario: Copy context without matching diff

- **GIVEN** Task Problems has a selected problem whose file is not changed in the current Review Scope
- **WHEN** the user runs `copy problem context`
- **THEN** the copied text SHALL include problem and source context
- **AND** it SHALL state that there is no diff in the current review scope.

### Requirement: Problem context command is surfaced in TUI commands

The browser SHALL expose `copy problem context` through command parsing, command catalog, and contextual action bars for Task Problems and Source File Page.

#### Scenario: Command is visible

- **GIVEN** the user opens command help or a relevant page action bar
- **WHEN** the browser renders commands
- **THEN** `copy problem context` SHALL be discoverable.

### Requirement: Browser filters Task Problems by text

The browser SHALL support a page-local text filter over current Task Problems.

#### Scenario: Filter by query

- **GIVEN** Task Problems include multiple paths and messages
- **WHEN** the user runs `problems find Foo`
- **THEN** the browser SHALL show only problems whose path, location, summary, severity, code, or message contains `Foo` case-insensitively.

#### Scenario: Clear query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `problems clear find`
- **THEN** the browser SHALL clear the query and show problems using the remaining filters and sort mode.

### Requirement: Text filter composes with existing Task Problems view state

The browser SHALL apply the text query after severity filtering and before sorting.

#### Scenario: Actions use queried visible list

- **GIVEN** Task Problems has an active text query
- **WHEN** the user runs `copy problem`, `copy problems`, `view problem`, or opens a problem
- **THEN** the action SHALL use the queried visible list.

#### Scenario: Header shows query

- **GIVEN** Task Problems has an active text query
- **WHEN** the page renders
- **THEN** the header SHALL show the active query.

#### Scenario: Page history restores query

- **GIVEN** Task Problems has an active text query
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active query SHALL be restored.

### Requirement: Browser saves focused problem context

The browser SHALL support saving the same focused Problem Context Markdown used
by `copy problem context`.

#### Scenario: Save selected task problem context

- **GIVEN** Task Problems has a selected problem with readable source
- **WHEN** the user runs `save problem context tmp/problem.md`
- **THEN** the browser SHALL write focused problem context Markdown to
  `tmp/problem.md`
- **AND** report the saved path.

#### Scenario: Save source page context

- **GIVEN** Source File Page is open for a readable source file
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL write focused source/diff context to
  `.cr/handoff/problem-context.md`.

#### Scenario: No context available

- **GIVEN** neither Task Problems nor Source File Page has an active context
- **WHEN** the user runs `save problem context`
- **THEN** the browser SHALL report that there is no problem context to save.

### Requirement: Problem context save handles write failures

The browser SHALL report file-write failures without changing current page,
selection, task state, or review scope.

#### Scenario: Destination cannot be written

- **GIVEN** Problem Context Markdown can be generated
- **WHEN** saving to the requested destination fails
- **THEN** the browser SHALL report the destination path and the write error.

### Requirement: Browser groups Task Problems by file

The browser SHALL support page-local file grouping for current Task Problems.

#### Scenario: Enable file grouping

- **GIVEN** Task Problems has visible problems from multiple files
- **WHEN** the user runs `problems group file`
- **THEN** the Task Problems page SHALL render file headers before each file's
  problem rows
- **AND** the page header SHALL show that grouping is active.

#### Scenario: Disable grouping

- **GIVEN** Task Problems is grouped by file
- **WHEN** the user runs `problems group none`
- **THEN** the Task Problems page SHALL render the flat problem list.

### Requirement: Grouping composes with visible problem actions

Task Problems grouping SHALL NOT change the visible problem list used by
selection and problem actions.

#### Scenario: Actions use visible problem list

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user opens, views, copies, or saves context for a selected problem
- **THEN** the action SHALL use the same filtered, queried, and sorted visible
  `TaskProblem` list as flat mode.

#### Scenario: Page history restores grouping

- **GIVEN** Task Problems has grouping enabled
- **WHEN** the user navigates away and then returns through page history
- **THEN** the active grouping mode SHALL be restored.

### Requirement: Copy visible same-file task problems
The browser SHALL let users copy all currently visible Task Problems that share
the selected problem's file path.

#### Scenario: Copy problems for the selected file
- **GIVEN** Task Problems contains visible problems for `src/A.ets` and
  `src/B.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL include only visible problems from
  `src/A.ets`
- **AND** the browser SHALL preserve page, selection, filters, sort, grouping,
  Review Scope, and task state

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `copy file problems`
- **THEN** the copied Markdown SHALL use only the currently visible filtered
  problems for the selected file

#### Scenario: Empty Problems list
- **GIVEN** no Task Problems are currently visible
- **WHEN** the user runs `copy file problems`
- **THEN** the browser SHALL report that there are no task problems to copy

### Requirement: Jump between visible Task Problems files

The browser SHALL let users move the Task Problems selection between file groups in the current visible Problems list.

#### Scenario: Jump to next file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/A.ets`
- **WHEN** the user runs `next problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`
- **AND** the browser SHALL preserve page, filters, sort, grouping, Review Scope, and task state

#### Scenario: Jump to previous file
- **GIVEN** Task Problems contains visible problems for `src/A.ets`, `src/B.ets`, and `src/C.ets`
- **AND** the selected problem is in `src/C.ets`
- **WHEN** the user runs `prev problem file`
- **THEN** the selected problem SHALL move to the first visible problem in `src/B.ets`

#### Scenario: Respect current visible filters
- **GIVEN** Task Problems has severity or text filters active
- **WHEN** the user runs `next problem file` or `prev problem file`
- **THEN** file jumps SHALL consider only the currently visible filtered problems

#### Scenario: Edge file keeps selection
- **GIVEN** the selected problem is already in the first or last visible file group
- **WHEN** the user runs the corresponding previous or next file jump command
- **THEN** the selected problem SHALL stay unchanged
- **AND** the browser SHALL show an explanatory status message

### Requirement: Task Output can hand off first parsed problem context

The Task Output page SHALL allow `copy problem context` and
`save problem context [PATH]` to use the first visible parsed task problem.

#### Scenario: Copy first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL contain the selected problem facts
- **AND** it SHALL include source context for that problem line

#### Scenario: Save first problem context from task output

- **GIVEN** the browser is on Task Output
- **AND** the current task output contains a repo-local parseable problem
- **WHEN** the user runs `save problem context PATH`
- **THEN** the same first-problem context SHALL be written to PATH

### Requirement: Problem context includes task output excerpt for task problems

The browser SHALL include a compact Task Output excerpt centered on the
problem's original output line when focused Problem Context Markdown is
generated from a parsed task problem.

#### Scenario: Copy selected task problem context with output excerpt

- **GIVEN** Task Problems has a selected problem parsed from captured task output
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected problem, nearby source,
  same-file diff context when available, and a Task Output excerpt containing the
  selected problem output line.

#### Scenario: Save first task-output problem context with output excerpt

- **GIVEN** Task Output has at least one visible parsed problem
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include a Task Output excerpt centered on the
  first visible parsed problem's output line.

### Requirement: Source File problem context uses selected source ranges

The browser SHALL use the active Source File selected range when generating
Problem Context Markdown directly from Source File Page.

#### Scenario: Copy selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the selected source range
- **AND** it SHALL NOT include source lines outside that selected range.

#### Scenario: Save selected Source File problem context

- **GIVEN** Source File Page is open with an active selected source range
- **WHEN** the user runs `save problem context`
- **THEN** the saved Markdown SHALL include the selected source range.

### Requirement: Source File problem context preserves line context fallback

The browser SHALL keep the existing Source File line-context behavior when no
source range is selected.

#### Scenario: Copy unselected Source File problem context

- **GIVEN** Source File Page is open without a selected source range
- **WHEN** the user runs `copy problem context`
- **THEN** the copied Markdown SHALL include the configured source context radius
  around the current source line.

### Requirement: Problem Diff Navigation

The browser SHALL allow users to jump from the selected task problem to that file's diff when the file exists in the current review scope.

#### Scenario: Task Problems opens problem diff

- **GIVEN** the browser is on Task Problems
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for that path
- **AND** File Detail scrolls to the rendered row matching the problem line when available

#### Scenario: Task Output opens selected problem diff

- **GIVEN** the browser is on Task Output
- **AND** a task problem is selected
- **AND** the selected problem path exists in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser opens File Detail for the selected problem path

#### Scenario: Problem file has no current diff

- **GIVEN** the selected task problem path is not in the current review scope
- **WHEN** the user runs `view problem diff`
- **THEN** the browser does not navigate
- **AND** it reports that no diff is available for the problem location

### Requirement: Save current Task Problems list

The browser SHALL support saving the current visible Task Problems list as Markdown.

#### Scenario: Save default problems list

- **GIVEN** the current task output contains visible problems
- **WHEN** the user runs `save problems`
- **THEN** the current visible problem list is saved to `.cr/handoff/task-problems.md`
- **AND** the browser reports the number of saved problems.

### Requirement: Save selected-file Task Problems list

The browser SHALL support saving visible Task Problems for the selected problem's file.

#### Scenario: Save file-specific problems list

- **GIVEN** the current visible problem list contains multiple files
- **AND** the selected problem belongs to `src/Two.ets`
- **WHEN** the user runs `save file problems tmp/two-problems.md`
- **THEN** only visible problems from `src/Two.ets` are saved to `tmp/two-problems.md`
- **AND** the browser reports the number of saved problems and selected path.

### Requirement: Step between task problems from Source File

The browser SHALL let Source File users step to adjacent parsed task problems without returning to Task Output or Task Problems.

#### Scenario: Move to next problem source

- **GIVEN** Source File is showing the selected task problem source
- **WHEN** the user runs `next problem`
- **THEN** Source File updates to the next task problem path and line
- **AND** the page remains Source File.

#### Scenario: Move to previous problem source

- **GIVEN** Source File is showing a later task problem source
- **WHEN** the user runs `prev problem`
- **THEN** Source File updates to the previous task problem path and line
- **AND** the page remains Source File.

#### Scenario: Preserve page history

- **GIVEN** Source File was opened from Task Problems
- **WHEN** the user runs `next problem`
- **AND** then returns with `b`
- **THEN** the browser returns to Task Problems, not to the previous Source File problem.

### Requirement: Show current task problem on Source File

The browser SHALL show a compact current task problem label on Source File when the current source target corresponds to the selected parsed task problem.

#### Scenario: Matching task problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header includes a compact task problem label.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the Source File page renders
- **THEN** the header does not show that stale task problem label.

### Requirement: Copy current Source File task problem

The browser SHALL let Source File users copy the task problem represented by the current source target.

#### Scenario: Matching current problem

- **GIVEN** Source File is open at `src/Foo.ets:12`
- **AND** the selected parsed task problem is also `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser copies that task problem handoff text.

#### Scenario: Stale selected problem

- **GIVEN** Source File is open at `src/Foo.ets:20`
- **AND** the selected parsed task problem is `src/Foo.ets:12`
- **WHEN** the user runs `copy problem`
- **THEN** the browser does not copy the stale selected problem
- **AND** reports that no current source problem is available.

### Requirement: Save Current Task Problem

The browser SHALL support saving the current single task problem as Markdown.

#### Scenario: Save selected problem from Task Problems

- **GIVEN** Task Problems has visible parsed problems
- **AND** one problem is selected
- **WHEN** the user runs `save problem`
- **THEN** cr writes that problem to `.cr/handoff/task-problem.md`
- **AND** the browser stays on Task Problems with selection preserved

#### Scenario: Save selected problem to requested path

- **GIVEN** a current task problem exists
- **WHEN** the user runs `save problem tmp/problem.md`
- **THEN** cr writes that problem to `tmp/problem.md`

#### Scenario: Refuse stale Source File problem

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem to save

### Requirement: Copy Current Problem Diff

The browser SHALL copy a lightweight file diff snippet for the current task problem when that problem belongs to a file in the current review scope.

#### Scenario: Copy selected problem diff from Task Problems

- **GIVEN** Task Problems has a selected parsed problem
- **AND** the problem path exists in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr copies a file diff snippet for that path
- **AND** the browser stays on the current page with selection preserved

#### Scenario: Refuse problem diff outside review scope

- **GIVEN** the current task problem path is not in the current review scope
- **WHEN** the user runs `copy problem diff`
- **THEN** cr does not copy text
- **AND** reports that no diff exists for that problem in the current review scope

### Requirement: Save Current Problem Diff

The browser SHALL save the current problem's lightweight file diff snippet as Markdown.

#### Scenario: Save current problem diff to default path

- **GIVEN** a current task problem has a changed file in the current review scope
- **WHEN** the user runs `save problem diff`
- **THEN** cr writes `.cr/handoff/problem-diff.md`

#### Scenario: Refuse stale Source File problem diff

- **GIVEN** Source File is open
- **AND** the selected parsed problem no longer exactly matches the current source path and line
- **WHEN** the user runs `save problem diff`
- **THEN** cr does not write a file
- **AND** reports that there is no current source problem diff to save

### Requirement: Copy or save current File Detail row problem diff

The browser SHALL let File Detail users copy or save the changed-file diff for the task problem that exactly matches the current changed file and rendered new-file line.

#### Scenario: Current diff row problem diff is copied

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **AND** the globally selected task problem points at another file
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser copies the diff for `src/One.ets`
- **AND** it does not copy the globally selected problem's file diff.

#### Scenario: Current diff row problem diff is saved

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem diff tmp/problem-diff.md`
- **THEN** the browser writes the changed-file diff for `src/One.ets`.

#### Scenario: Current diff row has no matching problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** the task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem diff`
- **THEN** the browser refuses the command
- **AND** it does not fall back to any globally selected task problem.

### Requirement: Enrich File Detail problem context with current-row task problem

The browser SHALL include problem text and nearby task output in File Detail problem context handoff when the current rendered new-file line exactly matches a parsed task problem.

#### Scenario: Current File Detail row matches a task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section for `src/One.ets:4`
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Current File Detail row has no matching task problem

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output has no problem for `src/One.ets:4`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include any globally selected task problem.

#### Scenario: Save enriched File Detail problem context

- **GIVEN** File Detail is open for `src/One.ets`
- **AND** the current rendered row maps to new-file line 4
- **AND** task output contains a problem for `src/One.ets:4`
- **WHEN** the user runs `save problem context tmp/context.md`
- **THEN** the saved context includes the current problem, task output excerpt, source, and diff.

### Requirement: Enrich Source File problem context with current task problem

The browser SHALL include problem text and nearby task output in Source File problem context handoff when the current source line exactly matches the selected parsed task problem.

#### Scenario: Current Source File line matches a task problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes a `Problem` section
- **AND** includes a nearby `Task Output` excerpt
- **AND** includes the current source context and changed-file diff.

#### Scenario: Source selection is active

- **GIVEN** Source File is open for `src/Foo.ets` at line 5
- **AND** the selected task problem is exactly `src/Foo.ets:5`
- **AND** a source range is selected
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context includes the selected source range
- **AND** still includes the current problem and task output excerpt.

#### Scenario: Current Source File line has no matching problem

- **GIVEN** Source File is open for `src/Foo.ets` at line 8
- **AND** the selected task problem points at another line or file
- **WHEN** the user runs `copy problem context`
- **THEN** the copied context still includes source and diff
- **AND** it does not include the stale selected task problem.
