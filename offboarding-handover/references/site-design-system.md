# Site Design System

Use this design system whenever the skill renders `site/index.html`.

The generated site is an internal handover portal for a technology or internet company. It should feel like a clean product workspace or knowledge base: dense, calm, searchable, and operational. It is not a marketing landing page, a slide deck, or an editorial magazine.

## Visual Direction

- Use a cold white workspace background: `#FBFCFE`.
- Use white surfaces for primary content and `#F4F7FB` for secondary panels.
- Use restrained enterprise blue and cyan accents.
- Keep cards, panels, inputs, and buttons at `8px` border radius or less.
- Avoid warm beige, decorative gradients, large hero art, oversized round cards, purple-blue gradient themes, and presentation-like cover pages.
- Prioritize scanning and repeated use over visual spectacle.

## Tokens

Use these core values unless the user provides a company-specific brand system:

```css
:root {
  --page: #FBFCFE;
  --surface: #FFFFFF;
  --surface-alt: #F4F7FB;
  --ink: #172033;
  --muted: #667085;
  --line: #E6EBF2;
  --line-strong: #CBD5E1;
  --primary: #2563EB;
  --primary-ink: #1D4ED8;
  --cyan: #0891B2;
  --success: #0E9F6E;
  --warning: #B7791F;
  --danger: #C2410C;
}
```

## Information Architecture

The HTML site is the entry point for the whole handover package. Order sections from highlights to detail, in this fixed sequence:

1. **交接速览**: handover person/successor/coordinator cards, KPI strip (included files, in-flight items, high-risk items, files pending review, unconfirmed checks), and a `接手前必读` takeaway panel with 3-5 anchor links.
2. **马上要接的事**: in-flight work table with item, module, status, next step, and a jump-to-file action. This is a first-class section, not a buried document.
3. **风险与待确认**: high-risk file list with locate-file actions, plus the offboarding check items with status pills.
4. **交接确认单**: printable sign-off table (check items + universal items such as device return and account revocation) and a signature grid for the handover person, successor, coordinator, and HR.
5. **核心文档**: generated markdown documents as tabs with embedded previews.
6. **交接材料**: searchable, filterable file table with inline expandable previews per row, domain chips with counts, followed by a collapsed appendix.
7. **附录 (collapsed `<details>`)**: filtering/exclusion explanation, organizing assumptions, and the large-file list. Process information never occupies first-class screen space.

Do not make the user open the generated folder tree first. The site should tell the successor where to start, what is risky, what is unfinished, and where every file lives.

## Required Components

- Sticky top bar with package title, `交接人 → 接手人` flow, state badge (`草稿待确认` / `正式交接包`), search focus, and a print button for the sign-off sheet.
- Draft banner with human-language missing facts (never internal gate slugs) when polished-output gates are not satisfied.
- Left navigation that links to each major section.
- Takeaway panel (`接手前必读`) that summarizes in-flight work, risks, and unconfirmed checks with anchor links.
- In-flight work table that can jump to and expand the matching file row.
- Risk queue with locate-file actions tied to the file table.
- Printable sign-off section with signature grid; print styles hide navigation, file table, documents, and appendix.
- Core document preview area for generated markdown pages.
- File explorer table with staged name (bold) plus original path (muted), domain, type, status, sensitivity, size, and actions.
- Inline preview rows expanded directly under the file row for Office/PDF/image/text/CSV files.
- Collapsed appendix for filtering report, assumptions, and large files.

## Interaction Rules

- Search must filter the full file table; hiding a row also collapses its inline preview.
- Domain chips and the domain filter stay in sync.
- `查看预览` toggles the inline preview row under the file; `打开原文件` opens the staged copy.
- Jump actions (from in-flight items or risks) clear filters, scroll to the row, expand its preview, and flash-highlight the row.
- Status and sensitivity values are displayed in Chinese (`草稿/评审中/定稿/历史归档`, `公开/内部/受限/机密`); raw values stay in data attributes for filtering.
- Static HTML cannot reliably force WPS/Office to open; use normal local file links and clear wording.
- Keyboard focus states must be visible.
- Tables must be horizontally scrollable on narrow screens.
- The page must work as a standalone local HTML file.

## Copy Rules

Write for normal business users, not developers.

- Good: `从这里开始阅读`
- Good: `仍需确认`
- Good: `优先核对`
- Good: `查看预览`
- Good: `打开原文件`
- Good: `草稿待确认`
- Avoid exposing implementation details such as manifest, script, API, parser, or internal pipeline names in user-facing text.
- Avoid `下载文件` unless the link truly downloads a file.
