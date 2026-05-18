# Update Mode

Use update mode when a handover package already exists and the user wants to:

- fill in missing facts
- replace `待补充`
- refresh the HTML site
- update the handover after new confirmations

## Recommended Flow

1. Read:
   - `.offboarding-handover/offboarding.config.json`
   - `.offboarding-handover/handover.manifest.json`
   - `.offboarding-handover/handover.answers.json` if present
2. Find missing fields from:
   - profile fields
   - checklist answers
   - any markdown pages that still imply unresolved handover facts
3. Ask only the missing or explicitly requested items
4. Write back `handover.answers.json`
5. Re-render:
   - `00-说明与导航/00-交接总览.md`
   - `04-未完事项与状态/*.md`
   - `site/index.html`

## Agent Rule

The user should say things like:

- “更新这个交接包”
- “把待补充补一下”
- “刷新一下 HTML”
- “把接手人改成王五”

Then the agent should enter refresh mode internally.

## Internal Script Hint

Recommended internal command for the agent:

```bash
python3 scripts/bootstrap_handover.py /target/path --refresh --no-scan --interactive
```

Use `--no-scan` when the files have not materially changed and you only want to refresh content.
