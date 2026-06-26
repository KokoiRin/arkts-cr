# Test Taxonomy

This document classifies the current test suite from two angles:

1. Test-pyramid scope: how many boundaries the test crosses.
2. Product semantics: whether the test reads like user-visible behavior.

The category tables below are mutually exclusive at file level: each file is assigned to the role it mostly serves.

Current snapshot:

- Test files: 130
- Test cases: 569
- Pure or near-pure unit tests: 20 files, 85 cases
- Cross-module integration tests: 24 files, 135 cases
- Product behavior component tests: 86 files, 349 cases

Pyramid health view:

- Unit or near-unit: 85 cases
- Product behavior component tests: 349 cases
- Cross-module integration, including CLI workflows: 135 cases
- CLI workflow tests inside the integration layer: 42 cases

This is not a healthy classic pyramid yet. The suite is currently heavy in behavior/component tests and light in unit tests. The product behavior tests are valuable because they describe what the tool should do, but many of them assert behavior through `BrowserCommandExecutor`, page rendering, or browser state instead of smaller domain modules.

## Category Definitions

### Pure Or Near-Pure Unit Tests

These tests describe deterministic logic in one small module or function family. They should stay compact and should usually not know about the browser loop, command executor, subprocess lifecycle, or full UI state.

They are useful as implementation guardrails, but they are not the main product manual.

### Cross-Module Integration Tests

These tests exercise multiple modules together: CLI entrypoints, browser loop redraw behavior, task runtime, persistence, git scopes, process lifecycle, or workspace state.

They are regression guardrails. They often protect bugs that are hard to see from a single function test.

### Product Behavior Component Tests

These tests directly describe user-visible behavior: selecting commits, opening files, navigating file detail/source/task pages, copying or saving context, running tasks, changing filters, using command palette actions, and seeing page content.

They are semantic cases, but most are not end-to-end tests. They are closer to component tests around browser state, command execution, and page rendering. They should read like the product specification, while the underlying parsing, selection, filtering, and formatting rules should move down into unit tests where possible.

### End-To-End Boundary

The closest end-to-end tests are the CLI workflow files that invoke the command as a user would. They currently account for 7 files and 42 cases:

- `test_cli_browser_entry_navigation.py`
- `test_cli_browser_scope_workflows.py`
- `test_cli_browser_task_workflows.py`
- `test_cli_browser_workspace_workflows.py`
- `test_cli_review_filtering.py`
- `test_cli_review_output.py`
- `test_cli_review_scopes.py`

These should stay few. They should cover the main user journeys, not every empty state or formatting variant.

## Pure Or Near-Pure Unit Tests

| Cases | File | Main Meaning |
| ---: | --- | --- |
| 3 | `test_browser_commands.py` | Parses browser commands. |
| 4 | `test_browser_input.py` | Normalizes browser input. |
| 9 | `test_browser_navigation.py` | Computes browser navigation movement. |
| 5 | `test_command_catalog.py` | Defines command catalog metadata. |
| 10 | `test_file_detail_navigation.py` | Computes file-detail navigation targets. |
| 7 | `test_handoff.py` | Renders handoff text. |
| 2 | `test_hunks.py` | Parses review hunks. |
| 6 | `test_outline_parsing.py` | Parses source outline and changed symbols. |
| 8 | `test_outline_symbol_labels.py` | Finds the current source symbol label. |
| 2 | `test_packaging.py` | Verifies packaging metadata. |
| 1 | `test_problem_context.py` | Formats problem context. |
| 3 | `test_purpose.py` | Derives source purpose from outline. |
| 1 | `test_review_changes.py` | Summarizes review changes. |
| 1 | `test_review_data.py` | Builds review data. |
| 1 | `test_snippet.py` | Renders diff snippets. |
| 5 | `test_source_file.py` | Reads and slices source files. |
| 1 | `test_summary.py` | Renders summary text. |
| 8 | `test_task_problem_extraction.py` | Extracts diagnostics from task output. |
| 4 | `test_text_search.py` | Searches text in page content. |
| 4 | `test_tree.py` | Renders changed-file trees. |

## Cross-Module Integration Tests

