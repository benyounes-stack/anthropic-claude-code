# Component catalog

`assets/report_template.html` ships CSS for these blocks but no fixed skeleton — a report is composed by picking the blocks that fit, in the order the story needs. Copy the markup below, fill in the data, delete what you don't need. Every block below is already styled; don't add new ad-hoc styling in the report HTML itself.

Color rule: `--primary`/`--accent` (from `brand.json`) are the only brand-colored things in this system — the header, section dividers, table headers, s-num, kpi-val. Everything else (green/red/orange/blue in tags, obj-bar, wins/fixes/actions/diag, plan-grid) is a **functional status color**: good/bad/warning/info. Never repaint those to brand colors — a red "fixes" box means "problem" regardless of whose brand it is.

## Section header (numbered)

Use for every top-level section. Numbers are sequential across the whole report, not reset per channel.

```html
<div class="section">
  <div class="section-header">
    <span class="s-num">01</span>
    <span class="s-title">Résultats S1 en un coup d'œil</span>
  </div>
  ... section content ...
</div>
```

## KPI row

3–5 headline numbers. `kpi-row` = 5 columns, `kpi-row-4` = 4, `kpi-row-3` = 3 — pick by how many you actually have, don't pad to 5 with a filler metric.

```html
<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">Revenu Meta</div>
    <div class="kpi-val">3,42M$</div>
    <div class="kpi-sub">+65% vs période précédente</div>
    <div class="tag tag-g">Croissance forte</div>
  </div>
  <!-- repeat -->
</div>
```

`.tag` variants: `tag-g` (green, good), `tag-r` (red, bad), `tag-o` (orange, caution), `tag-b` (blue, informational), `tag-neutral` (gray, no judgment — e.g. "en attente de données").

## Objective vs. actual bar

For stating a target next to the measured result. **Only use `.obj-g`/`.obj-r` when the two numbers were computed the same way** (same attribution window, same currency, same period length) — otherwise a "target beaten" claim is comparing apples to oranges. When methods differ (e.g. the objective was set in Triple Whale's attribution but you only have the platform's own numbers), use `.obj-neutral` and say so in the text — don't render a verdict you can't back up.

```html
<div class="obj-g">
  <span><strong>Revenu :</strong> Objectif 500K$ → Résultat 839 968$</span>
  <span class="val">+68% ✓</span>
</div>
<div class="obj-neutral">
  <span><strong>ROAS :</strong> Objectif 15× (attribution Triple Whale) vs 16,9× mesuré (attribution Meta) — méthodes non comparables, TW en attente de connexion.</span>
  <span class="val">Non comparable</span>
</div>
```

## Channel/phase divider

Marks a shift in subject — a new ad channel, or a new phase of a plan. Use an emoji that's easy to scan (🟣 for one channel, 🔴 for another, 🎯 for a plan section) — icon + label carries the distinction, not a background hue (brand color stays Noir/Jaune throughout).

```html
<div class="divider">
  <span class="divider-icon">🟣</span>
  <h2>Meta Ads</h2>
  <span class="divider-meta">Le canal principal · 202 533$ · ROAS 16,9×</span>
</div>
```

## Month-by-month grid

One card per period (month/quarter). Mark the standout period with `.best` — but only if it's genuinely the best on the metric you're leading with, not decorative.

```html
<div class="month-grid">
  <div class="m-card">
    <div class="m-label">Janvier</div>
    <div class="m-big">555 776$ <span style="font-size:13px;color:var(--muted)">revenu</span></div>
    <div class="m-row"><span class="m-key">Spend</span><span class="m-val">30 173$</span></div>
    <div class="m-row"><span class="m-key">ROAS</span><span class="m-val co">18,4×</span></div>
  </div>
  <div class="m-card best">
    <div class="m-label best-l">Mars — ✦ Meilleur mois</div>
    <div class="m-big" style="color:var(--green)">723 835$ <span style="font-size:13px">revenu</span></div>
    <div class="m-row"><span class="m-key">Spend</span><span class="m-val">34 093$</span></div>
    <div class="m-row"><span class="m-key">ROAS</span><span class="m-val cg">21,2× ↑</span></div>
  </div>
</div>
```

`.cg`/`.cr`/`.co`/`.cb` on a value = green/red/orange/blue text, for a quick up/down read inside a row.

