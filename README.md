# cr

`cr` is a small command line helper for reviewing local Git changes without opening a full IDE. It is aimed at human review after AI coding.

The first version is intentionally simple: Python standard library only, regex-based ArkTS / ETS / TS outline parsing, and terminal-friendly text output.

## Install

Requires Python 3.9 or newer.

From this repository:

```bash
python3 -m pip install --user -e .
cr --help
```

If `cr` is installed but the shell still says `command not found`, add Python's user script directory to your current shell:

```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
cr --help
```

You can also run it without installing:

```bash
PYTHONPATH=src python3 -m cr --help
```

## Commands

### `cr` / `cr browse`

Opens an interactive review browser. This is the default entry point when you run `cr` without a subcommand.

```text
$ cr
Interactive review
  ↑/↓ or j/k: move    Enter/→: open file   ←/b: back to list
  /: filter files     c: clear filter      o: open in editor
  n/p: next/previous  r: refresh           q: quit

Changed files (2 files, +7 -4)
  1  README.md           +2 -1  modified
> 2  src/pages/Home.ets  +5 -3  modified

cr:list> Enter
File 2/2  src/pages/Home.ets:11  +5 -3
  changes:
  @@ -9,5 +9,5 @@ struct HomePage {
    12      | -    Text(this.title)
         12 | +    Text(this.title + ' updated')

cr:file> o
Opened src/pages/Home.ets:11
```

The browser mirrors the common source-control flow in editors: a changed-file list first, then a focused diff view for one file, with quick next/previous navigation. In an interactive terminal, `cr` redraws a single full-screen review area instead of appending repeated output. Use arrow keys or `j/k` to move and Enter to open the selected file. Press `/` to filter the changed-file list by path, and press `c` to clear the active filter. In non-interactive line mode, use `/query`, `filter query`, or `clear`. Use `r` after editing files to refresh the change list; the active filter is preserved and selection is clamped to the refreshed list. Press `o` to open the current file in an editor. In terminals that support OSC-8 links, file paths are clickable; some terminals only open `https` links, so `o` is the reliable local-file fallback. It supports the same scope filters as `diff`, plus `--context`, `--sort`, `--untracked`, `--color`, `--links`, `--link-scheme`, and `--open-cmd`:

```bash
cr browse --code
cr browse --sort risk
cr browse --context 0
cr browse --untracked
cr browse --links always
cr browse --links always --link-scheme vscode
cr browse --open-cmd 'code -g {fileline}'
```

### `cr diff`

Shows changed files, added/deleted lines, and likely modified symbols for `.ets` and `.ts` files.

```text
$ cr diff
Git diff stat:
 src/pages/Home.ets | 8 +++++---

Changed file tree:
  └─ src
     └─ pages
        └─ Home.ets +5 -3 modified: build, aboutToAppear
```

Use filters when a working tree is noisy:

```bash
cr diff --code
cr diff --code src/pages
cr diff --untracked --code
cr diff --color always
```

Review staged/index changes explicitly:

```bash
cr diff --staged
cr diff --staged --code
cr diff --all --code
cr diff --base main --code
cr diff --range main..feature --code
```

By default, `cr diff` includes unstaged tracked changes and does not scan untracked files, because untracked discovery can be slow in large working trees. Add `--untracked` when you want new files too. `--staged` stays index-only. If both staged and unstaged tracked changes exist, `cr` prints a short note so you do not miss the other side. Use `--all` when you want one combined local-change view, `--base REF` to compare the current tree or HEAD against a branch or commit such as `main`, or `--range OLD..NEW` to compare two refs without checking out `NEW`. Terminal color defaults to `--color auto`; use `--color always` or `--color never` to force it. Clickable file links default to `--links auto`; use `--links always` or `--links never` to force them. `--link-scheme vscode` emits `vscode://file/...:line` links for terminals that can open VS Code URLs.

### `cr outline <file>`

Prints a rough file structure.

```text
$ cr outline src/pages/Home.ets
purpose: ArkTS page/component HomePage with methods aboutToAppear, build
src/pages/Home.ets
└─ class HomePage (line 3)
   ├─ method aboutToAppear (line 7)
   └─ method build (line 11)
```

### `cr review`

