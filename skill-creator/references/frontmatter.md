# Frontmatter 配置指南

> SKILL.md 的 YAML frontmatter 控制技能的加载行为、可见性和执行环境。

## 必需字段

### `name` (可选但推荐)

Skill 的显示名称。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | String |
| 限制 | 最大 64 字符，仅小写字母和连字符 |
| 默认值 | 目录名称 |

**示例**:
```yaml
name: pdf-tool
```

**命名规范**:
- 使用小写字母和连字符
- 优先使用动名词形式 (verb-ing): `processing-pdfs`
- 简洁描述功能: `web-scraper`、`git-helper`

### `description` (必需)

功能描述和触发场景。这是 Claude 决定何时加载 Skill 的主要依据。

| 属性 | 说明 |
|------|------|
| 状态 | **必需** |
| 类型 | String (多行) |
| 限制 | 最大 1024 字符，非空 |
| 写作风格 | 第三人称，使用 "should be used when..." |

**示例**:
```yaml
description: |
  Comprehensive document creation and editing with tracked changes support.
  Use this skill when Claude needs to work with .docx files for: creating new
  documents, modifying content, working with tracked changes, or adding comments.
```

**最佳实践**:
- 使用第三人称描述
- 明确说明"何时使用" (Use when...)
- 列出主要功能场景
- 避免第二人称 ("you")

---

## 调用控制字段

### `argument-hint` (可选)

自动完成时显示的参数提示。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | String |

**示例**:
```yaml
argument-hint: "[issue-number]"
```

### `disable-model-invocation` (可选)

设为 `true` 后，Claude 不会自动加载此 Skill。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 默认值 | `false` |

**使用场景**: 仅限用户主动触发的 Skill（如 `/commit` 命令）

### `user-invocable` (可选)

设为 `false` 后，此 Skill 将从 `/` 菜单中隐藏。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 默认值 | `true` |

**使用场景**: 仅供 Claude 内部使用的辅助 Skill

### 三种调用模式对比

| 模式 | 配置 | 用户调用 | Claude 自动调用 |
|------|------|----------|-----------------|
| 默认模式 | (无配置) | ✓ | ✓ |
| 用户独占 | `disable-model-invocation: true` | ✓ | ✗ |
| Claude 独占 | `user-invocable: false` | ✗ | ✓ |

---

## 工具与模型字段

### `allowed-tools` (可选)

Skill 激活时 Claude 可以无需用户许可直接使用的工具列表。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | List[String] |

**示例**:
```yaml
allowed-tools: ["Bash", "Read", "Write"]
```

### `model` (可选)

指定激活此 Skill 时使用的模型。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | String |
| 可选值 | `claude-opus-4-20250514`, `claude-sonnet-4-20250514`, `claude-haiku-4-20250514` |

**示例**:
```yaml
model: "claude-sonnet-4-20250514"
```

---

## 子 Agent 配置字段

### `context` (可选)

设为 `fork` 后，Skill 将在独立的子 agent 上下文中运行。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | String |
| 可选值 | `fork` |

**使用场景**: 需要隔离对话状态的 Skill

### `agent` (可选)

配合 `context: fork` 使用，指定使用的子 agent 类型。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | String |
| 可选值 | `Bash`, `general-purpose`, 等 |

**示例**:
```yaml
context: fork
agent: general-purpose
```

---

## 生命周期钩子 (Hooks)

### `hooks` (可选)

定义 Skill 生命周期钩子，在特定事件发生时执行命令。钩子仅在 Skill 激活期间运行，Skill 完成后自动清理。

| 属性 | 说明 |
|------|------|
| 状态 | 可选 |
| 类型 | Object |

### 支持的事件

Skill 钩子支持以下事件：

| 事件 | 触发时机 |
|------|----------|
| `PreToolUse` | 工具执行前 |
| `PostToolUse` | 工具成功执行后 |
| `Stop` | Claude 完成响应时 |

### Hook 类型

| 类型 | 说明 |
|------|------|
| `command` | 执行 bash 命令 |
| `prompt` | 使用 LLM 评估决策（仅 `Stop` 事件） |

### 配置结构

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash|Write"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
          timeout: 30
          once: false
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/format.sh"
  Stop:
    - hooks:
        - type: prompt
          prompt: "检查是否所有任务完成: $ARGUMENTS"
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `matcher` | String | 工具匹配模式（仅 PreToolUse/PostToolUse），支持精确匹配、正则或 `*` |
| `type` | String | `command` 或 `prompt` |
| `command` | String | bash 命令路径 |
| `prompt` | String | LLM 评估提示词 |
| `timeout` | Number | 超时时间（秒），默认 60 |
| `once` | Boolean | 设为 `true` 后仅执行一次，然后自动移除（仅 Skill 支持） |

### Matcher 示例

| Matcher | 匹配 |
|---------|------|
| `Write` | 仅 Write 工具 |
| `Edit\|Write` | Edit 或 Write |
| `Read.*` | Read 开头的工具 |
| `*` 或 `""` | 所有工具 |

### 环境变量

Hook 命令可使用以下环境变量：

| 变量 | 说明 |
|------|------|
| `$CLAUDE_PROJECT_DIR` | 项目根目录绝对路径 |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |

### Hook 输入 (JSON via stdin)

Hook 通过 stdin 接收 JSON 输入：

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/project/dir",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### Hook 输出

#### 简单模式 (退出码)

| 退出码 | 行为 |
|--------|------|
| `0` | 成功，继续执行 |
| `2` | 阻止操作，stderr 显示给 Claude |
| 其他 | 非阻塞错误，verbose 模式显示 stderr |

#### JSON 输出模式

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "原因说明",
    "updatedInput": {
      "field": "new_value"
    },
    "additionalContext": "额外上下文"
  }
}
```

### 使用场景

**PreToolUse**:
- 命令验证（阻止危险操作）
- 自动批准安全操作
- 修改工具参数

**PostToolUse**:
- 代码格式化
- 运行 linter
- 记录操作日志

**Stop**:
- 智能判断是否继续工作
- 验证任务完成度

---

## 完整示例

```yaml
---
name: git-commit-helper
description: |
  Automated git commit workflow with message generation. Use this skill when
  Claude needs to create git commits: staging files, generating commit messages,
  and creating commits with proper formatting.

argument-hint: "[message]"
disable-model-invocation: false
user-invocable: true
allowed-tools: ["Bash", "Read"]
model: "claude-sonnet-4-20250514"
context: fork
agent: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate-git.sh"
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
          once: true
---

# Git Commit Helper

> 此 Skill 用于自动化 git 提交流程

## 核心功能

1. 自动检测变更文件
2. 生成规范的提交信息
3. 执行 git commit 操作
```

### Hook 脚本示例

**`.claude/hooks/validate-git.sh`** (Bash 命令验证):
```bash
#!/bin/bash
# 阻止危险的 git 命令
if echo "$command" | grep -qE "git (clean|reset|force-delete)"; then
    echo "危险命令已被阻止" >&2
    exit 2
fi
exit 0
```

**`.claude/hooks/check-style.sh`** (代码风格检查):
```bash
#!/bin/bash
# 检查文件是否符合代码风格
file_path=$(echo "$tool_input" | jq -r '.file_path')
if [[ "$file_path" == *.py ]]; then
    python3 -m py_compile "$file_path" || exit 2
fi
exit 0
```
