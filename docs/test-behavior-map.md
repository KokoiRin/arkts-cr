# Test Behavior Map

This document is generated from `# Behavior:` comments in the test suite.

- Behavior cases: 569
- Source directory: `tests/`
- Requirement links are currently placeholders: `[Requirement: TODO]` in source comments.

## Groups

- 范围与工作区入口: 76 cases
- 提交选择: 8 cases
- 变更文件列表: 67 cases
- 文件详情阅读: 80 cases
- 源码阅读与符号: 70 cases
- 构建任务与输出: 89 cases
- 任务问题列表: 61 cases
- 上下文复制与保存: 11 cases
- 评审备注: 26 cases
- 命令面板与帮助: 19 cases
- CLI 工作流: 18 cases
- TUI 框架与导航: 22 cases
- 底层格式化与解析: 10 cases
- 其他行为: 12 cases

## 范围与工作区入口

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_back_from_commit_file_returns_to_commit_file_list` | 当用户在scope home中验证cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_can_open_scope_home_in_line_mode` | 当用户在scope home中打开范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_can_switch_from_worktree_to_recent_commits` | 当用户在scope home中切换cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_can_switch_review_scopes_in_line_mode` | 当用户在scope home中切换cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_can_switch_to_base_and_range_scopes` | 当用户在scope home中切换cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_filters_recent_commits_in_line_mode` | 当用户在scope home中过滤cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_scope_workflows.py` | `test_cli_browser_shows_recent_commits_when_no_worktree_changes` | 当用户在scope home中展示cli、scope、workflows、cli时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_can_mark_seen_and_show_remaining_files` | 当用户在CLI browser中展示工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_can_unmark_seen_and_return_to_all_files` | 当用户在CLI browser中验证工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_explicit_scope_ignores_saved_workspace` | 当用户在scope home中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_ignores_malformed_saved_workspace` | 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_pathspec_ignores_saved_workspace_filter` | 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_workspace_workflows.py` | `test_cli_browser_restores_saved_workspace_filter_and_file` | 当用户在CLI browser中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_can_review_all_staged_and_unstaged_changes_together` | 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_can_review_staged_changes` | 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_can_review_staged_deletions` | 当用户在scope home中验证cli、scopes、cli、can时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_includes_untracked_files_only_when_requested` | 当用户在scope home中验证cli、scopes、cli、includes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_notes_when_the_other_git_side_has_changes` | 当用户在scope home中验证cli、scopes、cli、notes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_review_compares_against_named_base` | 当用户在scope home中验证cli、scopes、cli、compares时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_scopes.py` | `test_cli_review_compares_explicit_ref_range_without_checkout` | 当用户在scope home遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_commit_picker_filtering.py` | `test_commit_picker_filter_matches_scope_summary_fields` | 当用户在scope home中过滤提交选择器、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_rendering.py` | `test_browse_screen_recent_commits_stays_scope_picker` | 当用户在scope home中验证提交选择器、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_git_scopes.py` | `test_git_all_changes_marks_mixed_staged_and_unstaged_sources` | 当用户在scope home中标记git、scopes、git、all时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_git_scopes.py` | `test_git_comparison_scopes_do_not_mark_local_sources` | 当用户在scope home中验证git、scopes、git、comparison时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_git_scopes.py` | `test_git_local_scopes_mark_staged_and_unstaged_sources` | 当用户在scope home中验证git、scopes、git、local时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_git_scopes.py` | `test_git_recent_commits_include_change_summary` | 当用户在scope home中验证git、scopes、git、recent时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_prompt_handoff_saves_scope_and_file_prompts_to_repo_relative_paths` | 当用户在scope home中保存提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_index_actions.py` | `test_browser_command_executor_stage_failure_does_not_refresh_scope` | 当用户在scope home遇到失败反馈时，系统应给出正确反馈或保持安全状态 |
| `tests/test_index_actions.py` | `test_browser_command_executor_stages_selected_file_and_refreshes_scope` | 当用户在scope home中选择index、actions、stages、refreshes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_index_actions.py` | `test_browser_command_executor_unstages_selected_file_and_refreshes_scope` | 当用户在scope home中选择index、actions、unstages、refreshes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_page_history.py` | `test_switch_review_scope_resets_page_history` | 当用户在scope home中切换history、switch、scope、resets时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_copies_visible_scope_prompt` | 当用户在scope home中复制提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_does_not_copy_empty_scope_prompt` | 当用户在scope home遇到提示词交接时，系统应给出正确反馈或保持安全状态 |
| `tests/test_prompt_handoff_scope_save_commands.py` | `test_browser_command_executor_does_not_save_empty_scope_prompt` | 当用户在scope home遇到提示词交接时，系统应给出正确反馈或保持安全状态 |
| `tests/test_prompt_handoff_scope_save_commands.py` | `test_browser_command_executor_saves_visible_scope_prompt_default_path` | 当用户在scope home中保存提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_scope_lifecycle.py` | `test_review_workspace_is_used_by_main_browser_implementation` | 当用户在scope home中验证工作区、生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_scope_lifecycle.py` | `test_review_workspace_loads_filters_and_switches_scope` | 当用户在scope home中过滤工作区、生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_scope_lifecycle.py` | `test_review_workspace_reloads_changes_preserving_selected_path` | 当用户在scope home中选择工作区、生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_scope_lifecycle.py` | `test_review_workspace_selects_commit_scope_and_captures_previous_scope` | 当用户在scope home中选择工作区、生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_scope_lifecycle.py` | `test_switch_review_scope_resets_view_state_but_keeps_task_panel` | 当用户在scope home中切换工作区、生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_seen_filters.py` | `test_browser_remaining_only_filters_seen_paths` | 当用户在workspace中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_seen_filters.py` | `test_review_workspace_mark_seen_and_advance_reports_last_file` | 当用户在workspace遇到工作区时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_workspace_seen_filters.py` | `test_review_workspace_mark_seen_and_advance_uses_remaining_index` | 当用户在workspace中验证工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_seen_filters.py` | `test_review_workspace_marks_selected_file_seen` | 当用户在workspace中选择工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_source_filters.py` | `test_browser_state_syncs_source_filter_with_workspace` | 当用户在workspace中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_source_filters.py` | `test_review_workspace_scope_switch_clears_source_filter` | 当用户在scope home中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_source_filters.py` | `test_review_workspace_source_filter_combines_with_path_and_remaining_filters` | 当用户在workspace中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_state_persistence.py` | `test_review_workspace_persists_source_filter` | 当用户在workspace中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_workspace_state_persistence.py` | `test_review_workspace_serializes_and_restores_workspace_state_data` | 当用户在workspace中验证工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_commands.py` | `test_scope_home_command_loads_scope_counts` | 当用户在scope home中加载范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_commands.py` | `test_scope_home_command_opens_scope_home` | 当用户在scope home中打开范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_commands.py` | `test_scope_home_count_loader_counts_review_scope_candidates` | 当用户在scope home中加载范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_commands.py` | `test_scope_home_refresh_reloads_scope_counts` | 当用户在scope home中加载范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_display.py` | `test_browse_screen_scope_home_shows_review_scope_entries` | 当用户在scope home中展示范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_display.py` | `test_scope_home_screen_shows_live_scope_counts` | 当用户在scope home中展示范围首页时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_selection.py` | `test_home_key_still_jumps_to_first_file_instead_of_opening_scope_home` | 当用户在scope home中打开范围首页、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_selection.py` | `test_scope_home_enter_opens_recent_commits` | 当用户在scope home中打开范围首页、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_scope_home_selection.py` | `test_scope_home_enter_switches_to_staged_scope` | 当用户在scope home中切换范围首页、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_note_actions.py` | `test_set_selected_review_note_updates_workspace_and_clears_file_cache` | 当用户在review note中选择评审备注、工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_stage_actions.py` | `test_stage_selected_path_is_available_for_local_scopes` | 当用户在scope home中选择stage、actions、stage、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_stage_actions.py` | `test_stage_selected_path_rejects_read_only_scopes` | 当用户在scope home中选择stage、actions、stage、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_stage_actions.py` | `test_unstage_selected_path_is_available_for_local_scopes` | 当用户在scope home中选择stage、actions、unstage、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_file_scope_commands.py` | `test_browser_command_executor_copies_file_detail_current_file_task_problems` | 当用户在scope home中复制文件详情、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_file_scope_commands.py` | `test_browser_command_executor_copies_selected_file_task_problems` | 当用户在scope home中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_file_scope_commands.py` | `test_browser_command_executor_copies_visible_selected_file_task_problems` | 当用户在scope home中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_file_scope_commands.py` | `test_browser_command_executor_reports_empty_selected_file_task_problems` | 当用户在scope home遇到任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_copy_file_scope_commands.py` | `test_browser_command_executor_reports_file_detail_current_file_without_task_problems` | 当用户在scope home遇到缺少前置条件、文件详情、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_does_not_persist_task_history` | 当用户在workspace中不执行工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_falls_back_to_index_when_path_is_missing` | 当用户在workspace遇到缺失状态、工作区时，系统应给出正确反馈或保持安全状态 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_restores_scope_filter_and_selected_path` | 当用户在scope home中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_saves_and_restores_progress_markers` | 当用户在workspace中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_saves_and_restores_review_notes` | 当用户在review note中保存评审备注、工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_browser_workspace_state_saves_under_git_dir` | 当用户在workspace中保存工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_workspace_state_ignores_invalid_json_version_or_schema` | 当用户在workspace中验证工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_workspace_state_persists_review_progress_filter_and_notes` | 当用户在review note中过滤工作区时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_workspace_persistence.py` | `test_workspace_state_uses_git_cr_path_and_skips_explicit_scopes` | 当用户在scope home中验证工作区时，系统应完成对应行为并保持页面状态正确 |

## 提交选择

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_commit_picker_filtering.py` | `test_commit_picker_filter_commands_are_isolated_from_file_filter` | 当用户在commit picker中过滤提交选择器、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_filtering.py` | `test_commit_picker_search_keeps_the_changed_file_filter` | 当用户在commit picker中过滤提交选择器、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_rendering.py` | `test_browse_screen_selected_commit_files_show_product_breadcrumb` | 当用户在commit picker中展示提交选择器、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_rendering.py` | `test_commit_picker_filter_empty_state` | 当用户在commit picker遇到空状态、提交选择器、渲染时，系统应给出正确反馈或保持安全状态 |
| `tests/test_commit_picker_rendering.py` | `test_commit_picker_filter_shows_matches_and_count` | 当用户在commit picker中展示提交选择器、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_rendering.py` | `test_commit_picker_rows_show_change_summary` | 当用户在commit picker中展示提交选择器、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_selection.py` | `test_commit_picker_number_selects_filtered_commit` | 当用户在commit picker中过滤提交选择器、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_commit_picker_selection.py` | `test_commit_picker_opens_the_selected_filtered_commit` | 当用户在commit picker中打开提交选择器、选择时，系统应完成对应行为并保持页面状态正确 |

