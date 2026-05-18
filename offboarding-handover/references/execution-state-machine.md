# Execution State Machine

Use this reference to run the offboarding-handover skill as a staged workflow, not as an open-ended conversation.

The goal is first-run correctness.

This skill should behave like a small workflow engine:

- each phase has an entry condition
- each phase has a required output
- each phase has a do-not-skip rule

## Core Principle

Do not optimize for conversational freedom.

Optimize for:

- correct first-run execution
- low omission risk
- stable handover output quality

## State Machine

### Phase 0 — Detect Context

Required actions:

- identify working directory
- detect whether `.offboarding-handover/` exists
- detect whether output directory exists
- detect whether this is first run or refresh/update

Exit condition:

- execution mode is identified as `first_run` or `refresh`

Do not skip:

- do not assume refresh just because some files exist
- do not assume first run just because output is missing

### Phase 1 — Inventory Baseline

Required actions:

- count total files
- count total directories
- list meaningful top-level branches
- count files by branch
- summarize extension distribution

Exit condition:

- inventory baseline is available

Do not skip:

- do not ask the user before inventory exists
- do not classify deeply before inventory exists

### Phase 2 — Trigger Check

Required actions:

- apply the hard trigger rule
- decide `single_agent` or `parallel_subagent`

Hard triggers:

- `total_files > 3000`
- `meaningful_top_level_branches > 8`
- internal + client/project + risk/compliance signals all present
- role confidence not high

Exit condition:

- execution mode is locked for this run

Do not skip:

- do not reinterpret a triggered folder as “simple enough”
- do not use subjective judgment to bypass a triggered parallel run

### Phase 3 — Parallel Subagent Fan-Out

Only required if Phase 2 selected `parallel_subagent`.

Required actions:

- explicitly announce the subagents to be launched
- launch at least 2 specialist subagents beyond inventory
- assign disjoint responsibilities

Preferred subagents:

- `offboarding-role-detector`
- `offboarding-project-mapper`
- `offboarding-risk-checker`
- `offboarding-missing-facts-detector`

Exit condition:

- subagent findings are returned

Do not skip:

- one inventory subagent alone is not enough
- do not ask the user before specialist subagents return
- do not generate outputs before synthesis

### Phase 4 — Synthesis and Coverage Check

Required actions:

- merge subagent findings
- check coverage against inventory
- identify missing critical facts

Exit condition:

- coordinator has:
  - likely role
  - likely industry
  - likely project/customer split
  - likely risk profile
  - a minimal question list

Do not skip:

- do not generate outputs before synthesis
- do not ask broad questions when a smaller question set is sufficient

### Phase 5 — Ask User

Required actions:

- ask the minimum high-value questions
- fill key people/date/status gaps
- avoid redundant questions already answered by evidence

Exit condition:

- answers state is sufficient for first polished HTML

Do not skip:

- do not ask before synthesis
- do not ask more than needed

### Phase 6 — Render

Required actions:

- update config
- update answers
- build manifest
- render markdown
- render HTML
- prune empty directories

Exit condition:

- handover package is generated

Do not skip:

- do not render from incomplete state when critical facts are still missing

### Phase 7 — Refresh Mode

Only for later runs.

Required actions:

- inspect missing facts
- ask only for unresolved items
- re-render outputs

Exit condition:

- HTML and markdown are refreshed

Do not skip:

- do not re-run heavy first-scan logic unless trust/rescan rules require it

## Strong Enforcement Rule

When a phase is incomplete, the agent must not silently proceed to later phases.

In particular:

- no inventory → no ask user
- hard trigger hit → no single-thread continuation
- no synthesis → no generation

## Recommended Transcript Pattern

The agent should make phase transitions visible.

Examples:

- `Phase 1 complete: inventory baseline ready.`
- `Phase 2 triggered parallel subagent mode.`
- `Phase 3: now launching offboarding-role-detector, offboarding-project-mapper, offboarding-risk-checker, offboarding-missing-facts-detector.`
- `Phase 4 complete: findings synthesized, preparing targeted questions.`
- `Phase 6: rendering final handover package.`
