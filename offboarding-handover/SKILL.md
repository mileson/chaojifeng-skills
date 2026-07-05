---
name: offboarding-handover
description: 帮助离职员工把自己杂乱的工作资料整理成结构化的离职交接包，包含可配置的分类规则、适配行业的文档分类体系、HTML 可视化交接入口以及可打包交付的 ZIP 输出。适用于需要协助离职员工梳理零散工作资料、搭建交接目录、生成可视化入口页面、整理符合岗位特点的交接内容时。
---

# Offboarding Handover（离职交接）

把杂乱的工作文件夹整理成一站式离职交接包。先从可配置的标准出发，按用户的岗位或行业做适配，再生成结构化的交接目录、可视化 HTML 入口和可交付的打包文件。

## 不可妥协规则

以下规则对本 skill 是强制性的，不得弱化为可选建议。

1. **清单盘点先行。**
   - 材料源文件夹未明确前，不得开始盘点。
   - 完整的清单基线建立之前，不得向用户提问。
   - 清单不存在之前，不得开始深度分类。

2. **硬触发条件必须遵守。**
   满足以下任一条件时，必须进入并行子代理模式：
   - `total_files > 3000`
   - 有效的顶层分支数 > 8
   - 内部资料 + 客户/项目资料 + 风险/合规信号同时出现
   - 角色置信度不高

3. **不得用个人判断推翻已触发的并行扫描。**
   - 一旦命中硬触发规则，不得以“文件夹足够简单”为由跳过。
   - 角色置信度高不能取消分支数触发条件。
   - 命名整洁不能取消分支数触发条件。

4. **只有一个清单 worker 是不够的。**
   - 单个后台清单子代理不满足并行子代理模式的要求。
   - 触发并行子代理模式后，必须至少再启动 2 个专职子代理才能继续。

5. **触发并行子代理模式后，向用户提问必须等待。**
   - 专职子代理返回之前不得向用户提问。
   - 综合分析与覆盖率检查完成之前，不得生成 markdown、HTML 或 ZIP。

6. **在对话记录中显式说明扇出动作。**
   触发并行子代理模式时，需明确说明将要启动：
   - `offboarding-role-detector`
   - `offboarding-project-mapper`
   - `offboarding-risk-checker`
   - `offboarding-missing-facts-detector`

   推荐话术：
   - `清单基线已完成，已命中并行扫描条件。现在我将并行调用 offboarding-role-detector、offboarding-project-mapper、offboarding-risk-checker、offboarding-missing-facts-detector。`

7. **证据不足时回退，而不是即兴发挥。**
   - 清单不完整时，回到清单盘点阶段。
   - 并行子代理证据薄弱时，回到并行扇出阶段。
   - 综合分析不完整时，不得进入提问或渲染阶段。

8. **没有源文件夹，就不扫描。**
   - 用户未提供文件夹时，先询问交接材料在哪里。
   - 可以接受 `当前文件夹` 或一个路径。
   - 进入 Phase 1 之前，先校验路径存在、是目录且可读。
   - 不得从历史输出、最近记录或相邻文件夹推断源文件夹。

9. **精修输出需要确认。**
   - 角色、面向接手人的关键事实、深度材料评审确认之前，不得生成精修 HTML 站点或 ZIP。
   - 这些事实缺失时，只生成草稿版扫描/报告视图，并明确说明还需确认什么。
   - 猜测出的角色只是路由提示，不是已确认的角色。

10. **身份与交接事实是硬门禁。**
   - 清单、触发处理、综合分析、覆盖率检查完成后，先问完精简的身份与接手人问题，再落盘最终文件。
   - 确认交接人/当事人、已知别名、职责边界、接手人、交接协调人、最后工作日。
   - 任一事实未知时，除非用户明确标记该事实为“有意留空”，输出必须保持草稿状态。
   - 不得把文件夹名、员工名命中或推断出的角色当作已确认身份。

11. **核心输出中不得混入他人材料或已废弃版本。**
   - 明显属于他人的交接包、个人总结、绩效评估、岗位说明、试用期材料和无关演示文稿，不得复制进核心交接包。
   - 提到他人的团队或项目材料可能相关，但除非已确认的交接范围支持纳入，否则必须进入 `review`。
   - 明显重复的文档版本必须在落盘前折叠；优先保留 final/发布/定稿版本，其次是最新的显式日期，最后是最新修改时间。
   - 每个被折叠的旧版本必须在 manifest 或过滤报告中记录其保留代表。

