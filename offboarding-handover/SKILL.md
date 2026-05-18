---
name: offboarding-handover
description: 帮助离职员工把自己杂乱的工作资料整理成结构化的离职交接包，包含可配置的分类规则、适配行业的文档分类体系、HTML 可视化交接入口以及可打包交付的 ZIP 输出。适用于需要协助离职员工梳理零散工作资料、搭建交接目录、生成可视化入口页面、整理符合岗位特点的交接内容时。
---

# Offboarding Handover

Create a one-stop offboarding package from a messy working folder. Start from a configurable standard, adapt it to the user's role or industry, then generate a structured handover directory, a visual HTML entry, and a deliverable package.

## Non-Negotiable Rules

These rules are mandatory for this skill. Do not reinterpret them as optional guidance.

1. **Inventory comes first.**
   - Do not inventory until the source materials folder is explicit.
   - Do not ask the user before a full inventory baseline exists.
   - Do not start deep classification before inventory exists.

2. **Hard triggers must be obeyed.**
   Parallel subagent mode is required if any of these are true:
   - `total_files > 3000`
   - meaningful top-level branches > 8
   - internal + client/project + risk/compliance signals all appear
   - role confidence is not high

3. **Do not override a triggered parallel run with personal judgment.**
   - Do not say the folder is “simple enough” once the hard trigger rule is hit.
   - High role confidence does not cancel the branch-count trigger.
   - Clean naming does not cancel the branch-count trigger.

4. **One inventory worker alone is not enough.**
   - A single backgrounded inventory subagent does not satisfy parallel subagent mode.
   - If parallel subagent mode is triggered, you must launch at least 2 additional specialist subagents before continuing.

5. **If parallel subagent mode is triggered, ask-user must wait.**
   - Do not ask the user before specialist subagents return.
   - Do not generate markdown, HTML, or ZIP before synthesis and coverage check are complete.

6. **Make the fan-out explicit in the transcript.**
   When parallel subagent mode is triggered, explicitly state that you are launching:
   - `offboarding-role-detector`
   - `offboarding-project-mapper`
   - `offboarding-risk-checker`
   - `offboarding-missing-facts-detector`

   Recommended wording:
   - `清单基线已完成，已命中并行扫描条件。现在我将并行调用 offboarding-role-detector、offboarding-project-mapper、offboarding-risk-checker、offboarding-missing-facts-detector。`

7. **If evidence is weak, roll back instead of improvising.**
   - If inventory is incomplete, return to inventory.
   - If parallel subagent evidence is weak, return to parallel fan-out.
   - If synthesis is incomplete, do not move to ask-user or render.

8. **No source folder, no scan.**
   - If the user did not provide a folder, ask where the handover materials are.
   - Accept `当前文件夹` or a path.
   - Validate that the path exists, is a directory, and is readable before Phase 1.
   - Do not infer the source folder from previous outputs, recent history, or nearby folders.

9. **Polished output requires confirmation.**
   - Do not generate a polished HTML site or ZIP until the role, successor-facing facts, and deep material review are confirmed.
   - If these facts are missing, generate only a draft scan/report view and clearly say what still needs confirmation.
   - A guessed role is a routing hint, not a confirmed role.

10. **Identity and handover facts are hard gates.**
   - After inventory, trigger handling, synthesis, and coverage are complete, ask the compact identity and successor-facing questions before staging final files.
   - Confirm the handover owner/person, known aliases, role boundary, successor, handover coordinator, and last working day.
   - If any of these facts are unknown, the output must remain a draft unless the user explicitly marks the fact as intentionally unknown.
   - Do not treat a folder name, employee-name hit, or inferred role as confirmed identity.

11. **No other-person or superseded files in core output.**
   - Clearly other-person handover packages, personal summaries, performance reviews, role descriptions, trial/probation materials, and unrelated presentations must not be copied into the core handover package.
   - Team or project materials that mention another person may be relevant, but they must go to `review` unless the confirmed handover scope supports including them.
   - Obvious duplicate document versions must be collapsed before staging; keep the final/release/fixed version first, then newest explicit date, then newest modified time.
   - Every collapsed older version must be recorded with the retained representative in the manifest or filtering report.

