# Role Output Templates

Use this reference after the role has been inferred and confirmed.

The goal is not to create a folder per file type. The goal is to create a handover view that matches how the successor will take over the role.

## Product / Requirement / Project Delivery

Use when the folder signals PRD, product plans, customer projects, delivery, training, rollout, backlog, or project status.

```text
离职交接包/
├── 00-说明与导航/
├── 01-交接信息/
├── 02-交接总览/
├── 03-专项交接/
│   ├── 10-客户项目与需求/
│   ├── 20-产品方案与知识库/
│   ├── 30-数据报表与测算/
│   ├── 40-客户与协作关系/
│   ├── 60-账号权限与资产/
│   ├── 70-合同对账与合规/
│   └── 80-历史归档参考/
├── 04-未完事项与状态/
│   └── 10-待跟进问题/
└── site/
```

Key successor questions:

- 哪些客户或项目还要接？
- 哪些需求、方案、蓝图、原型是当前有效版本？
- 哪些问题、上线范围、验收、试点或推广动作没收尾？
- 哪些报表、测算表、合同、对账材料需要继续维护？

## Sales / Presales

Use when the folder signals customers, opportunities, quotes, bids, contracts, receivables, or CRM exports.

Recommended directories:

- `10-客户与商机`
- `20-报价投标与方案`
- `30-合同回款与风险`
- `40-客户联系人与沟通记录`
- `80-历史归档参考`

## Operations / Customer Success

Use when the folder signals SOP, customer onboarding, activities, content calendars, tickets, operations data, or customer groups.

Recommended directories:

- `10-日常SOP与流程`
- `20-客户/用户运营`
- `30-活动与内容`
- `40-数据复盘与报表`
- `50-异常与待跟进`

## Engineering / Testing / Data

Use when the folder signals repos, deployment, scripts, environments, test cases, issues, reports, metrics, or dashboards.

Recommended directories:

- `10-系统与服务边界`
- `20-部署运行与账号权限`
- `30-测试用例与缺陷`
- `40-数据口径与报表`
- `50-遗留问题与排障记录`

## Finance / Legal / HR / Admin

Use when the folder signals contracts, seals, certificates, reimbursements, payroll, social benefits, personnel materials, or approvals.

Recommended directories:

- `10-待办与经办事项`
- `20-合同证照与审批`
- `30-结算报销与台账`
- `40-纸质材料与实物`
- `50-风险与权限`

## Rules

- Confirm the role before applying a role template.
- If two roles overlap, choose one primary template and add secondary directories only when needed.
- Keep file types as tags and filters, not top-level directories.
- Put old versions and broad historical context under `历史归档参考`, not under active work.