12. **落盘文件名必须对接手人友好。**
   - 复制进交接包的文件必须使用脱离原始杂乱文件夹也能看懂的标准化名称。
   - 只重命名落盘副本；除非用户明确要求就地重组，否则绝不重命名或移动原始源文件。
   - 在 manifest 或过滤报告中保留原文件名、原路径、标准化落盘名以及版本/被取代映射。
   - 无法生成安全的标准化名称时，把文件留在 `review`，而不是带着易混淆的名称悄悄复制。

## 按需加载

- 决定如何分类文件与文件夹时，读 [references/default-taxonomy.md](references/default-taxonomy.md)。
- 创建或更新配置文件与 manifest 时，读 [references/config-contract.md](references/config-contract.md)。
- 存储首轮回答或后续刷新更新时，读 [references/answers-contract.md](references/answers-contract.md)。
- 文件夹杂乱或岗位特殊、需要检查真实产物来分类内容时，读 [references/agent-classification.md](references/agent-classification.md)。
- 用户未明确指定材料文件夹、扫描之前，读 [references/source-folder-gate.md](references/source-folder-gate.md)。
- 需要从文件信号推断可能角色、或决定首轮问哪些问题时，读 [references/role-detection-and-ask-user.md](references/role-detection-and-ask-user.md)。
- 准备首轮问题集时，读 [references/first-run-questions.md](references/first-run-questions.md)。
- 角色确认之后、选定输出目录结构之前，读 [references/role-output-templates.md](references/role-output-templates.md)。
- 把大型或混杂文件夹当作已深度整理之前，读 [references/deep-material-review.md](references/deep-material-review.md)。
- 文件夹大或含糊、想用子代理并行做首次扫描分析时，读 [references/multi-agent-orchestration.md](references/multi-agent-orchestration.md)。
- 需要可执行的协调者/worker 首次扫描手册时，读 [references/first-scan-team-playbook.md](references/first-scan-team-playbook.md)。
- 需要建立完整清单基线、决定是否分片扫描、验证覆盖率时，读 [references/full-inventory-and-sharding.md](references/full-inventory-and-sharding.md)。
- 需要严格按阶段推进的首轮执行模型时，读 [references/execution-state-machine.md](references/execution-state-machine.md)。
- 现有状态可能过期、不完整或不可信、需要安全回退到较早阶段时，读 [references/trust-recovery-and-rescan.md](references/trust-recovery-and-rescan.md)。
- 在 Claude Code 或 Codex 中运行、需要把托管的离职交接子代理同步到本地代理目录时，读 [references/claude-agent-sync.md](references/claude-agent-sync.md)。
- 用户想刷新既有交接包并替换待补充项时，读 [references/update-mode.md](references/update-mode.md)。
- 检查交接是否遗漏常见真实离职事项时，读 [references/high-risk-missed-items.md](references/high-risk-missed-items.md)。
- 源文件夹范围偏大、属于团队级/公司级/客户级，或可能包含他人文件、公开材料、重复版本、生成产物时，读 [references/relevance-filtering.md](references/relevance-filtering.md)。
- 撰写站点文案、生成的 markdown 或文件级摘要之前，读 [references/successor-view.md](references/successor-view.md)。
- 修改生成的 HTML 站点样式或交互模型之前，读 [references/site-design-system.md](references/site-design-system.md)。
- 把生成的 HTML 站点当作精修成品之前，读 [references/site-quality-checklist.md](references/site-quality-checklist.md)。
- 需要一次性完成脚手架、扫描、分类、渲染、导出时，运行 [scripts/bootstrap_handover.py](scripts/bootstrap_handover.py)。
- 需要创建或刷新本 skill 使用的托管 Claude 或 Codex 子代理时，运行 [scripts/sync_claude_agents.py](scripts/sync_claude_agents.py)。

## 工作流

按阶段门禁的工作流运行本 skill，不要当成自由探索。

### Phase 0 — 环境检测

- 判断是首次运行还是刷新
- 判断脚手架是否已存在
- 判断输出是否已存在
- 确认材料源文件夹；缺失时先问用户再扫描
- 除非用户明确要求，拒绝把 `离职交接包`、`site`、ZIP 文件或 `.offboarding-handover` 等生成输出目录当作源根目录

### Phase 1 — 清单基线

- 文件总数
- 目录总数
- 顶层分支
- 各分支文件数
- 扩展名分布

### Phase 2 — 触发检查

满足以下任一条件时，必须进入并行子代理模式：

- `total_files > 3000`
- 有效的顶层分支数 > 8
- 内部资料 + 客户/项目资料 + 风险/合规信号同时出现
- 角色置信度不高

### Phase 3 — 并行子代理扇出

如果 Phase 2 触发了并行子代理模式：

