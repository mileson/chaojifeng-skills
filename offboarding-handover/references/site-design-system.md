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

The HTML site is the entry point for the whole handover package. It should connect:

- profile and handover owner information
- delivery state: draft vs formal
- recommended reading path
- key generated markdown documents
- successor-facing active projects, next actions, and risks
- quick previews for supported files
- module/domain overview
- high-risk items
- ongoing items and unresolved checks
- all staged files with search and filters

Do not make the user open the generated folder tree first. The site should tell the successor where to start, what is risky, what is unfinished, and where every file lives.

## Required Components

- Sticky top bar with package title, profile summary, and search focus.
- Draft/formal state banner when polished-output gates are not satisfied.
- Left or top navigation that links to each major section.
- Compact KPI strip for scanned files, total size, high-risk items, and pending status.
- Reading path or quick-start panel that links to the generated markdown previews.
- File preview area for Office/PDF/image/text files when the renderer can extract a useful preview.
- Module/domain grid or table with counts and sample files.
- Risk queue for sensitive, asset, compliance, or unresolved items.
- Core document preview area for generated markdown pages.
- File explorer table with domain, source, output path, type, scope, status, sensitivity, and size.

## Interaction Rules

- Search must filter the full file table.
- Domain filters must work for both the module view and file table.
- Preview links should open the matching preview panel instead of forcing the user to browse folders.
- File table actions should prefer `查看预览` and `打开原文件`.
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
