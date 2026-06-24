## Context

`BrowserState` 已经集中管理当前交互状态：`mode`、`filter_text`、`selected`、`list_scroll`、`file_scroll` 等。review scope 的权威源目前仍是 `argparse.Namespace` 上的 `staged`、`all_changes`、`base`、`ref_range`、`untracked` 字段。持久化需要尊重这个边界：保存时从两边取事实，恢复时先恢复 scope，再加载 changes，再恢复 filter 和 selected。

## Persisted Shape

状态文件位置：

```text
.git/cr/browse-state.json
```

保存 JSON：

```json
{
  "version": 1,
  "scope": {
    "staged": false,
    "all_changes": false,
    "base": null,
    "ref_range": null,
    "untracked": false
  },
  "filter_text": "src/",
  "selected_path": "src/App.ts",
  "selected_index": 2,
  "mode": "file"
}
```

`selected_path` 是主恢复依据；如果路径不再存在于当前 filtered changes 中，再 fallback 到 `selected_index` 并 clamp。

## Restore Rules

只在默认 browse session 恢复：

- 没有 `--staged` / `--all` / `--base` / `--range` / `--untracked`
- 没有 pathspec

这些参数一旦显式出现，就表达了用户本次意图，不能被历史状态覆盖。`--sort`、`--context`、`--code` 等展示参数仍可和恢复状态组合。

## Save Rules

clean exit 时保存：

- `q` / `quit` / `exit`
- EOF
- interrupt 退出前也尝试保存当前状态

不保存 build lifecycle、recent commits 列表、commit drill-in、scroll/cache。它们是会话内瞬时状态，保存会让恢复语义变复杂。

## Non-goals

- 不支持 bare repo 或 worktree 中 `.git` 是文件的情况；这可以后续用 git-dir helper 扩展。
- 不做跨仓库云同步。
- 不提供用户可编辑的状态文件 schema。
