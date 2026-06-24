## 1. CLI Surface

- [x] 1.1 Add `--copy-cmd` browse argument
- [x] 1.2 Add `--reveal-cmd` browse argument

## 2. File Action Runtime

- [x] 2.1 Add configured copy command resolution: CLI > `CR_COPY_CMD` > platform fallback
- [x] 2.2 Add configured reveal command resolution: CLI > `CR_REVEAL_CMD` > platform fallback
- [x] 2.3 Keep failure messages non-fatal and user-facing

## 3. Browser Wiring

- [x] 3.1 Pass configured copy command from browser args to copy helpers
- [x] 3.2 Pass configured reveal command from browser args to reveal helpers
- [x] 3.3 Preserve existing copy/reveal behavior without configuration

## 4. Documentation

- [x] 4.1 Update README usage
- [x] 4.2 Update CONTEXT, design, navigation roadmap, and P0 docs

## 5. Verification

- [x] 5.1 Run focused tests, full tests, compile check, OpenSpec strict validation, and diff check
- [x] 5.2 Run Warden scope review
