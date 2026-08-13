# Offer anatomy and block catalog

`assets/offer_template.html` ships the CSS and a cover; the body is composed from the blocks below. Copy the markup, fill it, delete what you don't need — and don't add ad-hoc styling in the offer HTML, the blocks are already styled and consistency is what makes the document look like it came from a firm rather than a freelancer's evening.

Color rule: `--primary` / `--accent` (from `brand.json`) are the only brand-colored elements. Green/red/orange/blue are **functional** — good / costly / caution / informational. Never repaint them to the brand palette; in an offer, red means "this is losing you money" and that meaning has to survive.

---

## Document order

Lead with their problem, close with the price. A proposal that opens with "qui sommes-nous" gets skimmed; one that opens with a number from the reader's own account gets read.

1. **Cover** — client name, offer object, date, validity.
2. **Ce que nous avons observé** — the audit. KPI row + 2–4 `.finding` blocks. This is the section that sells; give it the most care.
3. **Notre lecture de la situation** — the verdict, in a few lines (`.lead` + a `.diag` or `.fixes` callout). One paragraph, not a treatise.
4. **Ce que nous proposons** — scope table, ordered by the client's pain, plus the exclusions block.
5. **Le plan** — `.timeline` with dates, or `.plan-grid` for three horizons.
6. **Ce que ça peut produire** — scenario table + `.assumption`. Three scenarios, assumptions visible.
7. **Investissement** — pricing (three options or one), with the `.value-box` self-financing line.
8. **Conditions** — terms grid, what the client supplies, validity.
9. **Signature**.

A renewal or a small upsell doesn't need all nine — a `.finding`, a scope table, a price and terms can be the whole document. Match the length to the size of the decision; a 14-page PDF for a 1 500 $/month add-on reads as padding.

---

## Section header

```html
<div class="section">
  <div class="section-header">
    <span class="s-num">01</span>
    <span class="s-title">Ce que nous avons observé</span>
  </div>
  <p class="lead">Audit du compte Meta sur 12 mois et des données Triple Whale, réalisé le 12 août 2026.</p>
  ...
</div>
```

## KPI row — the audit headline

3–5 numbers, from their account, with the period stated. Never pad to five.

```html
<div class="kpi-row-4">
  <div class="kpi">
    <div class="kpi-label">Budget média / 12 mois</div>
    <div class="kpi-val">480 000 $</div>
    <div class="kpi-sub">Meta uniquement</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">MER blended</div>
    <div class="kpi-val">5,0×</div>
    <div class="kpi-sub">Seuil de rentabilité : 1,6×</div>
    <div class="tag tag-g">Rentable</div>
  </div>
</div>
```

## Finding — the core block

The observation → consequence → proposal chain from `diagnostic.md`. **Cite the source and period** in `.f-src`: it's what separates an audit from an opinion, and it's the first thing a sceptical client checks.

```html
<div class="finding">
  <div class="f-obs">38% du budget des 90 derniers jours est allé sur des campagnes au-dessus du CPA cible.</div>
  <div class="f-cost">≈ 14 200 $ de budget récupérable par trimestre, à volume constant.</div>
  <div class="f-fix"><strong>Ce qu'on propose :</strong> restructuration du compte en phase 1, avant toute hausse de budget.</div>
  <div class="f-src">Source : Meta Ads, 15 mai → 12 août 2026 · CPA cible fourni par le client</div>
</div>
```

Keep `.f-cost` empty rather than inventing a figure. A finding without a price tag is still a finding; a fabricated one voids the document.

## Value box — the self-financing line

The single most persuasive element in the offer. Use `breakeven_uplift` from `offer_math.py` — never a hand-computed figure.

```html
<div class="value-box">
  <div class="v-big">+4,1%</div>
  <div class="v-txt">C'est la hausse de chiffre d'affaires à partir de laquelle
    l'accompagnement <strong>s'autofinance intégralement</strong> — soit environ 8 200 $/mois
    de CA additionnel, à marge constante (62%).</div>
</div>
```

## Scope table + exclusions

Volume and cadence in the middle column; the finding it answers in the right one. That third column is what makes the scope feel earned rather than assembled.

```html
<table class="tbl tbl-left scope-tbl">
  <thead><tr><th>Prestation</th><th>Ce qui est livré</th><th>Pourquoi</th></tr></thead>
  <tbody>
    <tr>
      <td>Pilotage média Meta</td>
      <td>Arbitrage quotidien, restructuration du compte, point hebdo de 30 min</td>
      <td class="why">38% du budget hors cible (constat 1)</td>
    </tr>
    <tr>
      <td>Production créative</td>
      <td>8 créatifs/mois (4 statiques, 4 UGC vidéo)</td>
      <td class="why">2 créatifs portent 81% de la dépense (constat 2)</td>
    </tr>
  </tbody>
</table>

<div class="excl">
  <h4>Non inclus</h4>
  <ul>
    <li>Budget média (payé directement par le client à Meta)</li>
    <li>Abonnements outils (Triple Whale, Klaviyo)</li>
    <li>Shooting photo/vidéo</li>
    <li>Développement du site</li>
  </ul>
</div>
```

