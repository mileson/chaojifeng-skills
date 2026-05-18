# Answers Contract

Use `.offboarding-handover/handover.answers.json` as the mutable answer state for first-run questions and later refresh updates.

Do not expose this file to the final handover receiver unless the user explicitly wants it.

## Minimal Shape

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

## Purpose

- `profile`: values that should appear directly in overview docs and HTML
- `routing`: first-run classification answers that help choose role or industry overlays
- `checks`: values that replace `待补充` items in the missed-items checklist
- `updated_at`: last refresh time

## Update Rule

- First run: create this file after asking the minimum high-value questions
- Refresh run: read the file, ask only for blanks or explicitly requested fields, then rewrite it
- HTML and markdown pages should be rendered from this file plus `offboarding.config.json` and `handover.manifest.json`