12. **Staged filenames must be successor-friendly.**
   - Files copied into the handover package must use standardized names that can be understood outside the original messy folder.
   - Rename staged copies only; never rename or move original source files unless the user explicitly asks for in-place reorganization.
   - Preserve original file name, original path, standardized staged name, and version/superseded mapping in the manifest or filtering report.
   - If a safe standardized name cannot be generated, keep the file in `review` instead of silently copying it with a confusing name.

## Load Only What You Need

- Read [references/default-taxonomy.md](references/default-taxonomy.md) when deciding how to classify files and folders.
- Read [references/config-contract.md](references/config-contract.md) when creating or updating config files and manifests.
- Read [references/answers-contract.md](references/answers-contract.md) when storing first-run answers or later refresh updates.
- Read [references/agent-classification.md](references/agent-classification.md) when the folder is messy or role-specific and you need to classify content by inspecting real artifacts.
- Read [references/source-folder-gate.md](references/source-folder-gate.md) before scanning when the user did not explicitly name the material folder.
- Read [references/role-detection-and-ask-user.md](references/role-detection-and-ask-user.md) when you need to infer the likely role from file signals or decide which first-run questions to ask.
- Read [references/first-run-questions.md](references/first-run-questions.md) when preparing the first-run question set.
- Read [references/role-output-templates.md](references/role-output-templates.md) after the role is confirmed and before choosing the output folder structure.
- Read [references/deep-material-review.md](references/deep-material-review.md) before treating a large or mixed folder as deeply organized.
- Read [references/multi-agent-orchestration.md](references/multi-agent-orchestration.md) when the folder is large or ambiguous and you want to parallelize first-scan analysis with subagents.
- Read [references/first-scan-team-playbook.md](references/first-scan-team-playbook.md) when you need an executable coordinator/worker playbook for the first scan.
- Read [references/full-inventory-and-sharding.md](references/full-inventory-and-sharding.md) when you need to build a full inventory baseline, decide whether to shard the scan, and verify coverage.
- Read [references/execution-state-machine.md](references/execution-state-machine.md) when you need the strict phase-gated execution model for first-run correctness.
- Read [references/trust-recovery-and-rescan.md](references/trust-recovery-and-rescan.md) when existing state may be stale, partial, or untrustworthy and you need to recover to an earlier phase safely.
- Read [references/claude-agent-sync.md](references/claude-agent-sync.md) when running in Claude Code or Codex and you need to sync managed offboarding subagents into the local agent directory.
- Read [references/update-mode.md](references/update-mode.md) when the user wants to refresh an existing handover package and replace pending items.
- Read [references/high-risk-missed-items.md](references/high-risk-missed-items.md) when checking whether the handover misses common real-world offboarding items.
- Read [references/relevance-filtering.md](references/relevance-filtering.md) when the source folder is broad, team-level, company-level, customer-level, or likely contains other people's files, public materials, duplicates, or generated assets.
- Read [references/successor-view.md](references/successor-view.md) before writing website copy, generated markdown, or file-level summaries.
- Read [references/site-design-system.md](references/site-design-system.md) before changing the generated HTML site style or interaction model.
- Read [references/site-quality-checklist.md](references/site-quality-checklist.md) before treating the generated HTML site as polished.
- Run [scripts/bootstrap_handover.py](scripts/bootstrap_handover.py) when you need to scaffold, scan, classify, render, or export in one pass.
- Run [scripts/sync_claude_agents.py](scripts/sync_claude_agents.py) when you need to create or refresh the managed Claude or Codex subagents used by this skill.

## Workflow

Run this skill as a phase-gated workflow, not as a freeform exploration.

### Phase 0 — Detect context

- detect first run vs refresh
- detect whether scaffold exists
- detect whether output exists
- confirm the source materials folder; if missing, ask the user before scanning
- reject generated output folders such as `离职交接包`, `site`, ZIP files, or `.offboarding-handover` as source roots unless explicitly requested

### Phase 1 — Inventory baseline

- total file count
- total directory count
- top-level branches
- file count by branch
- extension distribution

### Phase 2 — Trigger check

Parallel subagent mode is required if any of these are true:

- `total_files > 3000`
- meaningful top-level branches > 8
- internal + client/project + risk/compliance signals all present
- role confidence is not high

### Phase 3 — Parallel subagent fan-out

If Phase 2 triggered parallel subagent mode:

