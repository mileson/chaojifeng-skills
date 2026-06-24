# 开源发布清单

> 此文件控制哪些 Skills 会被同步到公共仓库 `chaojifeng-skills`

## 使用说明

1. 在下方的 `待发布` 列表中添加你想要开源的 skill 名称
2. 运行 `python sync-skills.py` 同步
3. 已发布的 skill 会自动移到 `已发布` 列表

---

## 待发布

<!-- 在这里添加想要开源的 skill，格式：- `[skill-name]` - 说明 -->
<!-- 示例：
- `lark-calendar` - 飞书日历管理
-->

## 已发布

<!-- 自动记录，手动添加：
- `skill-name` - 发布日期
-->
- `shenbi-maliang` - 2026-06-24（独立仓库：https://github.com/mileson/shenbi-maliang）

## 不发布

<!-- 明确不发布的 skill（敏感/内部/依赖外部服务等） -->
- `secrets-vault` - 包含敏感信息管理
- `feishu-*` - 依赖内部飞书应用配置
- `lark-*` - 依赖内部 Lark 应用配置
- `wechat-*` - 依赖内部微信配置
- `commercial-*` - 商业项目相关
- `offboarding-*` - 内部离职流程
- `agent-onboarding` - OpenClaw 内部入职流程
- `openprd-*` - OpenPrd 内部工作流
- `conversation-pattern-miner*` - 包含历史对话分析
- `*已废弃*` - 已废弃的 skills

---

## 发布检查清单

发布前确认：
- [ ] Skill 代码中没有硬编码的 API 密钥
- [ ] SKILL.md 中的描述适合公开
- [ ] 移除内部域名/内网地址
- [ ] examples/ 中的示例数据脱敏
- [ ] scripts/ 中的脚本不包含敏感路径
