# cr

`cr` 是一个面向代码 review 和常用仓库操作的 terminal workbench / lightweight TUI。它的长期目标是把日常 IDE 里的高频动作收进一个舒服的终端界面：看改动、切 commit、跑 build/test/lint、打开编辑器，以及后续更多仓库操作。

日常使用时不用记很多命令：进入有改动的 Git 仓库，直接运行：

```bash
cr
```

这会打开交互式 review browser。后续大部分操作都在里面完成。

产品导航层级固定为 `Review Scope -> Changed Files -> File Detail`：先选择或恢复一个变化集合，再看这个集合里改了哪些文件，最后进入单个文件详情。详细设计见 [docs/workbench-navigation.md](docs/workbench-navigation.md)。

交互界面由一个固定 browser frame 管理，不是普通 stdout 日志流。当前 frame 分四层：

```text
上下文区        当前 review scope 和临时状态反馈，比如 opened / invalid choice
主工作区        文件树、commit 列表、单文件 diff、command palette
后台任务面板    build 等后台任务的状态、最近输出和最近任务结果
命令提示区      cr:list> / cr:file> / cr:commits> / cr:task>
```

build/test/lint 运行时普通页面只刷新后台任务面板；主工作区仍然可以继续浏览，最底下的命令提示不会被日志挤走。需要看完整日志时输入 `: task output` 或 `: output` 进入可滚动的任务输出页；只有停在这个页面时，主工作区才会跟随任务输出刷新。raw-key 模式里的普通操作反馈会显示在上下文区，不会追加到 prompt 下面。用户打开 `:` 或 `/` 这种临时输入后，界面会回到同一个固定 frame。

## 安装

需要 Python 3.9 或更新版本。

在本仓库里执行：

```bash
python3 -m pip install --user -e .
cr --help
```

如果安装后 shell 里提示 `cr: command not found`，把 Python 用户脚本目录加到当前 shell：

```bash
export PATH="$(python3 -m site --user-base)/bin:$PATH"
```

也可以不安装，直接从源码运行：

```bash
PYTHONPATH=src python3 -m cr
```

## 日常用法

在有本地改动的 Git 仓库里运行：

```bash
cr
```

界面会先显示 changed-file list，选中文件后进入单文件 diff 视图。
真实 TUI 顶部会显示当前 Review Scope 和一行动作提示，比如当前页面可用的
打开、过滤、done-next、hunk 导航、查找、任务或命令面板入口。

常用按键：

```text
↑/↓ 或 j/k    移动选择
Enter / →     打开当前文件的 review 视图
← / b         返回上一页
forward       前进到刚才返回前的页面
/             按路径过滤文件
:             输入命令
c             清除过滤
m             标记当前文件已看
n / p         下一项 / 上一项
PageUp/PageDown 或 u/d  分页
Home/End       跳到顶部 / 底部
scopes        打开 Review Scope 首页
g             选择最近 commit
w             回到工作区改动
r             刷新改动；在文件详情里会尽量保留当前文件
o             用编辑器打开当前文件
q             退出
```

在文件 review 视图里，`↑/↓` 或 `j/k` 会滚动当前文件内容；`]` / `[` 会跳到下一个 / 上一个 diff hunk；`: next change` / `: prev change` 会跳到下一条 / 上一条实际 `+` 或 `-` 改动行；`: copy change` 会复制当前实际改动行的轻量 review 片段；`: note change TEXT` 会把当前改动行的位置和备注追加到当前文件 note；`: find TEXT` 会在当前文件详情里查找文本，`: next match` / `: prev match` 会继续跳到下一个 / 上一个匹配；`: open line` / `: copy line` 会对当前渲染行的新文件行号执行打开或复制锚点；`: open hunk` 会打开当前 hunk，`: copy hunk` 会复制当前 hunk review 片段；`r` 刷新后如果当前文件仍在当前 scope/filter 里，会留在这个文件详情；`n/p` 仍然用于切到下一个 / 上一个文件。

打开 command palette：

```text
: commands
```

在真实 TUI 里按 `:` 后直接回车，或输入 `?`，也会打开 command palette。可以用 `↑/↓` 或 `j/k` 选择命令，按 `Enter` 执行；按 `/` 搜索命令，过滤结果会显示匹配数量并优先展示命令/标题命中的结果；按 `c` 清除命令搜索，按 `b` 回到文件列表。需要参数的命令，比如 `base main` 和 `range main..HEAD`，仍然通过 `:` 输入。