## 变更文件列表

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_changed_file_page_content.py` | `test_browse_filter_matches_paths_and_clamps_selection` | 当用户在产品行为中过滤选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_browse_list_lines_wrapper_passes_source_filter` | 当用户在产品行为中过滤changed、content、browse、list时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_browse_screen_only_measures_visible_list_rows` | 当用户在产品行为中验证changed、content、browse、only时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_browse_tree_highlights_guides_and_uses_plain_white_file_names` | 当用户在产品行为中验证changed、content、browse、tree时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_builds_compacted_changed_file_tree` | 当用户在task output中验证changed、content、content、builds时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_changed_file_header_shows_source_filter` | 当用户在产品行为中展示changed、content、content、changed时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_changed_file_header_shows_source_summary` | 当用户在产品行为中展示changed、content、content、changed时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_changed_file_rows_show_source_badges` | 当用户在产品行为中展示changed、content、content、changed时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_owns_prompt_labels_and_scroll_window` | 当用户在产品行为中验证changed、content、content、owns时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_changed_file_page_content.py` | `test_page_content_source_summary_omits_zero_and_empty_sources` | 当用户在产品行为遇到changed、content、content、summary时，系统应给出正确反馈或保持安全状态 |
| `tests/test_command_palette_catalog.py` | `test_command_palette_lists_selected_file_index_actions` | 当用户在command palette中选择命令面板时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_execution.py` | `test_command_palette_back_restores_the_changed_file_list_selection` | 当用户在command palette中选择命令面板、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_filtering.py` | `test_command_palette_search_keeps_the_changed_file_filter` | 当用户在command palette中过滤命令面板、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_done_next_commands.py` | `test_browser_command_executor_marks_done_and_moves_next_in_changed_files` | 当用户在产品行为中移动done、next、marks、done时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browse_parser_accepts_file_action_command_configuration` | 当系统处理file action的配置时，系统应解析出正确结果 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_anchor_falls_back_to_path_without_line` | 当用户在file action遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_copies_selected_anchor` | 当用户在file action中复制action、copies、anchor时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_copies_selected_path` | 当用户在file action中复制action、copies、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_opens_selected_file` | 当用户在file action中打开action、opens时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_reveals_selected_file` | 当用户在file action中选择action、reveals时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browser_command_executor_shows_file_action_diagnostics` | 当用户在file action中展示action、shows、action、diagnostics时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_browser_commands.py` | `test_browser_file_actions_report_when_no_changed_file_is_available` | 当用户在file action中验证action、actions、report、no时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_discover_macos_clipboard_and_reveal_commands` | 当用户在file action中验证action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_include_source_in_failures` | 当用户在file action遇到失败反馈时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_report_missing_platform_commands` | 当用户在file action遇到缺失状态时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_use_configured_copy_command` | 当用户在file action中复制action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_use_configured_reveal_command` | 当用户在file action中验证action、copy、reveal、helpers时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_copy_reveal_helpers.py` | `test_file_action_helpers_use_environment_configuration` | 当用户在file action中验证配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_open_helpers.py` | `test_file_action_helpers_include_source_in_open_failures` | 当用户在file action遇到失败反馈时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_action_open_helpers.py` | `test_open_command_falls_back_to_macos_open` | 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_open_helpers.py` | `test_open_command_prefers_gui_editor_with_line` | 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_action_open_helpers.py` | `test_open_command_source_reports_cli_env_platform_and_missing` | 当用户在file action遇到缺失状态时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_action_open_helpers.py` | `test_open_command_uses_configured_template` | 当用户在file action中打开action、open、helpers、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_refresh_rendering.py` | `test_refresh_preserves_file_detail_when_selected_file_survives` | 当用户在file detail中选择文件详情、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_refresh_rendering.py` | `test_refresh_returns_to_changed_files_when_file_detail_disappears` | 当用户在file detail中刷新文件详情、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_index_actions.py` | `test_browser_command_executor_stage_reports_empty_selection` | 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_index_actions.py` | `test_browser_command_executor_unstage_reports_empty_selection` | 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_index_actions.py` | `test_git_stage_and_unstage_path_update_index` | 当用户在file action中验证index、actions、git、stage时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_copy_commands.py` | `test_browser_command_executor_does_not_copy_problem_diff_without_changed_file` | 当用户在task problem遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_diff_view_commands.py` | `test_browser_command_executor_reports_problem_diff_without_changed_file` | 当用户在task problem遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_copies_selected_file_prompt` | 当用户在prompt handoff中复制提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_selected_file_save_commands.py` | `test_browser_command_executor_saves_selected_file_prompt_default_path` | 当用户在prompt handoff中保存提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_selected_file_save_commands.py` | `test_browser_command_executor_saves_selected_file_prompt_explicit_path` | 当用户在prompt handoff中保存提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_edit_commands.py` | `test_browser_command_executor_sets_and_clears_selected_file_note` | 当用户在review note中选择评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_diff_commands.py` | `test_browser_command_executor_copies_selected_diff_in_raw_status` | 当用户在产品行为中复制diff、copies、diff、raw时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_diff_commands.py` | `test_browser_command_executor_copies_selected_diff_snippet` | 当用户在产品行为中复制diff、copies、diff、snippet时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_diff_commands.py` | `test_browser_command_executor_saves_selected_diff_in_raw_status` | 当用户在产品行为中保存diff、saves、diff、raw时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_diff_commands.py` | `test_browser_command_executor_saves_selected_diff_snippet` | 当用户在产品行为中保存diff、saves、diff、snippet时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_diff_actions.py` | `test_copy_diff_handoff_contains_only_the_selected_file` | 当用户在prompt handoff中复制diff、actions、copy、diff时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_diff_actions.py` | `test_copy_selected_diff_snippet_reports_empty_selection` | 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_selected_file_diff_actions.py` | `test_save_selected_diff_snippet_reports_empty_selection` | 当用户在file action遇到选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_selected_file_diff_actions.py` | `test_save_selected_diff_snippet_reports_write_failure` | 当用户在file action遇到失败反馈时，系统应给出正确反馈或保持安全状态 |
| `tests/test_selected_file_diff_actions.py` | `test_save_selected_diff_snippet_writes_default_handoff_file` | 当用户在prompt handoff中保存diff、actions、save、diff时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_copy_selected_change_renders_current_added_row` | 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_copy_selected_change_renders_current_deleted_row` | 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_copy_selected_hunk_renders_only_active_hunk` | 当用户在file detail中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_copy_selected_line_copies_current_new_file_anchor` | 当用户在file action中复制line、change、actions、copy时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_open_hunk_targets_the_active_hunk_line` | 当用户在file detail中打开line、change、actions、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_line_change_actions.py` | `test_open_line_targets_the_current_added_line` | 当用户在file action中打开line、change、actions、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_note_actions.py` | `test_change_note_describes_the_current_added_row` | 当用户在review note中验证note、actions、change、note时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_note_actions.py` | `test_change_note_describes_the_current_deleted_row` | 当用户在review note中验证note、actions、change、note时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_prompt_actions.py` | `test_prompt_handoff_contains_only_the_selected_file` | 当用户在prompt handoff中选择提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_reference_actions.py` | `test_copy_anchor_points_to_the_first_changed_line` | 当用户在file action中复制reference、actions、copy、anchor时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_selected_file_reference_actions.py` | `test_copy_selected_path_returns_status_message` | 当用户在file action中复制reference、actions、copy、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_snippet.py` | `test_file_diff_snippet_renders_compact_selected_file_context` | 当用户在file action中渲染snippet、diff、snippet、renders时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_navigation_commands.py` | `test_browser_command_executor_reports_source_file_diff_without_changed_file` | 当用户在source file遇到缺少前置条件、源码文件、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_tree.py` | `test_renders_changed_files_as_directory_tree` | 当用户在产品行为中渲染tree、renders、changed、directory时，系统应完成对应行为并保持页面状态正确 |

## 文件详情阅读

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_cli_review_output.py` | `test_cli_compacts_deep_paths_and_can_color_diff_hunks` | 当用户在file detail中验证cli、output、cli、compacts时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_output.py` | `test_cli_review_accepts_configurable_hunk_context` | 当用户在file detail中验证cli、output、cli、accepts时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_current_task_problem_save_commands.py` | `test_browser_command_executor_saves_file_detail_current_row_task_problem` | 当用户在file detail中保存文件详情、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_copies_current_change_in_file_detail` | 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_notes_current_change_in_file_detail` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_reports_change_note_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_reports_change_note_without_changed_row` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_reports_copy_change_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_change_commands.py` | `test_browser_command_executor_reports_copy_change_without_changed_row` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_finds_text_in_file_detail` | 当用户在file detail中查找文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_repeats_file_detail_find_matches` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_reports_empty_and_missing_find` | 当用户在file detail遇到缺失状态、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_reports_find_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_reports_repeat_find_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_reports_repeat_find_without_matches` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_find_commands.py` | `test_browser_command_executor_reports_repeat_find_without_query` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_copies_current_hunk_in_file_detail` | 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_reports_copy_hunk_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_reports_copy_hunk_without_hunks` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_reports_hunk_navigation_outside_file_detail` | 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_reports_open_hunk_without_hunks` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_surfaces_copy_hunk_failure` | 当用户在file detail遇到失败反馈、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_hunk_commands.py` | `test_browser_command_executor_surfaces_open_hunk_failure` | 当用户在file detail遇到失败反馈、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_line_commands.py` | `test_browser_command_executor_copies_current_line_in_file_detail` | 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_line_commands.py` | `test_browser_command_executor_opens_current_line_in_file_detail` | 当用户在file detail中打开文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_line_commands.py` | `test_browser_command_executor_reports_line_action_outside_file_detail` | 当用户在file detail遇到文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_line_commands.py` | `test_browser_command_executor_reports_line_action_without_new_line` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_navigation.py` | `test_active_hunk_extracts_sanitized_diff_lines_and_position` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_active_hunk_line_uses_nearest_rendered_hunk_header` | 当用户在file detail中渲染文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_changed_row_navigation_wraps_between_added_and_deleted_rows` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_current_changed_row_distinguishes_added_and_deleted_rows` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_current_new_line_ignores_deleted_and_metadata_rows` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_file_detail_find_matches_rendered_text_without_ansi_styles` | 当用户在file detail遇到缺少前置条件、文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_navigation.py` | `test_hunk_navigation_clamps_scroll_to_visible_window` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_hunk_navigation_moves_between_rendered_hunk_headers` | 当用户在file detail中渲染文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation.py` | `test_hunk_navigation_reports_edges_and_empty_diff` | 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_navigation.py` | `test_repeated_file_detail_find_wraps_in_both_directions` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_jumps_between_changed_rows_in_file_detail` | 当用户在file detail中跳转文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_jumps_to_next_hunk_in_file_detail` | 当用户在file detail中跳转文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_jumps_to_previous_hunk_in_file_detail` | 当用户在file detail中跳转文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_marks_done_and_opens_next_file_detail` | 当用户在file detail中打开文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_opens_current_hunk_in_file_detail` | 当用户在file detail中打开文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_reports_changed_row_navigation_outside_file_detail` | 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_reports_changed_row_navigation_without_changed_rows` | 当用户在file detail遇到缺少前置条件、文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_navigation_commands.py` | `test_browser_command_executor_reports_open_hunk_outside_file_detail` | 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_page_content.py` | `test_browse_file_lines_show_seen_or_todo_status` | 当用户在file detail中展示文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_page_content.py` | `test_browse_file_screen_omits_review_queue_dock_when_short` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_page_content.py` | `test_browse_file_screen_scrolls_long_content` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_page_content.py` | `test_browse_file_screen_shows_review_queue_dock` | 当用户在file detail中展示文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_page_content.py` | `test_browse_lines_show_review_notes` | 当用户在file detail中展示文件详情、评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_commands.py` | `test_browser_command_executor_reports_file_detail_without_file_problems` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_problem_commands.py` | `test_browser_command_executor_steps_file_detail_previous_problem` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_commands.py` | `test_browser_command_executor_steps_file_detail_problem_to_visible_diff_line` | 当用户在file detail中验证文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_commands.py` | `test_browser_command_executor_steps_file_detail_problem_without_visible_diff_line` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_problem_context_copy_commands.py` | `test_browser_command_executor_copies_file_detail_problem_context` | 当用户在file detail中复制问题上下文、文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_context_copy_commands.py` | `test_browser_command_executor_copies_file_detail_problem_context_with_current_problem` | 当用户在file detail中复制当前问题、问题上下文、文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_context_empty_states.py` | `test_browser_command_executor_reports_file_detail_problem_context_without_new_line` | 当用户在file detail遇到空状态、缺少前置条件、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_problem_context_save_commands.py` | `test_browser_command_executor_saves_file_detail_problem_context` | 当用户在file detail中保存问题上下文、文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_problem_context_save_commands.py` | `test_browser_command_executor_saves_file_detail_problem_context_with_current_problem` | 当用户在file detail中保存当前问题、问题上下文、文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_refresh_rendering.py` | `test_browse_screen_file_detail_shows_product_breadcrumb` | 当用户在file detail中展示文件详情、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_copy_commands.py` | `test_browser_command_executor_copies_file_detail_source_context` | 当用户在file detail中复制源码上下文、文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_copy_commands.py` | `test_browser_command_executor_copies_file_detail_source_symbol` | 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_copy_commands.py` | `test_browser_command_executor_does_not_use_selected_problem_for_file_detail_context` | 当用户在file detail中选择文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_copy_commands.py` | `test_browser_command_executor_reports_file_detail_copy_source_without_new_line` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_source_copy_commands.py` | `test_browser_command_executor_reports_file_detail_copy_symbol_without_new_line` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_reports_view_source_outside_file_detail` | 当用户在file detail遇到文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_reports_view_source_symbol_without_new_line` | 当用户在file detail遇到缺少前置条件、文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_reports_view_source_without_new_line` | 当用户在file detail遇到缺少前置条件、文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_views_current_file_detail_source_line` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_views_current_file_detail_source_symbol` | 当用户在file detail中验证文件详情、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_file_detail_source_navigation_commands.py` | `test_browser_command_executor_views_source_symbol_line_without_symbol` | 当用户在file detail遇到缺少前置条件、文件详情、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_hunks.py` | `test_renders_hunks_without_git_file_headers` | 当用户在file detail遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_hunks.py` | `test_truncates_long_hunks` | 当用户在file detail中验证hunks、truncates、long、hunks时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_copy_commands.py` | `test_browser_command_executor_copies_file_detail_current_row_problem_diff` | 当用户在file detail中复制文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_copy_commands.py` | `test_browser_command_executor_does_not_copy_file_detail_row_problem_diff_without_problem` | 当用户在file detail遇到缺少前置条件、文件详情时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_diff_save_commands.py` | `test_browser_command_executor_saves_file_detail_current_row_problem_diff` | 当用户在file detail中保存文件详情时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_save_commands.py` | `test_browser_command_executor_saves_file_detail_source_symbol` | 当用户在file detail中保存文件详情、源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_single_commands.py` | `test_browser_command_executor_copies_file_detail_current_row_task_problem` | 当用户在file detail中复制文件详情、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_single_commands.py` | `test_browser_command_executor_does_not_copy_file_detail_row_without_problem` | 当用户在file detail遇到缺少前置条件、文件详情、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_list_save_commands.py` | `test_browser_command_executor_saves_file_detail_current_file_task_problems` | 当用户在file detail中保存文件详情、任务问题时，系统应完成对应行为并保持页面状态正确 |