- 先按目录归属分片
- 并行启动专职子代理
- 不得把一个后台清单 worker 当作足够

### Phase 4 — 综合分析与覆盖率

- 合并子代理发现
- 对照清单基线验证覆盖率
- 准备最少量的高价值问题

### Phase 4.1 — 角色确认门禁

- 从证据推断可能的角色或角色族
- 应用角色模板之前，请用户确认或纠正角色、交接人/当事人、已知别名和职责边界
- 只问避免最终交接包出现 `待补充` 所需的最小接手人问题集
- 确认接手人、交接协调人、最后工作日，以及未知事实是否有意留空
- 角色未确认时，只以草稿扫描/报告形式继续

### Phase 4.5 — 相关性过滤

- 落盘之前先决定 `include`、`review` 或 `exclude`
- 把员工姓名当作强信号，而不是必要门槛
- 仅在有明确理由时排除，例如他人的交接文件夹、公开模板、生成产物、已被取代的版本
- 落盘前排除明显无关的他人材料；含糊的共享项目材料放入 `review`
- 含糊的团队或项目材料留在 `review`，不要悄悄复制
- 对明显的文档版本去重，保留最新或定稿代表
- 记录被版本折叠的旧路径及其保留代表

### Phase 4.6 — 落盘文件名标准化

- 为每个复制的 `include` 文件生成对接手人友好的落盘文件名
- 使用稳定的命名模式，例如 `{序号}-{项目或客户简称}-{主题}-{材料类型}-{状态}-{日期}-{版本}.{扩展名}`
- 文件类型保留为扩展名和标签，不作为顶层文件夹
- 把原名称、原路径、落盘名称、重命名理由写入 manifest 或过滤报告
- 除非用户明确要求就地重组，绝不重命名原始源文件

### Phase 4.8 — 深度材料评审

- 最终综合之前抽样审阅高价值文档
- 按项目、客户、工作流、进行状态、风险、接手人动作对材料分组
- 避免仅因文件位于 `归档` 下就把大量无关文件塞进 `未完事项与状态`
- 把旧版本和历史背景标记为参考资料，而不是进行中的交接工作

### Phase 5 — 询问用户

- 只在综合分析之后提问
- 补齐否则会变成 `待补充` 的关键事实
- 关键事实仍缺失时，输出保持草稿状态

### Phase 6 — 渲染

- 更新配置与回答
- 构建 manifest
- 渲染 markdown
- 渲染 HTML
- 清理空目录
- 仅当精修输出门禁满足、或用户明确要求草稿 ZIP 时才导出 ZIP

### Phase 7 — 刷新

- 检查未解决事项
- 只针对缺失事实提问
- 重新渲染 markdown 和 HTML

### 信任恢复

- 中间状态不完整、过期或支撑薄弱时，回退到最早的不可信阶段
- 不要自动信任 manifest、输出或部分扫描产物
- 命中硬触发规则但并行子代理证据薄弱时，回到 Phase 3，而不是继续推进

精修输出门禁：

- 材料文件夹已确认
- 角色已由用户确认
- 交接人/当事人、已知别名、职责边界、接手人、交接协调人、最后工作日均已确认或有意标记为未知
- 面向接手人的信息需求已确认
- 深度材料评审已完成
- 目录结构从已确认的角色模板中选定
- 每个落盘文件的保留决定已完成
- 他人材料已排除或列入待评审
- 明显的文档版本已折叠并记录
- 落盘文件名已标准化且原名映射已保留

## 分类规则

- 先决定保留级别：`include`、`review` 或 `exclude`。
- 先按 `scope` 分，再按 `doctype`，最后按 `status` 和 `sensitivity`。
- Word、PowerPoint、Excel、PDF 只作为标签。除非用户明确要求，不要把它们做成顶层文件夹。
- 优先使用 `组织知识`、`岗位材料`、`项目产物`、`法务/合规`、`设计/资产`、`历史参考` 作为分类锚点。
- 把 `必读现行材料` 和 `历史参考` 分开。
- 把链接和在线文档当作一等资产。即使源头留在线上，也保留本地索引。
- 不要把宽泛的团队或公司文件夹里的所有文件都复制走。只复制有交接价值的文件，不确定的列入待评审，被排除的说明原因。
- 员工姓名、别名和缩写是强纳入信号，但不是必要条件。没有员工姓名的文件，只要角色、项目、客户、风险或运营上下文支持其交接价值，也可以纳入。
- 明显与本人无关的他人个人材料、全公司公开模板、生成的原型导出物、已被取代的版本，默认不落盘进交接包。
- 他人的个人评估、个人演示、岗位说明、试用期材料和交接包是强排除信号，除非用户明确确认它们属于本次交接。
- 提到他人的共享项目文件不自动排除；除非已确认范围证明它们是交接关键项，否则留在 `review`。
- 落盘文件名应为接手人的阅读和排序做标准化，同时保持原名称和路径可追溯。
- 除非映射明显稳定且低风险，不要持续向脚本里扩充大型硬编码角色词典。
- 需要细粒度角色适配时，以 `grep`/`find` 检查真实文件夹为基线，`rg` 作为可选加速器，然后把解析出的映射写进配置或 manifest 输出。
- 把 `归档`、`历史`、`archive` 当作状态信号，而不是自动归属目录。位于 `归档` 下的文件仍可能是产品方案、项目产物、合同、报告或现行参考。

