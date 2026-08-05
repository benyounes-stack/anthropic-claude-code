---
name: custom-reports
description: Generate polished, branded client-facing PDF reports ("rapports sur mesure" / custom reports) from any data source — uploaded files (Excel, CSV, Word, PDF), raw text pasted in conversation, connected data (Google Drive, Gmail, Slack, GitHub), a database/API, or advertising platforms like Meta Ads, Google Ads, or Triple Whale. Use this whenever the user asks for a "rapport", "report", "compte-rendu", a business/financial/media-performance summary as a PDF, or wants recurring reporting on KPIs, sales, ad spend, funnel/creative performance, or project activity — even if they don't explicitly say "PDF" or name this skill. Produces a numbered-section report (KPI summary, channel/topic deep dives, diagnostic callouts, action plan) styled with the client's branding, built only from data actually available — never invents numbers for sources that aren't connected.
---

# Rapports sur mesure (Custom Reports)

This skill turns whatever data the user has into a polished, branded PDF report. It's opinionated about **honesty and composition** (real data only, built from a fixed catalog of blocks so every report looks like it belongs to the same family) while staying flexible about **which blocks a given report actually uses** — a quick internal KPI recap and a full six-month media-performance deep dive share the same visual language but not the same length.

## Workflow

1. **Scope the report before building anything.** Nail down:
   - **What's it about** — a single metric recap, a multi-channel ad-performance report, a financial summary, an incident report, etc.
   - **Sources** — uploaded file(s), pasted text, a connector (Drive/Gmail/Slack/GitHub/Meta Ads/Google Ads/Triple Whale — check what's actually attached this session, connectors get added and dropped between sessions), a database/API.
   - **Period** and **audience** (internal vs. client-facing — affects tone, not honesty).
   - If the user already gave this (file attached, clear ask), infer and confirm briefly rather than interrogating.

2. **Audit data availability before promising a structure.** If the user describes an ambitious report (multiple channels, funnel breakdowns, financials, customer cohorts), check what's *actually* connected and callable right now — don't assume a connector from an earlier message in the conversation is still live; MCP connections can drop mid-session. Tell the user plainly which requested sections you can build with real data, which need a connector that isn't attached, and which need information only they have (margins, internal costs, business context, growth plans) — see **Data honesty** below before writing a single number.

3. **Gather and understand the data.** Read every source fully — don't skim a spreadsheet, compute the actual totals/deltas. Pull connector data at the granularity the analysis needs (e.g. ad-level fields for a creative deep-dive, not just campaign totals). If two sources measure the same thing differently (e.g. a platform's own attribution vs. a third-party attribution tool like Triple Whale), keep them labeled separately — never blend or silently pick one as "the" number.

4. **Build charts using the `dataviz` skill.** Load it before writing any chart code — it defines the palette, chart-type heuristics, and accessibility rules (including: never a dual-axis chart — use small multiples or index to a common base instead when two series have very different scales). Render each as a standalone PNG (150–200 dpi) sized for a print page via matplotlib. Keep it to the charts that carry the story, not one per metric.

5. **Compose the report from the block catalog** in `references/components.md` — read it before writing HTML. Copy `assets/report_template.html` per report (don't edit the shared copy), fill the header placeholders, then build the body by picking blocks: section headers (numbered sequentially), KPI rows, objective-vs-actual bars, dividers between channels/phases, month grids, tables, the four callout roles (wins/fixes/actions/diagnostic), phased plan grids, creative cards, and data-gap notes. See **Report anatomy** below for how to pick and order them.
   - Branding: `references/brand.json` has the company's real colors/logo/footer text — use it as-is. `--primary`/`--accent` are the *only* brand-colored elements; every status color (green/red/orange/blue in tags, obj-bars, callout boxes, plan-grid) is functional and must never be repainted to brand colors — see `components.md`'s color rule.
   - Logo: the HTML is opened as a `file://` URL, so `<img src="...">` must resolve from wherever the working copy lives — copy `assets/logo.png` next to it, or use the skill's absolute path.

6. **Render to PDF** with the bundled script:
   ```bash
   node .claude/skills/custom-reports/scripts/render_pdf.js <input.html> <output.pdf>
   ```
   Headless Chromium (Playwright) with page breaks and a running footer (company name + page numbers from `brand.json`). Verify the PDF actually rendered (non-zero size, expected page count) before calling it done.

7. **Deliver the PDF** (e.g. via `SendUserFile`) and summarize what's in it — including what's *not* in it and why, if anything was scoped out.

## Data honesty — read this before writing any number

This is the part that actually makes a client trust the report:

- **Never fabricate a number a source doesn't give you.** No invented margins, no guessed COGS, no placeholder conversion rate. If the user's requested structure needs data you don't have, either get it from them directly, or cut that section, or add it as a `.note.gap` block naming exactly what's missing and why (connector not attached, connector dropped mid-session, needs manual input).
- **Never compare numbers computed by different methods as if they were the same metric.** The most common trap: a platform's own reported ROAS/revenue (e.g. Meta's `purchase_roas`) runs structurally higher than a third-party attribution tool's number (e.g. Triple Whale) because the attribution windows differ. If an objective was set using one method and you only have the other, show both labeled by source and use `.obj-neutral` — don't render a "+240% objective beaten" that's actually comparing apples to oranges.
- **State the report's scope up front** when it's narrower than what was originally asked for (e.g. "ce rapport couvre Meta uniquement — Google Ads et Triple Whale ne sont pas connectés") so the reader isn't left assuming silence means zero activity on the missing channel.
- **Qualitative/contextual content (market research, competitive landscape) is fine and valuable** — just label it as research/context, not as the client's own measured data, and cite sources.

## Report anatomy

A report is a sequence of numbered `.section` blocks (numbering continues across the whole document, not per-channel), with `.divider` blocks marking a shift in subject. There's no fixed section count — build only what the data supports. A typical media-performance report's shape:

1. **Résultats en un coup d'œil** — KPI row + objective-vs-actual bars (or `.note.gap` if the objective isn't fairly comparable yet).
2. **Portée de ce rapport** *(when scope is partial)* — one paragraph + gap notes naming what's covered and what's pending.
3. Per-channel/topic sections, each opened by a `.divider`: what's performing (`.wins`), month-by-month (`.month-grid`), breakdowns (`.tbl`), what's broken (`.fixes`), why (`.diag`), creative-level detail (`.creative-card`) where the data supports it.
4. **Contexte marché** *(when relevant)* — research-backed context, clearly labeled as external/qualitative.
5. **Plan d'action** — `.plan-grid`, phased (e.g. urgent/mid-term/growth), each item tied to a specific finding above.
6. **Ce qu'il manque pour le prochain rapport** *(when anything was scoped out)* — a short, honest list of what needs to happen (connect X, get Y from the client) before the next edition can cover it.

A simple internal recap doesn't need all of this — a KPI row, one or two callout boxes, and a short analysis paragraph can be the whole report. Match the depth to what the user actually asked for and what the data actually supports; don't pad a thin dataset out to look like a full media-performance deep dive.

## Files in this skill

- `assets/report_template.html` — CSS + header/footer skeleton. Copy per report; body is composed from `references/components.md`.
- `references/components.md` — the block catalog: markup + when to use each one. Read before composing a report.
- `scripts/render_pdf.js` — HTML → PDF via headless Chromium (Playwright). Don't reimplement this.
- `references/brand.json` — editable branding (colors, logo, footer text). Update it when the user gives real brand values so future reports pick them up automatically.
