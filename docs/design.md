# cr minimal design

## Requirement card

Implement a lightweight terminal-first code reading tool named `cr`.

## Expected behavior

- `cr diff`
  - Runs `git diff --stat` by default.
  - Supports `--staged` to read staged/index changes via `git diff --cached`.
  - Supports `--all` to read combined staged and unstaged tracked changes via `git diff HEAD`.
  - Includes untracked files in the default and `--all` views.
  - Notes when the other side of the Git index/working tree also has matching changes.
  - Lists changed files as a directory tree with added and deleted line counts.
  - Supports `--code` and optional path filters to reduce noisy output.
  - Marks added/deleted/renamed files when Git reports those statuses.
  - For `.ets` and `.ts` files, reports likely modified functions or methods.
  - Falls back to `unknown` when a symbol cannot be identified.
- `cr outline <file>`
  - Reads one source file and prints a coarse tree.
  - Prints a short purpose hint before the structure.
  - Recognizes `class`, `struct`, `interface`, `function`, and common ArkTS lifecycle or visibility-qualified methods.
  - Uses regex and line text only; exact parsing is explicitly out of scope.
- `cr review`
  - Combines diff stats and outline.
  - Supports `--staged` to review index changes instead of unstaged working tree changes.
  - Supports `--all` to review staged and unstaged tracked changes together.
  - Includes untracked files in the default and `--all` views.
  - Notes when the other side of the Git index/working tree also has matching changes.
  - Supports `--code` and optional path filters.
  - Supports `--summary` for summary/tree only output.
  - Supports `--no-hunks` to keep structure while hiding detailed diff hunks.
  - Supports `--context N` to choose how many surrounding lines each hunk includes.
  - Supports `--json` for machine-readable output.
  - Starts with a compact summary table for scan-first review.
  - Starts with a changed-file directory tree so reviewers see where edits sit in the repository.
  - Shows a first-changed-line `path:line` anchor for each file when Git can identify one.
  - Shows lightweight path-based risk hints for lockfiles, config files, and generated files.
  - Shows deleted files as deleted and avoids fake purpose/outline output for missing files.
  - Prints a short purpose hint for code files before detailed hunks.
  - Prints compact per-file diff hunks so reviewers can see actual added/deleted text.
  - Prints old/new line numbers beside hunk lines.
  - For changed `.ets` and `.ts` files, prints file stats, structure, and marks likely modified symbols.
  - For other changed files, prints stats and compact diff hunks.
- `cr browse`
  - Opens the interactive review browser by default when running `cr` without a subcommand.
  - Shows a changed-file list first, then a focused per-file diff view.
  - Uses a fixed redraw area in interactive TTYs so navigation does not append repeated output.
  - Supports keyboard navigation with arrows or `j/k`, Enter or right arrow to open a file, `n/p` for next/previous, `b` or left arrow to return, `r` to refresh, and `q` to quit.
  - Supports path filtering inside the session: `/` opens filter input in raw-key mode, `/query` and `filter query` work in line mode, and `c` / `clear` clears the filter.
  - Applies filtering to list rendering, numeric selection, next/previous navigation, editor opening, and refresh selection clamping.

## Not doing

- No tree-sitter or language server integration.
- No perfect TypeScript or ArkTS syntax model.
- No IDE UI, pager, third-party TUI framework, or mouse interaction.

## Design

- Runtime dependencies: Python standard library only.
- CLI: `argparse` subcommands.
  - Packaging:
    - Expose `cr` from `setup.py` as a console script pointing at `cr.cli:main`.
    - Avoid `pyproject.toml` for now because older pip versions try to download isolated build dependencies before editable installs.
- Git:
  - Call `git diff --stat` for the requested behavior and failure handling.
  - Add `--cached` for staged mode.
  - Add `HEAD` for the combined staged + unstaged mode.
  - Add a caller-provided ref for `--base REF` comparisons against a branch or commit.
  - Add a caller-provided `OLD..NEW` range for explicit two-ref comparisons.
  - Read code content from `NEW` when rendering outlines for `--range OLD..NEW`.
  - Call `git diff --numstat` for stable added/deleted counts.
  - Call `git diff --name-status --find-renames` to attach file status metadata.
  - Call `git ls-files --others --exclude-standard` for untracked files in non-staged views.
  - Treat readable untracked files as full-file additions for counts, anchors, and compact hunks.
  - Omit inline content for binary, non-UTF-8, or over-200 KB untracked files.
  - Pass optional CLI paths through Git pathspecs.
  - Call `git diff --unified=0 -- <file>` to find changed new-file line numbers.
