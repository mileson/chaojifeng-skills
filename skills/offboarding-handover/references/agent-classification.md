# Agent-Led Classification

Use this approach when the target folder is messy, role-specific, or contains ambiguous materials that should not be classified by hard-coded script rules alone.

## Principle

Prefer agent judgment over script expansion when classification depends on:

- role semantics
- team context
- business vocabulary
- mixed folders with overlapping document types
- deciding whether something is current, archival, or merely reference material

The script may provide a baseline classification, but the agent should correct it after inspection.

Use this tool strategy:

1. `grep` + `find` as the compatibility baseline
2. `rg` as the recommended acceleration layer when available
3. platform-native alternatives such as PowerShell `Get-ChildItem` + `Select-String` when shell tooling differs

## Recommended Inspection Flow

1. Start with directory and filename discovery.
2. Use `find` to list candidate files. If `rg` exists, `rg --files` is a faster equivalent.
3. Use `grep -RInE` on filenames or short text patterns to cluster likely materials. If `rg` exists, prefer `rg` for speed. If the environment is PowerShell-first, use `Select-String`.
4. Read only small targeted slices of representative files when needed.
5. Decide whether the file should be `include`, `review`, or `exclude`.
6. Decide the business object, then write the chosen mapping into the output structure or manifest.
7. For high-value materials, record why the successor needs it, not only where the file was moved.

## Useful Shell Patterns

List files:

```bash
find /target/path -type f
```

Find likely product files:

```bash
grep -RInE "PRD|需求池|用户调研|竞品|roadmap|原型" /target/path
```

Find likely engineering files:

```bash
grep -RInE "repo|仓库|部署|上线|runbook|密钥|token|数据库|域名" /target/path
```

Find likely sales or client files:

```bash
grep -RInE "客户|商机|合同|报价|回款|跟进|CRM" /target/path
```

Find likely operations files:

```bash
grep -RInE "活动|投放|渠道|素材|复盘|排期|内容日历" /target/path
```

## Optional Acceleration

If `rg` exists, use it as a faster replacement for some searches, but do not make the skill depend on it.

List files:

```bash
rg --files /target/path
```

## Environment Note

In the current workspace I verified `grep`, `find`, and `rg` all exist. Treat that as local context only. The skill should remain portable by keeping `grep` + `find` as the baseline and `rg` as the preferred accelerator when present.

## Decision Heuristics

- If a file mainly helps the successor continue the current role, prefer `文档知识` or a business domain under `专项交接`.
- If a file mainly records access, devices, accounts, systems, or secrets, prefer `资产权限`.
- If a file mainly records contracts, salary, reimbursement, social benefits, proofs, or restrictions, prefer `合规结算`.
- If a file is old and no longer part of the active handover path, prefer `交接状态` and place it under historical references.
- `归档` or `archive` in the path should not override stronger business signals such as project, requirement, report, contract, or customer.
- If a folder mixes active and historical materials, split them rather than forcing the whole folder into one bucket.
- If a file is clearly someone else's personal material, company-wide public reference, an older duplicate version, or generated export noise, do not stage it by default. Put the reason in the filtering report.
- If a file has no employee name but clearly belongs to the role, project, customer, risk, account, or ongoing work, keep it as a handover candidate.

## Output Expectation

After agent-led review, the final manifest or staged output should reflect the resolved classification, not merely the script's first guess.

For each important cluster, the agent should be able to say: what the successor is taking over, current status, next action, risk, and supporting files.
