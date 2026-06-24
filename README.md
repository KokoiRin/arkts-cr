# cr

`cr` 是一个轻量的命令行代码 review 工具，用来快速查看本地 Git 改动。它适合 AI 写完代码后，人再做一次扫描、定位和确认。

日常使用时不用记很多命令：进入有改动的 Git 仓库，直接运行：

```bash
cr
```

这会打开交互式 review browser。后续大部分操作都在里面完成。

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
n / p         下一项 / 上一项
PageUp/PageDown 或 u/d  分页
Home/End       跳到顶部 / 底部
g             选择最近 commit
r             刷新改动
o             用编辑器打开当前文件
q             退出
```

在文件 review 视图里，`↑/↓` 或 `j/k` 会滚动当前文件内容；`n/p` 仍然用于切到下一个 / 上一个文件。

如果终端不支持真实 TUI，`cr` 会退回行模式。行模式里可以输入：

```text
/Second
filter Second
clear
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

打开编辑器：

```bash
cr --open-cmd 'code -g {fileline}'
```

运行仓库编译：

```text
:
build
```

编译会在底部打开一个 5-10 行的小日志面板，主区域仍然可以继续浏览文件树和 diff。`DouyinHarmony` 仓会默认执行 `./remote buildEntry --app douyin`；其他仓可以用 `--build-cmd` 或 `CR_BUILD_CMD` 配置：

```bash
cr --build-cmd './remote buildEntry --app douyin'
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
