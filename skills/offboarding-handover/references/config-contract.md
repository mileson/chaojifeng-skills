# Config Contract

Use `.offboarding-handover/offboarding.config.json` as the internal config path. Keep it out of the final handover package.

For mutable first-run and refresh answers, also use `.offboarding-handover/handover.answers.json`.

## Minimal Shape

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

## Expectations

- Keep `version` as a string.
- Keep `presentation_modules` at four items unless the user explicitly wants a different UX.
- Keep `content_domains` at eight items unless the user provides a company-specific standard.
- Record assumptions in adjacent notes or in the generated overview document when values are inferred.
- Treat `employee_name`, `handover_owner`, `successor`, `handover_coordinator`, `last_working_day`, and `role` as confirmed facts or explicit unknowns before final delivery.
- Keep owner aliases in `relevance.owner_aliases`; do not infer identity only from folder names or scattered name hits.

## Manifest Shape

The scaffold script generates `.offboarding-handover/handover.manifest.json`.

Recommended top-level keys:

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

## File Record Shape

Each manifest file record should include:

- `source`
- `original_name`
- `original_path`
- `relative_path`
- `size`
- `modified_at`
- `staged_name` when files are copied into the output tree
- `staged_path` when files are copied into the output tree
- `rename_reason` when the staged filename differs from the original filename
- `scope`
- `doctype`
- `status`
- `sensitivity`
- `domain`
- `reasons`
- `retain_decision`
- `retain_reasons`
- `owner_evidence` when the file is retained because it matches the confirmed handover owner, alias, role, project, or successor need
- `other_person_signal` when the file name or metadata mentions another person
- `review_reason` when the file must be checked before inclusion
- `exclude_reason` when the file is excluded from core output
- `version_group_key` when the file belongs to a version group
- `superseded_by` when the file was excluded as an older version

## Staged Filename Mapping

When files are copied into the handover package, create a mapping that allows the successor to understand both the clean delivery name and the source provenance.

Recommended staged filename pattern:

```text
{序号}-{项目或客户简称}-{主题}-{材料类型}-{状态}-{日期}-{版本}.{扩展名}
```

Rules:

- Rename staged copies only; never rename original source files unless the user explicitly asks for in-place reorganization.
- Keep the original extension exactly.
- Use short, stable Chinese or English terms that make sense without opening the original folder.
- Prefer final/release/fixed/latest wording in the staged name only when the retained file truly represents the selected version.
- Omit empty fields instead of adding placeholder text.
- Avoid emoji, slashes, colons, repeated whitespace, and punctuation that is unsafe across operating systems or ZIP tools.
- If two staged names collide, append a short numeric suffix and record the reason.
- If a readable staged name cannot be generated confidently, keep the file in `review` and ask for confirmation.

## Safe Defaults

- Default `industry` to `internet`.
- Default `projects/assets/accounts` to `true`.
- Default `clients/legal` to `false` unless the folder strongly suggests otherwise.
- Default polished-output gates to `false`; a guessed role is draft-only until confirmed.
- Default to staged output instead of in-place file moves.
- Default to copying only `include` files. `review` and `exclude` files should remain in the source folder and appear in the filtering report.
- Default other-person personal materials to `exclude`; default ambiguous shared materials that mention another person to `review`.
- Default duplicate version groups to one retained representative, preferring final/release/fixed variants first, newest explicit date second, and newest file modified time third.
- Default copied filenames to standardized staged names with a reversible original-name mapping.
- Default ZIP export should be skipped for draft output unless the agent explicitly uses a draft ZIP flag after telling the user.
- Keep config and manifest in `.offboarding-handover/`, not in the final delivery folder.
- Render the HTML site with the fixed `tech-portal` style from `site-design-system.md`.

## Internal Script Modes

Default internal executable used by the agent:

```bash
python3 scripts/bootstrap_handover.py /target/path --interactive
```

Internal examples for the agent:

```bash
python3 scripts/bootstrap_handover.py /target/path --no-scan
python3 scripts/bootstrap_handover.py /target/path --stage-mode none
python3 scripts/bootstrap_handover.py /target/path --zip-output
python3 scripts/bootstrap_handover.py /target/path --employee-name "张三" --department "产品部" --role "产品经理" --profile-confirmed --successor-view-confirmed --deep-review-complete
python3 scripts/bootstrap_handover.py /target/path --refresh --no-scan --interactive
```
