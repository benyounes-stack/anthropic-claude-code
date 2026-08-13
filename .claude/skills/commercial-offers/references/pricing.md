# Pricing

Two rules govern everything here.

**One: never invent the agency's own prices.** They live in `rate_card.json`. If it's unconfigured, ask the user for their real numbers and write them into that file — it's a one-time cost that makes every future offer consistent. A price you made up will be quoted to a client, and the user will discover it in a negotiation.

**Two: the price must be defensible from the client's economics, not from a price list.** The rate card says what the agency charges; `offer_math.py` says whether this particular client can carry it. When they disagree, the client's economics win — either resize the scope, or change the model.

---

## The models

### Fixed retainer
Predictable both ways, simplest to sign, easiest to defend when the value is ongoing work.
**Fits:** established relationships, stable spend, scopes with steady output (media buying + creative + reporting).
**Weak spot:** the client feels it in a bad month. Mitigate by attaching the retainer to committed deliverables, not to hours.

### Retainer + performance
A lower base plus a percentage of incremental revenue, or a bonus on hitting a target.
**Fits:** the *profitable-and-scalable* verdict, and clients who resist a full retainer.
**Non-negotiable design points:** define the baseline period explicitly and in writing, pay on **incremental** revenue above it (never total revenue), key it on a metric both sides can verify — **MER or blended ROAS beats attributed ROAS**, which is arguable by definition — and cap it, so a viral month doesn't produce an invoice the client refuses to pay. An uncapped performance clause is a future dispute.
**Never** promise a guaranteed result to secure the deal.

### Percentage of ad spend
Familiar to media buyers, scales with the account.
**Fits:** large, stable budgets.
**Weak spot:** the incentive points the wrong way — you're paid more for spending more, which the client will name. If you use it, expect that objection and answer it with a floor + a profitability guardrail in the same clause.

### Project / sprint (fixed fee, fixed deliverable)
An audit, an account restructure, a creative batch, a tracking rebuild, a Q4 preparation.
**Fits:** cold prospects (low-commitment first yes), rescue phases, and anything with a clear end state.
**Strategic use:** the best entry point in the calendar. A paid audit that converts to a retainer is a far higher-probability sale than a 12-month contract to someone who has never worked with you.

### Hybrid / phased
Different structure per phase — e.g. fixed-fee diagnostic month 1, then a retainer from month 2 once scope is known.
**Fits:** uncertain situations, most rescues, and any offer where you'd otherwise be pricing blind. It also protects the user: quoting a 12-month scope for an account you've seen for 20 minutes is how unprofitable contracts happen.

---

## Commitment, discounts, indexation

- Longer commitment earns a discount, never the reverse. Present it as a choice (mensuel / 3 mois / 6 mois) — offering the client a decision they control raises the odds one of them is yes.
- Keep the discount meaningful but modest (roughly 5–15%); a large one implies the base price was arbitrary.
- If the fee is indexed on spend or revenue, define the floor, the ceiling, and the review cadence. Unbounded indexation is a dispute waiting to happen.
- Onboarding/setup fees are legitimate when there's real front-loaded work (audit, account restructure, tracking). Name the work, don't call it "frais de dossier".
- Everything the client must supply — budget, access, product feed, brand assets, response time — belongs in the offer, in writing. Half of failed mandates fail there, and the clause protects the user more than the client.

---

## The sanity checks (run `offer_math.py`, then read the flags)

The script computes these; your job is to act on them.

| Check | Why it matters |
|---|---|
| **Fee vs gross profit** | A fee eating a large share of the client's monthly gross profit won't survive the first slow month, whatever they said when signing. |
| **Fee vs media budget** | A retainer that dwarfs the media budget makes the client feel they're paying for management rather than results. Below roughly 3× fee in media, restructure or descope. |
| **Required uplift to break even on the fee** | The most useful number in the whole offer: *"l'accompagnement s'autofinance à +6,4% de CA"*. If that figure is large, the offer is a hard sell — and you know it before the client does. |
| **Profitability before the fee** | If the client is below breakeven MER already, adding a fee makes it worse. The offer must fix economics first; scaling scope here is indefensible. |
| **Margin known?** | No margin → no profit claims, projections stay at revenue level, and the assumption is stated in the PDF. |

A `blocker` flag means the offer as sized cannot be defended. Resize it, change the model, or tell the user the deal isn't worth taking at that price. Passing the flag along and pricing anyway defeats the point of computing it.

---

## Presenting the price

- **Three options beat one.** Essentiel / Croissance / Performance — same diagnostic, three depths. The question shifts from *whether* to *which*, and the middle option is chosen far more often than a single option is accepted. Make each one coherent on its own; a deliberately crippled cheap tier reads as manipulation.
- **Anchor against the money in play**, not against nothing: the fee next to the media budget it manages, or next to the recoverable waste identified in the audit. "3 500 $/mois" is abstract; "3 500 $/mois pour piloter 45 000 $ de budget média et récupérer ~14 000 $/trimestre de dépense inefficace" is a decision.
- **Always show what's *not* included.** It protects the user in month four and reads as confidence, not restriction.
- **State validity and terms**: offer valid until [date], payment terms, notice period, start date.
- **Never show your cost or margin** in a client-facing document.

---

## The walk-away price (internal brief only)

Every offer needs a floor the user knows before the call: the price below which this client isn't worth serving, given the work the audit revealed. Put it in the internal brief with the reasoning — expected workload, account condition, client difficulty, strategic value.

Also list, in order, what to concede: scope depth first, commitment length second, price last. A user who concedes price first has nothing left to trade, and teaches the client that the number was never real.