| Cases | File | Main Meaning |
| ---: | --- | --- |
| 4 | `test_browser_feedback.py` | Browser loop feedback and redraw behavior. |
| 1 | `test_browser_main_loop.py` | Browser main loop wiring. |
| 3 | `test_browser_redraw.py` | Redraw behavior across browser states. |
| 6 | `test_cli_browser_entry_navigation.py` | CLI browser entry navigation workflows. |
| 7 | `test_cli_browser_scope_workflows.py` | CLI scope workflows. |
| 2 | `test_cli_browser_task_workflows.py` | CLI task workflows. |
| 6 | `test_cli_browser_workspace_workflows.py` | CLI workspace workflows. |
| 8 | `test_cli_review_filtering.py` | CLI review filtering behavior. |
| 6 | `test_cli_review_output.py` | CLI review output behavior. |
| 7 | `test_cli_review_scopes.py` | CLI review scope handling. |
| 10 | `test_frame.py` | Full browser frame rendering. |
| 4 | `test_git_scopes.py` | Git scope loading through repository state. |
| 5 | `test_review_workspace_scope_lifecycle.py` | Review workspace lifecycle across scope changes. |
| 4 | `test_review_workspace_seen_filters.py` | Seen-state filters in the review workspace. |
| 3 | `test_review_workspace_source_filters.py` | Source filters in the review workspace. |
| 2 | `test_review_workspace_state_persistence.py` | Review workspace state persistence. |
| 1 | `test_task_browser_entrypoints.py` | Task entrypoint browser integration. |
| 8 | `test_task_command_configuration.py` | Task command configuration and launch integration. |
| 6 | `test_task_output_history.py` | Task output history integration. |
| 5 | `test_task_panel_refresh.py` | Task panel refresh behavior. |
| 4 | `test_task_rerun.py` | Task rerun lifecycle. |
| 14 | `test_task_runtime.py` | Task process runtime and output capture. |
| 10 | `test_task_stop_lifecycle.py` | Task stop and process-group lifecycle. |
| 9 | `test_workspace_persistence.py` | Browser workspace persistence on disk. |

## Product Behavior Component Tests

