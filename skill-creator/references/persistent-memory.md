# Persistent Memory Pattern

## Table of Contents

1. [When to Use](#when-to-use)
2. [Memory File Format](#memory-file-format)
3. [SKILL.md Integration](#skillmd-integration)
4. [Read/Write Rules](#readwrite-rules)
5. [Capacity Management](#capacity-management)
6. [Example: 10-Execution Memory](#example)

---

## When to Use

Add persistent memory when the skill meets **any** of these criteria:

| Signal | Example |
|--------|---------|
| Will be used repeatedly for similar tasks | content-creator, deployment-pipeline |
| Has user preferences that vary per person | writing style, platform choices, naming conventions |
| Benefits from learning what worked/failed | training frameworks, code generators |
| Maintains state across sessions | project trackers, ongoing workflows |

**Skip memory** for one-off, stateless tasks (pdf-rotate, image-resize, format-converter).

## Memory File Format

Create `data/memory.md` in the skill directory. First execution auto-populates it:

```markdown
# [Skill Name] Memory

> Auto-maintained. Read before each execution, update after completion.

## Execution History

| # | Date | Task Summary | Outcome | Key Learning |
|---|------|-------------|---------|-------------|

## User Preferences

## Known Issues & Workarounds

## Learned Patterns
```

### Section Purposes

| Section | What to record | Update frequency |
|---------|---------------|-----------------|
| **Execution History** | One-line summary per execution | Every execution |
| **User Preferences** | Discovered habits, style choices, defaults | When new preference found |
| **Known Issues** | Errors encountered and their fixes | When issue occurs or resolves |
| **Learned Patterns** | Strategies proven effective across multiple runs | Periodically, during compression |

## SKILL.md Integration

Add this section to the generated skill's SKILL.md:

```markdown
## Persistent Memory

Before executing, read `data/memory.md` for context from previous executions.

After completing each execution:
1. Append one-line summary to Execution History (keep last 20 entries)
2. Update User Preferences if new patterns discovered
3. Record any new issues or workarounds
4. Add effective patterns to Learned Patterns

When Execution History exceeds 20 entries, summarize oldest 10 into
Learned Patterns and remove them.
```

## Read/Write Rules

### Read (start of every execution)

1. Read `data/memory.md`
2. Use **User Preferences** to inform default choices
3. Check **Known Issues** to preemptively avoid past errors
4. Reference **Learned Patterns** for proven strategies

### Write (end of every execution)

1. **Always**: Append one row to Execution History
2. **If applicable**: Add/update User Preferences
3. **If error occurred**: Add to Known Issues with workaround
4. **If pattern confirmed across 3+ executions**: Promote to Learned Patterns

### What NOT to write

- Raw task content (articles, code, reports) — only summaries
- Sensitive information (API keys, passwords, personal data)
- Redundant entries — check for duplicates before writing

## Capacity Management

Memory must stay concise to be useful as context. Rules:

| Metric | Threshold | Action |
|--------|-----------|--------|
| Execution History rows | > 20 | Summarize oldest 10 → Learned Patterns, delete them |
| User Preferences items | > 15 | Merge similar items, remove outdated ones |
| Known Issues items | > 10 | Archive resolved issues (remove from file) |
| Total file size | > 300 lines | Full compression pass: summarize, deduplicate, prune |

## Example

A `content-creator` skill's memory after 10 executions:

```markdown
# Content Creator Memory

> Auto-maintained. Read before each execution, update after completion.

## Execution History

| # | Date | Task Summary | Outcome | Key Learning |
|---|------|-------------|---------|-------------|
| 6 | 2026-01-20 | AI编程教程 → xhs+wechat | ✅ 8.2分 | 教程类适合分步骤配图 |
| 7 | 2026-01-25 | Cursor技巧 → xhs | ✅ 8.7分 | 短标题+emoji开头点击率高 |
| 8 | 2026-01-28 | Agent框架对比 → wechat+zhihu | ✅ 8.5分 | 知乎版需要更多数据支撑 |
| 9 | 2026-02-01 | Vibe Coding心得 → xhs | ✅ 9.1分 | 个人故事型爆款率最高 |
| 10 | 2026-02-05 | MCP教程 → wechat | ✅ 8.0分 | 长文章需要更多小标题断句 |

## User Preferences

- 写作风格：口语化、轻松、避免学术腔
- 小红书标题：必须带 emoji，控制在 20 字内
- 微信公众号：偏好 2500-3000 字，3-5 个配图
- 选题偏好：AI 编程实战 > 工具评测 > 行业分析

## Known Issues & Workarounds

- 小红书敏感词"最好"触发限流 → 用"超赞"替代
- 旧封面脚本已下线：封面生成统一走 article-illustrator 单入口 `run_illustration_pipeline.py`

## Learned Patterns

- 个人经历+实操步骤的组合文章评分最高（平均 8.8+）
- 先写小红书版本再扩展为公众号版本，效率更高
- 配图在 3 张时阅读完成率最优（来自 #1-#5 的总结）
```