- shard by directory ownership first
- spawn specialist subagents in parallel
- do not treat one backgrounded inventory worker as sufficient

### Phase 4 — Synthesis and coverage

- merge subagent findings
- verify coverage against inventory baseline
- prepare minimal high-value questions

### Phase 4.1 — Role confirmation gate

- infer likely role or role family from evidence
- ask the user to confirm or correct the role, handover owner/person, known aliases, and responsibility boundary before applying a role template
- ask only the smallest set of successor-facing questions needed to avoid a `待补充` final package
- confirm successor, handover coordinator, last working day, and whether unknown facts are intentionally unknown
- if the role is not confirmed, continue only as a draft scan/report

### Phase 4.5 — Relevance filtering

- decide `include`, `review`, or `exclude` before staging files
- treat employee name as a strong signal, not a required gate
- exclude only when there is a clear reason, such as other people's handover folders, public templates, generated assets, or superseded versions
- exclude clearly unrelated other-person materials before staging; put ambiguous shared project materials in `review`
- keep ambiguous team or project materials in `review` instead of copying them silently
- deduplicate obvious document versions and keep the latest or final representative
- record version-collapsed older paths and their retained representative

### Phase 4.6 — Staged filename normalization

- generate successor-friendly staged filenames for every copied `include` file
- use a stable pattern such as `{序号}-{项目或客户简称}-{主题}-{材料类型}-{状态}-{日期}-{版本}.{扩展名}`
- keep file types as extensions and tags, not top-level folders
- write original name, original path, staged name, and rename reason to the manifest or filtering report
- never rename original source files unless the user explicitly requests in-place reorganization

### Phase 4.8 — Deep material review

- sample high-value documents before final synthesis
- group materials by project, customer, workflow, active status, risk, and successor action
- avoid putting many unrelated files into `未完事项与状态` simply because they live under `归档`
- mark old versions and historical context as references, not active handover work

### Phase 5 — Ask user

- ask only after synthesis
- fill key facts that would otherwise become `待补充`
- if key facts remain missing, keep the output in draft state

### Phase 6 — Render

- update config and answers
- build manifest
- render markdown
- render HTML
- prune empty directories
- export ZIP only when polished-output gates are satisfied or the user explicitly asks for a draft ZIP

### Phase 7 — Refresh

- inspect unresolved items
- ask only for missing facts
- re-render markdown and HTML

### Trust recovery

- if intermediate state is incomplete, stale, or weakly supported, fall back to the earliest untrusted phase
- do not automatically trust manifest, output, or partial scan artifacts
- if the hard trigger rule was hit but parallel subagent evidence is weak, return to Phase 3 instead of continuing

Polished output gates:

- material folder confirmed
- role confirmed by the user
- handover owner/person, known aliases, role boundary, successor, handover coordinator, and last working day confirmed or intentionally marked unknown
- successor-facing information needs confirmed
- deep material review completed
- directory structure chosen from the confirmed role template
- retention decisions completed for every staged file
- other-person materials excluded or listed for review
- obvious document versions collapsed and recorded
- staged filenames standardized and original-name mapping preserved

## Classification Rules

- Decide retention first: `include`, `review`, or `exclude`.
- Use `scope` first, then `doctype`, then `status` and `sensitivity`.
- Keep Word, PowerPoint, Excel, and PDF as tags only. Do not make them top-level folders unless the user explicitly asks.
- Prefer `organization knowledge`, `role materials`, `project artifacts`, `legal/compliance`, `design/assets`, and `historical references` as classification anchors.
- Separate `must-read current materials` from `historical references`.
- Treat links and online docs as first-class assets. Keep a local index even when the source stays online.
- Do not copy every file from a broad team or company folder. Copy only files with handover value, list uncertain files for review, and explain excluded files.
- Employee names, aliases, and initials are strong include signals but not mandatory. Files without the employee's name may still be included when role, project, customer, risk, or operational context supports handover value.
- Clearly unrelated personal materials for other people, company-wide public templates, generated prototype exports, and superseded versions should not be staged into the handover package by default.
- Other people's personal reviews, personal presentations, role descriptions, trial/probation materials, and handover packages are strong exclusion signals unless the user explicitly confirms they are part of this handover.
- Shared project files that mention another person are not automatic excludes; keep them in `review` unless the confirmed scope proves they are handover-critical.
- Staged file names should be normalized for successor reading and sorting, while original names and paths remain traceable.
- Do not keep expanding the script with large, hard-coded role dictionaries unless the mapping is clearly stable and low-risk.
- For nuanced role overlays, inspect the real folder with `grep`/`find` as the baseline and `rg` as an optional accelerator, then write the resolved mapping into config or manifest outputs.
- Treat `归档`, `历史`, and `archive` as status signals, not automatic destinations. A file under `归档` can still be a product plan, project artifact, contract, report, or active reference.

