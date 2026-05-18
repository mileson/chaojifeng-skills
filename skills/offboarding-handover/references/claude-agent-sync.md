# Claude Agent Sync

Use this reference when the skill runs inside Claude Code or Codex and depends on dedicated offboarding subagents.

## Goal

Keep the offboarding subagents under skill control, while syncing them incrementally into:

- `~/.claude/agents/`
- `~/.codex/agents/`

## Managed Strategy

The skill owns the source templates in:

- `agents/offboarding-*.md`
- `agents/codex/offboarding-*.toml`

Each managed agent must include:

- `managed-by: offboarding-handover`
- `managed-version: 1`

## Sync Rules

- if the target agent does not exist → create it
- if the target agent exists and contains `managed-by: offboarding-handover` → update it in place
- if the target agent exists but is not managed by this skill → do not overwrite it

## Internal Sync Script

Use:

```bash
python3 scripts/sync_claude_agents.py
```

Optional explicit mode:

```bash
python3 scripts/sync_claude_agents.py --runtime claude
python3 scripts/sync_claude_agents.py --runtime codex
python3 scripts/sync_claude_agents.py --runtime both
```

Run this on:

- first run in Claude Code when team mode may be needed
- first run in Codex when team mode may be needed
- after agent template changes
- when a managed agent is missing

## Safety Rule

Do not overwrite user-owned custom agents with the same name unless the user explicitly asks.

## Fallback Rule

If the environment is neither Claude Code nor Codex, or runtime detection is not confident enough, do not hard-require local agent files. Fall back to the skill instructions and coordinator prompt logic so the handover flow still works.
