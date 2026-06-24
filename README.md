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
命令提示区      cr:list> / cr:file> / cr:commits>
```

build/test/lint 运行时只允许刷新后台任务面板；主工作区仍然可以继续浏览，最底下的命令提示不会被日志挤走。raw-key 模式里的普通操作反馈会显示在上下文区，不会追加到 prompt 下面。用户打开 `:` 或 `/` 这种临时输入后，界面会回到同一个固定 frame。

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

常用按键：

```text
↑/↓ 或 j/k    移动选择
Enter / →     打开当前文件的 review 视图
← / b         回到文件列表
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
r             刷新改动
o             用编辑器打开当前文件
q             退出
```

在文件 review 视图里，`↑/↓` 或 `j/k` 会滚动当前文件内容；`n/p` 仍然用于切到下一个 / 上一个文件。

打开 command palette：

```text
: commands
```

在真实 TUI 里按 `:` 后直接回车，或输入 `?`，也会打开 command palette。可以用 `↑/↓` 或 `j/k` 选择命令，按 `Enter` 执行；按 `/` 搜索命令，按 `c` 清除命令搜索，按 `b` 回到文件列表。需要参数的命令，比如 `base main` 和 `range main..HEAD`，仍然通过 `:` 输入。

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
查看 commit 后，按 `b` 会逐层返回：文件 diff -> 该 commit 的 changed-file list -> 最近 commit 列表；按 `w` 会回到原来的工作区改动范围。

标记 review 进度：

```text
m / seen / done        把当前文件标记为已看
todo / unseen / unmark 取消已看标记
remaining              只显示还没看的文件
allfiles / show all    回到全部改动文件
```

文件列表会显示整体进度，比如 `Progress: 3/12 seen`，每个文件前也会显示 `[x]` 或 `[ ]`。单文件 diff 顶部会显示当前文件是 `seen` 还是 `todo`。

切换 review scope：

```text
: worktree          查看未暂存工作区改动
: staged            查看暂存区改动
: all               查看 staged + unstaged 的本地改动
: base main         查看当前工作区/HEAD 相对 main 的改动
: range main..HEAD  查看两个 ref 之间的改动
```

界面会显示 `Scope: ...`，这样你能一直知道当前是在看 worktree、staged、all、base、range、recent commits 还是某个 commit。

默认 `cr browse` 会在退出时把当前 scope、filter、选中文件、list/file 层级和 review 进度保存到 `.git/cr/browse-state.json`；下次直接运行 `cr` 会恢复这个 review workspace。显式传入 `--staged`、`--all`、`--base`、`--range`、`--untracked` 或路径参数时，本次命令优先，不会被历史状态覆盖。

打开编辑器：

```bash
cr --open-cmd 'code -g {fileline}'
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
: stop     停止正在运行的任务
: rerun    重跑最近一次任务
```

任务面板会区分 `running`、`stopping`、`stopped`、`succeeded` 和 `failed`，并显示 compact recent task history。后台任务会放进独立进程组，`: stop` / `: cancel` 会先温和收口整个任务进程组；如果短时间内仍未退出，会升级强杀，减少残留子进程继续刷日志。`DouyinHarmony` 仓的 build 会默认执行 `./remote buildEntry --app douyin`；其他仓可以用 `--build-cmd` 或 `CR_BUILD_CMD` 配置 build，用 `--test-cmd` / `CR_TEST_CMD` 配置 test，用 `--lint-cmd` / `CR_LINT_CMD` 配置 lint：

```bash
cr --build-cmd './remote buildEntry --app douyin' --test-cmd 'npm test' --lint-cmd 'npm run lint'
```

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
