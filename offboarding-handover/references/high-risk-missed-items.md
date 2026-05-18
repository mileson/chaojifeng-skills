# High-Risk Missed Items

Use this checklist after the main handover structure is done. It focuses on things ordinary white-collar employees often forget, but which later block operations, create disputes, or leave security gaps.

## How to Use

1. Review this table before finalizing the manifest and site.
2. Mark each item as one of:
   - `已确认无需交接`
   - `已交接`
   - `待补充`
3. If an item exists but is not yet represented in the handover package, add it to:
   - `资产权限`
   - `合规结算`
   - `交接状态`
   depending on its nature.

## Agent Checklist Table

| 序号 | 检查项 | 典型内容 | 建议放置位置 | 状态 | 当前持有人/责任人 | 接手人 | 补充说明 |
|---|---|---|---|---|---|---|---|
| 1 | 单位经办人/专办员身份 | 公积金、税务、社保、银行、报销系统经办身份 | 合规结算 | 待补充 |  |  |  |
| 2 | 工作微信/企微/客户群/运营账号 | 工作微信号、企微外部联系人、客户群、公众号、小程序、视频号、社媒后台 | 资产权限 / 合规结算 | 待补充 |  |  |  |
| 3 | 税务 UKey / 网银 U盾 / 支付凭证 | 税控 UKey、U盾、付款 token、开票权限 | 合规结算 | 待补充 |  |  |  |
| 4 | 印章 / 营业执照 / 证照袋 | 公章、财务章、法人章、电子印章、营业执照原件/复印件 | 合规结算 / 交接状态 | 待补充 |  |  |  |
| 5 | 涉密载体 / 纸质材料 | U 盘、硬盘、纸质合同、报价单、会议材料、手写记录 | 交接状态 | 待补充 |  |  |  |
| 6 | 公积金封存/转移后续责任 | 谁封存、谁转移、何时办、需要什么材料 | 合规结算 | 待补充 |  |  |  |
| 7 | 手机号绑定与验证码链路 | 个人手机号、邮箱、OTP、短信验证码、验证器 App 绑定 | 资产权限 | 待补充 |  |  |  |
| 8 | 个人工作台资产 | 本地脚本、书签、SQL、Postman、宏、模板、笔记库、个人云盘工作资料 | 资产权限 / 文档知识 | 待补充 |  |  |  |
| 9 | 口头约定 / 非书面规则 | 聊天线程、会议口头结论、默认规则、客户暗约定 | 文档知识 / 风险遗留 | 待补充 |  |  |  |
| 10 | 责任边界 / 未完事项 | 已完成、未完成、已提醒风险、后续责任人 | 风险遗留 | 待补充 |  |  |  |
| 11 | 备用金 / 借款 / 未核销报销 | 差旅借款、备用金、垫付款、未核销报销单 | 合规结算 | 待补充 |  |  |  |
| 12 | 发票开票权限 / 发票专用章 | 开票后台、税控设备、发票章、发票领用责任 | 合规结算 | 待补充 |  |  |  |
| 13 | 纸质档案移交目录 | 档案清点表、卷宗目录、交接目录、涉密目录 | 交接状态 | 待补充 |  |  |  |
| 14 | 涉密文件分类移交或销毁 | 密级文档、附件、纸质副本、载体销毁记录 | 交接状态 / 合规结算 | 待补充 |  |  |  |
| 15 | 群主责任 / 内容监管责任 | 微信群/社群群主、运营人、审核责任人 | 资产权限 / 合规结算 | 待补充 |  |  |  |
| 16 | 客户资源与聊天沉淀可用性 | 历史聊天、客户标签、支付记录、能否继续登录和查看 | 关系人 / 资产权限 | 待补充 |  |  |  |
| 17 | 证照原件/复印件的实际保管 | 营业执照、资质证照、复印件、扫描件保管位置 | 交接状态 / 合规结算 | 待补充 |  |  |  |
| 18 | 应收款 / 催收中的尾项 | 谁欠款、催收到哪一步、谁继续跟进 | 合规结算 / 关系人 | 待补充 |  |  |  |

## Detailed Guidance

### 1. Unit operator identities

Check whether the departing employee is registered as an operator, handler, or administrator for:

- housing fund accounts
- tax systems
- social insurance systems
- bank or treasury platforms
- invoice or reimbursement systems

Why it is missed:

- this is not a normal login account, but a unit-facing service identity

What to capture:

- system name
- current operator identity
- replacement operator
- change procedure or pending step

References:

- https://zjj.sz.gov.cn/hdjl/ywzs/gjj/jcl/content/post_12518057.html
- https://gjj.gz.gov.cn/bsfw/cjwt/jc/content/post_10295421.html

