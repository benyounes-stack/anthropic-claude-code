---
name: custom-reports
description: Generate polished, branded client-facing PDF reports ("rapports sur mesure" / custom reports) from any data source — uploaded files (Excel, CSV, Word, PDF), raw text pasted in conversation, connected data (Google Drive, Gmail, Slack, GitHub), a database/API, or advertising platforms like Meta Ads. Use this whenever the user asks for a "rapport", "report", "compte-rendu", a business/financial/performance summary as a PDF, or wants recurring reporting on KPIs, sales, ad spend, project activity, or incidents — even if they don't explicitly say "PDF" or name this skill. Produces a fixed-structure report (executive summary, key findings/KPIs with charts, detailed analysis, recommendations) styled with the client's branding.
---

# Rapports sur mesure (Custom Reports)

This skill turns whatever data the user has into a polished, branded PDF report. It is deliberately opinionated about **structure** (so every report is consistent and easy to skim) while staying flexible about **source** and **content** (so it works for a Meta Ads performance recap, a monthly business review, a financial summary, or an incident report).

## Workflow

1. **Clarify only what's missing.** Before producing anything, make sure you know:
   - **Source(s)**: uploaded file(s), pasted text, a connector (Drive/Gmail/Slack/GitHub — check `ListConnectors` if unsure what's attached), a database/API, or an ads platform export.
   - **Report type**: business/activity, financial, or generic. This mostly affects *what goes in* "Constats & indicateurs clés" and "Analyse", not the skeleton.
   - **Period covered** and **audience** (internal vs. client-facing — affects tone, not structure).
   - If the user already gave this in their message (file attached, clear ask), don't re-ask — infer and confirm briefly instead of interrogating.
   - Meta Ads / other ad-platform data: no live connector is assumed. If the user wants ads data and hasn't provided an export, ask them to export CSV/Excel from the platform's dashboard, or check `ListConnectors`/`SearchMcpRegistry` in case one is attached this session.

2. **Gather and understand the data** before writing a word of the report. Read every source file fully (don't skim a spreadsheet — compute the actual totals/deltas). For connectors, pull only what's relevant to the stated period.

3. **Build the charts first, using the `dataviz` skill.** Load it before writing any chart code — it defines the palette, chart-type heuristics, and accessibility rules. Render each chart as a standalone PNG (150–200 dpi, transparent or white background) sized for a print page, e.g. via matplotlib. Save them next to the report's working files. Keep it to the 2-4 charts that actually carry the story (a KPI trend, a breakdown, a comparison) — a report with ten charts is harder to read than one with three good ones.

4. **Fill the HTML template** (`assets/report_template.html`) with the report content. Copy the template rather than editing it in place, then replace the placeholders:
   - `{{TITLE}}`, `{{SUBTITLE}}`, `{{PERIOD}}`, `{{DATE}}` — cover page / header info.
   - `{{EXEC_SUMMARY}}` — 3-6 sentences, the "if they read nothing else" takeaway.
   - `{{KPI_CARDS}}` — a row of `<div class="kpi-card">` blocks (label, big number, delta vs. previous period) for the 3-5 headline metrics. See the template comments for the exact markup.
   - `{{CHARTS}}` — `<img>` tags pointing at the PNGs from step 3, each inside a `<figure>` with a caption.
   - `{{ANALYSIS}}` — the detailed narrative: what happened, why, what's notable. Use `<h3>` subsections if there's more than one theme.
   - `{{RECOMMENDATIONS}}` — an ordered or bulleted list of concrete next steps, tied back to specific findings above. Skip filler recommendations that don't follow from the data.
   - `{{ANNEXES}}` — optional; delete the whole `<section id="annexes">` block if there's nothing to append (raw data tables, methodology notes).
   - Branding: read `references/brand.json` for the company name, colors, and logo path, and set the corresponding CSS variables / `<img>` src in the template's `:root`/header. If `brand.json` has no logo configured, fall back to the text wordmark already in the template — don't invent a logo.

5. **Render to PDF** with the bundled script — don't hand-roll a PDF pipeline:
   ```bash
   node .claude/skills/custom-reports/scripts/render_pdf.js <input.html> <output.pdf>
   ```
   This prints via headless Chromium (Playwright, already available in this environment) with proper page breaks and a running footer showing the company name and page numbers (pulled from `references/brand.json`). Check the resulting PDF actually rendered (non-zero size, expected page count) before telling the user it's done.

6. **Deliver the PDF** to the user (e.g. via `SendUserFile` if available) and briefly summarize what's in it — don't just say "done."

## Fixed report structure

Every report uses this skeleton, regardless of type or source. Consistency here is the point — a client who receives several of these should be able to jump straight to "Recommandations" without relearning the layout each time.

1. **Couverture / En-tête** — logo, report title, period, generation date.
2. **Résumé exécutif** — the headline, in a few sentences.
3. **Constats & indicateurs clés** — KPI cards + the 2-4 supporting charts.
4. **Analyse** — the narrative explaining the numbers.
5. **Recommandations** — concrete, numbered next steps.
6. **Annexes** *(optional)* — raw tables, methodology, caveats.

Don't add extra top-level sections (a "Conclusion" that restates the executive summary, a "Contexte" preamble, etc.) — if something needs saying, it belongs inside one of the five sections above. If a report type genuinely needs something structurally different (e.g. an incident report needing a timeline), ask the user before deviating rather than silently changing the skeleton.

## Report-type notes

- **Business/activité**: KPIs are usually activity volumes, completion rates, or engagement metrics. Analysis should connect movement in the numbers to concrete events (a campaign, a hire, a process change).
- **Financier**: KPIs are typically revenue, cost, margin, cash position. Always show the comparison basis (vs. budget, vs. prior period) next to each number — a raw figure without a baseline isn't useful in a financial report.
- **Générique/configurable**: ask the user for their own KPI list and section emphasis up front; the skeleton stays the same, only the KPI/analysis content changes.

## Branding

`references/brand.json` holds the default look (company name, primary/accent colors, logo path, footer confidentiality line). It ships with sensible neutral defaults. If the user gives you their real brand colors or a logo file, update `references/brand.json` so future reports pick it up automatically — don't just hardcode it into one report's HTML.

## Files in this skill

- `assets/report_template.html` — the HTML/CSS skeleton with print-ready `@page` rules. Copy per report, fill placeholders.
- `scripts/render_pdf.js` — HTML → PDF via headless Chromium (Playwright). Handles page numbers and margins; don't reimplement this.
- `references/brand.json` — editable branding defaults (colors, logo, footer text).