## First-Run Behavior

On the first run in a folder, create a scaffold before moving files if the user has not asked for destructive reorganization. Prefer copy or staged-output workflows over direct in-place moves until the user confirms the mapping is acceptable.

If the user did not provide a material folder, ask for it first. The user may reply `当前文件夹` or provide a path. Do not begin inventory until the folder is validated.

If the environment supports interactive questioning, ask for a compact first-run profile after inventory, trigger handling, synthesis, and coverage. Otherwise infer a draft routing guess from the folder contents and record assumptions in the config. A non-interactive default is not a confirmed role.

The compact first-run profile must confirm:

- handover owner/person and known aliases
- role or responsibility boundary
- successor
- handover coordinator
- last working day
- whether unknown facts should remain intentionally unknown

For large or ambiguous folders, do not jump straight from scan to final HTML. First run the full state machine: inventory → trigger check → parallel subagents if required → synthesis → ask user → render.

The coordinator should follow `references/first-scan-team-playbook.md` rather than inventing an ad-hoc team every time.
The coordinator should also follow `references/full-inventory-and-sharding.md` so that scan coverage is measurable before parallel work begins.

If the hard trigger rule is hit, the agent must not stop after inventory and must not proceed directly to asking the user or generating outputs.
If a phase is incomplete, the agent must not silently continue to a later phase.
If current state is not trustworthy enough, the agent must roll back to the appropriate earlier phase instead of improvising past the gap.

## Output Expectations

Produce these artifacts unless the user narrows scope:

- a config file that records taxonomy and project metadata
- a normalized handover directory
- an HTML entry page rendered from the manifest
- a manifest or index of key files and staged targets
- a filtering report that shows included, review, excluded, and version-collapsed materials
- a filename mapping that shows original path/name and standardized staged name for copied files
- an optional ZIP package

## HTML Site Standard

The generated `site/index.html` is the front door for the whole handover package.

- Use the fixed technology-company internal portal style in `references/site-design-system.md`.
- Use `#FBFCFE` as the page background.
- Keep the interface clean, dense, searchable, and operational.
- Connect every generated core handover document from the site instead of making the successor browse the folder tree first.
- Surface high-risk items, unfinished work, and missing facts before the full file table.
- Do not imitate PPT or magazine layouts, horizontal slide navigation, WebGL hero backgrounds, decorative gradients, or large marketing-style hero sections.
- Do not expose implementation details such as scripts, manifests, or internal scan steps in user-facing copy unless the user explicitly asks for technical output.

## Agent Execution

The script is the agent's internal execution entrypoint. Do not instruct the end user to run it manually unless the user explicitly asks for command-line usage.

```bash
python3 scripts/bootstrap_handover.py /path/to/folder --interactive
```

Useful internal flags for the agent:

- `--no-scan`: scaffold only
- `--stage-mode copy|none`: copy files into the output tree or only classify them
- `--zip-output`: force zip export
- `--refresh`: refresh an existing handover package from saved answers and new prompts
- `--profile-confirmed`: mark the role/profile direction as confirmed by the user
- `--successor-view-confirmed`: mark successor-facing facts and reading needs as confirmed
- `--deep-review-complete`: mark agent-led deep material review as complete
- `--allow-draft-zip`: export a ZIP even when the package is still a draft
- `--employee-name`, `--department`, `--role`, `--industry`, `--last-working-day`, `--handover-owner`, `--successor`: write first-run answers without TTY prompts

## User Interaction Rule

- The end user should interact with the **skill**, not the script.
- If the user has not confirmed the material folder, ask for it before scanning.
- On first run, the agent should inspect the folder, infer likely role and risks, then ask a compact set of questions before generating the first polished HTML.
- If the user has not confirmed the role or successor-facing facts, generate a draft only.
- On later runs, the agent should detect unresolved items such as `待补充`, ask only for the missing facts, update internal state, then refresh markdown and HTML.
- Treat command examples as agent implementation details, not user-facing instructions.