如果终端不支持真实 TUI，`cr` 会退回行模式。行模式里可以输入：

```text
/Second
filter Second
clear
commands
scopes
m
remaining
allfiles
todo
g
1
q
```

## 常见场景

只看代码文件：

```bash
cr --code
```

按风险或改动量排序：

```bash
cr --sort risk
cr --sort churn
```

包含未跟踪文件：

```bash
cr --untracked
```

调小 diff 上下文：

```bash
cr --context 0
```

工作区没有未提交改动，或者当前改动已经暂存时，直接运行 `cr` 会显示最近的 commit 列表。也可以在文件列表里按 `g`，手动切到最近 commit 列表；选中某个 commit 后会进入这个 commit 的 changed-file list。
查看 commit 后，按 `b` 会返回上一页；如果当前 session 没有页面历史，则回退到产品层级默认行为。按 `forward` 可以前进到刚才返回前的页面；按 `w` 会回到原来的工作区改动范围。

标记 review 进度：

```text
m / seen / done        把当前文件标记为已看
done next / seen next  标记已看并前进到下一个文件
todo / unseen / unmark 取消已看标记
remaining              只显示还没看的文件
allfiles / show all    回到全部改动文件
note TEXT              给当前文件写一条 review 备注
note change TEXT       给当前实际改动行追加 review 备注
note                   清除当前文件的 review 备注
notes                  汇总当前 workspace 的 review 备注
notes QUERY            按路径或备注内容过滤 review 备注
copy notes             复制当前 review 备注汇总
copy notes QUERY       复制过滤后的 review 备注汇总
copy diff              复制当前文件的轻量 diff review 片段
copy hunk              复制当前 diff hunk review 片段
copy line              复制当前文件详情行或 Source File Page 目标行的 path:line
copy source            复制 Source File Page 目标行附近源码片段
source context N       设置 copy source 的上下文半径，默认 3
copy change            复制当前实际改动行 review 片段
save diff [PATH]       保存当前文件的轻量 diff review 片段
find TEXT              在当前文件详情里查找渲染文本
next match             跳到当前 find 的下一个匹配
prev match             跳到当前 find 的上一个匹配
next change            跳到当前文件的下一条实际改动行
prev change            跳到当前文件的上一条实际改动行
open hunk              在编辑器里打开当前 diff hunk
open line              在编辑器里打开当前文件详情行
next hunk / ]          跳到当前文件的下一个 diff hunk
prev hunk / [          跳到当前文件的上一个 diff hunk
copy prompt            复制当前可见改动的 AI review handoff
copy prompt file       复制当前文件的 AI review handoff
save prompt [PATH]     保存当前可见改动的 AI review handoff
save prompt file [PATH] 保存当前文件的 AI review handoff
```

文件列表会显示整体进度，比如 `Progress: 3/12 seen`，每个文件前也会显示 `[x]` 或 `[ ]`。`done next` / `seen next` 会把当前文件标记为已看并前进到下一个可见文件；在 File Detail 里执行时会继续打开下一个文件详情，在 `remaining` 模式里不会跳过下一个未看文件。有备注的文件行会显示 `note` 标记；单文件 diff 顶部会显示当前文件是 `seen` 还是 `todo`，并在有备注时显示完整 `note: ...`。`note change TEXT` 会把当前 File Detail 中实际 `+` 或 `-` 改动行的位置追加进当前文件 note，added 行写成 `line N: TEXT`，deleted 行写成 `old line N: TEXT`；已有文件 note 会用 ` | ` 追加而不是覆盖。`notes` 会按当前 changed-file 顺序汇总备注，并把不在当前变更里的持久化备注追加到末尾；`notes QUERY` 会按路径或备注文本做大小写不敏感过滤。`copy notes` / `notes copy` 会复制完整汇总文本，`copy notes QUERY` 会复制过滤后的汇总文本。`copy diff` 会复制当前文件的轻量 Markdown diff 片段，包含当前 scope 下的 hunk、anchor、seen 状态和 review 备注，但不带 AI prompt 请求文案；`copy hunk` 会复制当前 File Detail hunk 的行号化 review 文本，适合只贴一个变更块；`copy change` 会复制当前 File Detail 中实际 `+` 或 `-` 改动行的单行 review 片段，added 行带 `path:line`，deleted 行只带旧行号；`save diff` 会把同样的片段保存成文件，默认路径是 `.cr/handoff/review-diff.md`，也可以在命令后传入自定义路径。`copy prompt` 会复制当前可见改动的 Markdown review handoff，并带上这些文件对应的 review 备注；`copy prompt file` 只复制当前文件及其备注，方便贴到聊天、AI prompt 或 PR comment。`save prompt` 和 `save prompt file` 会把同样的 Markdown 保存成文件，默认路径分别是 `.cr/handoff/review-prompt.md` 和 `.cr/handoff/review-prompt-file.md`，也可以在命令后传入自定义路径。

