# Claude 代理同步

当 skill 运行在 Claude Code 或 Codex 中、依赖专用离职交接子代理时，使用本参考。

## 目标

让离职交接子代理保持由 skill 管控，同时增量同步到：

- `~/.claude/agents/`
- `~/.codex/agents/`

## 托管策略

skill 拥有源模板：

- `agents/offboarding-*.md`
- `agents/codex/offboarding-*.toml`

每个托管代理必须包含：

- `managed-by: offboarding-handover`
- `managed-version: 1`

## 同步规则

- 目标代理不存在 → 创建
- 目标代理存在且包含 `managed-by: offboarding-handover` → 就地更新
- 目标代理存在但不由本 skill 托管 → 不覆盖

## 内部同步脚本

使用：

```bash
python3 scripts/sync_claude_agents.py
```

可选的显式模式：

```bash
python3 scripts/sync_claude_agents.py --runtime claude
python3 scripts/sync_claude_agents.py --runtime codex
python3 scripts/sync_claude_agents.py --runtime both
```

在以下时机运行：

- 在 Claude Code 中首次运行且可能需要团队模式时
- 在 Codex 中首次运行且可能需要团队模式时
- 代理模板变更之后
- 托管代理缺失时

## 安全规则

除非用户明确要求，不要覆盖用户自建的同名代理。

## 回退规则

环境既不是 Claude Code 也不是 Codex，或运行时检测置信度不足时，不硬性要求本地代理文件。回退到 skill 指令和协调者提示词逻辑，让交接流程照常运转。
