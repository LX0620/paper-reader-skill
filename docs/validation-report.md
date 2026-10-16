# v0.2.0 本地验证记录

日期：2026-10-16。
环境：Linux；Python 3.13.5。

## 已完成

- `python -m unittest discover -s tests -v`：35/35 项通过。
- 在临时目录中分别执行首次安装与备份升级的完整 CLI 命令，包含空格路径与可选 AGENTS 路由，均返回成功。
- 配置检查确认 `allow_implicit_invocation: true`；描述前置阅读/论文触发词。
- 模板检查确认五个阅读阶段、研究地图七问、5个研究想法的七项内容与四维评价。
- 安装测试确认旧技能完整备份、备份不在技能发现目录、复制失败保留旧版。
- 路由测试确认保留原指令、备份原文件、重复执行不重复追加、遵守非空 override 优先级、异常标记和超限内容不覆盖。
- 保留的 PDF 辅助脚本通过8项测试：页码、哈希、提取、指定页渲染、输入/输出保护及加密输入拒绝。

## 尚未验证

没有在用户的 Codex、Windows 或 WSL 实际会话中进行自动触发或论文阅读验收。
没有使用真实论文验证五步阅读质量，没有运行 GitHub Actions，也没有上传 GitHub。
这些测试不证明模型必然触发、不遗漏内容或学术判断必然正确。

## 逐项测试记录

```text
test_encrypted_input (test_pdf.PdfTests.test_encrypted_input) ... ok
test_extract_pages_hash_and_low_text (test_pdf.PdfTests.test_extract_pages_hash_and_low_text) ... ok
test_extract_selected_pages (test_pdf.PdfTests.test_extract_selected_pages) ... ok
test_invalid_dpi (test_pdf.PdfTests.test_invalid_dpi) ... ok
test_invalid_input (test_pdf.PdfTests.test_invalid_input) ... ok
test_page_selection (test_pdf.PdfTests.test_page_selection) ... ok
test_refuse_existing_output (test_pdf.PdfTests.test_refuse_existing_output) ... ok
test_render_selected_pages (test_pdf.PdfTests.test_render_selected_pages) ... ok
test_frontmatter (test_skill.SkillTests.test_frontmatter) ... ok
test_install_and_refuse_overwrite (test_skill.SkillTests.test_install_and_refuse_overwrite) ... ok
test_invocation_policy (test_skill.SkillTests.test_invocation_policy) ... ok
test_json_templates (test_skill.SkillTests.test_json_templates) ... ok
test_no_private_papers_in_skill (test_skill.SkillTests.test_no_private_papers_in_skill) ... ok
test_privacy_ignore_rules (test_skill.SkillTests.test_privacy_ignore_rules) ... ok
test_referenced_resources_exist (test_skill.SkillTests.test_referenced_resources_exist) ... ok
test_reject_destination_inside_source (test_skill.SkillTests.test_reject_destination_inside_source) ... ok
test_configure_router_preserves_old_bytes_and_keeps_backup (test_workflow.RouterTests.test_configure_router_preserves_old_bytes_and_keeps_backup) ... ok
test_empty_override_falls_back (test_workflow.RouterTests.test_empty_override_falls_back) ... ok
test_invalid_router_keeps_instructions_untouched (test_workflow.RouterTests.test_invalid_router_keeps_instructions_untouched) ... ok
test_merge_is_idempotent (test_workflow.RouterTests.test_merge_is_idempotent) ... ok
test_merge_rejects_malformed_markers (test_workflow.RouterTests.test_merge_rejects_malformed_markers) ... ok
test_merge_retains_surrounding_text (test_workflow.RouterTests.test_merge_retains_surrounding_text) ... ok
test_nonempty_override_is_used (test_workflow.RouterTests.test_nonempty_override_is_used) ... ok
test_oversize_router_keeps_instructions_untouched (test_workflow.RouterTests.test_oversize_router_keeps_instructions_untouched) ... ok
test_failed_stage_copy_leaves_old_skill (test_workflow.UpgradeTests.test_failed_stage_copy_leaves_old_skill) ... ok
test_install_alone_does_not_modify_codex_profile (test_workflow.UpgradeTests.test_install_alone_does_not_modify_codex_profile) ... ok
test_unrelated_target_is_not_replaced (test_workflow.UpgradeTests.test_unrelated_target_is_not_replaced) ... ok
test_update_is_valid_for_first_install (test_workflow.UpgradeTests.test_update_is_valid_for_first_install) ... ok
test_upgrade_preserves_entire_backup_outside_skills (test_workflow.UpgradeTests.test_upgrade_preserves_entire_backup_outside_skills) ... ok
test_automatic_execution_and_honest_limits (test_workflow.WorkflowTests.test_automatic_execution_and_honest_limits) ... ok
test_exact_five_stages (test_workflow.WorkflowTests.test_exact_five_stages) ... ok
test_idea_fields_and_ratings (test_workflow.WorkflowTests.test_idea_fields_and_ratings) ... ok
test_removed_old_transfer_module (test_workflow.WorkflowTests.test_removed_old_transfer_module) ... ok
test_required_report_sections (test_workflow.WorkflowTests.test_required_report_sections) ... ok
test_trigger_keywords_are_frontloaded (test_workflow.WorkflowTests.test_trigger_keywords_are_frontloaded) ... ok
```
