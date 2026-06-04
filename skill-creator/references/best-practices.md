# Skill 最佳实践指南

> 本文档基于 Anthropic 官方最佳实践编写，适用于创建高质量 Skills。

## 写作风格

### 第三人称描述

Frontmatter 和正文应使用第三人称，而非第二人称。

**推荐**:
```yaml
description: |
  This skill should be used when Claude needs to process PDF files,
  extract text, or convert document formats.
```

**避免**:
```yaml
description: |
  Use this skill when you need to work with PDF files...
```

### 动词优先形式

正文应使用动词优先的指令形式，而非描述性句子。

**推荐**:
```markdown
## 创建流程

1. 收集用户需求
2. 设计目录结构
3. 生成 SKILL.md
```

**避免**:
```markdown
## 创建流程

1. 你需要收集用户需求
2. 然后设计目录结构
3. 最后生成 SKILL.md
```

---

## 文档长度控制

### SKILL.md 目标长度

| 部分 | 目标长度 | 说明 |
|------|----------|------|
| Frontmatter | < 20 行 | 仅包含必需配置 |
| 正文主体 | 1,500-2,000 词 | 核心功能说明 |
| 总行数 | < 500 行 | 保持简洁 |

### Progressive Disclosure（渐进式披露）

将详细内容分层放置：

```
SKILL.md (500 行以内)
  ├── 核心功能说明
  ├── 基本使用流程
  └── 引用 references/
      ├── frontmatter.md (详细配置)
      ├── workflows.md (多步骤流程)
      └── examples.md (代码示例)
```

**原则**:
- SKILL.md 包含 80% 使用场景所需的信息
- references/ 包含深入细节和边缘情况

---

## 文件结构规范

### 标准目录结构

```
skill-name/
├── SKILL.md           # 必需，主说明文件
├── template.md        # 可选，Claude 填写的模板
├── examples/
│   └── sample.md      # 可选，示例输出文件
├── reference.md       # 可选，详细参考文档
└── scripts/
    └── helper.py      # 可选，工具脚本（执行，不加载）
```

**官方标准结构来源**: https://code.claude.com/docs/en/skills

### Scripts (scripts/)

可执行代码文件，用于需要确定性执行或重复编写的任务。

**特点**:
- 代码不会被加载到对话上下文
- 通过 Bash 工具调用执行
- 适合自动化脚本、数据处理等

**示例**: `render_mermaid.py`、`validate.py`

### References (reference.md 或 references/)

参考文档，按需加载到上下文中。

**特点**:
- 包含详细的技术文档
- 通过 Read 工具按需读取
- 适合配置说明、API 文档等

**示例**: `frontmatter.md`、`workflows.md`

### Examples (examples/)

示例文件，展示预期的输出格式或使用模式。

**特点**:
- 按需加载到上下文
- 展示预期的输出格式
- 便于 Claude 学习模式

**示例**: `examples/sample.md`、`examples/basic-test.js`

### Template (template.md)

模板文件，供 Claude 填写生成内容。

**特点**:
- 定义输出结构
- Claude 按模板填充内容
- 适合报告生成等场景

**示例**: 报告模板、文档模板、PR 描述模板

---

## 命名规范

### Skill 目录命名

| 规范 | 示例 |
|------|------|
| 小写字母 + 连字符 | `pdf-tool` |
| 动名词形式 (优先) | `processing-pdfs` |
| 功能描述 | `git-helper` |

**避免**:
- 驼峰命名: `PdfTool`
- 下划线: `pdf_tool`
- 含糊名称: `helper`、`utils`

---

## Frontmatter 最佳实践

### Description 写作模板

```
[核心功能描述]. Use this skill when Claude needs to [主要使用场景]:

- [场景 1]
- [场景 2]
- [场景 3]
```

**示例**:
```yaml
description: |
  Comprehensive PDF manipulation toolkit. Use this skill when Claude needs to
  work with .pdf files for: extracting text and tables, merging or splitting
  documents, filling forms, or converting to other formats.
```

### Allowed-Tools 配置

仅添加 Skill 核心功能必需的工具：

```yaml
# 好的示例 - 精确
allowed-tools: ["Bash", "Read"]

# 避免 - 过于宽泛
allowed-tools: ["*"]
```

---

## 测试建议

### 多模型兼容性

在不同模型上测试 Skill 行为：

| 模型 | 用途 |
|------|------|
| Opus | 复杂推理、长上下文 |
| Sonnet | 平衡性能与成本 |
| Haiku | 快速响应、简单任务 |

### 用户场景验证

确保 Skill 在以下场景中正常工作：

1. **自动触发**: Claude 根据任务自动加载
2. **手动调用**: 用户通过 `/skill-name` 调用
3. **参数传递**: 带参数的调用
4. **上下文隔离**: 与其他 Skill 的交互

---

## 官方参考

- **Anthropic Skills 文档**: https://code.claude.com/docs/en/skills
- **官方模板仓库**: https://github.com/anthropics/skills
- **最佳实践**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