### 2. Work WeChat / enterprise messaging / customer groups / operated social accounts

Check whether the employee controls:

- work WeChat accounts
- Enterprise WeChat external contacts
- customer group chats
- official account backends
- mini-program backends
- video or social media brand accounts

Why it is missed:

- these are often mixed with personal phones or personal chat habits

What to capture:

- account or platform
- bound phone number or email
- admin or owner role
- customer relationship impact
- transfer target

References:

- https://www.sdcourt.gov.cn/wfwcqfy/443527/443501/12509536/index.html
- https://news.cctv.com/2023/12/28/ARTIVYIPvVn22XOVavjxIrLS231228.shtml

### 3. Tax UKey / bank UShield / bank seal specimen / payment credentials

Check whether the employee holds or controls:

- tax UKey
- banking UShield
- payment approval token
- invoice issuance permissions
- bank reserved seal specimen process

Why it is missed:

- these are often treated as small physical tools, but they directly affect payments and invoicing

What to capture:

- credential type
- serial or identifier
- physical holder
- return status
- successor or custodian

References:

- https://www.gz.gov.cn/xw/zwlb/content/mpost_5734246.html
- https://pccz.court.gov.cn/filedownloads/2024/2024-08-28/%E7%A1%AE%E8%AE%A4%E6%B8%85%E7%AE%97%E6%96%B9%E6%A1%88%E6%B0%91%E4%BA%8B%E8%A3%81%E5%AE%9A%E4%B9%A61724830715605.pdf?fn=%E7%A1%AE%E8%AE%A4%E6%B8%85%E7%AE%97%E6%96%B9%E6%A1%88%E6%B0%91%E4%BA%8B%E8%A3%81%E5%AE%9A%E4%B9%A6.pdf

### 4. Electronic seals / physical seals / business license originals

Check whether the employee can access or physically holds:

- company seal
- finance seal
- legal representative seal
- electronic seal account
- business license original or copies used operationally

Why it is missed:

- many small or fast-moving teams keep these with whoever actually handles work

What to capture:

- item name
- storage location
- holder
- return or transfer confirmation

References:

- https://www.gov.cn/xinwen/2020-08/07/content_5533146.htm
- https://pccz.court.gov.cn/filedownloads/2024/2024-08-28/%E7%A1%AE%E8%AE%A4%E6%B8%85%E7%AE%97%E6%96%B9%E6%A1%88%E6%B0%91%E4%BA%8B%E8%A3%81%E5%AE%9A%E4%B9%A61724830715605.pdf?fn=%E7%A1%AE%E8%AE%A4%E6%B8%85%E7%AE%97%E6%96%B9%E6%A1%88%E6%B0%91%E4%BA%8B%E8%A3%81%E5%AE%9A%E4%B9%A6.pdf

### 5. Confidential media and paper materials

Check whether the employee has:

- USB drives
- external hard drives
- printed contracts
- printed quotations
- meeting packets
- handwritten notes with customer, pricing, or credential details

Why it is missed:

- teams focus on files and forget physical carriers

What to capture:

- media type
- content type
- storage place
- handover or destruction status

References:

- https://gfdy.tj.gov.cn/ztzl/rfzs/202402/t20240222_6541644.html

### 6. Housing fund sealing or transfer follow-up

Check whether the package says not only that housing fund stops, but also:

- who handles sealing
- who handles transfer
- what the next responsible person is
- what supporting documents are needed

Why it is missed:

- many handovers stop at “will be stopped” and never define who actually finishes the procedure

What to capture:

- current state
- next step
- responsible party
- evidence or receipt

References:

- https://www.yw.gov.cn/art/2024/5/16/art_1229142865_1804614.html

### 7. Bound phone numbers and verification chains

Check whether systems are actually transferable, or whether they depend on:

- one personal mobile number
- one personal mailbox
- one person's OTP or SMS reception
- one person's authenticator app

Typical systems:

- social accounts
- mini-programs
- advertising platforms
- payment systems
- developer platforms
- domain or cloud accounts

What to capture:

- bound identifier
- system name
- replacement plan
- transfer blocked or not

Reference:

- https://www.sichuanpeace.gov.cn/azsf/20250829/2992286.html

### 8. Personal workstation assets

Check whether the employee relies on hidden productivity materials that never entered official docs:

- browser bookmarks
- local scripts
- SQL snippets
- Postman collections
- spreadsheet macros
- local templates
- note-taking vaults
- personal cloud folders used for company work

Why it is missed:

- it lives in the employee's workflow, not in the formal project system

What to capture:

- asset type
- local path or tool name
- whether it is still needed
- where it should be migrated

