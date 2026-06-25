## Context

Full task output handoff already exists through `copy task` and `save task [PATH]`. Task Output Page also supports search. The missing high-frequency operation is a compact failure-tail package: users often need the last 20-80 lines of a failed build, not the whole log.

## Goals / Non-Goals

**Goals:**

- `copy task tail` copies a compact Markdown handoff containing task type, status, command, and the last 40 output lines.
- `copy task tail N` copies the last N output lines, clamped to a practical range.
- `save task tail [PATH]` saves the default 40-line tail to `.cr/handoff/task-output-tail.md` or a user path.
- Empty current task state reports a no-output message without clipboard or filesystem side effects.

**Non-Goals:**

- No historical task output browsing.
- No log filtering, regex, severity parsing, or tool-specific diagnostic parser changes.
- No new task capture capacity, persistence, or task lifecycle behavior.
- No configurable global default.

## Decisions

1. **Tail formatting lives in Task Runtime.**
   - `cr.ui.tasks` already owns full task handoff Markdown. Tail handoff should reuse the same task facts and differ only in output line windowing and title.

2. **The default is a command-level constant, not user state.**
   - Defaulting to 40 lines covers the common failure-tail case without adding settings or persisted state.

3. **Save tail keeps a separate default filename.**
   - `.cr/handoff/task-output-tail.md` avoids overwriting the full output handoff file and makes the artifact self-explanatory.

4. **Optional N applies only to copy in this first slice.**
   - `copy task tail N` is ergonomic in line mode. `save task tail [PATH]` keeps path parsing unambiguous and uses the default tail size.

## Risks / Trade-offs

- Tail may omit the real error if the useful context is earlier in the log. Users can still use `copy task` or Task Output find.
- `save task tail 80` is treated as a path in this slice to avoid ambiguous command parsing; this can be revisited only if real usage needs it.
- Very small N could produce low-context snippets, so N is clamped to at least 1.
