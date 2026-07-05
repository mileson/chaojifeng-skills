# Successor View

Use this reference when writing generated markdown, the HTML site, and file-level summaries.

The package is for the successor, not for the person or agent who organized the folder. The successor needs to answer:

1. What am I taking over?
2. What should I read first?
3. What is still in progress?
4. Who should I contact?
5. Which files support each project or decision?
6. What is risky, sensitive, overdue, or easy to miss?
7. Which files can I preview here, and which should I open in Office/WPS?

## Required First Screen

The first screen of `site/index.html` should show:

- handover owner and successor (`交接人 → 接手人` in the header)
- confirmed role or role still awaiting confirmation
- current delivery state badge: draft or formal
- KPI strip: included files, in-flight items, high-risk items, pending review, unconfirmed checks
- `接手前必读` takeaways with anchor links to the matching sections

Do not lead with scan mechanics.

## Preferred Sections (in order)

- `交接速览`: people, dates, KPIs, and takeaways
- `马上要接的事`: in-flight work with status, next step, and jump-to-file actions
- `风险与待确认`: accounts, sensitive data, contracts, customer risks, check-item statuses
- `交接确认单`: printable sign-off table and signature grid for both sides plus the coordinator
- `核心文档`: generated markdown previews as tabs
- `交接材料`: searchable file table with inline expandable previews, `查看预览` and `打开原文件`
- `附录` (collapsed): filtering explanation, assumptions, large files

## Copy Rules

- Good: `接手人先看这里`
- Good: `打开原文件`
- Good: `查看预览`
- Good: `仍需确认后才能作为正式交接包交付`
- Avoid: `扫描完成`
- Avoid: `manifest`
- Avoid: `parser`
- Avoid: `pipeline`
- Avoid: `下载文件` unless the action truly downloads a file

## Draft State

If role, successor, handover owner, last working day, or deep review is missing, the site must clearly state that it is a draft. A draft can help review the scan, but it should not be presented as the final handover package.
