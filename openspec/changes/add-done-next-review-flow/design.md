## Context

当前 product hierarchy 是 `Review Scope -> Changed Files -> File Detail`。Review progress 已经通过 `m` / `seen` / `done` 标记当前文件，`remaining` 会隐藏 seen 文件；文件导航通过 `n` / `p` 切换文件，并在 File Detail 中打开对应文件详情。

`done next` 是一个组合工作流，但它需要知道 `remaining` 模式会在 mark seen 后改变 visible list，所以不能只简单复用“mark 后再 next”的旧顺序。

## Goals / Non-Goals

**Goals:**

- 提供 `done next` 和 `seen next`。
- 标记当前 visible selected file 为 seen。
- 在 Changed Files 层选择下一个可见文件；在 File Detail 层继续显示下一个 File Detail。
- 在 `remaining` 模式下不跳过更新后列表中的第一个 next item。
- 保持 notes、task state、filters、Review Scope 和 workspace persistence 行为不变。

**Non-Goals:**

- 不新增自动跳过已看文件的普通 `n` 行为。
- 不自动切换 Review Scope。
- 不在 Command Palette 中放入需要上下文解释的参数化变体之外的新 overlay。
- 不改变 `m`、`seen`、`done`、`n`、`p` 的现有行为。

## Decisions

1. 命令名使用 `done next` / `seen next`。
   - 理由：它读起来像 review workflow，而不是底层导航原语；`done` 已经是 mark seen 的现有别名。
   - 替代方案：`m next`。暂不采用，避免把命令面扩得太散。

2. 在 Changed Files 层保持列表层，在 File Detail 层保持详情层。
   - 理由：动作不应强迫用户跨产品层级；当前在哪一层工作，就在那一层前进。
   - 替代方案：无论在哪都打开下一个 File Detail。暂不采用，因为列表层用户可能只是批量 triage。

3. 在 `remaining` 模式下先记住当前 selected index，再 mark seen，然后在更新后的 visible list 中选择同一个 index。
   - 理由：当前文件消失后，原 index 位置自然对应“下一个未看文件”；如果超出尾部则 clamp 到最后一个 remaining file。

4. 执行器持有组合动作。
   - 理由：这个 workflow 组合 progress state、visible selection、page preservation 和 status feedback；暂时没有必要新建 module，后续如果 progress workflows 继续增长再抽深模块。

## Risks / Trade-offs

- 组合动作让 `BrowserCommandExecutor` 多一个分支。缓解：只新增一个局部 helper，仍复用 `seen_paths` 和 `BrowserNavigation`。
- `remaining` 模式下最后一个文件被标记后可见列表为空。缓解：返回 Changed Files 空状态/保持列表，并给出明确消息。
- 命令别名过多可能让 catalog 变噪。缓解：只支持 `done next` / `seen next`，不新增隐式别名。
