## Context

`cr.ui.tasks` already owns command resolution and project task preset discovery. Diagnostics should deepen that module by making the resolution explanation available through a small interface, instead of duplicating priority rules in `browser.py`.

## Goals / Non-Goals

**Goals:**

- Add `tasks` as a command-palette and command-prompt action.
- Explain the winning source for `build`, `test`, and `lint`.
- Show malformed `.cr/tasks.json` as diagnostic output.
- Keep diagnostics side-effect free.

**Non-Goals:**

- Do not add a task editor.
- Do not validate arbitrary schemas beyond the current supported keys.
- Do not change command precedence.
- Do not make invalid presets fatal.

## Decisions

### 1. `tasks` means diagnostics, not execution

`build`, `test`, and `lint` execute tasks. `tasks` is reserved for explaining configured task sources.

### 2. Source rules live in `cr.ui.tasks`

The browser should not know the precedence chain. It asks Task Runtime for diagnostic lines and displays them through the existing message/status path.

### 3. Invalid presets remain non-fatal

Diagnostics expose malformed preset files, but task execution remains tolerant and continues to resolve from other sources.

## Risks / Trade-offs

- [Risk] Raw-key status can only show compact text. -> Mitigation: diagnostics are short one-line summaries joined with separators in raw-key mode.
- [Risk] Exact shell quoting can be noisy. -> Mitigation: use the existing `shlex.split` / shell-quote display style for resolved commands.
