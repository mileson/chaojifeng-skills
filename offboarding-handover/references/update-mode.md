# 更新模式

当交接包已存在且用户想要以下操作时，使用更新模式：

- 补齐缺失事实
- 替换 `待补充`
- 刷新 HTML 站点
- 在新的确认之后更新交接内容

## 推荐流程

1. 读取：
   - `.offboarding-handover/offboarding.config.json`
   - `.offboarding-handover/handover.manifest.json`
   - `.offboarding-handover/handover.answers.json`（如存在）
2. 从以下位置找出缺失字段：
   - profile 字段
   - 清单类回答
   - 仍暗示存在未解决交接事实的 markdown 页面
3. 只询问缺失或用户明确要求的项目
4. 写回 `handover.answers.json`
5. 重新渲染：
   - `00-说明与导航/00-交接总览.md`
   - `04-未完事项与状态/*.md`
   - `site/index.html`

## 代理规则

用户可能会说：

- “更新这个交接包”
- “把待补充补一下”
- “刷新一下 HTML”
- “把接手人改成王五”

此时代理应在内部进入刷新模式。

## 内部脚本提示

推荐代理使用的内部命令：

```bash
python3 scripts/bootstrap_handover.py /target/path --refresh --no-scan --interactive
```

文件没有实质变化、只想刷新内容时，使用 `--no-scan`。