## 源码阅读与符号

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_cli_review_output.py` | `test_cli_diff_outline_and_review_in_temp_repo` | 当用户在source file中验证cli、output、cli、diff时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_catalog.py` | `test_command_list_lines_group_commands_by_purpose` | 当用户在产品行为中验证catalog、list、lines、group时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_current_task_problem_save_commands.py` | `test_browser_command_executor_does_not_save_stale_source_file_problem` | 当用户在source file遇到过期状态、源码文件、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_current_task_problem_save_commands.py` | `test_browser_command_executor_saves_source_file_current_task_problem` | 当用户在source file中保存源码文件、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_outline_parsing.py` | `test_maps_changed_lines_to_methods` | 当系统处理source file的outline、parsing、maps、changed时，系统应映射出正确结果 |
| `tests/test_outline_parsing.py` | `test_parses_arkts_structure` | 当系统处理source file的outline、parsing、parses、arkts时，系统应解析出正确结果 |
| `tests/test_outline_parsing.py` | `test_parses_enum_blocks_as_symbols` | 当系统处理source file的outline、parsing、parses、enum时，系统应解析出正确结果 |
| `tests/test_outline_parsing.py` | `test_parses_generic_function_like_symbols` | 当系统处理source file的outline、parsing、parses、generic时，系统应解析出正确结果 |
| `tests/test_outline_parsing.py` | `test_parses_override_and_accessor_members` | 当系统处理source file的outline、parsing、parses、override时，系统应解析出正确结果 |
| `tests/test_outline_parsing.py` | `test_renders_tree` | 当用户在source file中渲染outline、parsing、renders、tree时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_current_nested_or_top_level_symbol` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_declaration_only_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_default_export_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_enum_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_exported_arrow_function_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_field_arrow_function_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_generic_symbols` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_outline_symbol_labels.py` | `test_symbol_label_identifies_override_and_accessor_members` | 当系统处理source file的outline、symbol、labels、symbol时，系统应识别出正确结果 |
| `tests/test_page_help_and_actions.py` | `test_help_screen_lists_source_file_commands` | 当用户在source file中验证源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_save_commands.py` | `test_browser_command_executor_does_not_save_stale_source_file_problem_diff` | 当用户在source file遇到过期状态、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_diff_save_commands.py` | `test_browser_command_executor_saves_source_file_current_problem_diff` | 当用户在source file中保存当前问题、源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_purpose.py` | `test_describes_arkts_page_component_from_path_and_symbols` | 当用户在产品行为中验证purpose、describes、arkts、component时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_purpose.py` | `test_describes_function_module` | 当用户在产品行为中验证purpose、describes、function、module时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_purpose.py` | `test_falls_back_to_path_when_no_symbols_are_found` | 当用户在产品行为中验证purpose、falls、back、path时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file.py` | `test_source_content_reads_lines_and_reports_missing_files` | 当用户在source file遇到缺失状态、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file.py` | `test_source_context_markdown_centers_target_and_can_include_symbol_label` | 当用户在source file中验证源码上下文、源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file.py` | `test_source_range_selection_marks_rows_and_renders_ordered_markdown` | 当用户在source file中渲染源码文件、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file.py` | `test_source_view_clamps_line_and_reports_missing_or_non_utf8_files` | 当用户在source file遇到缺失状态、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file.py` | `test_source_view_windows_the_target_line_inside_repo_file` | 当用户在source file中验证源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_configuration.py` | `test_browser_command_executor_sets_source_context_lines` | 当用户在source file中验证源码上下文、源码文件、配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_copy_commands.py` | `test_browser_command_executor_copies_configured_source_file_context` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_copy_commands.py` | `test_browser_command_executor_copies_selected_source_range` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_copy_commands.py` | `test_browser_command_executor_copies_source_file_context` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_copy_commands.py` | `test_browser_command_executor_copies_source_file_context_with_symbol` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_copy_commands.py` | `test_browser_command_executor_copies_source_file_page_line` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_context_empty_states.py` | `test_browser_command_executor_reports_empty_source_context_copy` | 当用户在source file遇到空状态、源码上下文、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_context_empty_states.py` | `test_browser_command_executor_reports_empty_source_file_line_copy` | 当用户在source file遇到空状态、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_context_empty_states.py` | `test_browser_command_executor_reports_missing_source_context_copy` | 当用户在source file遇到空状态、缺失状态、源码上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_context_empty_states.py` | `test_browser_command_executor_reports_source_context_without_source_page` | 当用户在source file遇到空状态、缺少前置条件、源码上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_context_save_commands.py` | `test_browser_command_executor_saves_selected_source_context_default_path` | 当用户在source file中保存源码上下文、源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_finds_text_in_source_file_page` | 当用户在source file中查找源码文件、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_jumps_source_file_symbols` | 当用户在source file中跳转源码文件、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_repeats_source_file_find_matches` | 当用户在source file中验证源码文件、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_reports_source_file_find_empty_states` | 当用户在source file遇到空状态、源码文件、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_reports_source_symbol_jump_boundaries` | 当用户在source file遇到源码文件、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_find_symbol_navigation.py` | `test_browser_command_executor_reports_source_symbol_jump_empty_states` | 当用户在source file遇到空状态、源码文件、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_navigation_commands.py` | `test_browser_command_executor_scrolls_and_opens_source_file_page` | 当用户在source file中打开源码文件、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_navigation_commands.py` | `test_browser_command_executor_views_source_file_diff` | 当用户在source file中验证源码文件、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_page_content.py` | `test_source_file_screen_renders_source_rows_and_error` | 当用户在source file中渲染源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_rendering.py` | `test_browse_screen_renders_source_file_page` | 当用户在source file中渲染源码文件、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_rendering.py` | `test_browse_source_file_screen_lines_hides_stale_task_problem` | 当用户在source file遇到过期状态、源码文件、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_rendering.py` | `test_browse_source_file_screen_lines_show_current_symbol` | 当用户在source file中展示源码文件、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_rendering.py` | `test_browse_source_file_screen_lines_show_matching_task_problem` | 当用户在source file中展示源码文件、任务问题、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_copies_selected_source_symbol_range` | 当用户在source file中复制源码文件、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_reports_source_select_to_without_mark` | 当用户在source file遇到缺少前置条件、源码文件、选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_reports_source_selection_without_source_page` | 当用户在source file遇到缺少前置条件、源码文件、选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_reports_source_symbol_selection_without_source_page` | 当用户在source file遇到缺少前置条件、源码文件、选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_reports_source_symbol_selection_without_symbol` | 当用户在source file遇到缺少前置条件、源码文件、选择时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_selects_current_source_symbol` | 当用户在source file中选择源码文件、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_selects_source_range_from_mark_to_current_line` | 当用户在source file中选择源码文件、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_selection_commands.py` | `test_browser_command_executor_sets_and_clears_source_selection` | 当用户在source file中选择源码文件、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_copy_commands.py` | `test_browser_command_executor_copies_source_accessor_symbol` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_copy_commands.py` | `test_browser_command_executor_copies_source_enum_symbol` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_copy_commands.py` | `test_browser_command_executor_copies_source_field_arrow_symbol` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_copy_commands.py` | `test_browser_command_executor_copies_source_file_symbol_directly` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_copy_commands.py` | `test_browser_command_executor_copies_source_generic_method_symbol` | 当用户在source file中复制源码文件时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_file_symbol_empty_states.py` | `test_browser_command_executor_reports_copy_source_symbol_without_symbol` | 当用户在source file遇到空状态、缺少前置条件、源码文件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_copy_single_commands.py` | `test_browser_command_executor_copies_source_file_current_task_problem` | 当用户在source file中复制源码文件、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_single_commands.py` | `test_browser_command_executor_does_not_copy_stale_source_file_problem` | 当用户在source file遇到过期状态、源码文件、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_steps_source_file_task_problems` | 当用户在source file中验证源码文件、任务问题时，系统应完成对应行为并保持页面状态正确 |

## 构建任务与输出

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_cli_browser_task_workflows.py` | `test_cli_interactive_browser_can_run_build_command` | 当用户在task output中验证cli、workflows、cli、interactive时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_browse_screen_action_bar_coexists_with_task_panel` | 当用户在产品行为中验证frame、browse、action、bar时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_browse_screen_pads_short_content_before_task_panel` | 当用户在产品行为中验证frame、browse、pads、short时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_browse_screen_places_task_panel_above_prompt` | 当用户在产品行为中验证frame、browse、places、panel时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_browse_screen_shows_command_list_with_task_panel` | 当用户在产品行为中展示frame、browse、shows、list时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_partial_task_panel_refresh_draws_without_full_clear_once` | 当用户在产品行为遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_frame.py` | `test_partial_task_panel_refresh_refuses_dirty_frame` | 当用户在产品行为中刷新frame、partial、panel、refresh时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_screen_layout_reserves_prompt_and_task_panel_regions` | 当用户在产品行为中验证frame、layout、reserves、prompt时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_task_panel_lines_include_current_task_and_recent_history` | 当用户在navigation中验证frame、panel、lines、include时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_task_output_handoff_saves_default_and_requested_paths` | 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_packaging.py` | `test_project_avoids_isolated_build_for_offline_editable_install` | 当用户在task output中验证packaging、project、avoids、isolated时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_context.py` | `test_problem_context_includes_problem_source_task_output_and_diff_sections` | 当用户在task problem中验证问题上下文、任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_save_commands.py` | `test_browser_command_executor_saves_task_output_problem_diff_default_path` | 当用户在task problem中保存任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_view_commands.py` | `test_browser_command_executor_views_selected_task_output_problem_diff` | 当用户在task problem中选择任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_data.py` | `test_build_review_data_attaches_matching_review_notes` | 当用户在task output中验证评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_command_configuration.py` | `test_background_task_runtime_uses_task_state_names` | 当用户在task output中验证配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_command_configuration.py` | `test_browser_command_executor_shows_task_diagnostics_without_starting_task` | 当用户在产品行为遇到缺少前置条件、配置时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_command_configuration.py` | `test_browser_command_executor_shows_task_schema_help_without_starting_task` | 当用户在产品行为遇到缺少前置条件、配置时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_command_configuration.py` | `test_browser_frame_module_owns_task_panel_presentation_implementation` | 当用户在产品行为中验证配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_command_configuration.py` | `test_build_command_detects_douyin_harmony_repo` | 当用户在task output中验证配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_command_configuration.py` | `test_lint_task_without_command_shows_configuration_hint` | 当用户在产品行为遇到缺少前置条件、配置时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_command_configuration.py` | `test_task_command_does_not_guess_test_or_lint_commands` | 当用户在产品行为中不执行配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_command_configuration.py` | `test_task_command_resolves_configured_test_and_lint_commands` | 当用户在产品行为中验证配置时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_copy_commands.py` | `test_browser_command_executor_copies_task_output` | 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_copy_commands.py` | `test_browser_command_executor_copies_task_output_match` | 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_copy_commands.py` | `test_browser_command_executor_copies_task_output_tail` | 当用户在task output中复制任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_empty_states.py` | `test_browser_command_executor_copy_task_match_requires_find` | 当用户在task output中复制空状态、任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_empty_states.py` | `test_browser_command_executor_copy_task_reports_empty_state` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_empty_states.py` | `test_browser_command_executor_copy_task_tail_reports_empty_state` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_empty_states.py` | `test_browser_command_executor_save_task_reports_empty_state` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_empty_states.py` | `test_browser_command_executor_save_task_tail_reports_empty_state` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_find_commands.py` | `test_browser_command_executor_finds_text_in_task_output` | 当用户在task output中查找任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_find_commands.py` | `test_browser_command_executor_repeats_task_output_find_matches` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_find_commands.py` | `test_browser_command_executor_reports_task_output_find_empty_states` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_history.py` | `test_browse_screen_task_panel_includes_task_history` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_history.py` | `test_completed_build_records_task_history_once` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_history.py` | `test_stop_without_running_build_does_not_record_task_history` | 当用户在task output遇到缺少前置条件、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_history.py` | `test_task_panel_collects_background_output` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_history.py` | `test_task_panel_renders_recent_task_history` | 当用户在task output中渲染任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_history.py` | `test_test_task_collects_background_output_and_history` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_page_content.py` | `test_task_output_screen_renders_current_task` | 当用户在task output中渲染任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_page_content.py` | `test_task_output_screen_renders_empty_state` | 当用户在task output遇到空状态、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_page_content.py` | `test_task_output_screen_renders_selected_problem` | 当用户在task problem中渲染任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_problem_commands.py` | `test_browser_command_executor_moves_task_output_problem_selection` | 当用户在task problem中选择任务输出、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_problem_commands.py` | `test_browser_command_executor_opens_task_output_page` | 当用户在task problem中打开任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_problem_commands.py` | `test_browser_command_executor_reports_task_output_view_without_problem` | 当用户在task problem遇到缺少前置条件、任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_output_problem_commands.py` | `test_browser_command_executor_scrolls_task_output_page` | 当用户在task problem中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_problem_commands.py` | `test_browser_command_executor_views_selected_task_output_problem_source` | 当用户在task problem中选择任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_rendering.py` | `test_browse_screen_renders_task_output_page` | 当用户在task output中渲染任务输出、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_rendering.py` | `test_task_output_page_tick_redraws_main_content_not_panel_only` | 当用户在task output中验证任务输出、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_save_commands.py` | `test_browser_command_executor_saves_task_output` | 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_save_commands.py` | `test_browser_command_executor_saves_task_output_match_default_path` | 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_output_save_commands.py` | `test_browser_command_executor_saves_task_output_tail` | 当用户在task output中保存任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_panel_refresh.py` | `test_browser_status_message_marks_frame_dirty_before_task_refresh` | 当用户在产品行为中刷新panel、refresh、status、message时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_panel_refresh.py` | `test_full_browser_redraw_primes_task_panel_frame_cache` | 当用户在产品行为中验证panel、refresh、full、redraw时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_panel_refresh.py` | `test_task_panel_partial_refresh_does_not_clear_screen` | 当用户在产品行为中刷新panel、refresh、panel、partial时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_panel_refresh.py` | `test_task_panel_partial_refresh_refuses_dirty_frame` | 当用户在产品行为中刷新panel、refresh、panel、partial时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_panel_refresh.py` | `test_task_panel_partial_refresh_refuses_stale_frame_layout` | 当用户在产品行为遇到过期状态时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_context_commands.py` | `test_browser_command_executor_copies_selected_task_output_problem_context` | 当用户在task problem中复制问题上下文、任务输出、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_context_commands.py` | `test_browser_command_executor_saves_selected_task_output_problem_context` | 当用户在task problem中保存问题上下文、任务输出、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_extracts_repo_local_problem_anchors_from_task_output` | 当用户在task problem中验证任务输出、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_rerun.py` | `test_build_rerun_keeps_previous_task_history` | 当用户在task output中保持rerun、build、rerun、keeps时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_rerun.py` | `test_build_rerun_starts_new_process_after_completion` | 当用户在task output中启动rerun、build、rerun、starts时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_rerun.py` | `test_build_rerun_while_running_does_not_start_second_process` | 当用户在task output中不执行rerun、build、rerun、while时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_rerun.py` | `test_rerun_repeats_recent_test_task_kind` | 当用户在task output中验证rerun、rerun、repeats、recent时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_invalid_project_task_presets_are_ignored` | 当用户在task output中验证runtime、invalid、project、presets时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_running_task_output_handoff_reports_no_output` | 当用户在task output遇到任务输出时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_runtime.py` | `test_start_task_uses_project_task_preset` | 当用户在task output中验证runtime、start、uses、project时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_started_task_collects_output_and_records_history` | 当用户在task output中验证runtime、started、collects、output时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_command_preserves_douyin_build_default_without_preset` | 当用户在task output遇到缺少前置条件时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_runtime.py` | `test_task_commands_can_be_defined_by_project_presets` | 当用户在task output中验证runtime、can、be、defined时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_commands_use_cli_env_presets_then_defaults` | 当用户在task output中验证runtime、use、cli、env时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_commands_use_explicit_cli_test_and_lint_commands` | 当用户在task output中验证runtime、use、cli、lint时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_diagnostics_report_presets_and_douyin_default` | 当用户在task output中验证runtime、diagnostics、report、presets时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_diagnostics_report_sources_errors_and_missing_commands` | 当用户在task output遇到缺失状态时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_runtime.py` | `test_task_output_handoff_includes_kind_status_command_and_output` | 当用户在task output中验证任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_output_tail_handoff_keeps_only_recent_lines` | 当用户在task output中保持任务输出时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_runtime_owns_process_lifecycle_implementation` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_runtime.py` | `test_task_schema_help_describes_project_tasks_json` | 当用户在task output中验证runtime、schema、help、describes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_start_records_process_group_id` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_stop_falls_back_when_process_group_stop_fails` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_stop_marks_stopped_not_failed` | 当用户在task output中标记生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_stop_records_stop_request_time` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_stop_terminates_child_processes` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_build_stop_without_running_build_shows_feedback` | 当用户在task output遇到缺少前置条件、生命周期时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_stop_lifecycle.py` | `test_poll_does_not_escalate_stopped_build_within_grace_period` | 当用户在task output中不执行生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_poll_escalates_stopped_build_only_once` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_poll_escalates_stopped_build_to_process_group_kill` | 当用户在task output中验证生命周期时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_stop_lifecycle.py` | `test_poll_escalates_stopped_build_without_process_group_to_process_kill` | 当用户在task output遇到缺少前置条件、生命周期时，系统应给出正确反馈或保持安全状态 |

