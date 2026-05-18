# Deep Material Review

Use this reference before generating a polished handover package from a large or mixed folder.

Fast filename sorting is not enough. The agent must review enough evidence to explain why the kept materials matter to the successor.

## Minimum Review Layers

1. Folder and filename inventory
2. Role and project clustering
3. Relevance filtering: include, review, exclude
4. Version grouping and latest/final representative selection
5. Targeted content sampling for high-value documents
6. Successor-facing synthesis: current status, next action, risk, owner/contact, supporting files

## Targeted Content Sampling

Read small excerpts instead of full documents unless the user asks for full extraction.

Prioritize:

- PRD, BRD, product plans, blueprints, implementation plans
- project schedules, launch plans, acceptance reports, issue logs
- customer-facing documents and training materials
- Excel/CSV files with tracking, budget, measurement, reconciliation, or backlog signals
- documents with `待解决`, `问题`, `风险`, `上线`, `结项`, `确认`, `最新`, `最终`

## Gate Before Polished Output

Do not generate a polished site or ZIP until:

- source folder is confirmed
- role or role family is confirmed
- successor-oriented questions are answered or explicitly marked unknown
- subagent/deep scan evidence has been synthesized
- the output directory structure reflects the confirmed role

If any item is missing, produce a draft scan report and state what still needs confirmation.

## Successor Summary Shape

For each important project or material cluster, synthesize:

- `接什么`: project, system, client, or workflow
- `当前状态`: active, historical, done, unknown
- `下一步`: concrete action or `待确认`
- `风险`: sensitive data, owner gap, version ambiguity, pending decision
- `资料`: linked files or previewable files
