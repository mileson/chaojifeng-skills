<div align="center">

# 超级峰 Skill

> 把超级峰在真实 AI 工作流里反复验证的经验，沉淀成可安装、可复用、可迁移的 Agent Skills。

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Install](https://img.shields.io/badge/install-npx%20skills%20add-blue)](#一行安装)
[![Skill Collection](https://img.shields.io/badge/Skill%20Collection-持续更新-7c3aed)](#skills-一览)

<br>

**少一点临场发挥，多一点可复用流程。**

这里收录超级峰在日常 AI 使用、内容生产、工作流自动化和工程协作中沉淀下来的实战 Skills。
每个 Skill 都是一个独立目录，既可以一键安装，也可以直接阅读 `SKILL.md` 当作工作流模板复用。

[Skills 一览](#skills-一览) · [一行安装](#一行安装) · [怎么使用](#怎么使用) · [仓库结构](#仓库结构) · [作者](#作者)

</div>

---

## 这个仓库是什么

这是一个公开的个人 Skill 集合。它不是教程合集，也不是泛泛的提示词库，而是把已经在真实场景里跑过的流程整理成可复用的 Agent Skill：

- 面向具体任务，而不是抽象概念。
- 保留执行门禁、输入要求和输出格式，减少每次重新解释。
- 每个 Skill 自带必要脚本、模板或空数据骨架，方便安装后马上使用。
- 私人素材、密钥、内部配置和未确认沉淀内容默认不进入公开仓库。

## 一行安装

安装独立 Skill：

```bash
npx skills add mileson/shenbi-maliang
```

只安装到 Claude Code：

```bash
npx skills add mileson/shenbi-maliang --agent claude-code
```

安装集合仓库里的其他 Skill 时，把下方表格里的安装命令复制过去即可。

## Skills 一览

| Skill | 简介 | 核心能力 | 适用场景 | 安装命令 |
| --- | --- | --- | --- | --- |
| [`shenbi-maliang`](https://github.com/mileson/shenbi-maliang) | 必须带真人形象照的人物迁移与参考图复刻流程 | 强制先确认形象照<br>支持单图、多图参考板和历史画册复用<br>内置形象照归档、画册归档和参考板脚本<br>独立主仓库只保留空数据骨架，不包含私人图片 | 用自己的形象照复刻封面、头像、海报、生活照或内容创作配图风格 | `npx skills add mileson/shenbi-maliang` |
| `video-content-factory` | 一体化口播视频内容工厂 | 阶段1：根据选题/背景材料生成口播稿与分镜稿<br>阶段2：ASR 转录、自动剪辑口误停顿、渲染透明特效轨<br>FFmpeg 合成、字幕/封面元数据、输出标准发布包 | 独立开发者、知识 IP、小团队稳定产出口播视频；B站/YouTube/抖音等平台 | `npx skills add mileson/chaojifeng-skills --skill video-content-factory` |
| `skill-creator` | Skill 创建与更新工作流 | 支持品牌模板与仓库层 / Skill 层 / 产物层署名边界<br>支持 Mermaid 方案图 + 已明确授权时的直执行链路<br>覆盖 frontmatter、目录结构、示例、脚本和持久化记忆设计 | 新建 Skill、重构 Skill 结构、补规范、拆 references、整理模板和脚本 | `npx skills add mileson/chaojifeng-skills --skill skill-creator` |
| `offboarding-handover` | 离职交接资料整理 | 支持可配置的分类规则，适配不同行业<br>自动生成 HTML 可视化入口页面<br>输出可打包交付的 ZIP 文件<br>多 Agent 协作：资料盘点、缺失检测、项目映射、风险检查 | 离职员工梳理零散工作资料、搭建交接目录、生成可视化入口 | `npx skills add mileson/chaojifeng-skills --skill offboarding-handover` |

## 怎么使用

装好后，在支持 Agent Skills 的环境里直接点名调用：

```text
[$shenbi-maliang] 使用我的默认形象照，参考这张图，生成一张 B站 16:9 封面。
```

如果环境还不支持自动加载 Skill，也可以打开对应目录里的 `SKILL.md`，把内容作为任务说明交给 Agent。

## 仓库结构

```text
.
├── README.md
├── publish-list.yaml
├── sync-skills.py
├── skill-creator/
├── video-content-factory/
└── offboarding-handover/
```

`shenbi-maliang` 已迁移为独立主仓库：<https://github.com/mileson/shenbi-maliang>

## 发布原则

- 公开仓库只保留可复用流程、脚本、模板和空数据骨架。
- 不提交真实 API key、token、账号凭证或私人联系方式。
- 不提交真人形象照、历史画册成品、未确认素材或本地运行产物。
- 每个 Skill 的 `SKILL.md` 应清楚说明输入要求、执行门禁、输出格式和不适用场景。

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

_持续更新中，欢迎 star 关注最新 Skill。_