## 任务问题列表

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_browser_redraw.py` | `test_task_problems_page_tick_redraws_main_content_not_panel_only` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_current_task_problem_save_commands.py` | `test_browser_command_executor_saves_selected_task_problem_default_path` | 当用户在task problem中保存任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_problem_context_handoff_saves_default_and_requested_paths` | 当用户在task problem中保存问题上下文时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_problem_diff_handoff_saves_default_and_requested_paths` | 当用户在task problem中保存handoff、problem、diff、handoff时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_task_problem_handoff_saves_default_and_requested_paths` | 当用户在task problem中保存任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_context_empty_failure_commands.py` | `test_browser_command_executor_reports_empty_problem_context_copy` | 当用户在task problem遇到失败反馈、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_context_empty_failure_commands.py` | `test_browser_command_executor_reports_empty_problem_context_save` | 当用户在task problem遇到失败反馈、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_context_empty_failure_commands.py` | `test_browser_command_executor_reports_missing_problem_context_source` | 当用户在task problem遇到缺失状态、失败反馈、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_context_empty_failure_commands.py` | `test_browser_command_executor_reports_problem_context_save_failure` | 当用户在task problem遇到失败反馈、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_problem_diff_copy_commands.py` | `test_browser_command_executor_copies_selected_task_problem_diff` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_problem_diff_view_commands.py` | `test_browser_command_executor_views_selected_task_problem_diff` | 当用户在task problem中选择任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_line_copy_commands.py` | `test_browser_command_executor_copies_problem_context_without_diff` | 当用户在task problem遇到缺少前置条件、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_problem_context_line_copy_commands.py` | `test_browser_command_executor_copies_source_page_problem_context` | 当用户在task problem中复制问题上下文时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_line_copy_commands.py` | `test_browser_command_executor_copies_source_page_problem_context_with_current_problem` | 当用户在task problem中复制当前问题、问题上下文时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_line_copy_commands.py` | `test_browser_command_executor_does_not_use_stale_source_problem_for_context` | 当用户在task problem遇到过期状态、问题上下文时，系统应给出正确反馈或保持安全状态 |
| `tests/test_source_problem_context_save_commands.py` | `test_browser_command_executor_saves_selected_source_problem_context` | 当用户在task problem中保存问题上下文时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_save_commands.py` | `test_browser_command_executor_saves_source_page_problem_context_default_path` | 当用户在task problem中保存问题上下文时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_selection_copy_commands.py` | `test_browser_command_executor_copies_selected_source_problem_context` | 当用户在task problem中复制问题上下文、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_source_problem_context_selection_copy_commands.py` | `test_browser_command_executor_copies_selected_source_problem_context_with_current_problem` | 当用户在task problem中复制当前问题、问题上下文、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_context_commands.py` | `test_browser_command_executor_copies_task_problem_context_with_diff` | 当用户在task problem中复制问题上下文、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_context_commands.py` | `test_browser_command_executor_saves_task_problem_context` | 当用户在task problem中保存问题上下文、任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_collection_commands.py` | `test_browser_command_executor_copies_all_task_problems` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_collection_commands.py` | `test_browser_command_executor_copies_filtered_task_problems` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_collection_commands.py` | `test_browser_command_executor_copies_queried_task_problems` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_collection_commands.py` | `test_browser_command_executor_copies_sorted_task_problems` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_copy_collection_commands.py` | `test_browser_command_executor_does_not_copy_empty_task_problems` | 当用户在task problem遇到任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_copy_single_commands.py` | `test_browser_command_executor_copies_selected_task_problem` | 当用户在task problem中复制任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_extracts_diagnostic_facts_from_common_problem_lines` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_problem_extraction_ignores_urls_missing_files_and_outside_paths` | 当用户在task problem遇到缺失状态、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_extraction.py` | `test_problem_handoff_text_preserves_diagnostic_facts` | 当用户在task problem中保持任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_severity_count_label_summarizes_visible_problem_set` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_severity_filter_preserves_original_problem_order` | 当用户在task problem中过滤任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_extraction.py` | `test_severity_sort_buckets_problems_without_reordering_each_bucket` | 当用户在task problem遇到缺少前置条件、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_extraction.py` | `test_text_query_matches_path_summary_severity_code_or_message` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_list_save_commands.py` | `test_browser_command_executor_saves_file_task_problems_requested_path` | 当用户在task problem中保存任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_list_save_commands.py` | `test_browser_command_executor_saves_task_problems_default_path` | 当用户在task problem中保存任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_content.py` | `test_browse_screen_renders_task_problems_page` | 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_empty_state` | 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_filtered_empty_state` | 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_grouped_by_file` | 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_problem_facts` | 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_query_empty_state` | 当用户在task problem遇到空状态、任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_query_state` | 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_content.py` | `test_task_problems_screen_renders_sort_state` | 当用户在task problem中渲染任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_filters.py` | `test_browser_command_executor_filters_task_problems_by_query` | 当用户在task problem中过滤任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_filters.py` | `test_browser_command_executor_filters_task_problems_by_severity` | 当用户在task problem中过滤任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_filters.py` | `test_browser_command_executor_groups_task_problems_by_file` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_filters.py` | `test_browser_command_executor_opens_task_problems_page` | 当用户在task problem中打开任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_filters.py` | `test_browser_command_executor_sorts_task_problems_by_severity` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_opens_filtered_task_problem` | 当用户在task problem中打开任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_opens_grouped_task_problem` | 当用户在task problem中打开任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_opens_queried_task_problem` | 当用户在task problem中打开任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_opens_selected_task_problem` | 当用户在task problem中打开任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_reports_no_task_problem_to_view` | 当用户在task problem遇到任务问题时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_views_selected_task_problem_source` | 当用户在task problem中选择任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_opening.py` | `test_browser_command_executor_views_sorted_task_problem_source` | 当用户在task problem中验证任务问题时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_selection.py` | `test_browser_command_executor_jumps_between_visible_task_problem_files` | 当用户在task problem中跳转任务问题、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_selection.py` | `test_browser_command_executor_jumps_to_next_task_problem_file` | 当用户在task problem中跳转任务问题、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_selection.py` | `test_browser_command_executor_jumps_to_previous_task_problem_file` | 当用户在task problem中跳转任务问题、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_selection.py` | `test_browser_command_executor_keeps_task_problem_selection_at_file_edges` | 当用户在task problem中选择任务问题、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_task_problem_page_selection.py` | `test_browser_command_executor_moves_task_problem_selection` | 当用户在task problem中选择任务问题、选择时，系统应完成对应行为并保持页面状态正确 |

