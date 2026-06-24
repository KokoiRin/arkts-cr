## 1. Scope Context Display

- [x] 1.1 增加 scope label helper，覆盖 worktree、staged、all、base、range、recent commits 和 selected commit
- [x] 1.2 在 list、file、commit list 和非 TTY 输出中展示 scope header

## 2. In-Session Scope Switching

- [x] 2.1 增加 worktree/staged/all scope 切换命令并重载 changed files
- [x] 2.2 增加 `base REF` 和 `range OLD..NEW` scope 切换命令
- [x] 2.3 scope 切换时清空 filter、selection、scroll 和 render cache，并保留 build 面板

## 3. Verification And Documentation

- [x] 3.1 增加 scope header、local scope 切换、base/range 切换和 commit scope 测试
- [x] 3.2 更新 README、`docs/design.md` 和 `docs/p0.md`，记录 review workspace 层级
- [x] 3.3 运行单元测试、编译检查、OpenSpec 校验和 diff check