切换 review scope：

```text
: worktree          查看未暂存工作区改动
: staged            查看暂存区改动
: all               查看 staged + unstaged 的本地改动
: base main         查看当前工作区/HEAD 相对 main 的改动
: range main..HEAD  查看两个 ref 之间的改动
```

界面会显示 `Scope: ...`，这样你能一直知道当前是在看 worktree、staged、all、base、range、recent commits 还是某个 commit。

默认 `cr browse` 会在退出时把当前 scope、filter、选中文件、list/file 层级、review 进度和 per-file note 保存到 `.git/cr/browse-state.json`；下次直接运行 `cr` 会恢复这个 review workspace。显式传入 `--staged`、`--all`、`--base`、`--range`、`--untracked` 或路径参数时，本次命令优先，不会被历史状态覆盖。

打开编辑器：

```bash
cr --open-cmd 'code -g {fileline}'
```

文件动作也可以配置：

```bash
cr --copy-cmd 'pbcopy' --reveal-cmd 'open -R {file}'
```

`copy path` / `copy anchor` / `copy diff` / `copy hunk` / `copy line` / `copy change` / `copy notes` / `copy notes QUERY` / `copy prompt` / `copy prompt file` 会把复制文本传给 copy 命令的 stdin，也支持 `{text}` 占位。`save diff` / `save prompt` / `save prompt file` 直接写入文件，不依赖剪贴板命令。`reveal` 支持 `{file}` 和 `{dir}` 占位。对应环境变量是 `CR_COPY_CMD` 和 `CR_REVEAL_CMD`。
如果文件动作失败，错误信息会带上当前使用的是 CLI、环境变量、平台 fallback 还是 missing；也可以在浏览器里输入 `: file actions` 主动查看 `open` / `copy` / `reveal` 的解析来源。

常用文件动作：

```text
: open         打开当前文件到首个改动行
: open hunk    打开当前 diff hunk 到编辑器
: copy path    复制当前文件相对路径
: copy anchor  复制当前文件 path:line review anchor
: copy diff    复制当前文件的轻量 diff review 片段
: copy hunk    复制当前 diff hunk review 片段
: copy line    复制当前文件详情行的 path:line
: copy change  复制当前实际改动行 review 片段
: save diff    保存当前文件的轻量 diff review 片段
: find TEXT    在当前文件详情里查找渲染文本
: note change TEXT 给当前实际改动行追加 review 备注
: next match   跳到当前 find 的下一个匹配
: prev match   跳到当前 find 的上一个匹配
: next change  跳到当前文件的下一条实际改动行
: prev change  跳到当前文件的上一条实际改动行
: next hunk    跳到当前文件的下一个 diff hunk
: prev hunk    跳到当前文件的上一个 diff hunk
: open line    打开当前文件详情行到编辑器
: copy prompt  复制当前可见改动的 AI review handoff
: copy prompt file 复制当前文件的 AI review handoff
: save prompt  保存当前可见改动的 AI review handoff
: save prompt file 保存当前文件的 AI review handoff
: reveal       在系统文件管理器里定位当前文件
: file actions 查看 open/copy/reveal 命令来源
```

运行仓库任务：

```text
:
build
```

任务会在底部打开一个 5-10 行的小日志面板，主区域仍然可以继续浏览文件树和 diff。后台日志更新只重画这个面板；如果终端尺寸或页面状态已经变化，会先恢复完整 browser frame，避免日志和用户操作互相打乱。面板会保留当前 session 最近完成的任务结果，方便重跑后仍能看到上一轮成功、失败或停止状态。

常用任务命令：

