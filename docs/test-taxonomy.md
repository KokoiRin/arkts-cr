# Test Taxonomy

这份文档定义当前测试套件的金字塔分层。业务域目录只是第二维度；第一维度必须是测试层级。

## 当前快照

- Test files: 130
- Test cases: 569
- UT / 单模块测试: 20 files, 85 cases (14.9%)
- 跨模块集成测试: 103 files, 442 cases (77.7%)
- 端到端 / CLI 工作流测试: 7 files, 42 cases (7.4%)

结论：当前不是健康的经典测试金字塔。UT 层太薄，integration 层承载了大量页面状态、命令执行器和浏览器状态回归；E2E 数量相对少，这是正确的，但还需要把更多集成层规则下沉成 UT。

## 分层定义

### UT / 单模块测试

只验证一个小模块或函数族的确定性规则。通常不应该知道 BrowserCommandExecutor、BrowserState、完整页面渲染、真实 Git 仓库、子进程生命周期或 CLI 输入输出。

### 跨模块集成测试

验证多个模块协作后的产品语义，例如页面内容、命令执行器、工作区状态、任务面板、文件动作、问题列表和复制/保存 handoff。它们有价值，但不应该无限增长；新增前先问同一规则能否落到 UT。

### 端到端 / CLI 工作流测试

从用户入口运行 CLI、临时 Git 仓库或浏览器工作流，只覆盖主路径和关键烟测。E2E 应该最少，不覆盖每个空状态、别名或格式细节。

## 目录规则

- `tests/unit/<domain>/`: 单模块规则和纯格式化/解析/选择逻辑。
- `tests/integration/<domain>/`: 跨模块产品语义和 UI 组件级回归。
- `tests/e2e/<domain>/`: CLI 或浏览器级端到端工作流。

业务域仍然保留在第二级目录，例如 `tests/unit/source_reading_symbols/` 或 `tests/integration/file_detail_reading/`。

## 新增测试准则

1. 默认先写 UT，只有当行为必须跨模块才能表达时才写 integration。
2. E2E 只保护 95% 高频主流程：选择 review scope/commit、选择文件阅读 diff/source、运行 build/test/lint 并查看 output/problems。
3. 如果一个 integration case 只是覆盖解析、过滤、排序、路径选择、文本裁剪、复制文本格式，应优先抽到更深模块并用 UT 覆盖。
4. 不要把 500+ case 当成 500+ 功能。它们多数是同一小产品面的状态、别名、空态和回归保护。

## 当前分布

| Level | Domain | Files | Cases |
| --- | --- | ---: | ---: |
| `unit` | TUI 框架与导航 | 2 | 13 |
| `unit` | 任务问题列表 | 2 | 15 |
| `unit` | 其他行为 | 1 | 3 |
| `unit` | 变更文件列表 | 1 | 1 |
| `unit` | 命令面板与帮助 | 1 | 5 |
| `unit` | 底层格式化与解析 | 4 | 10 |
| `unit` | 文件详情阅读 | 2 | 12 |
| `unit` | 构建任务与输出 | 3 | 4 |
| `unit` | 源码阅读与符号 | 4 | 22 |
| `integration` | TUI 框架与导航 | 3 | 8 |
| `integration` | 上下文复制与保存 | 4 | 13 |
| `integration` | 任务问题列表 | 10 | 46 |
| `integration` | 其他行为 | 3 | 13 |
| `integration` | 变更文件列表 | 14 | 59 |
| `integration` | 命令面板与帮助 | 4 | 14 |
| `integration` | 提交选择 | 3 | 10 |
| `integration` | 文件详情阅读 | 15 | 67 |
| `integration` | 构建任务与输出 | 15 | 85 |
| `integration` | 源码阅读与符号 | 13 | 47 |
| `integration` | 范围与工作区入口 | 14 | 54 |
| `integration` | 评审备注 | 5 | 26 |
| `e2e` | CLI 工作流 | 3 | 20 |
| `e2e` | 构建任务与输出 | 1 | 2 |
| `e2e` | 范围与工作区入口 | 3 | 20 |

