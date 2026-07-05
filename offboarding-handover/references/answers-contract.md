# 回答契约

把 `.offboarding-handover/handover.answers.json` 作为首轮问题及后续刷新更新的可变回答状态。

除非用户明确需要，不要把这个文件暴露给最终的交接接收方。

## 最小结构

```json
{
  "profile": {
    "last_working_day": "",
    "handover_owner": "",
    "successor": ""
  },
  "routing": {
    "work_type": "",
    "has_client_projects": "",
    "has_inflight": "",
    "has_assets_or_sensitive": ""
  },
  "checks": {
    "work_wechat": "",
    "paper_notes": "",
    "otp_binding": "",
    "oral_rules": "",
    "reimbursement": "",
    "group_owner": "",
    "customer_transfer": ""
  },
  "updated_at": ""
}
```

## 用途

- `profile`：应直接出现在总览文档和 HTML 中的值
- `routing`：帮助选择角色或行业适配层的首轮分类回答
- `checks`：用于替换遗漏事项清单中 `待补充` 项的值
- `updated_at`：最近一次刷新时间

## 更新规则

- 首次运行：问完最少量的高价值问题后创建此文件
- 刷新运行：读取文件，只针对空白项或用户明确要求的字段提问，然后重写
- HTML 和 markdown 页面应从此文件加上 `offboarding.config.json` 和 `handover.manifest.json` 渲染
