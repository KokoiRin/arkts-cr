## Why
The browser already has many page-specific commands, but `help` only prints a
global key summary. Users need a current-page help view that explains what can
be done on the page they are looking at, in Chinese, without losing their place.

## What Changes
- Add a Help page to the browser page model.
- Make `help`, `h`, and `?` open Chinese help for the current page.
- Preserve page history so `b` returns to the page that opened Help.
- Chinese-localize the visible action bar and command help surfaces touched by
  this feature.

## Impact
- Affects interactive browser navigation and rendering only.
- Existing command literals remain stable; only visible descriptions change.
