# Role Detection and Ask-User Reference

Use this reference when the folder is messy and you need to:

1. infer the user's likely role from file signals
2. decide which first-run questions have the highest information gain
3. choose an industry or role overlay without hard-coding the whole classification

Keep this file for **early routing only**. Do not treat it as a final role verdict.

## Core Principles

- Infer by **evidence combinations**, not by one file.
- Prefer **business object and recurring artifacts** over job titles written inside documents.
- Ask the user only the **smallest set of questions** needed to reduce ambiguity.
- Treat role detection as a **routing hint**, not a truth source.
- A detected role is not confirmed until the user accepts or corrects it.

## Confidence Rule

Use these confidence levels:

- **High**: 3+ strong signals align
- **Medium**: 2 strong signals align, but cross-functional overlap exists
- **Low**: only generic files such as meeting notes, weekly reports, or screenshots

Strong signals include:

- stable folder names
- repeated artifact types
- role-specific keywords
- role-specific systems or tools

## Default First-Run Routing

On first run, try to answer these 4 questions before asking deeper follow-ups:

1. What kind of work does this folder mostly represent?
2. Does it include client or project handover?
3. Are there unfinished items that someone must continue?
4. Are there accounts, permissions, devices, contracts, or other sensitive items?

## Recommended First-Run Questions

Use short user-facing wording.

### Q1
**这批资料最接近你哪类工作？**

Recommended options:

- 产品/需求/方案
- 项目实施/交付
- 运营/客户成功
- 销售/售前
- 研发/测试/数据
- 财务/法务/人事/行政
- 其他

### Q2
**这里面主要是内部资料，还是也包含客户/项目资料？**

Recommended options:

- 主要是内部资料
- 内部和客户/项目资料都有
- 主要是客户/项目资料
- 还不确定

### Q3
**有没有还在推进、还没收尾的事？**

Recommended options:

- 有，且比较多
- 有，但不多
- 基本没有
- 还不确定

### Q4
**有没有账号、权限、设备或敏感资料需要交接？**

Recommended options:

- 有，比较多
- 有，少量
- 基本没有
- 还不确定

Optional final free-text prompt:

- **还有哪类内容最怕漏掉？**

After the scan, ask a confirmation question before polished output:

- **我推断这批资料主要按「{角色/职责}」交接，是否准确？如果不准确，请直接改。**

## Role Signal Matrix

Use this as a quick lookup table. The goal is not perfect classification. The goal is better follow-up questions.