Combines diff and outline for code review.

```text
$ cr review
Review changes:
Summary:
  2 files, +7 -4
  path                change  status    anchor                 risk  focus
  README.md           +2 -1   modified  README.md:4            -     -
  src/pages/Home.ets  +5 -3   modified  src/pages/Home.ets:11  -     build

Changed file tree:
  ├─ README.md +2 -1 line 4
  └─ src
     └─ pages
        └─ Home.ets +5 -3 modified: build line 11

src/pages/Home.ets +5 -3 @ src/pages/Home.ets:11
  purpose: ArkTS page/component HomePage with methods aboutToAppear, build
  changes:
  @@ -9,5 +9,5 @@ struct HomePage {
    11   11 |   build() {
    12      | -    Text(this.title)
         12 | +    Text(this.title + ' updated')
    13   13 |   }
  modified: build
  outline:
  └─ class HomePage (line 3)
     ├─ method aboutToAppear (line 7)
     └─ method build * (line 11)

README.md +2 -1
```

`review` starts with a compact summary table, then a repository-level file map, then expands each file with a short purpose hint and compact diff hunks. Code files also include their outline and modified symbols. Deep paths are shortened around the changed files' common directory so large monorepos stay readable. The `anchor` column and detail header point to the first changed line for quick terminal navigation. Hunk rows include old/new line numbers so changes are easy to quote in chat. The `risk` column flags lockfiles, config files, and generated files for extra human attention.

Deleted files are marked directly in the file tree and details:

```text
src/utils/helper.ts +0 -3 deleted
  changes:
  @@ -1,3 +0,0 @@
  -export function helper(): string {
  -  return 'a'
  -}
```

`review` supports the same filters as `diff`:

```bash
cr review --code
cr review src/pages
cr review --code src/pages
cr review --staged --code
cr review --all --code
cr review --base main --code
cr review --range main..feature --code
```

For large changes, control output depth:

```bash
cr review --summary
cr review --no-hunks
cr review --context 5
cr review --sort risk
cr review --sort churn
cr review --summary --sort risk
cr review --sort risk --pick 2
cr review --summary --seen src/app.ts
cr review --summary --seen src/app.ts --remaining
cr review --summary --code src/pages
cr review --untracked --code
cr review --color always
```

Hunk context defaults to 2 lines; use `--context 0` for only changed lines or a larger value when surrounding code matters. For big reviews, `--sort risk` puts lockfiles, config, and generated files first, while `--sort churn` puts the largest changed files first. The default `--sort git` keeps Git's order. Summary rows include an `idx` column; use `--pick N` with the same filters and sort to expand only that file. Use `--seen PATH` to mark files you have already reviewed, and add `--remaining` to hide them.

Emit machine-readable JSON for scripts or AI prompts:

```bash
cr review --json
cr review --json --summary --code
cr review --json --context 0
cr review --json --sort risk
```

JSON output includes `other_changes` counts for staged/unstaged changes outside the current view, plus per-file `anchor`, `first_changed_line`, and `risk_hints` fields. With `--untracked`, untracked text files are reported as `status: "untracked"` with their contents shown as added lines unless the file is binary, non-UTF-8, or over 200 KB; those cases get a short omitted-content note instead.

Emit a compact Markdown package when you want to paste a review into chat or an AI reviewer:

```bash
cr review --prompt
cr review --prompt --sort risk --context 0
cr review --prompt --sort risk --pick 2
cr review --prompt --seen src/app.ts --remaining
cr review --prompt --code src/pages
```

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

Basic manual checks:

```bash
# Run diff/review from a Git repository that has local tracked changes.
PYTHONPATH=src python3 -m cr diff
PYTHONPATH=src python3 -m cr outline tests/fixtures/Sample.ets
PYTHONPATH=src python3 -m cr review
PYTHONPATH=src python3 -m cr review --untracked
```

## Architecture

The root `cr` package stays intentionally small. Behavior lives in four module
groups:

- `cr.vcs`: Git diff/status adapters.
- `cr.source`: lightweight source outline and purpose hints.
- `cr.review`: review data assembly and renderers.
- `cr.ui`: terminal styling and interactive browser behavior.

See `CONTEXT.md` and `docs/design.md` before adding new modules.
