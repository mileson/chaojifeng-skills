# Site Quality Checklist

Use this checklist before treating a generated handover site as polished.

## P0 Must Pass

- The page opens as a local standalone HTML file.
- The first screen shows what this package is, who it is for, and where to start.
- If the package is a draft, the first screen clearly says what still needs confirmation.
- The first screen shows handover owner/person, successor, handover coordinator, role boundary, and last working day, or clearly marks unknown facts as draft blockers.
- Every generated core document is reachable from the site:
  - `00-交接总览.md`
  - `01-阅读顺序.md`
  - `00-交接信息.md`
  - `00-进行中事项总表.md`
  - `01-高遗漏检查清单.md`
  - `02-交接结论说明.md`
- High-risk items are visible without scrolling through the full file table.
- The site shows how many files were included, need review, and were excluded.
- The filtering report is reachable from the core document area.
- The site or filtering report shows other-person exclusions and review candidates when such files were detected.
- The site or filtering report shows version-collapsed files and their retained representative.
- The site or file table shows standardized staged names and preserves original file names/paths.
- File search and domain filters work.
- Local staged file links use relative paths that work from `site/index.html`.
- Office/PDF/image/text files either have a useful local preview or a clear `打开原文件` action.
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