## 首次运行行为

在一个文件夹里首次运行时，如果用户没有要求破坏性重组，先创建脚手架再考虑移动文件。在用户确认映射可接受之前，优先使用复制或分级输出，而不是直接就地移动。

用户未提供材料文件夹时，先询问。用户可以回复 `当前文件夹` 或提供一个路径。文件夹校验通过之前不得开始盘点。

如果环境支持交互式提问，在清单、触发处理、综合分析、覆盖率完成后，询问精简的首轮画像。否则，从文件夹内容推断草稿级路由猜测，并把假设记录进配置。非交互式默认值不等于已确认的角色。

精简首轮画像必须确认：

- 交接人/当事人及已知别名
- 角色或职责边界
- 接手人
- 交接协调人
- 最后工作日
- 未知事实是否应有意留空

对大型或含糊的文件夹，不要从扫描直接跳到最终 HTML。先跑完整状态机：清单 → 触发检查 → 必要时并行子代理 → 综合分析 → 询问用户 → 渲染。

协调者应遵循 `references/first-scan-team-playbook.md`，而不是每次临时发明一套团队分工。
协调者还应遵循 `references/full-inventory-and-sharding.md`，确保并行工作开始前扫描覆盖率可度量。

命中硬触发规则时，代理不得止步于清单盘点，也不得直接进入提问或产出生成。
某个阶段未完成时，代理不得悄悄进入后续阶段。
当前状态不够可信时，代理必须回退到相应的较早阶段，而不是绕过缺口即兴推进。

## 输出预期

除非用户收窄范围，产出以下工件：

- 记录分类体系和项目元数据的配置文件
- 规范化的交接目录
- 从 manifest 渲染的 HTML 入口页面
- 关键文件与落盘目标的 manifest 或索引
- 展示纳入、待评审、排除、版本折叠情况的过滤报告
- 展示原路径/原名与标准化落盘名的文件名映射
- 可选的 ZIP 打包

## HTML 站点标准

生成的 `site/index.html` 是整个交接包的门面。

- 使用 `references/site-design-system.md` 中固定的科技公司内部门户风格。
- 页面背景使用 `#FBFCFE`。
- 界面保持干净、信息密集、可搜索、可操作。
- 从站点直连每一份生成的核心交接文档，不要让接手人先去翻文件夹树。
- 在完整文件表之前，优先呈现高风险事项、未完成工作和缺失事实。
- 不要模仿 PPT 或杂志排版、横向翻页导航、WebGL 大背景、装饰性渐变或大型营销式 hero 区。
- 除非用户明确要求技术输出，不要在用户可见文案中暴露脚本、manifest、内部扫描步骤等实现细节。

## 代理执行

脚本是代理的内部执行入口。除非用户明确要求命令行用法，不要指导最终用户手动运行它。

```bash
python3 scripts/bootstrap_handover.py /path/to/folder --interactive
```

代理可用的内部参数：

- `--no-scan`：只生成脚手架
- `--stage-mode copy|none`：把文件复制进输出树，或只做分类
- `--zip-output`：强制导出 ZIP
- `--refresh`：基于已保存回答和新的提问刷新既有交接包
- `--profile-confirmed`：标记角色/画像方向已由用户确认
- `--successor-view-confirmed`：标记面向接手人的事实与阅读需求已确认
- `--deep-review-complete`：标记代理主导的深度材料评审已完成
- `--allow-draft-zip`：即使交接包仍是草稿也导出 ZIP
- `--employee-name`、`--department`、`--role`、`--industry`、`--last-working-day`、`--handover-owner`、`--successor`：在无 TTY 提示的情况下写入首轮回答

## 用户交互规则