## 上下文复制与保存

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_browser_feedback.py` | `test_browse_context_line_shows_status_message` | 当用户在产品行为中展示feedback、browse、context、line时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_diff_handoff_saves_default_and_requested_paths` | 当用户在prompt handoff中保存handoff、diff、handoff、saves时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_handoff.py` | `test_review_notes_handoff_saves_default_and_requested_paths` | 当用户在prompt handoff中保存评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_page_help_and_actions.py` | `test_contextual_action_bar_matches_current_page` | 当用户在产品行为中验证help、actions、contextual、action时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_page_help_and_actions.py` | `test_contextual_action_bar_uses_line_fitting` | 当用户在产品行为中验证help、actions、contextual、action时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_copies_prompt_in_raw_status` | 当用户在prompt handoff中复制提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_does_not_copy_missing_file_prompt` | 当用户在prompt handoff遇到缺失状态、提示词交接时，系统应给出正确反馈或保持安全状态 |
| `tests/test_prompt_handoff_copy_commands.py` | `test_browser_command_executor_surfaces_prompt_copy_failure` | 当用户在prompt handoff遇到失败反馈、提示词交接时，系统应给出正确反馈或保持安全状态 |
| `tests/test_prompt_handoff_rendering.py` | `test_prompt_handoff_renders_review_notes_in_summary_and_detail` | 当用户在prompt handoff中渲染提示词交接、评审备注、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_save_feedback.py` | `test_browser_command_executor_saves_prompt_in_raw_status` | 当用户在prompt handoff中保存提示词交接时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_prompt_handoff_save_feedback.py` | `test_browser_command_executor_surfaces_prompt_save_failure` | 当用户在prompt handoff遇到失败反馈、提示词交接时，系统应给出正确反馈或保持安全状态 |

## 评审备注

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_copies_filtered_review_notes` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_copies_filtered_review_notes_in_raw_status` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_copies_review_notes` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_copies_review_notes_in_raw_status` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_does_not_copy_empty_review_notes` | 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_does_not_copy_unmatched_review_notes` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_copy_commands.py` | `test_browser_command_executor_reports_copy_review_notes_failures` | 当用户在review note遇到失败反馈、评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_lines.py` | `test_copy_review_notes_copies_filtered_lines` | 当用户在review note中复制评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_lines.py` | `test_copy_review_notes_skips_empty_or_unmatched_notes` | 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_lines.py` | `test_review_note_lines_filter_by_path_or_note_text` | 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_lines.py` | `test_review_note_lines_order_current_changes_before_extra_notes` | 当用户在review note中验证评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_lines.py` | `test_review_note_lines_show_empty_states` | 当用户在review note遇到空状态、评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_filters_review_notes_by_path_case_insensitive` | 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_filters_review_notes_in_raw_status` | 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_filters_review_notes_without_navigation` | 当用户在review note遇到缺少前置条件、评审备注、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_shows_empty_filtered_review_notes` | 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_shows_review_notes_in_raw_status` | 当用户在review note中展示评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_list_commands.py` | `test_browser_command_executor_shows_review_notes_without_navigation` | 当用户在review note遇到缺少前置条件、评审备注、导航时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_save_commands.py` | `test_browser_command_executor_does_not_save_empty_review_notes` | 当用户在review note遇到评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_save_commands.py` | `test_browser_command_executor_reports_save_review_notes_failures` | 当用户在review note遇到失败反馈、评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_save_commands.py` | `test_browser_command_executor_saves_review_notes_default_path` | 当用户在review note中保存评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_save_commands.py` | `test_browser_command_executor_saves_review_notes_requested_path` | 当用户在review note中保存评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_state.py` | `test_browser_state_review_note_lines_filter_by_note_and_path` | 当用户在review note中过滤评审备注时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_note_state.py` | `test_browser_state_review_note_lines_filter_empty_state` | 当用户在review note遇到空状态、评审备注时，系统应给出正确反馈或保持安全状态 |
| `tests/test_review_note_state.py` | `test_browser_state_review_note_lines_order_current_changes_before_extra_notes` | 当用户在review note中查看当前变更和额外备注顺序时，系统应优先展示当前变更备注 |
| `tests/test_review_note_state.py` | `test_browser_state_review_note_lines_show_empty_state` | 当用户在review note遇到空状态、评审备注时，系统应给出正确反馈或保持安全状态 |

## 命令面板与帮助

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_opens_page_help` | 当用户在产品行为中打开opens、help时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_back_returns_to_page_that_opened_command_palette` | 当用户在command palette中打开命令面板、导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_back_returns_to_page_that_opened_help` | 当用户在navigation中打开导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_catalog.py` | `test_command_help_groups_commands_by_workflow` | 当用户在产品行为中验证catalog、help、groups、workflow时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_catalog.py` | `test_command_palette_screen_renders_filter_selection_and_scroll` | 当用户在command palette中渲染命令面板、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_catalog.py` | `test_command_query_empty_or_question_mark_opens_command_list` | 当用户在产品行为遇到catalog、query、empty、or时，系统应给出正确反馈或保持安全状态 |
| `tests/test_command_catalog.py` | `test_executable_palette_entries_include_actions_not_parameter_templates` | 当用户在产品行为中验证catalog、executable、palette、entries时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_catalog.py` | `test_command_palette_entries_include_only_executable_commands` | 当用户在command palette中验证命令面板时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_catalog.py` | `test_command_palette_lists_source_filter_actions` | 当用户在command palette中过滤命令面板时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_execution.py` | `test_command_palette_enter_executes_filtered_command` | 当用户在command palette中过滤命令面板时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_execution.py` | `test_command_palette_enter_executes_selected_command_not_file_open` | 当用户在command palette中打开命令面板时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_filtering.py` | `test_command_palette_clear_keeps_file_filter` | 当用户在command palette中过滤命令面板、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_filtering.py` | `test_command_palette_filter_matches_command_group_and_description` | 当用户在command palette中过滤命令面板、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_filtering.py` | `test_command_palette_filter_ranks_command_matches_before_description_matches` | 当用户在command palette中过滤命令面板、过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_rendering.py` | `test_command_palette_screen_marks_selected_command` | 当用户在command palette中选择命令面板、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_rendering.py` | `test_command_palette_screen_shows_filter_and_empty_results` | 当用户在command palette遇到命令面板、渲染时，系统应给出正确反馈或保持安全状态 |
| `tests/test_command_palette_rendering.py` | `test_command_palette_screen_shows_filter_match_count` | 当用户在command palette中展示命令面板、渲染时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_command_palette_rendering.py` | `test_command_palette_selection_is_independent_from_file_selection` | 当用户在command palette中选择命令面板、渲染、选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_page_help_and_actions.py` | `test_help_screen_explains_current_page_actions_in_chinese` | 当用户在产品行为中验证help、actions、help、explains时，系统应完成对应行为并保持页面状态正确 |

