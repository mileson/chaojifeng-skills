# Relevance Filtering

Use this reference when the user gives a broad team, department, customer, or company folder and expects a personal handover package.

The goal is not to move every file into a nicer folder. The goal is to reduce successor review cost by keeping files that have handover value and explaining why other files were left out.

## Core Principle

Do not use the employee name as the only inclusion gate.

- A file that names the employee is a strong include signal.
- A file that does not name the employee can still be highly relevant if it belongs to the person's role, project, customer, current delivery, account, risk, or operational responsibility.
- A file should be excluded only when there is a clear reason it is not useful for this handover.
- If ownership or handover value is unclear, put it in `review` instead of copying it silently or excluding it silently.

## Retention Decisions

Every scanned file should receive one of these decisions before staging:

- `include`: copy into the handover package.
- `review`: do not copy by default; list it for the user or successor to confirm.
- `exclude`: do not copy; list the reason in the filtering report.

The decision should be recorded in the manifest with concise reasons.

## Identity and Ownership Baseline

Before copying files, the coordinator must have a working identity baseline:

- handover owner/person
- known aliases, initials, department names, product-line names, and common project ownership markers
- role or responsibility boundary confirmed by the user, or marked as draft-only
- successor and handover coordinator, or intentionally unknown

Use this baseline for routing, but do not use it as a single hard inclusion gate. A file without the owner name can still be relevant; a file with another person's name can still be a shared project artifact. The decision must be explained.

## Strong Include Signals

Include when there is no stronger exclusion signal and the file matches at least one of these:

- employee name, known alias, initials, or role-specific owner marker
- current customer or project materials that match the employee's handover scope
- plans, milestones, delivery notes, launch materials, issues, risks, or follow-up records
- account, permission, device, system, customer, contract, reimbursement, invoice, or settlement materials
- handover-critical generated markdown produced by this skill
- final reports, current training decks, blueprints, operating manuals, SOPs, metrics, dashboards, or stakeholder maps

## Strong Exclusion Signals

Exclude when the file is clearly not useful for this employee's handover:

- macOS resource files such as `._*` and `.DS_Store`
- temporary Office files such as `~$*.docx`
- other people's handover folders such as `工作交接-某人` when the folder does not name the employee
- other people's personal review, personal summary, personal role description, or talent inventory files
- other people's personal presentations, probation/trial forms, performance-review materials, personal OKR/goal decks, personal role descriptions, and private work summaries unless explicitly confirmed as part of this handover
- company-wide templates, public policies, general examples, and reference cases unless tied to a current handover item
- old versions superseded by a newer or final version of the same document
- generated prototype export assets such as `images/`, `resources/`, `js`, `css`, icon sprites, fonts, and static demo files
- dependency/vendor/cache folders or tool-generated build output

## Review Signals

Put files in `review` when they may matter but should not be copied without confirmation:

- team-authored material with no clear personal owner
- customer/project folders that match the department but not the employee's known role
- archives such as `.zip`, `.rar`, or `.7z` that may contain many unrelated files
- public templates that appear to be attached to an active customer/project delivery
- prototype entry files where the source design file is missing
- materials with multiple names where the employee is one of several contributors
- shared meeting decks, project plans, customer materials, or demos that mention another person but appear tied to the confirmed handover scope

## Other-Person Material Guard

When a file path or name contains a person name that is not the confirmed handover owner or alias:

1. If the file is clearly personal, choose `exclude`.
   - examples: personal述职, personal总结, trial/probation forms, talent inventory, role description, another person's handover folder
2. If the file is a shared project/customer/workflow artifact, choose `review` unless the confirmed scope proves it is handover-critical.
   - examples: project meeting decks, customer presentations, training material, demo notes, cross-functional reports
3. If the user confirms this other-person file is required supporting evidence, choose `include` and record the confirmation reason.
4. Never copy a file with another person's name into the core package silently.

The filtering report should show representative other-person exclusions and review candidates.

## Version Deduplication

When several files look like versions of the same document:

1. Normalize the name by removing dates, version suffixes, copy markers, and final/draft markers.
2. Group only within the same or closely related folder and same extension.
3. Keep the best representative:
   - explicit final/release/fixed version first
   - newest explicit date second
   - newest modified time third
4. Mark the older versions as `exclude` with a superseded reason.
5. Keep the superseded file path and retained file path in the manifest or filtering report.

Do not deduplicate files with different business meaning just because their names are short or generic.

## Staged Filename Normalization

Files copied into the handover package should be renamed for successor reading and sorting. Rename staged copies only; never rename original source files unless the user explicitly asks for in-place reorganization.

Recommended staged filename pattern:

```text
{序号}-{项目或客户简称}-{主题}-{材料类型}-{状态}-{日期}-{版本}.{扩展名}
```

Field rules:

- `序号`: three digits within a section, based on reading priority or stable manifest order, such as `001`
- `项目或客户简称`: stable short label such as `DBN大北农`, `越秀`, `猪联网Pro`, or `供应链`
- `主题`: the cleaned business topic after removing noise such as `副本`, `复制`, repeated `最终`, bracket counters, and temporary markers
- `材料类型`: controlled terms such as `需求说明`, `培训材料`, `蓝图设计`, `会议纪要`, `对账表`, `项目计划`, `操作手册`, `评估报告`, `原型源文件`
- `状态`: controlled values such as `current`, `final`, `review`, or `historical`
- `日期`: `YYYYMMDD`, using explicit filename date first, then document date, then modified time
- `版本`: `v01`, `v02`, or `final`; collapsed old versions should not be copied into core output

Staged filename constraints:

- keep the original file extension
- avoid path separators, control characters, emoji, repeated whitespace, and punctuation that is unsafe across systems
- prefer concise names; keep the filename understandable without relying on the source folder
- if two staged names collide, append a short stable suffix and record the collision resolution
- if the agent cannot generate a safe meaningful staged name, put the item in `review`

Manifest records should include:

- `original_name`
- `original_path`
- `staged_name`
- `staged_path`
- `rename_reason`
- `version_group_key` when applicable
- `superseded_by` when applicable

## Prototype and Generated Asset Folding

For prototype or UI folders, do not copy every exported static asset.

Prefer:

- source files such as `.rp`, `.fig`, `.sketch`, `.drawio`, `.vsdx`
- a single entry HTML if it is the only readable artifact
- compressed bundles when they are clearly the intended deliverable
- a short index in the filtering report explaining that generated assets were folded

## Output Expectations

The final package should include:

- copied `include` files only
- `review` candidates listed in the site and filtering report
- `exclude` counts and representative examples
- version groups where older files were excluded
- original-to-staged filename mapping for copied files
- reasons that a normal business user can understand

The successor should be able to answer:

- What did we keep?
- What still needs confirmation?
- What did we intentionally leave out?
- Which duplicate versions were collapsed?
- What is the readable handover filename, and where did the original file come from?
