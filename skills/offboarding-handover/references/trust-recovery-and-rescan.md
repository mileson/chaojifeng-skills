# Trust Recovery and Rescan

Use this reference when the current session appears to have partial state, stale state, or untrustworthy intermediate outputs.

The goal is to stop the agent from pretending a phase was completed when the evidence is weak.

## Core Principle

Do not trust intermediate state automatically.

Trust must be earned by evidence.

If the evidence is weak, the workflow should fall back to:

- resuming an earlier phase
- rerunning a missing phase
- or forcing a fresh scan

## What counts as intermediate state

Examples:

- `.offboarding-handover/offboarding.config.json`
- `.offboarding-handover/handover.answers.json`
- `.offboarding-handover/handover.manifest.json`
- inventory summaries
- shard assignments
- coverage files
- existing HTML output

## Trust Levels

### High trust

Use existing state directly only when:

- state files exist
- they match the current expected structure
- they are internally consistent
- they reflect the current folder state closely enough
- there is no sign a required phase was skipped

### Medium trust

Use the state as hints only when:

- some state exists, but it is incomplete
- some expected files are missing
- output exists without clear generation evidence
- manifest exists but coverage evidence is absent

In this case:

- reuse what is safe
- rerun missing phases

### Low trust

Treat current state as non-authoritative when:

- scaffold files are missing or obviously stale
- manifest exists but output is absent and the generation chain is unclear
- inventory exists but parallel subagent mode should have triggered and did not
- user explicitly asks to “仔细调研”, “重新扫描”, “重新看看效果”, or similar
- the current folder structure no longer matches the recorded state

In this case:

- rerun from an earlier phase
- prefer a fresh first-scan path if needed

## Rescan Triggers

Force at least a partial rescan when any of these are true:

- `handover.manifest.json` is missing
- output directory is missing and there is no trustworthy render trace
- inventory baseline is missing
- coverage evidence is missing after a triggered parallel scan
- parallel threshold was hit but fewer than 2 specialist subagents were actually launched
- top-level branches now differ materially from the recorded baseline
- file counts differ materially from the recorded baseline

## Phase Recovery Rules

### If Phase 1 is untrusted

Return to:

- Phase 1 — Inventory Baseline

### If Phase 2 trigger decision is untrusted

Return to:

- Phase 1 or 2, depending on whether the inventory is still trustworthy

### If Phase 3 fan-out is untrusted

Return to:

- Phase 3 — Parallel Subagent Fan-Out

Do not continue to ask-user or render.

### If Phase 4 synthesis is untrusted

Return to:

- Phase 4 — Synthesis and Coverage Check

### If Phase 5 answers are untrusted

Return to:

- Phase 5 — Ask User

### If Phase 6 render is untrusted

Return to:

- Phase 6 — Render

## Strong Recovery Rule

If the hard trigger rule was hit, but the current evidence only shows:

- inventory
- or inventory + one worker

then Phase 3 must be treated as incomplete.

Do not reinterpret that as “good enough”.

## Recommended Transcript Pattern

When trust is low, the agent should say so explicitly.

Examples:

- `当前中间状态可信度不足，我将回退到清单基线阶段重新核对。`
- `已命中并行条件，但缺少足够的 subagent 执行证据。我将重新进入并行扫描阶段。`
- `manifest 存在，但 coverage 证据不足，因此我不会直接复用它来生成最终交接包。`