## Mandatory Parallel-Subagent Rule

- One backgrounded inventory worker alone does **not** count as a valid parallel first scan.
- If parallel subagent mode is triggered, the agent must spawn additional parallel subagents with disjoint responsibilities before continuing.
- If parallel subagent mode is triggered, the agent must complete synthesis and coverage check before asking the user.
- If parallel subagent mode is triggered, the agent should explicitly state the fan-out step in the transcript, naming the subagents it is about to launch. Do not hide the transition behind vague wording such as `继续扫描`.
- In Claude Code environments, prefer these dedicated subagents when parallel subagent mode is triggered:
  - `offboarding-inventory-baseliner`
  - `offboarding-role-detector`
  - `offboarding-project-mapper`
  - `offboarding-risk-checker`
  - `offboarding-missing-facts-detector`
- Subagent model routing:
  - If the current runtime is GPT/Codex, prefer `gpt-5.4` for offboarding specialist subagents.
  - If the current runtime is Claude, prefer `haiku` for offboarding specialist subagents.
  - Treat this as a runtime selection rule. Do not edit generated or managed agent config files solely to enforce it.
- These Claude subagents should preload the `offboarding-handover` skill via their `skills` frontmatter so they inherit the same playbook and references at startup.
- In Claude Code environments, before relying on the dedicated offboarding subagents, sync the managed agent templates from this skill into `~/.claude/agents/` if they are missing or outdated.
- In Codex environments, before relying on the dedicated offboarding subagents, sync the managed agent templates from this skill into `~/.codex/agents/` if they are missing or outdated.
- In environments that are neither Claude Code nor Codex, do not hard-require local agent files. Fall back to the skill instructions, coordinator logic, and prompt-based worker decomposition so the flow still works.

## Recommended Transcript Pattern

When the hard trigger rule is hit, prefer wording like:

- `清单基线已完成，已命中并行扫描条件。现在我将并行调用 offboarding-role-detector、offboarding-project-mapper、offboarding-risk-checker、offboarding-missing-facts-detector。`

After that, launch the subagents instead of continuing in a single thread.

## Division of Responsibilities

- Let the script handle deterministic infrastructure:
  - scaffold generation
  - config writing
  - answers-state writing
  - manifest writing
  - standard markdown page rendering
  - HTML rendering
  - empty-directory pruning
  - ZIP export
- Let the agent handle nuanced judgment:
  - role-specific classification
  - deciding whether a file is current or historical reference
  - deciding whether a document belongs to business handover, legal/compliance, or general knowledge
  - correcting ambiguous auto-classification results after inspecting filenames and file contents
  - deciding whether parallel subagent orchestration is worth the overhead
  - building the inventory baseline before deep analysis
  - deciding whether to shard by directory
  - assigning parallel workers with disjoint responsibilities
  - checking scan coverage before synthesis
  - synthesizing findings from parallel workers into one question set and one final handover view
  - confirming the source folder and role before polished output
  - deciding the successor-facing directory template
  - reviewing high-value materials enough to explain status, next action, risk, and supporting files

## Validation Checklist

- The config is valid against the contract.
- The generated directory includes the expected top-level modules.
- The HTML entry references the generated modules and key documents.
- The HTML entry follows `references/site-design-system.md`.
- The HTML entry passes the P0 items in `references/site-quality-checklist.md`.
- The HTML entry and filtering report show how many files were included, need review, and were excluded.
- Draft output is clearly labeled when polished-output gates are not met.
- File entries prefer `查看预览` plus `打开原文件`; do not label local Office links as downloads unless they truly download.
- The manifest can be read without opening the original chaotic folder.
- The manifest records original name, original path, standardized staged name, retention decision, and version/superseded mapping.
- Core staged files do not include clearly unrelated other-person personal materials.
- Obvious duplicate document versions are collapsed before final output.
- Staged file names are readable, sortable, and useful to a successor outside the original source tree.
- High-risk items such as accounts, devices, and legal materials are surfaced explicitly.
- The missed-items checklist has been reviewed for accounts, seals, certificates, working phones, paper records, and unit operator identities.