| Likely role | Strong file signals | Typical keywords | Typical systems/tools | Main confusion boundary |
|---|---|---|---|---|
| 产品经理 | PRD, 需求池, 路线图, 原型说明, 竞品分析, 用户调研 | 需求, 版本, 优先级, 验收, 迭代, 功能 | Jira Product Discovery, Aha!, Axure, 墨刀, Figma | 容易和项目经理、设计混淆 |
| 项目经理/交付 | 项目计划, 里程碑, 风险台账, 周报, RAID, 验收 | 里程碑, 资源, 风险, 进度, 交付, 验收 | Jira, MS Project, Asana, 飞书项目 | 容易和产品、实施、运营混淆 |
| 运营/客户成功 | SOP, 日报周报, 活动排期, 运营复盘, FAQ, 工单处理 | 拉新, 留存, 转化, 活动, 工单, 履约 | 企业微信, 客服系统, OMS, WMS, TMS | 容易和销售、项目经理混淆 |
| 销售/售前 | 客户清单, 商机台账, 报价单, 标书, 方案书, 回款跟进 | 商机, 报价, 客户, 回款, 线索, 成交 | Salesforce, HubSpot, 销售易, 纷享销客 | 容易和法务、项目经理混淆 |
| 财务 | 总账, 应收应付, 发票, 凭证, 预算, 对账, 结账 | 科目, 对账, 报销, 税务, 预算, 凭证 | SAP FI/CO, Oracle, 用友, 金蝶, NetSuite | 容易和HR、采购混淆 |
| 法务 | 红线合同, 审查意见, NDA, 授权书, 用印, 争议材料 | 条款, 风险, 合规, 红线, 保密, 知识产权 | Ironclad, DocuSign, Adobe Sign, CLM | 容易和销售、HR混淆 |
| HR | JD, 简历, Offer, 入转调离, 花名册, 绩效, 培训签到 | 招聘, 转正, 考勤, 绩效, 社保, 公积金 | Workday, SuccessFactors, 北森, Moka, ADP | 容易和财务、法务混淆 |
| 研发 | 源码目录, 接口文档, 配置文件, migration, runbook, 故障复盘 | 代码, 接口, 部署, schema, 发布, 异常 | GitHub, GitLab, Jenkins, Kubernetes, Sentry | 容易和测试、运维混淆 |
| 测试 | 测试计划, 用例, 缺陷单, 回归报告, 环境矩阵, 验收清单 | 提测, 回归, 缺陷, 用例, 通过率, 复现 | TestRail, Xray, Zephyr, JMeter, BrowserStack | 容易和研发、产品混淆 |
| 设计 | 设计稿, 组件库, 交互稿, 视觉规范, 切图, 设计走查 | 视觉, 交互, 组件, 版式, 动效, 品牌 | Figma, Sketch, PS, AE | 容易和产品混淆 |
| 数据/BI | SQL, 指标口径, 看板, 报表, 埋点, ETL | 指标, 口径, SQL, 看板, 留存, 转化 | Tableau, Power BI, Looker, 数据平台 | 容易和产品、运营混淆 |

## Fast Role Heuristics

Use these shortcut rules:

- If you see `PRD + 原型 + 版本规划`, lean **产品**
- If you see `项目计划 + 风险台账 + 验收`, lean **项目经理/交付**
- If you see `SOP + 日报周报 + 活动排期`, lean **运营**
- If you see `报价单 + 商机台账 + 客户跟进`, lean **销售**
- If you see `凭证 + 发票 + 对账`, lean **财务**
- If you see `红线合同 + 审查意见 + 用印`, lean **法务**
- If you see `简历 + Offer + 入转调离`, lean **HR**
- If you see `源码 + 配置 + 部署`, lean **研发**
- If you see `测试用例 + 缺陷单 + 回归报告`, lean **测试**
- If you see `Figma/Sketch + 组件库 + 视觉规范`, lean **设计**
- If you see `SQL + 指标口径 + 看板`, lean **数据/BI**

## Industry Overlay

Use industry as a second-layer hint, not the first verdict.

| Industry | More likely roles | More likely file signals | Better follow-up question |
|---|---|---|---|
| 互联网/软件 | 产品, 研发, 测试, 运维, 数据, 增长运营 | PRD, 接口文档, 发布记录, 埋点表, 看板权限 | 你主要交接的是产品线、系统、数据，还是线上权限？ |
| 制造 | 生产, PMC, 工艺, 质量, 设备, 采购 | BOM, SOP, 工艺卡, 排产表, 巡检记录 | 你负责的是产线、工艺、质量、设备，还是供应商？ |
| 零售/电商 | 商品, 店铺运营, 直播, 投流, 仓配协同 | SKU表, 活动档期, 中控表, 投放复盘, 库存表 | 你更偏商品、店铺、直播、投流，还是仓配？ |
| 金融 | 客户经理, 风控, 合规, 投研, 清算 | 客户档案, 审批流, 风控规则, 投研报告 | 是否涉及客户资产、授信审批或合规留痕？ |
| 教育 | 教研, 教务, 学员管理, 课程顾问 | 教案, 题库, 排课表, 学员档案 | 你负责的是课程内容、教学运营，还是学员管理？ |
| 医疗/医药 | 注册, CRA, 医学, 学术, 安全合规 | 注册资料, 研究方案, 学术材料, AE记录 | 是否有注册、临床、医学或安全合规材料？ |
| 物流供应链 | 仓储, 调度, 计划, 物流规划 | 路由表, 时效SLA, 异常工单, 供应计划 | 你更偏仓、运、配、计划，还是承运商管理？ |
| 地产/工程 | 项目管理, 招采, 造价, 设计管理 | 图纸, 签证变更, 招投标, 进度计划 | 是否涉及项目现场、图纸、合同或结算？ |

