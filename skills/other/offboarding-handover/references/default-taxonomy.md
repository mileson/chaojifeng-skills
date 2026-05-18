# Default Taxonomy

Use this taxonomy when the user has not supplied a company-specific standard.

## Presentation Modules

These are the four modules shown in the generated site and overview flow:

1. `交接信息`
2. `交接总览`
3. `专项交接`
4. `未完事项与状态`

## Content Domains

These are the eight default content domains the skill should preserve underneath the presentation layer:

1. `工作事项`
2. `关系人`
3. `文档知识`
4. `指标口径`
5. `风险遗留`
6. `资产权限`
7. `合规结算`
8. `交接状态`

## Recommended Output Tree

```text
离职交接包/
├── 00-说明与导航/
│   ├── 00-交接总览.md
│   ├── 01-阅读顺序.md
│   └── 02-文件清单.md
├── 01-交接信息/
├── 02-交接总览/
├── 03-专项交接/
│   ├── 10-工作事项/
│   ├── 20-关系人与协作方/
│   ├── 30-文档与知识资产/
│   ├── 40-指标与口径/
│   ├── 50-风险与遗留事项/
│   ├── 60-资产与权限/
│   └── 70-合规与结算/
├── 04-未完事项与状态/
│   ├── 00-进行中事项总表.md
│   ├── 01-高遗漏检查清单.md
│   └── 02-交接结论说明.md
└── site/
    └── index.html
```

## Tag Axes

Use these tag axes in config, manifests, or generated indexes.

### scope

- `org`
- `role`
- `project`
- `legal`
- `design`
- `historical`

### doctype

- `docx`
- `pptx`
- `xlsx`
- `pdf`
- `kb`
- `minutes`
- `sop`
- `template`
- `contract`
- `asset`
- `link`

### status

- `draft`
- `review`
- `final`
- `historical`

### sensitivity

- `public`
- `internal`
- `restricted`
- `confidential`

## Role Overlays

Enable these overlays when the role is clear:

- `product`: PRD, requirement pool, user research, competition analysis, roadmap
- `product_delivery`: customer projects, requirements, delivery plans, rollout, training, backlog, issue logs
- `operations`: activity plan, channels, content calendar, campaign review
- `sales`: customer list, opportunity stage, contract, receivables, owner map
- `engineering`: repositories, deployment docs, service ownership, runbooks, secrets rotation
- `finance`: ledger, reports, reimbursement, tax items, unsettled items
- `legal`: contract ledger, disputes, review queue, seals and approvals
- `hr`: recruiting pipeline, candidate notes, employee records, leave/socfund items

## Handling Principles

- Keep source files when possible; use generated folders as the handover view.
- Treat `site/index.html` as the successor's first entry, not as a decorative appendix.
- Copy only files with handover value. Use the filtering report for review and excluded materials.
- Mark `final` versions explicitly.
- Place unresolved items, ongoing work, and risks in one unique place.
- Separate company-owned accounts and assets from personal ones.
- Treat `归档` and `历史` as status signals. Do not send all archived files to `未完事项与状态`.
- When the confirmed role is product/project delivery, prefer directories such as `客户项目与需求`, `产品方案与知识库`, `数据报表与测算`, `客户与协作关系`, `合同对账与合规`, and `历史归档参考`.