## 文件清单

### UT / 单模块测试

| Cases | File |
| ---: | --- |
| 2 | `tests/unit/build_tasks_output/test_packaging.py` |
| 1 | `tests/unit/build_tasks_output/test_problem_context.py` |
| 1 | `tests/unit/build_tasks_output/test_review_data.py` |
| 1 | `tests/unit/changed_file_list/test_snippet.py` |
| 5 | `tests/unit/command_palette_help/test_command_catalog.py` |
| 10 | `tests/unit/file_detail_reading/test_file_detail_navigation.py` |
| 2 | `tests/unit/file_detail_reading/test_hunks.py` |
| 3 | `tests/unit/miscellaneous/test_browser_commands.py` |
| 1 | `tests/unit/parsing_formatting/test_review_changes.py` |
| 1 | `tests/unit/parsing_formatting/test_summary.py` |
| 4 | `tests/unit/parsing_formatting/test_text_search.py` |
| 4 | `tests/unit/parsing_formatting/test_tree.py` |
| 6 | `tests/unit/source_reading_symbols/test_outline_parsing.py` |
| 8 | `tests/unit/source_reading_symbols/test_outline_symbol_labels.py` |
| 3 | `tests/unit/source_reading_symbols/test_purpose.py` |
| 5 | `tests/unit/source_reading_symbols/test_source_file.py` |
| 7 | `tests/unit/task_problem_list/test_handoff.py` |
| 8 | `tests/unit/task_problem_list/test_task_problem_extraction.py` |
| 4 | `tests/unit/tui_navigation/test_browser_input.py` |
| 9 | `tests/unit/tui_navigation/test_browser_navigation.py` |

### 跨模块集成测试

