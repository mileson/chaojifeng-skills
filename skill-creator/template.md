---
# SKILL.md 模板
# 参考: https://code.claude.com/docs/en/skills

# ========== Frontmatter (必需) ==========

name: skill-name
# (可选) Skill 显示名称
# 省略时使用目录名称
# 示例: "pdf-tool", "web-scraper"

description: |
  Brief description of what this skill does and when to use it.
# (必需) 功能描述和触发场景
# 影响 Claude 何时加载此 Skill
# 示例: |
#   Comprehensive PDF manipulation toolkit. Use when Claude needs to work with
#   .pdf files for: extracting text, merging documents, filling forms, or
#   converting to other formats.

# ========== 以下字段均为可选 ==========

# argument-hint: "[argument-name]"
# 参数提示（如 "[file-path]"、"issue-number"）

# disable-model-invocation: true
# 设为 true 后，仅用户可调用（/skill-name）

# user-invocable: false
# 设为 false 后，从 / 菜单隐藏（仅 Claude 自动调用）

# allowed-tools: ["Bash", "Read", "Write"]
# 激活时无需许可即可使用的工具

# model: "claude-sonnet-4-20250514"
# 指定模型（省略时使用默认模型）

# context: fork
# 设为 fork 后在子 agent 中运行（隔离对话上下文）

# agent: general-purpose
# 配合 context: fork 使用，指定子 agent 类型

# hooks:
#   pre-skill-load: "command"
#   pre-skill-unload: "command"
# 生命周期钩子

---

# [Skill 名称]

> [核心原则或注意事项]

## 关于此 Skill

[简要描述 Skill 的用途和价值主张 - 1-2 段]

### Skill 提供的功能

1. [功能 1]
2. [功能 2]
3. [功能 3]

## 核心原则

### 原则 1

[描述核心设计原则和最佳实践]

## 使用流程

[描述使用此 Skill 的工作流程]

### 步骤 1: [步骤名称]

[详细说明]

### 步骤 2: [步骤名称]

[详细说明]

---

## Persistent Memory

<!-- 删除此段落如果该 Skill 不需要持续性记忆（一次性任务型 Skill） -->
<!-- 保留此段落如果该 Skill 会被反复使用、需要积累学习经验 -->

Read `data/memory.md` before each execution for context from previous runs.

After completing each execution:
1. Append one-line summary to Execution History (keep last 20 entries)
2. Update User Preferences if new patterns discovered
3. Record any new issues or workarounds
4. Add effective patterns to Learned Patterns

When Execution History exceeds 20 entries, summarize oldest 10 into Learned Patterns and remove them.

---

## 进阶阅读

- **详细 Frontmatter 配置**: 见 [frontmatter.md](references/frontmatter.md)
- **文件结构和最佳实践**: 见 [best-practices.md](references/best-practices.md)
