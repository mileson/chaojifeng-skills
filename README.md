# 超级峰 Skill

> 超级峰在日常 AI 使用过程中沉淀下来的实战经验 Skills，帮助更多人更高效地用 AI 提效

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 简介

这里收录的是超级峰在日常 AI 使用过程中持续沉淀下来的实战经验 Skills，希望帮助更多人像超级峰一样，更高效地使用 AI 提效。

## Skills 一览

执行对应命令即可安装；如果你只想安装到 Claude Code，可在命令后追加 `--agent claude-code`。

| Skill | 简介 | 核心能力 | 适用场景 | 安装命令 |
| --- | --- | --- | --- | --- |
| `offboarding-handover` | 离职交接资料整理 | 支持可配置的分类规则，适配不同行业<br>自动生成 HTML 可视化入口页面<br>输出可打包交付的 ZIP 文件<br>多 Agent 协作：资料盘点、缺失检测、项目映射、风险检查 | 离职员工梳理零散工作资料、搭建交接目录、生成可视化入口 | `npx skills add mileson/chaojifeng-skills --skill offboarding-handover` |
| `skill-creator` | Skill 创建与更新工作流 | 支持品牌模板与仓库层 / Skill 层 / 产物层署名边界<br>支持 Mermaid 方案图 + 已明确授权时的直执行链路<br>覆盖 frontmatter、目录结构、示例、脚本和持久化记忆设计<br>提供 `--exact-path` 初始化、快速校验和 Mermaid 渲染辅助脚本 | 新建 Skill、重构 Skill 结构、补规范、拆 references、整理模板和脚本 | `npx skills add mileson/chaojifeng-skills --skill skill-creator` |
| `video-content-factory` | 一体化口播视频内容工厂 | 阶段1：根据选题/背景材料生成口播稿与分镜稿，按句预绑定特效模式 ID<br>阶段2：ASR 转录、自动剪辑口误停顿、按分镜渲染透明 hyperframes 特效轨<br>FFmpeg 合成、字幕/封面元数据、输出标准发布包 | 独立开发者、知识 IP、小团队稳定产出口播视频；B站/YouTube/抖音等平台 | `npx skills add mileson/chaojifeng-skills --skill video-content-factory` |

## 正在筹备

- AI 与自动化：围绕日常 AI 工作流、Agent 协作、任务自动化和效率提升持续补充
- 内容创作：覆盖写作、配图、排版整理和多平台发布等更轻量的创作场景
- iOS 与客户端开发：聚焦功能开发、测试、本地化、发布和常见工程问题
- 开发提效工具：整理代码审查、文档生成、项目规范和文件处理等通用能力
- 文档与知识整理：沉淀表格、文档、图示、资料归档和结构化整理相关 Skill
- 图片与媒体处理：补充截图标注、GIF/视频处理、图片生成和格式转换能力

## 许可证

MIT

## 作者

- SoulCard: [超级峰](https://soulcard.me/card/chaojifeng)
- X: [Mileson07](https://x.com/Mileson07)
- 小红书: [超级峰](https://www.xiaohongshu.com/user/profile/58b798d050c4b4193c8111c7)
- 抖音: [超级峰](https://www.douyin.com/user/MS4wLjABAAAA2I1fDroAQZrM8Tdz6MZfd28MCaRizKmD2-lr7UQP-a0)
- 快手: [超级峰](https://www.kuaishou.com/profile/3xeqsssav5aif84)
- 即刻: [超级峰](https://web.okjike.com/u/E769500F-3283-4BAE-B2F3-D1F0E944CB70)

---

_持续更新中，欢迎 star 关注最新动态_
