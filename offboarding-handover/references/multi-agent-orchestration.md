# Multi-Agent Orchestration

Use this reference when the offboarding folder is large, mixed, role-ambiguous, or contains both business and compliance risk.

This is an **agent execution strategy**, not a user-facing feature.

## Why use multiple agents on first scan

For small or clean folders, a single agent is enough.

For large or messy folders, multiple agents improve:

- speed through parallel exploration
- classification quality through separated concerns
- question quality by cross-checking role, project, and risk signals

## External Product Research Summary

### OpenAI Codex

Current official materials emphasize parallel agent workflows:

- OpenAI says Codex can work on many tasks in parallel, each in its own isolated environment.
- The Codex app is described as a command center for managing multiple agents at once, with parallel work and built-in worktrees.
- OpenAI also recommends using AGENTS.md to provide persistent instructions, and recommends parallel exploration patterns such as Best-of-N for alternative solutions.

Practical implication for this skill:

- Use a **coordinator + parallel workers** pattern
- Keep workers isolated by responsibility
- Feed the final result back into one synthesized handover view

### Claude Code

Current official materials distinguish between:

- **subagents**: focused workers inside one session, each with its own context window
- **agent teams**: multiple Claude Code sessions coordinated by one lead, better when workers need parallel collaboration

Claude’s official guidance says:

- use subagents when only the result matters
- use agent teams when workers need to coordinate or challenge each other
- avoid teams for sequential or highly coupled tasks

Practical implication for this skill:

- first scan should be modeled **subagent-first**
- one lead coordinates multiple specialized subagents
- agent teams are optional, not required, for this workflow
- workers should operate independently and return structured findings

## Recommended Subagent Topology

Use **1 coordinator + up to 4 subagents**.

Do not exceed 5 agents total unless the user explicitly wants deep research.

### Team Lead

**Role:** Handover coordinator

Responsibilities:

- inspect whether the folder is small enough for single-agent handling
- decide whether multi-agent mode is worth the token cost
- assign bounded scan tasks
- collect findings
- detect conflicts between workers
- decide the first-round ask-user questions
- synthesize final classification and trigger rendering

### Worker 1: Role Detector

Responsibilities:

- infer likely role from filenames, directories, artifacts, and tool names
- output top 1-3 likely roles with confidence
- highlight ambiguity boundaries

Best for:

- product vs project vs operations
- engineering vs testing vs data
- finance vs HR vs legal

### Worker 2: Project and Business Mapper

Responsibilities:

- cluster files by project, product line, customer, or business stream
- identify current vs historical materials
- detect whether customer-facing or project-delivery content exists

Best for:

- “这批资料主要是内部还是客户/项目资料”
- first draft of `03-专项交接`

### Worker 3: Risk and Asset Checker

Responsibilities:

- identify accounts, permissions, devices, credentials, contracts, invoices, seals, or sensitive files
- flag high-risk missing items likely to become `待补充`

Best for:

- `资产权限`
- `合规结算`
- first-round risk questions

### Worker 4: Inflight and Missing-Facts Detector

Responsibilities:

- identify unfinished work, pending status, follow-up tasks, and unresolved handover facts
- detect what must be asked before the first polished HTML is generated

Best for:

- `00-进行中事项总表.md`
- `01-高遗漏检查清单.md`
- update mode question lists

## When to Use Parallel Subagent Mode

Enable parallel subagent mode when any of these are true:

- file count is large
- many top-level folders or mixed business domains exist
- role is ambiguous
- both internal and customer/project materials appear
- assets/compliance risk appears non-trivial
- the initial single-agent scan would likely produce too many `待补充`

Prefer single-agent mode when:

- the folder is already clean
- the role is obvious
- there are few files
- the task is mainly to refresh missing facts, not reclassify the whole package

## Recommended First-Scan Workflow

1. Coordinator performs a very light scan
2. Coordinator decides single-agent or parallel-subagent mode
3. If parallel-subagent mode:
   - spawn subagents in parallel
   - give each worker a disjoint responsibility
4. Workers return:
   - findings
   - confidence
   - unresolved questions
5. Coordinator synthesizes:
   - likely role
   - likely industry overlay
   - likely project/customer split
   - likely risk profile
6. Coordinator asks the smallest high-value question set
7. Coordinator generates config + answers + manifest + HTML

## Required Worker Output Format

Each worker should return:

- `scope`: what slice it inspected
- `findings`: top findings
- `confidence`: high / medium / low
- `conflicts`: where another role or interpretation might also fit
- `questions`: 2-5 follow-up questions worth asking the user

## Anti-Patterns

Do not use parallel subagent mode like this:

- multiple workers reading the same whole folder without role separation
- multiple workers all trying to produce the final classification
- teams for tiny refresh-only tasks
- workers editing the same files or same output slices in parallel

## How this maps to the current Codex environment

In this Codex environment, the practical pattern is:

- use one main agent as coordinator
- use `spawn_agent` for bounded parallel workers
- keep each worker read-heavy and write-light
- let only the main agent update the final skill outputs

This matches the official product direction from both Codex and Claude Code:

- parallel workers are useful
- isolated contexts reduce pollution
- one lead should synthesize and decide

## Claude Code Practical Rule

For this skill, Claude Code subagents are the default parallel mechanism.

Do not block the workflow on experimental agent teams.

If experimental agent teams are available, they may be used as an optional enhancement for extremely large or highly collaborative scans, but they are not required for normal execution.

## Sources

### Official OpenAI sources

- Introducing Codex  
  https://openai.com/index/introducing-codex/
- Introducing the Codex app  
  https://openai.com/index/introducing-the-codex-app/
- Using Codex with your ChatGPT plan  
  https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- How OpenAI uses Codex  
  https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf

### Official Anthropic / Claude Code sources

- Claude Code subagents  
  https://code.claude.com/docs/en/sub-agents
- Claude Code settings  
  https://code.claude.com/docs/en/settings
- Claude Code agent teams  
  https://code.claude.com/docs/en/agent-teams

## Context7 note

I first checked Context7 for Claude Code. It returned usable but incomplete material, mostly mirrored or repository-based documentation. I therefore supplemented it with official Anthropic docs for the authoritative behavior details above.
