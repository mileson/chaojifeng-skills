# chaojifeng-skills

> Chaojifeng 的 Claude Code Skills 集合 | 160+ 生产级 AI 编程助手技能

[![Skills Count](https://img.shields.io/badge/Skills-160+-blue)](https://github.com/mileson/chaojifeng-skills)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 简介

这是我个人维护的 Claude Code Skills 集合，涵盖：

- **飞书/Lark 生态** - 日程、任务、文档、会议、多维表格等
- **微信生态** - 公众号、小程序、社群管理
- **iOS 开发** - MVVM 架构、测试脚本、本地化、TestFlight
- **内容创作** - 文章生成、配图、排版、多平台发布
- **AI 工具** - 多 Agent 协作、OpenPrd、图像生成
- **开发工具** - 代码审查、安全审查、文档生成

## 快速开始

### 安装单个 Skill

```bash
cd ~/.claude/skills
git clone https://github.com/mileson/chaojifeng-skills.git temp
cp -r temp/skills/{skill-name} .
rm -rf temp
```

### 安装全部 Skills

```bash
cd ~/.claude/skills
git clone https://github.com/mileson/chaojifeng-skills.git temp
cp -r temp/skills/* .
rm -rf temp
```

## Skills 分类

### 飞书/Lark 生态
| Skill | 说明 |
|-------|------|
| `lark-calendar` | 日程与会议管理 |
| `lark-task` | 任务管理 |
| `lark-doc` | 云文档操作 |
| `lark-wiki` | 知识库管理 |
| `lark-im` | 即时通讯 |
| `lark-mail` | 邮件操作 |
| `lark-minutes` | 会议纪要 |
| `lark-base` | 多维表格 |
| `lark-drive` | 云空间管理 |
| `feishu-card` | 互动卡片发送 |

### 微信生态
| Skill | 说明 |
|-------|------|
| `wechat-mp-cloudflare-proxy` | 公众号 API 代理 |
| `wechat-group-hygiene` | 群成员活跃度分析 |
| `weapp-dev-mcp` | 小程序开发 MCP |
| `markdown-to-wechat` | Markdown 转微信格式 |

### iOS 开发
| Skill | 说明 |
|-------|------|
| `ios-mvvm-refactor` | MVVM 架构重构 |
| `ios-feature-creator` | 功能模块创建 |
| `ios-test-script-generator` | 测试脚本生成 |
| `ios-localization-auto-translator` | 自动翻译 |
| `ios-colorscheme-validator` | 颜色规范检查 |
| `ios-testflight-remote-release` | TestFlight 发布 |

### 内容创作
| Skill | 说明 |
|-------|------|
| `topic-to-wechat` | 全自动文章创作发布 |
| `article-illustrator` | 文章配图助手 |
| `markdown-image-uploader` | 图片上传图床 |
| `jike-content-creator` | 即刻内容创作 |
| `xhs-note-creator-auto` | 小红书笔记创作 |

### AI 与 Agent
| Skill | 说明 |
|-------|------|
| `agent-team-research` | 多 Agent 协作调研 |
| `ai-image-generator` | AI 图像生成 |
| `openprd-harness` | OpenPrd 需求管理 |
| `ai-elements` | AI 组件库 |

### 开发工具
| Skill | 说明 |
|-------|------|
| `code-review` | 代码审查 |
| `security-review` | 安全审查 |
| `skill-creator` | Skill 创建向导 |
| `file-manual` | 文件说明书生成 |
| `folder-manual` | 文件夹说明书生成 |

### 文档处理
| Skill | 说明 |
|-------|------|
| `docx` | Word 文档操作 |
| `pdf` | PDF 文档处理 |
| `xlsx` | 表格处理 |
| `excalidraw-diagram` | Excalidraw 图表 |

## 开发指南

### 创建新 Skill

参考 [`skill-creator`](skills/skill-creator/) 模板：

```
your-skill/
├── SKILL.md           # Skill 定义
├── references/        # 参考文档
├── examples/          # 使用示例
├── scripts/           # 辅助脚本
└── templates/         # 模板文件
```

### SKILL.md 格式

```markdown
---
name: your-skill
description: 一句话描述
version: 1.0.0
author: Chaojifeng
tags: [tag1, tag2]
triggers:
  - "当用户提到..."
---

# 详细说明
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 关于

作者：[Chaojifeng](https://github.com/mileson)

---

_这些 Skills 是我在日常开发中积累的工具集，希望能帮助到更多开发者。_
