## Behavior

`copy problem diff` copies the same lightweight file diff snippet used by `copy diff`, but selects the file from the current task problem rather than the current changed-file row.

`save problem diff [PATH]` saves the same Markdown. Without a path, it writes `.cr/handoff/problem-diff.md`.

Current-problem rules:

- Task Problems: use the selected visible task problem.
- Task Output: use the selected parsed output problem.
- Source File: use only the selected parsed problem that exactly matches the current source path and target line, matching the `problem:` header and `copy/save problem` stale-protection behavior.

If the problem's path is not in the current review scope, the command reports that no diff is available and does not copy or write anything.

## Boundaries

The parser adds stable command actions. `browser.py` chooses the current problem and renders the diff snippet. `handoff.py` owns only default path resolution and file writing. Existing review-data and snippet modules continue to own diff contents.