| Cases | File |
| ---: | --- |
| 10 | `tests/integration/build_tasks_output/test_frame.py` |
| 8 | `tests/integration/build_tasks_output/test_task_command_configuration.py` |
| 3 | `tests/integration/build_tasks_output/test_task_output_copy_commands.py` |
| 5 | `tests/integration/build_tasks_output/test_task_output_empty_states.py` |
| 3 | `tests/integration/build_tasks_output/test_task_output_find_commands.py` |
| 6 | `tests/integration/build_tasks_output/test_task_output_history.py` |
| 3 | `tests/integration/build_tasks_output/test_task_output_page_content.py` |
| 5 | `tests/integration/build_tasks_output/test_task_output_problem_commands.py` |
| 2 | `tests/integration/build_tasks_output/test_task_output_rendering.py` |
| 3 | `tests/integration/build_tasks_output/test_task_output_save_commands.py` |
| 5 | `tests/integration/build_tasks_output/test_task_panel_refresh.py` |
| 4 | `tests/integration/build_tasks_output/test_task_problem_context_commands.py` |
| 4 | `tests/integration/build_tasks_output/test_task_rerun.py` |
| 14 | `tests/integration/build_tasks_output/test_task_runtime.py` |
| 10 | `tests/integration/build_tasks_output/test_task_stop_lifecycle.py` |
| 10 | `tests/integration/changed_file_list/test_changed_file_page_content.py` |
| 8 | `tests/integration/changed_file_list/test_file_action_browser_commands.py` |
| 6 | `tests/integration/changed_file_list/test_file_action_copy_reveal_helpers.py` |
| 5 | `tests/integration/changed_file_list/test_file_action_open_helpers.py` |
| 3 | `tests/integration/changed_file_list/test_file_detail_refresh_rendering.py` |
| 3 | `tests/integration/changed_file_list/test_problem_diff_view_commands.py` |
| 2 | `tests/integration/changed_file_list/test_prompt_handoff_selected_file_save_commands.py` |
| 1 | `tests/integration/changed_file_list/test_review_note_edit_commands.py` |
| 4 | `tests/integration/changed_file_list/test_selected_diff_commands.py` |
| 5 | `tests/integration/changed_file_list/test_selected_file_diff_actions.py` |
| 6 | `tests/integration/changed_file_list/test_selected_file_line_change_actions.py` |
| 3 | `tests/integration/changed_file_list/test_selected_file_note_actions.py` |
| 1 | `tests/integration/changed_file_list/test_selected_file_prompt_actions.py` |
| 2 | `tests/integration/changed_file_list/test_selected_file_reference_actions.py` |
| 3 | `tests/integration/command_palette_help/test_command_palette_catalog.py` |
| 3 | `tests/integration/command_palette_help/test_command_palette_execution.py` |
| 4 | `tests/integration/command_palette_help/test_command_palette_filtering.py` |
| 4 | `tests/integration/command_palette_help/test_command_palette_rendering.py` |
| 3 | `tests/integration/commit_selection/test_commit_picker_filtering.py` |
| 5 | `tests/integration/commit_selection/test_commit_picker_rendering.py` |
| 2 | `tests/integration/commit_selection/test_commit_picker_selection.py` |
| 4 | `tests/integration/context_copy_save/test_page_help_and_actions.py` |
| 6 | `tests/integration/context_copy_save/test_prompt_handoff_copy_commands.py` |
| 1 | `tests/integration/context_copy_save/test_prompt_handoff_rendering.py` |
| 2 | `tests/integration/context_copy_save/test_prompt_handoff_save_feedback.py` |
| 6 | `tests/integration/file_detail_reading/test_file_detail_change_commands.py` |
| 7 | `tests/integration/file_detail_reading/test_file_detail_find_commands.py` |
| 7 | `tests/integration/file_detail_reading/test_file_detail_hunk_commands.py` |
| 4 | `tests/integration/file_detail_reading/test_file_detail_line_commands.py` |
| 8 | `tests/integration/file_detail_reading/test_file_detail_navigation_commands.py` |
| 5 | `tests/integration/file_detail_reading/test_file_detail_page_content.py` |
| 4 | `tests/integration/file_detail_reading/test_file_detail_problem_commands.py` |
| 2 | `tests/integration/file_detail_reading/test_file_detail_problem_context_copy_commands.py` |
| 1 | `tests/integration/file_detail_reading/test_file_detail_problem_context_empty_states.py` |
| 2 | `tests/integration/file_detail_reading/test_file_detail_problem_context_save_commands.py` |
| 5 | `tests/integration/file_detail_reading/test_file_detail_source_copy_commands.py` |
| 6 | `tests/integration/file_detail_reading/test_file_detail_source_navigation_commands.py` |
| 4 | `tests/integration/file_detail_reading/test_problem_diff_copy_commands.py` |
| 1 | `tests/integration/file_detail_reading/test_source_file_symbol_save_commands.py` |
| 5 | `tests/integration/file_detail_reading/test_task_problem_copy_single_commands.py` |
| 8 | `tests/integration/miscellaneous/test_browser_command_executor.py` |
| 4 | `tests/integration/miscellaneous/test_done_next_commands.py` |
| 1 | `tests/integration/miscellaneous/test_task_browser_entrypoints.py` |
| 7 | `tests/integration/review_notes/test_review_note_copy_commands.py` |
| 5 | `tests/integration/review_notes/test_review_note_lines.py` |
| 6 | `tests/integration/review_notes/test_review_note_list_commands.py` |
| 4 | `tests/integration/review_notes/test_review_note_save_commands.py` |
| 4 | `tests/integration/review_notes/test_review_note_state.py` |
| 4 | `tests/integration/scope_and_workspace/test_git_scopes.py` |
| 6 | `tests/integration/scope_and_workspace/test_index_actions.py` |
| 2 | `tests/integration/scope_and_workspace/test_page_history.py` |
| 2 | `tests/integration/scope_and_workspace/test_prompt_handoff_scope_save_commands.py` |
| 5 | `tests/integration/scope_and_workspace/test_review_workspace_scope_lifecycle.py` |
| 4 | `tests/integration/scope_and_workspace/test_review_workspace_seen_filters.py` |
| 3 | `tests/integration/scope_and_workspace/test_review_workspace_source_filters.py` |
| 2 | `tests/integration/scope_and_workspace/test_review_workspace_state_persistence.py` |
| 4 | `tests/integration/scope_and_workspace/test_scope_home_commands.py` |
| 2 | `tests/integration/scope_and_workspace/test_scope_home_display.py` |
| 3 | `tests/integration/scope_and_workspace/test_scope_home_selection.py` |
| 3 | `tests/integration/scope_and_workspace/test_selected_file_stage_actions.py` |
| 5 | `tests/integration/scope_and_workspace/test_task_problem_copy_file_scope_commands.py` |
| 9 | `tests/integration/scope_and_workspace/test_workspace_persistence.py` |
| 4 | `tests/integration/source_reading_symbols/test_current_task_problem_save_commands.py` |
| 4 | `tests/integration/source_reading_symbols/test_problem_diff_save_commands.py` |
| 1 | `tests/integration/source_reading_symbols/test_source_file_context_configuration.py` |
| 5 | `tests/integration/source_reading_symbols/test_source_file_context_copy_commands.py` |
| 4 | `tests/integration/source_reading_symbols/test_source_file_context_empty_states.py` |
| 1 | `tests/integration/source_reading_symbols/test_source_file_context_save_commands.py` |
| 6 | `tests/integration/source_reading_symbols/test_source_file_find_symbol_navigation.py` |
| 3 | `tests/integration/source_reading_symbols/test_source_file_navigation_commands.py` |
| 1 | `tests/integration/source_reading_symbols/test_source_file_page_content.py` |
| 4 | `tests/integration/source_reading_symbols/test_source_file_rendering.py` |
| 8 | `tests/integration/source_reading_symbols/test_source_file_selection_commands.py` |
| 5 | `tests/integration/source_reading_symbols/test_source_file_symbol_copy_commands.py` |
| 1 | `tests/integration/source_reading_symbols/test_source_file_symbol_empty_states.py` |
| 4 | `tests/integration/task_problem_list/test_problem_context_empty_failure_commands.py` |
| 4 | `tests/integration/task_problem_list/test_source_problem_context_line_copy_commands.py` |
| 2 | `tests/integration/task_problem_list/test_source_problem_context_save_commands.py` |
| 2 | `tests/integration/task_problem_list/test_source_problem_context_selection_copy_commands.py` |
| 5 | `tests/integration/task_problem_list/test_task_problem_copy_collection_commands.py` |
| 3 | `tests/integration/task_problem_list/test_task_problem_list_save_commands.py` |
| 8 | `tests/integration/task_problem_list/test_task_problem_page_content.py` |
| 5 | `tests/integration/task_problem_list/test_task_problem_page_filters.py` |
| 8 | `tests/integration/task_problem_list/test_task_problem_page_opening.py` |
| 5 | `tests/integration/task_problem_list/test_task_problem_page_selection.py` |
| 4 | `tests/integration/tui_navigation/test_browser_feedback.py` |
| 1 | `tests/integration/tui_navigation/test_browser_main_loop.py` |
| 3 | `tests/integration/tui_navigation/test_browser_redraw.py` |

### 端到端 / CLI 工作流测试

| Cases | File |
| ---: | --- |
| 2 | `tests/e2e/build_tasks_output/test_cli_browser_task_workflows.py` |
| 6 | `tests/e2e/cli_workflows/test_cli_browser_entry_navigation.py` |
| 8 | `tests/e2e/cli_workflows/test_cli_review_filtering.py` |
| 6 | `tests/e2e/cli_workflows/test_cli_review_output.py` |
| 7 | `tests/e2e/scope_and_workspace/test_cli_browser_scope_workflows.py` |
| 6 | `tests/e2e/scope_and_workspace/test_cli_browser_workspace_workflows.py` |
| 7 | `tests/e2e/scope_and_workspace/test_cli_review_scopes.py` |

## 调整方向

近期目标不是删除大批 integration 测试，而是停止继续倒挂：新需求优先抽规则到 `cr.review`、`cr.source`、`cr.vcs` 或更小的 `cr.ui.*` 模块，并让 UT 数量逐步超过 integration。