- 最终用户应与 **skill** 交互，而不是与脚本交互。
- 用户尚未确认材料文件夹时，扫描之前先询问。
- 首次运行时，代理应先检查文件夹、推断可能的角色与风险，再问一组精简问题，然后才生成第一版精修 HTML。
- 用户尚未确认角色或接手人事实时，只生成草稿。
- 后续运行时，代理应检测 `待补充` 等未解决事项，只针对缺失事实提问，更新内部状态，然后刷新 markdown 和 HTML。
- 把命令示例当作代理实现细节，而不是面向用户的操作指引。

## 强制并行子代理规则

- 仅有一个后台清单 worker **不**算有效的并行首次扫描。
- 触发并行子代理模式后，代理必须再启动职责互不重叠的并行子代理才能继续。
- 触发并行子代理模式后，代理必须先完成综合分析和覆盖率检查，再向用户提问。
- 触发并行子代理模式后，代理应在对话记录中显式说明扇出步骤，点名即将启动的子代理。不要用 `继续扫描` 之类的模糊措辞掩盖这一转变。
- 在 Claude Code 环境中，触发并行子代理模式时优先使用这些专用子代理：
  - `offboarding-inventory-baseliner`
  - `offboarding-role-detector`
  - `offboarding-project-mapper`
  - `offboarding-risk-checker`
  - `offboarding-missing-facts-detector`
- 子代理模型路由：
  - 当前运行时是 GPT/Codex 时，离职交接专职子代理优先使用 `gpt-5.4`。
  - 当前运行时是 Claude 时，离职交接专职子代理优先使用 `haiku`。
  - 把这当作运行时选择规则。不要仅为满足该规则去编辑生成的或托管的代理配置文件。
- 这些 Claude 子代理应通过 frontmatter 的 `skills` 字段预加载 `offboarding-handover` skill，以便启动时继承同一套手册和参考资料。
- 在 Claude Code 环境中，依赖专用离职交接子代理之前，如果托管代理模板缺失或过期，先把它们从本 skill 同步到 `~/.claude/agents/`。
- 在 Codex 环境中，依赖专用离职交接子代理之前，如果托管代理模板缺失或过期，先把它们从本 skill 同步到 `~/.codex/agents/`。
- 在既不是 Claude Code 也不是 Codex 的环境中，不硬性要求本地代理文件。回退到 skill 指令、协调者逻辑和基于提示词的 worker 分解，让流程照常运转。

## 推荐话术模式

命中硬触发规则时，优先使用类似措辞：

- `清单基线已完成，已命中并行扫描条件。现在我将并行调用 offboarding-role-detector、offboarding-project-mapper、offboarding-risk-checker、offboarding-missing-facts-detector。`

之后启动子代理，而不是继续单线程推进。

## 职责分工

- 让脚本处理确定性的基础设施：
  - 脚手架生成
  - 配置写入
  - 回答状态写入
  - manifest 写入
  - 标准 markdown 页面渲染
  - HTML 渲染
  - 空目录清理
  - ZIP 导出
- 让代理处理需要细致判断的部分：
  - 岗位特定的分类
  - 判断文件是现行材料还是历史参考
  - 判断文档属于业务交接、法务/合规还是通用知识
  - 检查文件名和文件内容后，纠正含糊的自动分类结果
  - 判断并行子代理编排是否值得开销
  - 深度分析之前先建立清单基线
  - 决定是否按目录分片
  - 分配职责互不重叠的并行 worker
  - 综合之前检查扫描覆盖率
  - 把并行 worker 的发现综合成一份问题集和一份最终交接视图
  - 精修输出之前确认源文件夹和角色
  - 决定面向接手人的目录模板
  - 充分审阅高价值材料，讲清状态、下一步动作、风险和支撑文件

## 验证清单

- 配置符合契约。
- 生成目录包含预期的顶层模块。
- HTML 入口引用了生成的模块和关键文档。
- HTML 入口遵循 `references/site-design-system.md`。
- HTML 入口通过 `references/site-quality-checklist.md` 的 P0 项。
- HTML 入口和过滤报告展示了纳入、待评审、排除的文件数量。
- 精修输出门禁未满足时，草稿输出有清晰标注。
- 文件条目优先提供 `查看预览` 加 `打开原文件`；除非真的会下载，不要把本地 Office 链接标成下载。
- 不打开原始杂乱文件夹也能读懂 manifest。
- manifest 记录了原名称、原路径、标准化落盘名、保留决定、版本/被取代映射。
- 核心落盘文件不包含明显无关的他人个人材料。
- 明显重复的文档版本在最终输出前已折叠。
- 落盘文件名可读、可排序，对脱离原始目录树的接手人有用。
- 账号、设备、法务材料等高风险事项被显式呈现。
- 已对照遗漏清单检查账号、印章、证书、工作手机、纸质记录和单位经办人身份。
