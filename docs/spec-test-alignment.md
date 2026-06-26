# Spec / Test Alignment

This document records the current alignment between the canonical OpenSpec and
the behavior-oriented test suite.

## Current Sources

- Canonical product spec: `openspec/specs/ai-change-workbench/spec.md`
- Behavior map: `docs/test-behavior-map.md`
- Test taxonomy: `docs/test-taxonomy.md`
- Test suite: `tests/unit/`, `tests/integration/`, `tests/e2e/`

## Snapshot

- OpenSpec requirements: 271
- OpenSpec scenarios: 582
- Behavior test cases: 569
- Test files: 130
- Test pyramid:
  - Unit: 20 files, 85 cases
  - Integration: 103 files, 442 cases
  - E2E: 7 files, 42 cases

The two sides are broadly aligned at the product-area level, but they are not
yet fully traceable at the individual scenario level.

## Aligned Areas

| Spec area | Test evidence |
| --- | --- |
| CLI diff / outline / review output | `tests/e2e/cli_workflows/test_cli_review_output.py`, `tests/e2e/cli_workflows/test_cli_review_filtering.py`, `tests/e2e/scope_and_workspace/test_cli_review_scopes.py` |
| Packaging / offline editable install | `tests/unit/build_tasks_output/test_packaging.py` |
| Review Scope / workspace state | `tests/integration/scope_and_workspace/`, `tests/e2e/scope_and_workspace/` |
| Changed Files list and file actions | `tests/integration/changed_file_list/` |
| File Detail reading/navigation/actions | `tests/unit/file_detail_reading/`, `tests/integration/file_detail_reading/` |
| Source File reading/symbol behavior | `tests/unit/source_reading_symbols/`, `tests/integration/source_reading_symbols/` |
| Task Panel / Task Output / task runtime | `tests/integration/build_tasks_output/`, `tests/e2e/build_tasks_output/` |
| Task Problems | `tests/unit/task_problem_list/`, `tests/integration/task_problem_list/` |
| Prompt handoff and save/copy flows | `tests/integration/context_copy_save/` |
| Review Notes | `tests/integration/review_notes/` |
| Command Palette and Help | `tests/unit/command_palette_help/`, `tests/integration/command_palette_help/` |
| TUI input, frame, and navigation | `tests/unit/tui_navigation/`, `tests/integration/tui_navigation/` |

## Adjustments Made

The canonical OpenSpec previously emphasized `cr browse` behavior and did not
fully capture several tested non-browser contracts. It now includes explicit
requirements for:

- `CLI diff summarizes local changes`
- `CLI outline summarizes a source file`
- `CLI review renders reviewable change context`
- `CLI review supports review scopes`
- `CLI package exposes the cr command`

These requirements correspond to existing tests rather than new behavior.

## Remaining Gaps

### 1. Test comments still use placeholder requirement links

Every test has a `Behavior:` comment, but the suffix still says
`[Requirement: TODO]`. This is intentionally not filled automatically yet:
simple keyword matching produced false links for low-level formatting and
packaging tests.

Next step: add stable requirement IDs to OpenSpec, then map tests to IDs with a
small reviewed allowlist per domain.

### 2. Scenario-level traceability is not one-to-one

OpenSpec currently has more scenarios than tests, but several tests cover
multiple scenarios at once. Conversely, some unit tests protect lower-level
formatting or parser details that support a broader requirement instead of a
single user-facing scenario.

Next step: generate a machine-readable trace file, for example
`docs/spec-test-trace.json`, with fields:

- `requirement`
- `scenario`
- `tests`
- `coverage`: `direct`, `supporting`, or `missing`

### 3. Integration layer is still too large

The taxonomy document already calls this out: 442 of 569 cases live in the
integration layer. That is consistent with the current product behavior suite,
but not a healthy long-term pyramid.

Next step: when touching a product area, move deterministic rules from
integration tests into unit tests before adding new UI-level cases.

### 4. OpenSpec archive state is dirty

The worktree currently shows many deleted files under `openspec/changes/...`
and corresponding archived copies under `openspec/changes/archive/...`. That is
an OpenSpec archive cleanup issue, not a product/test mismatch.

Next step: handle archive cleanup as its own commit, separate from product spec
or test changes.

## Working Rule

For future changes:

1. Update `openspec/specs/ai-change-workbench/spec.md` for user-visible product
   contracts.
2. Add or update tests at the lowest appropriate pyramid layer.
3. Update `docs/test-behavior-map.md` after changing Behavior comments.
4. Update this alignment document when a new domain appears or a gap is closed.