## Pricing — three options

Three coherent depths of the same diagnostic. Mark the recommended one `.featured`; grey out what a tier doesn't include with `.off` rather than hiding it, so the difference is legible.

```html
<div class="price-grid">
  <div class="price-card">
    <div class="p-name">Essentiel</div>
    <div class="p-price">2 500 $<small>/mois</small></div>
    <div class="p-note">Sans engagement</div>
    <ul class="p-list">
      <li>Pilotage média Meta</li>
      <li>Reporting mensuel</li>
      <li class="off">Production créative</li>
    </ul>
  </div>
  <div class="price-card featured">
    <div class="p-name">Croissance</div>
    <div class="p-price">4 500 $<small>/mois</small></div>
    <div class="p-note">Engagement 6 mois · setup 3 500 $</div>
    <ul class="p-list">
      <li>Tout Essentiel</li>
      <li>8 créatifs/mois</li>
      <li>Flows CRM</li>
    </ul>
  </div>
  <div class="price-card">...</div>
</div>
```

Single price instead:

```html
<div class="price-single">
  <div class="ps-main">4 500 $<small style="font-size:13px;color:var(--muted)">/mois</small></div>
  <div class="ps-side">Engagement 6 mois. Pour piloter 46 000 $/mois de budget média,
    soit <strong>9,8% du budget géré</strong>.</div>
</div>
```

## Scenarios

Straight from `offer_math.py`. Three columns, assumptions visible, and the word *scénario* — never *garantie*.

```html
<table class="tbl">
  <thead><tr><th>Scénario</th><th>Budget média</th><th>CA mensuel</th><th>Contribution nette</th></tr></thead>
  <tbody>
    <tr><td>Prudent — budget constant</td><td>40 000 $</td><td>200 000 $</td><td>78 900 $</td></tr>
    <tr class="win"><td>Base — +15% budget, −3% efficacité</td><td>46 000 $</td><td>215 000 $</td><td>82 200 $</td></tr>
    <tr><td>Ambitieux — +35% budget, −8% efficacité</td><td>54 000 $</td><td>231 500 $</td><td>84 400 $</td></tr>
  </tbody>
</table>

<div class="assumption">
  <h4>Hypothèses</h4>
  <ul>
    <li>Marge brute constante à 62% (fournie par le client)</li>
    <li>Baseline = moyenne mensuelle des 12 derniers mois</li>
    <li>Scénarios calculés à partir des données du compte, hors saisonnalité exceptionnelle</li>
    <li>Ce sont des projections, pas des engagements de résultat</li>
  </ul>
</div>
```

## Timeline

Dates, not durations — a dated plan is checkable, which is exactly why it's reassuring.

```html
<div class="timeline">
  <div class="tl-item">
    <div class="tl-when">Semaines 1–2 · sept.</div>
    <div class="tl-title">Audit technique et restructuration</div>
    <div class="tl-body">Correction du tracking, refonte de l'architecture des campagnes.</div>
    <div class="tl-out"><strong>Livrable :</strong> compte restructuré, tracking validé</div>
  </div>
  <div class="tl-item">...</div>
</div>
```

## Data-gap note

What you couldn't see. Naming it costs nothing and prevents the client discovering a hole in the audit on their own.

```html
<div class="note gap">
  <strong>Périmètre de l'audit :</strong> Meta Ads et Triple Whale uniquement.
  Google Ads et Klaviyo n'ont pas été consultés — les constats ci-dessus ne
  couvrent pas ces canaux.
</div>
```

## Terms and signature

```html
<div class="terms-grid">
  <div class="term"><span class="t-key">Durée</span><span class="t-val">6 mois</span></div>
  <div class="term"><span class="t-key">Préavis</span><span class="t-val">30 jours</span></div>
  <div class="term"><span class="t-key">Facturation</span><span class="t-val">Mensuelle, à 15 jours</span></div>
  <div class="term"><span class="t-key">Budget média</span><span class="t-val">Payé directement par le client</span></div>
  <div class="term"><span class="t-key">Offre valable jusqu'au</span><span class="t-val">12 septembre 2026</span></div>
  <div class="term"><span class="t-key">Démarrage</span><span class="t-val">1er septembre 2026</span></div>
</div>

<div class="sign">
  <div class="sign-box">
    <div class="sb-role">Pour TPS Digital Services</div>
    <div class="sb-name">Nom · Fonction</div>
    <div class="sb-line">Date et signature</div>
  </div>
  <div class="sign-box">
    <div class="sb-role">Pour le client</div>
    <div class="sb-name">Nom · Fonction</div>
    <div class="sb-line">Date, signature et mention « bon pour accord »</div>
  </div>
</div>
```

## Layout helpers

`.page-break` forces a new page before an element (use before Investissement so the price starts a page). `.no-break` keeps a block from splitting across pages — worth putting on `.price-grid`, `.value-box` and `.sign`.
