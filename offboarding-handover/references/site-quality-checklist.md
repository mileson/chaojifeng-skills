# Site Quality Checklist

Use this checklist before treating a generated handover site as polished.

## P0 Must Pass

- The page opens as a local standalone HTML file.
- Sections follow the highlights-to-detail order: 交接速览 → 马上要接的事 → 风险与待确认 → 交接确认单 → 核心文档 → 交接材料 → 附录.
- The first screen shows what this package is, who it is for, and the `接手前必读` takeaways.
- If the package is a draft, the banner says what still needs confirmation in human language, never internal gate slugs.
- The first screen shows handover owner/person, successor, handover coordinator, role, and last working day, or clearly marks unknown facts as draft blockers.
- In-flight work is a first-class section with status, next step, and a working jump-to-file action.
- A printable sign-off section exists with check-item statuses and a signature grid; print view hides navigation, documents, file table, and appendix.
- Every generated core document is reachable from the site:
  - `00-交接总览.md`
  - `01-阅读顺序.md`
  - `00-交接信息.md`
  - `00-进行中事项总表.md`
  - `01-高遗漏检查清单.md`
  - `02-交接结论说明.md`
- High-risk items are visible without scrolling through the full file table, and each one can locate its file row.
- The site shows how many files were included, need review, and were excluded.
- The filtering report, assumptions, and large-file list live in a collapsed appendix, not first-class sections.
- The site or filtering report shows other-person exclusions and review candidates when such files were detected.
- The site or filtering report shows version-collapsed files and their retained representative.
- The file table shows standardized staged names (bold) with original paths preserved (muted).
- File search and domain filters work; filtering a row away also collapses its inline preview.
- Local staged file links use relative paths that work from `site/index.html`.
- Office/PDF/image/text/CSV files have inline expandable previews under their rows, or a clear `打开原文件` action when no preview is possible.
- Status and sensitivity labels render in Chinese for business users.
- File actions do not use `下载` wording unless the browser action is truly download-only.
- Text does not overlap or overflow on desktop or mobile widths.
- No clearly unrelated other-person personal material appears in the core file table.
- No obvious superseded older version appears in the core file table unless explicitly justified.
- Copied core files use readable, sortable, successor-facing staged filenames.

## P1 Should Pass

- The visual style follows `references/site-design-system.md`.
- The page uses `#FBFCFE` as the workspace background.
- Controls, panels, and cards use restrained radius, spacing, and borders.
- The site uses semantic HTML landmarks such as `header`, `nav`, `main`, `section`, and `table`.
- Buttons and links have visible focus states.
- Empty states explain what is empty and what the user should do next.
- File table can search both standardized staged names and original names.

## P2 Useful Polish

- Tables are horizontally scrollable on narrow screens.
- The active document preview tab is visually clear.
- Risk and pending states use color sparingly and consistently.
- The page remains useful when there are zero scanned files.
- The page remains useful when profile fields are still `待补充`.
- Draft state explains the next user action rather than presenting the package as final.
- Review candidates make clear why confirmation is needed.

## P3 Nice To Have

- Print styles keep the summary, risk queue, and document links readable.
- Large tables preserve row hover and zebra striping for scanning.
- Counts and status labels are compact enough for repeated operational use.
- Filename mapping can be exported or read without opening the source folder.