## CLI 工作流

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_browser_command_list_is_discoverable_in_line_mode` | 当用户在CLI browser中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_defaults_to_browser_when_options_are_passed` | 当用户在CLI browser中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_defaults_to_interactive_browser` | 当用户在CLI browser中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_interactive_browser_can_open_current_file` | 当用户在CLI browser中打开导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_interactive_browser_filters_files_in_line_mode` | 当用户在CLI browser中过滤导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_entry_navigation.py` | `test_cli_interactive_browser_opens_file_and_navigates` | 当用户在CLI browser中打开导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_browser_task_workflows.py` | `test_cli_interactive_browser_can_run_test_command` | 当用户在CLI browser中验证cli、workflows、cli、interactive时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_filters_to_code_files_and_path_prefixes` | 当用户在CLI review中过滤过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_flags_lockfile_config_and_generated_risks` | 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_marks_deleted_code_files_without_fake_symbols` | 当用户在CLI review遇到缺少前置条件、过滤时，系统应给出正确反馈或保持安全状态 |
| `tests/test_cli_review_filtering.py` | `test_cli_omits_untracked_binary_and_large_file_contents` | 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_review_picks_one_file_by_summary_index` | 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_review_sorts_large_reviews_by_risk_or_churn` | 当用户在CLI review中验证过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_cli_review_tracks_seen_files_and_filters_remaining` | 当用户在CLI review中过滤过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_filtering.py` | `test_code_filter_does_not_show_doc_only_stats` | 当用户在CLI review中展示过滤时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_output.py` | `test_cli_can_emit_clickable_file_links` | 当用户在CLI review中验证cli、output、cli、can时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_output.py` | `test_cli_review_emits_prompt_ready_markdown_package` | 当用户在CLI review中验证cli、output、cli、emits时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_cli_review_output.py` | `test_cli_review_shows_first_changed_line_anchor` | 当用户在CLI review中展示cli、output、cli、shows时，系统应完成对应行为并保持页面状态正确 |

## TUI 框架与导航

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_runs_forward_navigation` | 当用户在navigation中运行导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_commands.py` | `test_browser_main_loop_delegates_to_command_parser` | 当系统处理产品行为的main、loop、delegates、parser时，系统应解析出正确结果 |
| `tests/test_browser_feedback.py` | `test_raw_key_invalid_selection_feedback_stays_inside_browser_frame` | 当用户在产品行为中选择选择时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_feedback.py` | `test_raw_key_open_feedback_stays_inside_browser_frame` | 当用户在产品行为中打开feedback、raw、key、open时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_feedback.py` | `test_raw_key_unknown_command_feedback_stays_inside_browser_frame` | 当用户在产品行为中验证feedback、raw、key、unknown时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_input.py` | `test_browser_input_idle_tick_uses_raw_idle_timeout` | 当用户在产品行为中验证input、input、idle、tick时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_input.py` | `test_browser_input_line_mode_returns_eof_and_interrupt_sentinels` | 当用户在产品行为中验证input、input、line、mode时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_input.py` | `test_browser_input_raw_key_reader_does_not_print_newline` | 当用户在产品行为中不执行input、input、raw、key时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_input.py` | `test_raw_key_command_read_does_not_print_newline` | 当用户在产品行为中不执行input、raw、key、read时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_main_loop.py` | `test_browser_main_loop_delegates_action_execution` | 当用户在产品行为中验证main、loop、main、loop时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_back_and_forward_restore_page_snapshots` | 当用户在navigation中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_back_preserves_existing_hierarchy_fallbacks` | 当用户在navigation中保持导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_browser_implementation_uses_page_model_and_navigation` | 当用户在navigation中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_new_branch_clears_forward_stack` | 当用户在navigation中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_opening_pages_resets_local_page_state` | 当用户在navigation中打开导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_page_model_names_current_pages` | 当用户在navigation中验证导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_navigation.py` | `test_replace_pages_does_not_modify_history` | 当用户在navigation中不执行导航时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_redraw.py` | `test_command_prompt_cancel_forces_full_browser_redraw` | 当用户在产品行为中验证redraw、prompt、cancel、forces时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_redraw.py` | `test_filter_prompt_cancel_forces_full_browser_redraw` | 当用户在产品行为中过滤redraw、filter、prompt、cancel时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_browse_screen_redraws_in_place` | 当用户在产品行为中验证frame、browse、redraws、place时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_frame.py` | `test_terminal_line_fitting_counts_visible_width` | 当系统处理产品行为的frame、terminal、line、fitting时，系统应统计出正确结果 |
| `tests/test_page_history.py` | `test_refresh_resets_page_history_for_reloaded_changes` | 当用户在navigation中加载history、refresh、resets、history时，系统应完成对应行为并保持页面状态正确 |

## 底层格式化与解析

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_packaging.py` | `test_setup_py_exposes_cr_console_script` | 当用户在产品行为中验证packaging、setup、py、exposes时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_review_changes.py` | `test_format_counts_handles_binary_stats` | 当系统处理产品行为的changes、format、counts、handles时，系统应统计出正确结果 |
| `tests/test_summary.py` | `test_renders_totals_and_one_line_per_file` | 当用户在产品行为中渲染summary、renders、totals、one时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_text_search.py` | `test_empty_query_and_missing_match_return_user_feedback` | 当用户在产品行为遇到缺失状态时，系统应给出正确反馈或保持安全状态 |
| `tests/test_text_search.py` | `test_find_text_can_search_first_line_when_requested` | 当用户在产品行为中验证text、search、find、text时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_text_search.py` | `test_find_text_ignores_ansi_and_matches_case_insensitively_after_header` | 当用户在产品行为中验证text、search、find、text时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_text_search.py` | `test_repeat_search_wraps_forward_and_backward` | 当用户在产品行为中验证text、search、repeat、search时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_tree.py` | `test_compacts_deep_tree_to_nearby_changed_directory` | 当用户在产品行为中验证tree、compacts、deep、tree时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_tree.py` | `test_formats_renamed_files_for_humans` | 当用户在产品行为中验证tree、formats、renamed、humans时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_tree.py` | `test_uses_common_directory_for_multiple_deep_changes` | 当用户在产品行为中验证tree、uses、common、directory时，系统应完成对应行为并保持页面状态正确 |

## 其他行为

| File | Test | Behavior |
| --- | --- | --- |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_applies_source_filter` | 当用户在产品行为中过滤applies、filter时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_changes_page_and_requests_redraw` | 当用户在产品行为中验证changes、requests、redraw时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_clears_source_filter` | 当用户在产品行为中过滤clears、filter时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_rejects_unknown_source_filter` | 当用户在产品行为中过滤rejects、unknown、filter时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_reports_quit_intent` | 当用户在产品行为遇到reports、quit、intent时，系统应给出正确反馈或保持安全状态 |
| `tests/test_browser_command_executor.py` | `test_browser_command_executor_reports_unknown_command_feedback` | 当用户在产品行为遇到reports、unknown、feedback时，系统应给出正确反馈或保持安全状态 |
| `tests/test_browser_commands.py` | `test_command_aliases_and_parameters_map_to_stable_actions` | 当用户在产品行为中验证aliases、parameters、map、stable时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_browser_commands.py` | `test_raw_slash_is_not_a_filter_command` | 当用户在产品行为中过滤raw、slash、not、a时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_done_next_commands.py` | `test_browser_command_executor_done_next_does_not_skip_remaining_file` | 当用户在产品行为中不执行done、next、done、next时，系统应完成对应行为并保持页面状态正确 |
| `tests/test_done_next_commands.py` | `test_browser_command_executor_done_next_reports_empty_visible_files` | 当用户在产品行为遇到done、next、done、next时，系统应给出正确反馈或保持安全状态 |
| `tests/test_done_next_commands.py` | `test_browser_command_executor_done_next_reports_last_visible_file` | 当用户在产品行为遇到done、next、done、next时，系统应给出正确反馈或保持安全状态 |
| `tests/test_task_browser_entrypoints.py` | `test_browser_test_command_starts_background_test_task` | 当用户在产品行为中启动entrypoints、starts、background时，系统应完成对应行为并保持页面状态正确 |

