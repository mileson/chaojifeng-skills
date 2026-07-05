# 配置契约

把 `.offboarding-handover/offboarding.config.json` 作为内部配置路径，不要放进最终交接包。

首轮和刷新的可变回答另外使用 `.offboarding-handover/handover.answers.json`。

## 最小结构

```json
{
  "version": "1",
  "profile": {
    "employee_name": "",
    "department": "",
    "role": "",
    "industry": "internet",
    "last_working_day": "",
    "handover_owner": "",
    "handover_coordinator": "",
    "successor": ""
  },
  "features": {
    "projects": true,
    "clients": false,
    "assets": true,
    "accounts": true,
    "legal": false,
    "relevance_filtering": true,
    "version_dedupe": true,
    "fold_generated_assets": true,
    "zip_export": true
  },
  "gates": {
    "source_dir_confirmed": false,
    "role_confirmed": false,
    "successor_view_confirmed": false,
    "deep_review_complete": false
  },
  "relevance": {
    "mode": "balanced",
    "owner_aliases": [],
    "exclude_other_people": true,
    "exclude_public_reference": true,
    "dedupe_versions": true,
    "fold_generated_assets": true
  },
  "taxonomy": {
    "presentation_modules": [
      "交接信息",
      "交接总览",
      "专项交接",
      "未完事项与状态"
    ],
    "content_domains": [
      "工作事项",
      "关系人",
      "文档知识",
      "指标口径",
      "风险遗留",
      "资产权限",
      "合规结算",
      "交接状态"
    ]
  },
  "labels": {
    "scope": ["org", "role", "project", "legal", "design", "historical"],
    "doctype": ["docx", "pptx", "xlsx", "pdf", "kb", "minutes", "sop", "template", "contract", "asset", "link"],
    "status": ["draft", "review", "final", "historical"],
    "sensitivity": ["public", "internal", "restricted", "confidential"]
  },
  "output": {
    "root_dir": "离职交接包",
    "site_dir": "离职交接包/site",
    "site_title": "离职交接入口",
    "site_style": "tech-portal",
    "zip_name": "离职交接包.zip"
  }
}
```

## 预期

- `version` 保持字符串。
- 除非用户明确想要不同的体验，`presentation_modules` 保持四项。
- 除非用户提供公司专属标准，`content_domains` 保持八项。
- 值是推断出来的时候，把假设记录在相邻备注或生成的总览文档中。
- 最终交付之前，把 `employee_name`、`handover_owner`、`successor`、`handover_coordinator`、`last_working_day`、`role` 当作已确认事实或显式未知。
- 当事人别名保存在 `relevance.owner_aliases`；不要仅凭文件夹名或零散的姓名命中推断身份。

## Manifest 结构

脚手架脚本生成 `.offboarding-handover/handover.manifest.json`。

推荐的顶层键：

- `generated_at`
- `source_root`
- `output_root`
- `site_entry`
- `profile`
- `presentation_modules`
- `modules`
- `stats`
- `files`
- `filename_mapping`
- `review_items`
- `excluded_items`
- `other_person_items`
- `version_groups`
- `retention_stats`
- `excluded_reason_counts`
- `high_risk_items`
- `delivery`
- `assumptions`
- `notes`

## 文件记录结构

manifest 中每条文件记录应包含：

- `source`
- `original_name`
- `original_path`
- `relative_path`
- `size`
- `modified_at`
- `staged_name`（文件被复制进输出树时）
- `staged_path`（文件被复制进输出树时）
- `rename_reason`（落盘名与原名不同时）
- `scope`
- `doctype`
- `status`
- `sensitivity`
- `domain`
- `reasons`
- `retain_decision`
- `retain_reasons`
- `owner_evidence`（因匹配已确认的交接人、别名、角色、项目或接手人需求而保留时）
- `other_person_signal`（文件名或元数据提到他人时）
- `review_reason`（纳入前必须核查时）
- `exclude_reason`（被排除出核心输出时）
- `version_group_key`（属于某版本组时）
- `superseded_by`（作为旧版本被排除时）

## 落盘文件名映射

文件被复制进交接包时，创建一份映射，让接手人既能理解干净的交付名，也能追溯来源。

推荐落盘文件名模式：

```text
{序号}-{项目或客户简称}-{主题}-{材料类型}-{状态}-{日期}-{版本}.{扩展名}
```

规则：

- 只重命名落盘副本；除非用户明确要求就地重组，绝不重命名原始源文件。
- 严格保留原始扩展名。
- 使用简短、稳定的中文或英文词汇，不打开原文件夹也能看懂。
- 只有保留的文件确实代表选定版本时，落盘名才使用 final/发布/定稿/最新等措辞。
- 空字段直接省略，不要加占位文本。
- 避免 emoji、斜杠、冒号、重复空白，以及跨操作系统或 ZIP 工具不安全的标点。
- 两个落盘名冲突时，追加简短数字后缀并记录原因。
- 无法自信地生成可读落盘名时，把文件留在 `review` 并请求确认。

## 安全默认值

- `industry` 默认 `internet`。
- `projects/assets/accounts` 默认 `true`。
- 除非文件夹强烈提示，`clients/legal` 默认 `false`。
- 精修输出门禁默认 `false`；猜测的角色在确认前只能是草稿。
- 默认分级输出，而不是就地移动文件。
- 默认只复制 `include` 文件。`review` 和 `exclude` 文件留在源文件夹，并出现在过滤报告中。
- 他人个人材料默认 `exclude`；提到他人的含糊共享材料默认 `review`。
- 重复版本组默认保留一个代表：final/发布/定稿变体优先，其次最新显式日期，最后最新文件修改时间。
- 复制的文件名默认使用标准化落盘名，并保留可逆的原名映射。
- 草稿输出默认跳过 ZIP 导出，除非代理在告知用户后显式使用草稿 ZIP 参数。
- 配置和 manifest 保存在 `.offboarding-handover/`，不放进最终交付文件夹。
- HTML 站点使用 `site-design-system.md` 中固定的 `tech-portal` 风格渲染。

## 内部脚本模式

代理默认使用的内部可执行入口：

```bash
python3 scripts/bootstrap_handover.py /target/path --interactive
```

代理的内部示例：

```bash
python3 scripts/bootstrap_handover.py /target/path --no-scan
python3 scripts/bootstrap_handover.py /target/path --stage-mode none
python3 scripts/bootstrap_handover.py /target/path --zip-output
python3 scripts/bootstrap_handover.py /target/path --employee-name "张三" --department "产品部" --role "产品经理" --profile-confirmed --successor-view-confirmed --deep-review-complete
python3 scripts/bootstrap_handover.py /target/path --refresh --no-scan --interactive
```