## Ask-User Branching Rules

After Q1-Q4, branch like this:

### If likely 产品
Ask:
- 你更想优先交接需求背景、功能方案、原型说明，还是迭代状态？
- 有没有口头约定但没写进文档的业务规则？

### If likely 项目/交付
Ask:
- 现在还有哪些项目或客户在推进中？
- 哪些项目最需要优先交接？

### If likely 运营
Ask:
- 需要优先整理活动、日常SOP、数据复盘，还是异常处理规则？
- 有没有依赖个人经验才能跑通的流程？

### If likely 销售/售前
Ask:
- 有没有还在跟进的客户机会、报价或投标事项？
- 哪些客户最需要优先说明当前状态？

### If likely 财务/法务/HR
Ask:
- 有没有证照、合同、用印、发票、报销、经办身份或纸质材料？
- 哪些内容只适合小范围查看？

### If likely 研发/测试/数据
Ask:
- 有没有脚本、环境配置、测试账号、报表口径或上线遗留问题？
- 哪些内容如果没人接手最容易出问题？

## Misclassification Warnings

- `Figma` alone does not mean design. Product also uses it.
- `合同` alone does not mean legal. Sales, procurement, and HR also handle contracts.
- `周报/会议纪要` alone does not mean project manager.
- `报表` alone does not mean finance. Data, operations, and sales also maintain reports.
- `客户群/客户沟通` alone does not mean sales. Customer success and project delivery often maintain them too.

## Output Expectation

When using this reference, produce:

1. a likely role guess
2. confidence level
3. top evidence signals
4. the next 2-4 questions worth asking
5. whether the role is confirmed or still draft-only

Good example:

- likely role: 产品经理
- confidence: medium
- evidence: `PRD`, `需求池`, `Figma原型`, `版本规划`
- next questions:
  - 你更想优先交接需求背景、方案，还是迭代状态？
  - 这里面是否也包含客户/项目资料？

## Sources

These sources informed the role and artifact patterns. Some role-to-file mappings are inferred from those role definitions.

- 人社部职业分类与数字职业说明  
  https://chinajob.mohrss.gov.cn/h5/c/2022-10-28/363398.shtml
- Boss 直聘职业百科与岗位说明（互联网、制造、零售、电商、教育、物流、工程等）  
  https://www.zhipin.com/
- Atlassian product and project management references  
  https://www.atlassian.com/agile/product-management/product-manager  
  https://www.atlassian.com/agile/project-management/product-vs-project-management
- Asana operations and project artifacts references  
  https://asana.com/teams/operations  
  https://asana.com/resources/how-project-status-reports
- HubSpot and Salesforce sales process references  
  https://blog.hubspot.com/sales/sales-pipeline  
  https://www.salesforce.com/resources/articles/sales-process/
- Thomson Reuters and Ironclad contract workflow references  
  https://legal.thomsonreuters.com/en/solutions/contract-lifecycle-management  
  https://ironcladapp.com/product/ironclad-for-legal/
- SHRM and ADP HR references  
  https://sps.shrm.org/sites/sps.shrm.org/files/HRBPPosting.pdf  
  https://www.adp.com/resources.aspx
- BrowserStack testing references  
  https://www.browserstack.com/guide/test-planning  
  https://www.browserstack.com/test-management/features/reports-analytics/what-is-test-execution-report
- Figma design system and handoff references  
  https://www.figma.com/design-systems/  
  https://www.figma.com/design-handoff/
