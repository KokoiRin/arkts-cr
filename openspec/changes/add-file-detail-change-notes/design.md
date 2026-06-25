## Context

当前产品层级仍是 `Review Scope -> Changed Files -> File Detail`。Review notes 是 Review Workspace 里的 path-keyed per-file state，`note TEXT` 设置整个文件备注，`notes` / `copy notes` 负责汇总和复制。File Detail 已经通过 `current_changed_row` 能识别当前 `state.file_scroll` 对应的 added/deleted 行。

本 change 不引入独立评论模型，只把“当前改动行的位置”编码进当前文件的 existing review note，作为轻量 follow-up 标记。

## Goals / Non-Goals

**Goals:**

- 在 File Detail 中提供 `note change TEXT`。
- 当前行是 added 行时追加 `line N: TEXT`；当前行是 deleted 行时追加 `old line N: TEXT`。
- 已有文件 note 时追加在同一行，用 ` | ` 分隔，保持现有 notes summary 的单行展示稳定。
- 清理 File Detail cache，让 note header 立刻刷新。

**Non-Goals:**

- 不新增多条结构化评论、resolved 状态、作者、时间戳或独立 note 存储 schema。
- 不改变 `note TEXT` 覆盖整个文件 note、`note` 清除文件 note 的语义。
- 不为 context/hunk header/metadata 行猜测改动位置。

## Decisions

1. 命令名使用 `note change TEXT`。
   - 理由：它和现有 `note TEXT` 在同一心智模型里，表达“给当前 change 写 note”。
   - 替代方案：`change note TEXT`。暂不采用，因为 note 系列命令已经存在，放在 `note` 前缀下更容易发现。

2. 继续使用 per-file review note 字符串，不新增结构化 line-note schema。
   - 理由：这是最小可用 P0，能立刻进入现有 note marker、File Detail header、workspace persistence、prompt handoff 和 copy notes 流程。
   - 替代方案：新增 path+line keyed note 数据结构。暂不采用，因为会牵动 persistence、prompt、summary 和后续迁移，当前还没有足够功能压力。

3. 多条 change note 使用 ` | ` 追加。
   - 理由：`review_note_lines` 当前以一条 note 生成一行 summary；保留单行可以避免多行 note 打乱 command/status 展示。
   - 替代方案：追加换行。暂不采用，因为现有 summary 没有多行缩进语义。

4. 解析当前位置仍放在 `file_detail_navigation`，写 note workflow 放在 `selected_file_actions`。
   - 理由：前者拥有渲染行解析规则，后者拥有 selected-file note mutation 和 workspace/cache 同步。

## Risks / Trade-offs

- `note change TEXT` 会占用一部分以前可能作为普通文件 note 的文本空间。缓解：仅 `note change ` 前缀触发，`note change` 仍可作为普通文件 note 文本。
- 字符串追加不是长期评论系统。缓解：OpenSpec 明确这是轻量 per-file note 扩展，未来如果要做结构化 comments，可迁移出独立 capability。
- 多条备注可能让单行 note 变长。缓解：这是已有 note 字符串的自然限制，P0 先保留可复制/可 prompt 的轻量形态。
