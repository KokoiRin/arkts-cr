## Context

`cr.ui.file_actions` already hides clipboard and file-browser subprocess details from `browser.py`. The configuration feature should deepen that module rather than making the browser know command templates or platform behavior.

## Goals / Non-Goals

**Goals:**

- Let users configure copy and reveal commands through CLI args and environment variables.
- Preserve the existing platform fallbacks when no custom command is configured.
- Keep copy/reveal failures as user-facing browser messages.
- Keep command templates small and shell-like, consistent with `--open-cmd`.

**Non-Goals:**

- Do not add project-local file action config yet.
- Do not add a general action registry.
- Do not change `open` / `--open-cmd`.
- Do not add UI for editing commands.

## Decisions

### 1. CLI/env first

Use `--copy-cmd` / `CR_COPY_CMD` and `--reveal-cmd` / `CR_REVEAL_CMD`. This matches the existing `--open-cmd` and task-command override style.

### 2. Copy sends text to stdin

Configured copy commands receive the copied text on stdin. They may also use `{text}` in the command template for tools that need an argument.

### 3. Reveal uses path placeholders

Configured reveal commands support `{file}` and `{dir}`. If no placeholder is used, the command still runs exactly as configured so users can wrap behavior in their own script.

### 4. Browser stays thin

`BrowserCommandExecutor` passes configured command strings into `cr.ui.file_actions`; it does not parse templates, launch subprocesses, or choose platform fallbacks.

## Risks / Trade-offs

- [Risk] `{text}` can contain spaces or punctuation. -> Mitigation: template formatting happens after `shlex.split`, matching existing `--open-cmd` behavior.
- [Risk] Copy commands that do not read stdin may ignore copied text unless `{text}` is used. -> Mitigation: README documents both stdin and placeholder behavior.
- [Risk] Environment variables can surprise tests. -> Mitigation: focused tests clear or set environment explicitly.
