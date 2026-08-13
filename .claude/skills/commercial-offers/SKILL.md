---
name: commercial-offers
description: Build a data-backed commercial offer, proposal, quote or renewal — "offre commerciale", "proposition commerciale", "devis", "proposal", "pitch", "upsell", "renouvellement", "je dois closer ce client" — for any client typology (ecom DTC, retail/omnicanal, lead gen/B2B, SaaS, local, marketplace, influence) and any moment of the year. Starts by interviewing the user with the questions that actually change the offer, then audits the client's real numbers (Meta ad accounts via the Facebook MCP, Shopify + Triple Whale via the Triple Whale MCP, or public signals like the Meta Ads Library for a cold prospect), diagnoses the client's economic situation, sizes scope and price against what that client can actually pay for, and outputs a branded PDF offer plus an internal negotiation brief. Use this whenever the user is preparing something to send a client or prospect to win, renew, expand or reprice work — even if they only say "prépare-moi une offre pour X" or "combien je facture à ce client". Not for delivering performance reports on work already done (that's the custom-reports skill).
---

# Offres commerciales (data-backed commercial offers)

An offer that quotes a price without quoting the client's own numbers is a brochure. This skill builds the opposite: a proposal where **every line of scope answers a finding in that client's account, and the price is checked against what that client's economics can actually carry.**

The value is not in prettier slides — it's in showing up already knowing the client's MER, where their budget leaks, and what the fee buys back. That's what makes an offer hard to negotiate down and safe to sign.

## The one rule that keeps it bullet proof

**Traceability.** Every scope item, every projection, every price must trace back to either (a) a number you actually pulled from that client's data, (b) something the user told you in the interview, or (c) a clearly-labeled assumption. Nothing appears in an offer "because proposals usually have it".

If you can't trace it, cut it or label it. A proposal with four justified services beats one with nine decorative ones — and it survives the client asking "why this line?", which is exactly where offers die.

## Workflow

Work through these in order. Steps 1–4 are what makes step 5 good; skipping the interview to jump straight to a PDF produces a generic offer that will get negotiated on price alone.

### 1. Frame the deal (before any question or data pull)

Establish from the conversation, asking only what's genuinely missing:
- **Who** — client/prospect name, and whether the user already has access to their accounts.
- **Deal type** — new business, renewal, upsell/expansion, win-back, repricing, or rescue (client is unhappy/leaving). These need very different offers; see `references/typologies.md`.
- **Deadline** — is this going out today or is there time for a proper audit? Say what you'll cut if it's rushed.

### 2. Round 1 — the questions data can't answer

Read `references/qualification.md` and run **round 1** with `AskUserQuestion` (batch up to 4 questions per call, 1–2 calls max). These are the cheap questions whose answers change which data you pull and which offer archetype applies — the client's objective, the deal type, who decides, what they're paying today.

Skip anything already answered in the conversation. Interrogating the user for facts they just gave you is the fastest way to make this skill annoying enough to stop using.

### 3. Audit the client's real numbers

Read `references/data-audit.md` — it has the exact tool sequence, the account-selection traps (this user has 50+ Meta ad accounts across clients in CAD/USD/EUR, many disabled; Triple Whale is connected to **one** store at a time), and what to pull per source.

Three access levels, all supported:
- **Full access** — Meta ad account(s) + Triple Whale/Shopify connected → the complete audit.
- **Partial** — e.g. Meta only, or the client sent a screenshot/export → audit what's there, name what's missing.
- **Cold prospect, no access** — use the public path: Meta Ads Library (`ads_library_search`) for their live creatives and how long they've been running, their storefront, whatever the user learned on the discovery call. This is a real audit, just a narrower one — say so in the offer rather than pretending to have seen the account.

Never present a number from one source as if it came from another, and never blend platform-reported ROAS with Triple Whale attribution into a single figure. Different methods, different numbers — label both.

### 4. Diagnose, then ask round 2

Read `references/diagnostic.md` and turn the data into a **situation verdict**: which of the recognizable states this client is in (profitable-and-scalable, spend-flat-margin-eroding, acquisition-dependent-no-retention, seasonal-peak-approaching, structurally-unprofitable-on-paid, account-in-trouble…). The verdict is what selects the offer archetype — not the client's industry.

Then run **round 2** of the interview (`references/qualification.md`): the questions that only make sense once you've seen the data — gross margin, stock/fulfilment capacity, budget appetite, what they'd do with more volume, why the drop in month X. These are also the questions that make the user look prepared when they get repeated on the call.

Margin is the one number to fight for: without it, every profit claim in the offer becomes unsupportable and the projections have to stay at revenue level.

### 5. Size the offer

- **Archetype** from the verdict × typology → `references/typologies.md`.
- **Scope** — pick services from `references/offer-catalog.md`, each attached to the finding it answers. Include a *not in scope* list; ambiguity about what's excluded is where client relationships rot.
- **Season** — read `references/seasonality.md` for where in the year this lands. An offer signed in August for a Q4-heavy ecom client is a different offer than the same scope signed in February, in urgency, phasing and price.
- **Price** — `references/pricing.md` for the model (retainer, retainer + performance, % of spend, project, hybrid) and the agency rate card in `references/rate_card.json`. If the rate card is still unconfigured, ask the user for their real numbers and write them into that file so future offers reuse them. **Never invent the agency's own prices.**

### 6. Run the economics through the script — don't do this arithmetic in your head

```bash
python3 .claude/skills/commercial-offers/scripts/offer_math.py inputs.json -o economics.json
```

It computes MER, breakeven MER, CAC, payback, fee load, **the revenue uplift needed for the fee to pay for itself**, and conservative/base/ambitious scenarios — and it raises guardrail flags (fee too heavy for the client's gross profit, retainer disproportionate to media budget, projections leaning on a margin you never got, client unprofitable before your fee). `python3 scripts/offer_math.py --example` prints a filled input file to start from.

Read the flags before writing a single price into the PDF. A `blocker` flag means the offer as sized is not defensible — resize it or change the model. Reporting a flag to the user and pricing anyway is the failure mode this script exists to prevent.

### 7. Compose and render

Copy `assets/offer_template.html` (don't edit the shared copy), fill the placeholders, and build the body from the blocks in `references/components.md` — cover, diagnostic, scope table, pricing, scenarios, timeline, terms, signature. Branding comes from `references/brand.json`. Then:

```bash
node .claude/skills/commercial-offers/scripts/render_pdf.js offer.html offer.pdf
```

Verify the PDF exists, is non-empty, and has a sane page count before calling it done.

### 8. Deliver both documents

The client-facing PDF **and** a short internal negotiation brief in chat (never inside the PDF):
- the three numbers to lead with on the call,
- the two objections this specific client will raise and the data-backed answer to each,
- what to concede first, and the **walk-away price** below which the work isn't worth taking.

Offer to also draft the covering email. Ask before sending anything to anyone.

## Honesty rules — these protect the user, not the client

An offer is a document someone may sign. Claims in it become obligations.

- **Projections are scenarios, not promises.** Always three (conservative / base / ambitious), always with the assumption stated in the same breath ("à budget constant et marge 62%"), always anchored to that client's own measured baseline — never a benchmark from another account. Never write a guaranteed ROAS, revenue or growth figure.
- **Never fabricate a number.** No invented margins, no plausible-looking CAC, no "industry average" presented as the client's. If it's missing, either ask, or state it as an open assumption the price depends on.
- **Say what you couldn't see.** "Audit basé sur Meta uniquement — Google Ads et Klaviyo non consultés" costs nothing and prevents a projection built on a channel you never looked at.
- **Beware the attribution trap.** If the client's internal target was set in Triple Whale attribution and you're quoting Meta's reported numbers (structurally higher), a "we'll beat your target" claim is arithmetically dishonest. Show both, labeled.
- **Don't let a diagnostic become an insult.** Prospect-facing findings are stated as opportunity ("38% du budget sur des campagnes sous le CPA cible") not as a verdict on their competence. The client may be the person who built those campaigns.

## Files in this skill

| File | Read it when |
|---|---|
| `references/qualification.md` | Before each interview round — the questions, in two rounds, with what each one changes |
| `references/data-audit.md` | Before touching any MCP tool — exact sequences, account-selection traps, per-source checklists |
| `references/diagnostic.md` | After the data, to reach the situation verdict that drives the offer |
| `references/typologies.md` | Client typologies × deal types → offer archetypes |
| `references/offer-catalog.md` | Services, deliverables, and the scope wording that avoids disputes |
| `references/pricing.md` | Pricing models, discount/commitment logic, sanity checks |
| `references/seasonality.md` | Where in the year the offer lands, and how that changes urgency and phasing |
| `references/components.md` | The HTML block catalog for composing the offer |
| `references/rate_card.json` | The agency's own prices — fill it once, reuse forever |
| `scripts/offer_math.py` | Every offer, for the economics and guardrails |
| `scripts/render_pdf.js` | To produce the PDF. Don't reimplement it |