## Table

`.trow` = totals row. `.win`/`.waste` = highlight a standout row green/red (a top performer, a budget sink) — use sparingly, only for rows the analysis text actually calls out.

```html
<table class="tbl">
  <thead><tr><th>Campagne</th><th>Spend</th><th>ROAS</th></tr></thead>
  <tbody>
    <tr class="win"><td>ACQ SCALING</td><td>46 550$</td><td>22,3×</td></tr>
    <tr><td>MARPIPE</td><td>37 328$</td><td>16,6×</td></tr>
    <tr class="trow"><td>Total</td><td>202 533$</td><td>16,9×</td></tr>
  </tbody>
</table>
```

## Callout boxes — wins / fixes / actions / diagnostic

Four fixed roles, don't invent a fifth:
- **`.wins`** — what's working, evidence-backed ("✓ X because Y, proven by Z").
- **`.fixes`** — what's actively broken and needs to stop/change now.
- **`.actions`** — forward-looking next steps, phrased as concrete moves ("→ tester X").
- **`.diag`** — the "why" behind a pattern in the data — diagnostic reasoning, not a to-do.

```html
<div class="wins">
  <h3>✅ Les winners</h3>
  <ul><li><strong>ROAS prospection a doublé</strong> — 12,5× → 22,7×, preuve que le ciblage TOFU s'améliore.</li></ul>
</div>
<div class="fixes">
  <h3>⚠ Ce qui brûle du budget</h3>
  <ul><li><strong>Campagne X à 392$/conversion</strong> — 9× le CPA moyen du compte.</li></ul>
</div>
<div class="actions">
  <h3>→ Prochaines étapes</h3>
  <ul><li><strong>Coupler l'offre de restock au retargeting BOFU</strong> pour contrer l'érosion du ROAS existing.</li></ul>
</div>
<div class="diag">
  <h3>⚡ Diagnostic</h3>
  <ul><li><strong>Le CPM a augmenté de 28%</strong> — la concurrence aux enchères monte avec le scaling, pas un problème de ciblage.</li></ul>
</div>
```

## Data-gap note

When a section of the requested report can't be built because a source isn't connected or wasn't provided — say so in the report itself, don't silently omit it or fabricate a placeholder number. This is not optional: a client-facing report with an invented margin or a guessed conversion rate is worse than one that names the gap.

```html
<div class="note gap">
  <strong>Non disponible dans ce rapport :</strong> le détail par funnel (TOFU/MOFU/BOFU) nécessite Triple Whale,
  pas encore connecté. Cette section sera ajoutée au prochain rapport une fois la connexion active.
</div>
```

## Phased plan / roadmap

Three horizons is the usual shape (urgent/now, mid-term, growth) — `.p-card.urgent` (red), `.p-card.mid` (orange), `.p-card.grow` (green). Each item should name a concrete action and, where possible, a target.

```html
<div class="plan-grid">
  <div class="p-card urgent">
    <div class="p-phase" style="color:var(--red)">Semaine 1</div>
    <div class="p-title">Stopper les pertes</div>
    <div class="p-item"><strong>Couper la campagne X</strong>392$/conv, 9× le CPA moyen.</div>
    <div class="p-target" style="color:var(--red)">~25K$ récupérés / trimestre</div>
  </div>
  <!-- .mid, .grow -->
</div>
```

## Creative-level card

For ad-level deep dives (needs creative-level API fields: hook rate, hold rate, CTR, CPA, ROAS, spend — pull these explicitly, they aren't in a standard campaign-level call).

```html
<div class="creative-card">
  <h4>🏆 #1 — Carousel Catalogue Static</h4>
  <div class="c-row">
    <div class="c-metric">Format<br><strong>Carousel</strong></div>
    <div class="c-metric">ROAS<br><strong style="color:var(--green)">18,5×</strong></div>
    <div class="c-metric">Spend<br><strong>11 585$</strong></div>
  </div>
  <div style="margin-top:10px;font-size:12px">Angle : produits premium 380$+ — le catalogue dynamique cible les collectionneurs sérieux.</div>
</div>
```

## Header meta row

```html
<div class="header-meta">
  <span>Période <strong>Jan → Juin 2026</strong></span>
  <span>Budget total <strong>202 533$</strong></span>
</div>
```
