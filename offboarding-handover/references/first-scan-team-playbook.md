# First-Scan Team Playbook

Use this playbook when the first scan is too large or too ambiguous for one agent to classify confidently.

This is the recommended execution pattern for the offboarding-handover skill.

## Objective

Before generating the first polished HTML, the team should answer:

1. what role or role family most likely owns this folder
2. whether the materials are mostly internal, client/project, or mixed
3. what unfinished work exists
4. what assets, permissions, and compliance risks exist
5. what minimum questions should be asked before rendering

Before all of that, the coordinator should establish a full inventory baseline as described in `references/full-inventory-and-sharding.md`.

## Hard Trigger Rule

After the inventory baseline is built, the coordinator **must** enter parallel subagent mode if any of the following is true:

- total file count is greater than 3000
- meaningful top-level branches are greater than 8
- internal materials, client/project materials, and risk/compliance signals are all present
- likely role confidence is not high

If none of the above is true, single-agent mode is allowed.

## Subagent Shape

Use **1 coordinator + up to 4 subagents**.

### Coordinator

Owns:

- kickoff and worker assignment
- reading only the minimum required references
- conflict resolution
- synthesis
- ask-user question design
- final rendering decision

### Worker A — Role Detector

Owns:

- likely role inference
- confidence and ambiguity boundaries
- top signals that support role detection

Read:

- `references/role-detection-and-ask-user.md`
- `references/agent-classification.md`

### Worker B — Project and Domain Mapper

Owns:

- clustering by project, product line, customer, internal initiative, or historical archive
- identifying what should become the main sections under `03-专项交接`

Read:

- `references/default-taxonomy.md`
- `references/agent-classification.md`

### Worker C — Risk and Asset Checker

Owns:

- accounts
- permissions
- devices
- credentials
- legal/compliance signals
- sensitive materials

Read:

- `references/high-risk-missed-items.md`
- `references/default-taxonomy.md`

### Worker D — Inflight and Missing-Facts Detector

Owns:

- unfinished work
- pending status
- likely `待补充` fields
- first-run question candidates

Read:

- `references/first-run-questions.md`
- `references/update-mode.md`

## Execution Steps

### Step 0 — Coordinator inventory baseline

Coordinator first builds a light but complete inventory:

- total files
- total dirs
- top-level branches
- file counts by branch
- extension distribution

Then coordinator decides whether to stay single-agent or switch to parallel subagent mode.

### Step 1 — Coordinator triage

Do a very light scan first.

If the folder is obviously small and clean, single-agent mode is allowed.

If the hard trigger rule is hit, parallel subagent mode is mandatory.

### Step 2 — Spawn subagents in parallel

Each worker should inspect a different concern, and for large folders should also have bounded path ownership.

**One backgrounded agent alone does not count as parallel subagent mode.**

Parallel subagent mode means:

- one coordinator
- plus at least 2 parallel subagents

Recommended target:

- 1 coordinator + 4 subagents

Before spawning them, the coordinator should explicitly announce the fan-out step in natural language.

Recommended announcement pattern:

- `清单基线已完成，已命中并行扫描条件。现在我将并行调用以下 subagents：role-detector、project-mapper、risk-checker、missing-facts-detector。`

If only two or three are needed, the coordinator should still explicitly name them.

Bad pattern:

- silently launching one extra worker
- saying only `继续扫描`
- implying that inventory alone already satisfied the parallel requirement

### Step 3 — Worker outputs

Each worker must return:

- `scope`
- `findings`
- `confidence`
- `conflicts`
- `questions`

### Step 4 — Coordinator synthesis

Coordinator merges outputs into:

- likely role
- likely industry overlay
- likely folder split
- likely high-risk checklist
- minimum ask-user question set

### Step 5 — Coverage check

Before asking the user, coordinator verifies:

- all meaningful branches were covered
- no major path slice was dropped
- duplicate ownership is understood

### Step 6 — Ask the user

Ask the smallest high-value question set needed to avoid a low-quality first HTML.

Prefer:

- role/work-type question
- internal vs client/project question
- unfinished-work question
- assets/sensitive-content question
- key people and dates question

### Step 7 — Generate

Only after the answers are collected:

- update config
- update answers state
- build manifest
- render markdown
- render HTML
- prune empty directories

## Output Contract for the Coordinator

Before generation, coordinator should be able to state:

- likely role:
- likely industry:
- customer/project mix:
- risk profile:
- unanswered critical facts:
- next questions to ask:

## Important Rule

Workers should not write the final handover outputs in parallel.

Only the coordinator should update:

- config
- answers
- manifest
- final markdown pages
- HTML

This prevents merge conflicts and inconsistent handover state.

## Never Skip These Rules

- Never treat inventory alone as sufficient parallel execution
- Never jump from inventory directly to final generation when parallel subagent mode was triggered
- Never ask the user before worker findings have been synthesized
- Never declare first scan complete without a coverage check