- Mixed staged/unstaged awareness:
  - Keep default and `--staged` views separate.
  - Offer `--all` as a single combined tracked-change view when separate views are too cumbersome.
  - Count matching changes on the other side using the same filters and pathspecs.
  - Print a short note in terminal output and expose `other_changes` in JSON.
- Filtering:
  - Use Git pathspecs for directory/file narrowing.
  - Apply `--code` after Git returns changed files, keeping the definition local to supported code extensions.
- Outline:
  - Detect symbols with conservative regular expressions.
  - Build a tree from indentation.
  - Estimate symbol end lines by brace balance.
- Purpose:
  - Build one compact hint from file extension, path keywords, and top-level symbols.
  - Prefer conservative labels over semantic guesses.
- Review:
  - Reuse the same stats, changed-line, and outline functions as the individual commands.
  - Build structured review data before rendering alternate output formats.
  - Render a compact summary table with stable per-view indexes before tree/detail output.
  - Include the first changed new-file line as an anchor in summary, file tree, detail headers, and JSON.
  - Include conservative path-based risk hints in summary, file tree, details, and JSON.
  - Render `--prompt` as compact Markdown for copying into AI or chat review handoff.
  - Treat output depth as a presentation concern in the CLI layer.
  - Keep Git order by default, but let `--sort risk`, `--sort churn`, and `--sort path` reorder summary/detail/JSON output for large-review navigation.
  - Let `--pick N` select the Nth file after filtering and sorting for focused single-file review.
  - Treat review progress as explicit command input: `--seen PATH` marks reviewed files and `--remaining` filters them without writing local state.
  - Use `git diff --unified=N -- <file>` for changed-text snippets, defaulting to `N=2`.
  - Render hunk bodies with old/new line-number columns while preserving the original `+`, `-`, and context text.
  - Hide Git metadata headers and truncate long hunk output to keep the terminal readable.
- Browse:
  - Keep `src/cr/cli.py` as the command parser and delegate interactive browse execution to `src/cr/browser.py`.
  - Treat browser session state as one module-owned concept: all changes, filtered visible changes, selected index, mode, and filter query.
  - Match filters as case-insensitive substrings against full Git paths, while continuing to render shortened display paths for readability.
  - Keep raw-key TTY support standard-library only: read one command key at a time, and use a simple `filter> ` line prompt after `/`.
  - Preserve non-TTY line mode for tests, pipes, and terminals where raw-key mode is unavailable.
- File tree:
  - Build a display-only path tree from changed file paths.
  - Add counts and code-symbol annotations only on leaves.

## Acceptance

- `python3 -m cr diff` works in a Git repository.
- `python3 -m cr outline <file>` prints a readable tree for ArkTS / ETS / TS-like input.
- `python3 -m cr review` prints changed files and code outlines.
- Unit tests cover outline parsing, diff stats parsing, changed-symbol mapping, and CLI behavior against a temporary Git repository.
- Unit tests cover changed-file tree rendering.
- Unit tests cover compact hunk rendering and `cr review` hunk output.
- Unit tests cover file-purpose hint rendering and CLI integration.
- Unit tests cover `--code` and path filtering for `diff` and `review`.
- Unit tests cover deleted-file CLI behavior and renamed-file summary formatting.
- Unit tests cover staged diff/review behavior, including staged deletions.
- Unit tests cover compact review summary rendering and CLI placement.
- Unit tests cover `--summary` and `--no-hunks` output depth controls.
- Unit tests cover `--json` structured review output.
- Unit tests cover `--prompt` Markdown review handoff output.
- Unit tests cover mixed staged/unstaged notes and JSON `other_changes`.
- Unit tests cover configurable review hunk context.
- Unit tests cover combined staged + unstaged review with `--all`.
- Unit tests cover baseline comparison with `--base REF`.
- Unit tests cover explicit two-ref comparison with `--range OLD..NEW`.
- Unit tests cover first changed-line anchors in terminal and JSON review output.
- Unit tests cover untracked files in default and `--all` review output.
- Unit tests cover binary and large untracked file guardrails.
- Unit tests cover lockfile/config/generated risk hints in terminal and JSON output.
- Unit tests cover large-review sorting by risk and churn in terminal and JSON output.
- Unit tests cover summary indexes and `--pick N` single-file extraction.
- Unit tests cover `--seen PATH` state markers and `--remaining` filtering in terminal, JSON, and prompt output.
- Unit tests cover old/new line-numbered hunk rendering.
- Unit tests cover the packaged `cr` console script entry point.
- Unit tests cover interactive browser filtering, fixed-screen redraw rendering, and non-TTY filtered selection.