| Cases | File | Main Meaning |
| ---: | --- | --- |
| 8 | `test_browser_command_executor.py` | Executes core browser commands. |
| 10 | `test_changed_file_page_content.py` | Shows changed-file page content. |
| 3 | `test_command_palette_catalog.py` | Shows command palette catalog entries. |
| 3 | `test_command_palette_execution.py` | Executes command palette selections. |
| 4 | `test_command_palette_filtering.py` | Filters command palette entries. |
| 4 | `test_command_palette_rendering.py` | Renders command palette UI. |
| 3 | `test_commit_picker_filtering.py` | Filters commits. |
| 5 | `test_commit_picker_rendering.py` | Renders the commit picker. |
| 2 | `test_commit_picker_selection.py` | Selects commits from the picker. |
| 4 | `test_current_task_problem_save_commands.py` | Saves the current task problem. |
| 4 | `test_done_next_commands.py` | Marks review progress and advances. |
| 8 | `test_file_action_browser_commands.py` | Runs file actions from the browser. |
| 6 | `test_file_action_copy_reveal_helpers.py` | Copies and reveals selected file targets. |
| 5 | `test_file_action_open_helpers.py` | Opens selected file targets. |
| 6 | `test_file_detail_change_commands.py` | Runs file-detail change commands. |
| 7 | `test_file_detail_find_commands.py` | Searches within file detail. |
| 7 | `test_file_detail_hunk_commands.py` | Navigates and acts on file-detail hunks. |
| 4 | `test_file_detail_line_commands.py` | Acts on file-detail lines. |
| 8 | `test_file_detail_navigation_commands.py` | Navigates file detail from commands. |
| 5 | `test_file_detail_page_content.py` | Shows file-detail page content. |
| 4 | `test_file_detail_problem_commands.py` | Moves between file-detail problems. |
| 2 | `test_file_detail_problem_context_copy_commands.py` | Copies file-detail problem context. |
| 1 | `test_file_detail_problem_context_empty_states.py` | Reports missing file-detail problem context. |
| 2 | `test_file_detail_problem_context_save_commands.py` | Saves file-detail problem context. |
| 3 | `test_file_detail_refresh_rendering.py` | Preserves file-detail rendering on refresh. |
| 5 | `test_file_detail_source_copy_commands.py` | Copies file-detail source context. |
| 6 | `test_file_detail_source_navigation_commands.py` | Jumps between file detail and source. |
| 6 | `test_index_actions.py` | Runs index actions for selected files. |
| 4 | `test_page_help_and_actions.py` | Shows page help and contextual actions. |
| 2 | `test_page_history.py` | Moves through page history. |
| 4 | `test_problem_context_empty_failure_commands.py` | Reports empty or failed problem-context commands. |
| 4 | `test_problem_diff_copy_commands.py` | Copies problem diff context. |
| 4 | `test_problem_diff_save_commands.py` | Saves problem diff context. |
| 3 | `test_problem_diff_view_commands.py` | Views problem diff context. |
| 6 | `test_prompt_handoff_copy_commands.py` | Copies prompt handoff text. |
| 1 | `test_prompt_handoff_rendering.py` | Renders prompt handoff content. |
| 2 | `test_prompt_handoff_save_feedback.py` | Reports prompt save feedback. |
| 2 | `test_prompt_handoff_scope_save_commands.py` | Saves scope prompt handoff. |
| 2 | `test_prompt_handoff_selected_file_save_commands.py` | Saves selected-file prompt handoff. |
| 7 | `test_review_note_copy_commands.py` | Copies review notes. |
| 1 | `test_review_note_edit_commands.py` | Edits review notes. |
| 5 | `test_review_note_lines.py` | Displays review-note lines. |
| 6 | `test_review_note_list_commands.py` | Lists review notes. |
| 4 | `test_review_note_save_commands.py` | Saves review notes. |
| 4 | `test_review_note_state.py` | Tracks review-note state. |
| 4 | `test_scope_home_commands.py` | Opens and refreshes scope home. |
| 2 | `test_scope_home_display.py` | Displays scope home. |
| 3 | `test_scope_home_selection.py` | Selects scopes from scope home. |
| 4 | `test_selected_diff_commands.py` | Copies selected diff context. |
| 5 | `test_selected_file_diff_actions.py` | Runs selected-file diff actions. |
| 6 | `test_selected_file_line_change_actions.py` | Runs selected-file line-change actions. |
| 3 | `test_selected_file_note_actions.py` | Runs selected-file note actions. |
| 1 | `test_selected_file_prompt_actions.py` | Runs selected-file prompt actions. |
| 2 | `test_selected_file_reference_actions.py` | Runs selected-file reference actions. |
| 3 | `test_selected_file_stage_actions.py` | Runs selected-file stage actions. |
| 1 | `test_source_file_context_configuration.py` | Configures source-file context size. |
| 5 | `test_source_file_context_copy_commands.py` | Copies source-file context. |
| 4 | `test_source_file_context_empty_states.py` | Reports missing source-file context. |
| 1 | `test_source_file_context_save_commands.py` | Saves source-file context. |
| 6 | `test_source_file_find_symbol_navigation.py` | Finds symbols in source files. |
| 3 | `test_source_file_navigation_commands.py` | Navigates source files. |
| 1 | `test_source_file_page_content.py` | Shows source-file page content. |
| 4 | `test_source_file_rendering.py` | Renders source-file pages. |
| 8 | `test_source_file_selection_commands.py` | Selects source-file ranges. |
| 5 | `test_source_file_symbol_copy_commands.py` | Copies source symbols. |
| 1 | `test_source_file_symbol_empty_states.py` | Reports missing source symbols. |
| 1 | `test_source_file_symbol_save_commands.py` | Saves source symbols. |
| 4 | `test_source_problem_context_line_copy_commands.py` | Copies source problem context for the current line. |
| 2 | `test_source_problem_context_save_commands.py` | Saves source problem context. |
| 2 | `test_source_problem_context_selection_copy_commands.py` | Copies source problem context for a selected range. |
| 3 | `test_task_output_copy_commands.py` | Copies task output. |
| 5 | `test_task_output_empty_states.py` | Reports missing task output. |
| 3 | `test_task_output_find_commands.py` | Finds text in task output. |
| 3 | `test_task_output_page_content.py` | Shows task-output page content. |
| 5 | `test_task_output_problem_commands.py` | Opens task output problems. |
| 2 | `test_task_output_rendering.py` | Renders task output. |
| 3 | `test_task_output_save_commands.py` | Saves task output. |
| 4 | `test_task_problem_context_commands.py` | Copies task problem context. |
| 5 | `test_task_problem_copy_collection_commands.py` | Copies task problem collections. |
| 5 | `test_task_problem_copy_file_scope_commands.py` | Copies file-scoped task problems. |
| 5 | `test_task_problem_copy_single_commands.py` | Copies a single task problem. |
| 3 | `test_task_problem_list_save_commands.py` | Saves task problem lists. |
| 8 | `test_task_problem_page_content.py` | Shows task-problem page content. |
| 5 | `test_task_problem_page_filters.py` | Filters task problems. |
| 8 | `test_task_problem_page_opening.py` | Opens task-problem pages and targets. |
| 5 | `test_task_problem_page_selection.py` | Selects task problems. |

## Practical Reading

For product planning, do not treat all 569 cases equally.

- The 349 behavior component cases are the product specification surface, but they are too large a share of the suite.
- The 135 integration cases are the regression safety net for stateful workflows; 42 of these are close to CLI end-to-end workflows.
- The 85 pure or near-pure unit tests are implementation guardrails, and this layer is too small for a healthy pyramid.

The current suite is therefore not saying the product has 569 features. It says a much smaller product surface is protected through many page states, command aliases, empty states, and regression cases.

## Rebalancing Direction

The desired direction is:

1. Keep a small number of CLI workflow tests for the three main journeys:
   - choose scope or commit
   - choose file and inspect code
   - run a build and inspect output/problems
2. Keep behavior component tests for page and command semantics that are genuinely user-facing.
3. Extract dense behavior rules from command/page tests into unit-tested modules:
   - task problem extraction and grouping
   - source/file-detail navigation target calculation
   - context rendering sections
   - command availability and command catalog rules
   - task output slicing, matching, and save/copy formatting
4. Avoid adding new UI-level cases for every edge condition if the same rule can be tested below the command executor.