### 9. Oral agreements and unwritten operating rules

Check whether important information exists only in:

- chat threads
- meeting memory
- unwritten customer agreements
- team “everyone knows this” rules

What to capture:

- statement
- affected project or customer
- source of agreement
- whether written evidence exists

### 10. Responsibility boundary and unresolved items

Check whether the package clearly says:

- what is already completed
- what was only warned but not finished
- what remains open
- who owns the next step

Why it matters:

- without this, handover turns into blame transfer

What to capture:

- item
- current completion state
- known risk
- next owner
- deadline if any

### 11. Cash advances / loans / unreconciled reimbursements

Check whether the departing employee still has:

- travel cash advances
- petty cash
- team advances
- unreconciled reimbursement claims
- payments made personally and not yet settled

Why it is missed:

- teams think “finance will see it”, but many items stay under an employee's name

What to capture:

- item type
- amount
- current state
- evidence or claim number
- settlement owner

Reference:

- https://sthj.ln.gov.cn/sthj/zfxxgk/fdzdgknr/czzj/hbzxzjxm/F5022FECE61B45568E783E1306022811/index.shtml

### 12. Invoice permissions / invoice seal

Check whether the employee still controls:

- invoice issuance backend
- tax device
- invoice seal
- invoice application or receiving responsibility

Why it is missed:

- teams often separate “finance account” from “actual operator”, and only the operator knows the process

What to capture:

- system or item
- current operator
- physical holder
- transfer confirmation

References:

- https://scjg.huangshi.gov.cn/ztzl/yhyshjzfjs/202208/t20220823_933151.html
- https://www.luan.gov.cn/hdjl/dwzsk/10477095.html

### 13. Paper archive transfer index

Check whether there is an actual transfer index for:

- paper files
- project binders
- archived contracts
- customer folders
- sealed archive packages

Why it is missed:

- teams hand over the materials but forget the index, so nobody can later prove completeness

What to capture:

- archive name
- quantity
- index path or paper list
- receiver

Reference:

- https://www.yw.gov.cn/art/2024/3/20/art_1229135557_59474584.html

### 14. Classified file transfer or destruction

Check whether sensitive or classified materials require:

- separate transfer
- destruction registration
- media destruction evidence
- classified cataloging

Why it is missed:

- people assume “sent to successor” is enough, but regulated materials often need a formal path

What to capture:

- file or media type
- classification level
- transfer or destruction method
- evidence

References:

- https://www.yw.gov.cn/art/2024/3/20/art_1229135557_59474584.html
- https://gfdy.tj.gov.cn/ztzl/rfzs/202402/t20240222_6541644.html

### 15. Group ownership and moderation responsibility

Check whether the employee is still the accountable person for:

- group ownership
- community moderation
- content review
- complaint handling
- broadcast or posting permissions

Why it is missed:

- teams transfer the account but forget the operational responsibility

What to capture:

- group or channel name
- current owner or admin
- replacement owner
- moderation duty

Reference:

- https://www.tlf.gov.cn/tlfs/c106653/201709/84c17e05ca064567af4bdc88678ff6e8.shtml

### 16. Customer resource and chat-history usability

Check whether transferred customer assets remain actually usable:

- can the successor still log in
- can they read chat history
- can they keep customer labels or segmentation
- can they continue payment or follow-up processes

Why it is missed:

- teams focus on nominal ownership, not operational usability

What to capture:

- platform
- retained data or not
- transfer success or blocker
- next action

Reference:

- https://www.ahjd.gov.cn/Jczwgk/show/3639895.html

### 17. Certificate originals or copies in real custody

Check whether the employee physically keeps:

- business license copies
- qualification certificates
- registration certificates
- copied packets used for external processes

Why it is missed:

- teams remember the seal, but forget the packet of certificates that travels with business handling

What to capture:

- certificate name
- original or copy
- storage place
- receiver

References:

- https://www.luan.gov.cn/hdjl/dwzsk/10477095.html
- https://www.gov.cn/xinwen/2020-08/07/content_5533146.htm

### 18. Receivables and collection tail items

Check whether the departing employee still owns:

- receivables follow-up
- collection tasks
- overdue payment communication
- disputed billing follow-up

Why it is missed:

- customer ownership may be handed over, but the money trail remains unclear

What to capture:

- customer
- amount
- current collection stage
- next owner
- next contact plan

Reference:

- https://www.fjax.gov.cn/zwgk/xwzx/tzgg/202510/t20251024_3224413.htm

## Minimum Recommended Output

At minimum, add one summary page or table called:

- `高遗漏检查清单`

It should contain these columns:

- `检查项`
- `状态`
- `当前持有人/责任人`
- `接手人`
- `补充说明`
