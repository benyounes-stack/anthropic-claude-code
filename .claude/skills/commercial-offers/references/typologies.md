# Typologies — client type × deal type → offer archetype

The **situation verdict** (`diagnostic.md`) decides what the offer fixes. The typology below decides which metrics it speaks in, what the client's real constraint is, and what a fair fee looks like relative to their business.

Use them together: verdict = the argument, typology = the language.

---

## Client typologies

### Ecom DTC (Shopify) — the default here
**Speaks in:** MER / blended ROAS, CAC, AOV, contribution margin, repeat rate, LTV:CAC.
**Real constraints:** creative volume, margin after COGS+shipping, stock, seasonality.
**Data available:** the full stack — Meta + Triple Whale + Shopify. The richest audits, so the highest standard of proof expected.
**Fee reality:** carries a retainer well above ~15–20k$/month of media. Below that, media budget can't absorb agency fees and the offer should be lighter (project, sprint, or a smaller scope).
**Watch:** an impressive ROAS on a 25%-margin product is a loss. Always convert to contribution.

### Marketplace-dependent (Amazon, Etsy, resellers)
**Speaks in:** TACOS, buy-box share, marketplace fees, blended margin across channels.
**Constraint:** the platform owns the customer relationship; margin is squeezed from both ends.
**Angle:** the offer is usually about **building the owned channel** (DTC site, email list, brand demand) to reduce platform dependence — a strategic sale, not a media-buying one.

### Retail / omnichannel / local physical
**Speaks in:** footfall, in-store attribution, catchment radius, cost per visit, in-store conversion.
**Constraint:** online metrics understate reality — a large share of the return is offline and invisible to the pixel.
**Angle:** never quote online ROAS alone; it makes their ads look worse than they are and prices your work below its value. Sell measurement (offline conversions, promo codes, surveys) as an early phase, then media.

### Lead gen / B2B services
**Speaks in:** CPL, lead→SQL rate, close rate, deal value, sales-cycle length, cost per acquired client.
**Constraint:** lead *quality* and the sales team's ability to work them — not lead volume.
**Angle:** an offer that only promises cheaper leads is weak and easily undercut. The strong offer connects ad spend to closed revenue, which requires CRM data — ask for it, and if it's absent, sell the tracking chain as phase 1.
**Watch:** long cycles mean results land after month 3. Structure the commitment accordingly, and never promise in-month ROI.

### SaaS / subscription
**Speaks in:** CAC payback (months), MRR/ARR, churn, trial→paid, LTV:CAC.
**Constraint:** payback period and cash. A CAC that pays back in 14 months is unfundable regardless of LTV.
**Angle:** offers are judged on payback and cohort quality, not ROAS. Performance clauses should key on paid conversions or retained MRR, never on trials.

### Local service business (clinic, salon, restaurant, trades)
**Speaks in:** cost per call/booking, no-show rate, revenue per client, capacity utilization.
**Constraint:** **capacity** — a fully-booked calendar cannot absorb more leads, and selling them more is selling harm.
**Angle:** small budgets, so keep the offer light and operational. Often the honest answer is a smaller scope than the user hoped to sell; a right-sized offer that renews for two years beats an oversized one that churns in three months.

### Info products / coaching / education
**Speaks in:** cost per lead, webinar/VSL conversion, refund rate, cash collected vs revenue billed.
**Constraint:** offer strength and creative angle dominate; media buying is secondary.
**Watch:** volatile, refund-heavy, and sometimes compliance-sensitive. Price with the volatility in mind (shorter commitment, higher base) and keep claims conservative.

### Creator / influencer brand
**Speaks in:** organic-to-paid ratio, whitelisting performance, launch spikes, community size.
**Constraint:** revenue is spiky and tied to the creator's own activity; paid amplifies, it doesn't create demand.
**Angle:** sell the flattening of the curve — evergreen acquisition between launches — plus creative systemization so growth isn't hostage to the founder's posting schedule.

---

## Deal types

### New business (cold or warm prospect)
Burden of proof is entirely on you: they have no reason to trust you. Lead with the diagnostic — findings in *their* account are the only credible currency before a track record exists. Keep phase 1 small and provable; the goal of a first offer is a first yes, not the biggest possible contract.

### Renewal
The trap is re-selling what they already have. A renewal must show **what was delivered** (facts, from the data) and then propose what changes next period — new objective, new phase, adjusted scope. A price increase needs a reason stated in the same document: scope grew, spend grew, or results earned it.

### Upsell / expansion
The strongest offer type, and the one most often botched by bundling. Isolate the new service, justify it with a finding, price it on its own so the client can say yes to the addition without reopening the existing contract. Never repackage the whole relationship to slip an increase past them — clients notice, and it costs trust worth more than the increase.

### Win-back
Name the reason they left, in the offer, before they think it. Unaddressed history is the objection that kills these silently. Then show what changed — in your method, or in their account since. Lower-risk structure (shorter commitment, tighter first phase) does the work here.

### Rescue (unhappy client, churn risk)
This is not a commercial offer with a diagnostic bolted on; it's a diagnostic with a commercial proposal at the end. Acknowledge the gap between promised and delivered plainly, show the corrected plan with dates, and make the terms explicitly less risky for them. A discount alone doesn't rescue anything — it confirms the work was overpriced.

### Repricing (same scope, new price)
The offer's whole job is justifying the delta: what has changed since the last price — their spend, the scope, the market, or the results. Show the fee as a share of what it manages (`offer_math.py` outputs exactly these ratios) rather than as a raw number; a fee that dropped from 12% to 6% of gross profit while results improved argues for itself.

---

## Choosing the archetype

The archetype is the intersection: **verdict × typology × deal type**, then sanity-checked against the season.

> Ecom DTC · acquisition-dependent-no-retention · upsell · February
> → offer archetype: *"Activer le deuxième achat"* — CRM/lifecycle add-on, priced standalone, sized on the repeat-rate gap found in Triple Whale, phased to be live before the spring peak, justified by revenue that requires no additional media budget.

That one line should be writable before you open the HTML template. If it isn't, the audit or the interview is incomplete — go back rather than compose around the gap.
