# CLI Review Workflows Specification

## Purpose
`cr` is a terminal-first AI change workbench used after AI-assisted
coding to inspect changes, navigate code, run lightweight validation tasks, and
handoff focused context back to AI or reviewers.

Non-interactive `cr diff`, `cr outline`, and `cr review` behavior.

## Requirements
### Requirement: CLI diff summarizes local changes
`cr diff` SHALL provide a scan-first summary of local Git changes without entering the interactive browser.

#### Scenario: Show changed-file statistics and tree
- **WHEN** the user runs `cr diff` in a repository with local changes
- **THEN** the CLI SHALL show Git diff statistics
- **AND** it SHALL render changed files as a directory tree with added/deleted counts and file status

#### Scenario: Filter CLI diff output
- **WHEN** the user passes `--code` or path arguments to `cr diff`
- **THEN** the CLI SHALL limit the visible changed files to matching code files or Git pathspecs

### Requirement: CLI outline summarizes a source file
`cr outline <file>` SHALL print a readable source summary for a single repo-local file.

#### Scenario: Show source purpose and symbols
- **WHEN** the user runs `cr outline <file>` for a supported ArkTS/TS-like file
- **THEN** the CLI SHALL print a compact purpose hint
- **AND** it SHALL print recognized class, struct, interface, function, method, field, enum, and related symbol rows where the lightweight parser can identify them

### Requirement: CLI review renders reviewable change context
`cr review` SHALL combine changed-file facts, source hints, and compact hunks into review-ready terminal output.

#### Scenario: Render default review output
- **WHEN** the user runs `cr review`
- **THEN** the CLI SHALL show a summary, changed-file tree, per-file facts, source purpose, modified-symbol hints, and compact diff hunks where available

#### Scenario: Control review output depth
- **WHEN** the user runs `cr review --summary`, `cr review --no-hunks`, or `cr review --context N`
- **THEN** the CLI SHALL preserve the selected review facts while changing how much hunk/source detail is rendered

#### Scenario: Emit structured and handoff formats
- **WHEN** the user runs `cr review --json` or `cr review --prompt`
- **THEN** the CLI SHALL emit machine-readable review data or prompt-ready Markdown without the normal terminal wrapper

### Requirement: CLI review supports review scopes
`cr review` SHALL let users choose the Git change scope from the command line.

#### Scenario: Review local and comparison scopes
- **WHEN** the user runs review with `--staged`, `--all`, `--base REF`, `--range OLD..NEW`, `--untracked`, or path arguments
- **THEN** the CLI SHALL render the requested scope without requiring checkout
- **AND** it SHALL keep deleted, renamed, binary, non-UTF-8, large, staged, unstaged, mixed, and untracked file facts readable

#### Scenario: Sort and pick large review output
- **WHEN** the user runs `cr review --sort risk`, `--sort churn`, `--sort path`, or `--pick N`
- **THEN** the CLI SHALL reorder or narrow the review output according to the selected scan strategy

### Requirement: CLI package exposes the cr command
The Python package SHALL expose `cr` as an offline-friendly console script.

#### Scenario: Install editable package without isolated build metadata
- **WHEN** the project is installed in editable mode in an environment without package-index access
- **THEN** `setup.py` SHALL expose the `cr=cr.cli:main` console script
- **AND** the project SHALL avoid build metadata that forces isolated dependency downloads for this package
