# Design

This P0 stays inside the existing source fact layer:

- `src/cr/source/outline.py` already recognizes optional `export` on containers and functions.
- Extend the shared declaration prefix to also allow `export default`.
- Keep all callers unchanged; Source File and File Detail already consume `parse_outline`.

The recognized shapes are named declarations only:

```text
export default class FeedStore { ... }
export default function createStore() { ... }
```

Anonymous default exports and default arrow expressions remain out of scope because they do not provide a stable symbol name for the existing label model.
