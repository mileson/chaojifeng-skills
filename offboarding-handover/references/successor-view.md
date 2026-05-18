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

- handover owner and successor
- confirmed role or role still awaiting confirmation
- current delivery state: draft or formal
- first three reading steps
- active risks and missing facts

Do not lead with scan mechanics.

## Preferred Sections

- `从这里开始`: practical reading path for the successor
- `当前要接的事项`: active projects, unresolved issues, next actions
- `风险与待确认`: accounts, sensitive data, contracts, customer risks, missing facts
- `核心文档`: generated markdown previews
- `文件预览`: quick previews for Office/PDF/image/text files when possible
- `已纳入文件`: searchable file table with `查看预览` and `打开原文件`

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
