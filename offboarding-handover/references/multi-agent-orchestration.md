# 多代理编排

离职文件夹大、混杂、角色含糊，或同时含业务与合规风险时，使用本参考。

这是一种**代理执行策略**，不是面向用户的功能。

## 为什么首次扫描要用多个代理

小而干净的文件夹，单代理足够。

大而杂乱的文件夹，多代理能提升：

- 速度：并行探索
- 分类质量：关注点分离
- 问题质量：交叉核对角色、项目、风险信号

## 外部产品调研摘要

### OpenAI Codex

当前官方材料强调并行代理工作流：

- OpenAI 表示 Codex 可以并行处理多个任务，每个任务运行在独立环境中。
- Codex 应用被描述为同时管理多个代理的指挥中心，支持并行工作和内置 worktree。
- OpenAI 还建议用 AGENTS.md 提供持久指令，并推荐 Best-of-N 等并行探索模式来获得备选方案。

对本 skill 的实际含义：

- 使用**协调者 + 并行 worker** 模式
- worker 按职责隔离
- 最终结果汇入一份综合的交接视图

### Claude Code

当前官方材料区分了：

- **subagents**：单个会话内的专注 worker，各自拥有独立上下文窗口
- **agent teams**：由一个 lead 协调的多个 Claude Code 会话，适合 worker 需要并行协作的场景

Claude 官方指南说：

- 只关心结果时用 subagents
- worker 需要相互协调或互相质疑时用 agent teams
- 顺序性强或高度耦合的任务避免用 teams

对本 skill 的实际含义：

- 首次扫描应以 **subagent 优先** 建模
- 一个 lead 协调多个专职 subagent
- agent teams 对本工作流是可选项，不是必需项
- worker 应独立工作并返回结构化发现

## 推荐子代理拓扑

使用 **1 个协调者 + 至多 4 个子代理**。

除非用户明确要求深度调研，总数不超过 5 个代理。

### 团队负责人（Team Lead）

**角色：** 交接协调者

职责：

- 判断文件夹是否小到单代理即可处理
- 决定多代理模式是否值得 token 成本
- 分配有边界的扫描任务
- 收集发现
- 检测 worker 之间的冲突
- 决定首轮问用户的问题
- 综合最终分类并触发渲染

### Worker 1：角色探测器

职责：

- 从文件名、目录、产物和工具名推断可能的角色
- 输出置信度最高的 1-3 个可能角色
- 标出含糊边界

擅长：

- 产品 vs 项目 vs 运营
- 工程 vs 测试 vs 数据
- 财务 vs 人事 vs 法务

### Worker 2：项目与业务映射器

职责：

- 按项目、产品线、客户或业务流聚类文件
- 区分现行与历史材料
- 检测是否存在面向客户或项目交付的内容

擅长：

- “这批资料主要是内部还是客户/项目资料”
- `03-专项交接` 的初稿

### Worker 3：风险与资产检查器

职责：

- 识别账号、权限、设备、凭证、合同、发票、印章或敏感文件
- 标记很可能变成 `待补充` 的高风险遗漏项

擅长：

- `资产权限`
- `合规结算`
- 首轮风险问题

### Worker 4：进行中事项与缺失事实探测器

职责：

- 识别未完成工作、待定状态、跟进任务和未解决的交接事实
- 检测生成第一版精修 HTML 之前必须问什么

擅长：

- `00-进行中事项总表.md`
- `01-高遗漏检查清单.md`
- 更新模式的问题清单

## 何时使用并行子代理模式

满足以下任一条件时启用：

- 文件数量大
- 顶层文件夹众多或业务领域混杂
- 角色含糊
- 内部与客户/项目材料同时出现
- 资产/合规风险不可忽视
- 单代理首扫很可能产出大量 `待补充`

优先单代理模式，当：

- 文件夹已经干净
- 角色明显
- 文件很少
- 任务主要是补齐缺失事实，而非重新分类整个包

## 推荐首次扫描工作流

1. 协调者做非常轻量的扫描
2. 协调者决定单代理还是并行子代理模式
3. 若并行子代理模式：
   - 并行启动子代理
   - 给每个 worker 互不重叠的职责
4. worker 返回：
   - 发现
   - 置信度
   - 未解决的问题
5. 协调者综合出：
   - 可能的角色
   - 可能的行业适配层
   - 可能的项目/客户划分
   - 可能的风险画像
6. 协调者问最小的高价值问题集
7. 协调者生成配置 + 回答 + manifest + HTML

## 必需的 worker 输出格式

每个 worker 应返回：

- `scope`：检查了哪个切片
- `findings`：主要发现
- `confidence`：取值 high、medium 或 low
- `conflicts`：可能也符合其他角色或解读的地方
- `questions`：值得问用户的 2-5 个追问

## 反模式

不要这样使用并行子代理模式：

- 多个 worker 不分职责地读同一个完整文件夹
- 多个 worker 都试图产出最终分类
- 为只需刷新的小任务组建团队
- worker 并行编辑相同文件或相同输出切片

## 与当前 Codex 环境的对应关系

在 Codex 环境中，实用模式是：

- 一个主代理作为协调者
- 用 `spawn_agent` 启动有边界的并行 worker
- 每个 worker 重读轻写
- 只有主代理更新最终的 skill 输出

这与 Codex 和 Claude Code 的官方产品方向一致：

- 并行 worker 有用
- 隔离上下文减少污染
- 由一个 lead 综合并决策

## Claude Code 实用规则

对本 skill，Claude Code subagents 是默认的并行机制。

不要让工作流阻塞在实验性的 agent teams 上。

如果实验性 agent teams 可用，可以在超大规模或高协作度的扫描中作为可选增强，但普通执行不需要它。

## 来源

### OpenAI 官方来源

- Codex 发布公告（Introducing Codex）  
  https://openai.com/index/introducing-codex/
- Codex 应用发布公告（Introducing the Codex app）  
  https://openai.com/index/introducing-the-codex-app/
- 在 ChatGPT 订阅中使用 Codex 的帮助文档  
  https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- OpenAI 内部如何使用 Codex  
  https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf

### Anthropic / Claude Code 官方来源

- Claude Code 子代理文档  
  https://code.claude.com/docs/en/sub-agents
- Claude Code 设置文档  
  https://code.claude.com/docs/en/settings
- Claude Code 代理团队文档  
  https://code.claude.com/docs/en/agent-teams

## Context7 说明

调研时先查了 Context7 的 Claude Code 资料，可用但不完整，多为镜像或仓库文档，因此上面的权威行为细节以 Anthropic 官方文档补充为准。
