# Add Task Problem Diff Jump

## Why

Task Output and Task Problems can jump from a build problem to Source File and can package problem/source/diff context for AI handoff. When the user wants to inspect the actual changed hunk that may have caused the failure, they still have to manually return to Changed Files, find the file, and scroll the diff.

This adds a small navigation bridge for the core loop: build problem -> source/diff inspection -> handoff.

## What Changes

- Add `view problem diff` for Task Output and Task Problems.
- The command opens File Detail for the selected/current problem's file when that file exists in the current review scope.
- File Detail scrolls to the rendered row matching the problem line when that line is visible in the diff.
- If the problem file is not changed in the current review scope, the command reports that no diff is available.

## Non-Goals

- No language-server lookup or code editing.
- No cross-file dependency collection.
- No synthetic diff for files outside the current review scope.
- No quick fixes or task-output parser changes.