```text
: build    启动编译
: test     运行测试
: lint     运行 lint
: tasks    查看 build/test/lint 命令来源
: tasks help  查看 .cr/tasks.json 格式
: task output 打开当前任务输出详情页
: problems 打开当前任务输出中的文件位置列表
: problems errors / warnings / info / note 只看对应 severity 的问题
: problems all 清除 Problems severity 过滤
: problems sort severity 按 error/warning/info/note 排序当前 Problems
: problems sort output 恢复 task output 顺序
: view problem 在 TUI 内查看 Problems 页当前问题附近源码
: copy problem 复制 Problems 页当前选中的问题
: copy problems 复制当前任务输出中的全部问题
: copy task 复制当前任务输出
: save task [PATH] 保存当前任务输出，默认 .cr/handoff/task-output.md
: stop     停止正在运行的任务
: rerun    重跑最近一次任务
```

任务面板会区分 `running`、`stopping`、`stopped`、`succeeded` 和 `failed`，并显示 compact recent task history。`: task output` / `: output` 会打开当前任务的完整输出视图，支持 `↑/↓`、`PgUp/PgDn`、`Home/End` 滚动，`find TEXT` 搜索当前日志，`next match` / `prev match` 继续跳转匹配，`b` 回到之前的代码页面；`: problems` / `: task problems` 会从当前任务输出里提取 `path:line[:column]` 文件位置和常见 `error` / `warning` / code / message 诊断信息，Problems 页标题会显示当前可见问题的 severity 数量；进入 Problems 页后可以用 `problems errors` / `problems warnings` / `problems info` / `problems note` 聚焦某类 severity，用 `problems all` 清除过滤，用 `problems sort severity` 优先看 error/warning/info/note，用 `problems sort output` 恢复原始 task output 顺序；选择问题后按 `Enter` 打开到编辑器，用 `view problem` 在 TUI 内查看问题附近源码，Source File Page 内也支持 `find TEXT` / `next match` / `prev match`、`copy line`、`source context N` 和 `copy source`，或用 `copy problem` / `copy problems` 复制当前可见问题。后台任务会放进独立进程组，`: stop` / `: cancel` 会先温和收口整个任务进程组；如果短时间内仍未退出，会升级强杀，减少残留子进程继续刷日志。`DouyinHarmony` 仓的 build 会默认执行 `./remote buildEntry --app douyin`；其他仓可以用 `--build-cmd` 或 `CR_BUILD_CMD` 配置 build，用 `--test-cmd` / `CR_TEST_CMD` 配置 test，用 `--lint-cmd` / `CR_LINT_CMD` 配置 lint：

```bash
cr --build-cmd './remote buildEntry --app douyin' --test-cmd 'npm test' --lint-cmd 'npm run lint'
```

也可以在仓库根目录放 `.cr/tasks.json`，把常用任务随项目保存：

```json
{
  "build": "./remote buildEntry --app douyin",
  "test": "npm test",
  "lint": "npm run lint"
}
```

任务命令优先级是 CLI 参数、环境变量、`.cr/tasks.json`、DouyinHarmony build 默认。这样日常直接运行 `cr` 后输入 `: test` / `: lint` 就能使用项目预设；输入 `: tasks` 可以查看当前 build/test/lint 分别来自哪个来源，并发现坏掉的 `.cr/tasks.json`。忘了格式时输入 `: tasks help`，会直接显示支持的 key、命令字符串要求和 JSON 示例。

这些参数都作用在默认的 `cr browse` 上。一般先直接 `cr`，只有工作区很大或很乱时再加参数。

## 其他命令

`cr` 默认等价于 `cr browse`。下面这些命令主要用于脚本、复制到聊天里，或者不想进入交互界面时使用。

快速摘要：

```bash
cr review --summary
```

输出完整 review 文本：

```bash
cr review
```

输出 JSON：

```bash
cr review --json
```

生成适合粘贴给 AI / 聊天的 Markdown：

```bash
cr review --prompt
```

只看 Git diff 树：

```bash
cr diff
```

查看单个文件的大致结构：

```bash
cr outline src/pages/Home.ets
```

## 架构

根 package `cr` 尽量保持很薄，主要负责 CLI 解析和分发。具体行为放在四个 package 里：

- `cr.vcs`：Git diff/status adapter。
- `cr.source`：轻量源码 outline 和文件用途提示。
- `cr.review`：review workflow、changed-file facts、hunks/tree/summary/prompt/risk 等渲染。
- `cr.ui`：终端样式、可点击链接和交互式 browser。

新增功能前先看 `CONTEXT.md` 和 `docs/design.md`，优先把行为放进对应的 deep module，再让 CLI 调用。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

基础手工检查：

```bash
PYTHONPATH=src python3 -m cr
PYTHONPATH=src python3 -m cr review --summary
PYTHONPATH=src python3 -m cr outline tests/fixtures/Sample.ets
```
