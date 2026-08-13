# Qualification — the interview

The interview exists to prevent the two ways an offer fails: **priced wrong** (you didn't know what they can pay or what they're paying now) and **scoped wrong** (you didn't know what they actually want or who has to approve it).

It runs in **two rounds on purpose**. Round 1 is before the data, so you know which accounts to pull and what "good" looks like for this client. Round 2 is after the data, so you can ask the sharp questions — "your November CPA doubled, was that the stock issue or a targeting change?" — instead of generic ones. Asking everything up front wastes the user's attention on questions the data would have answered for free.

## How to ask

Use `AskUserQuestion`, up to 4 questions per call, **at most 2 calls per round**. Write options that are real answers, not categories — "3 000–8 000 $/mois" beats "budget moyen". Always leave room for "je ne sais pas / à confirmer avec le client": a forced guess is worse than a known gap, because a guess silently becomes a number in the PDF.

Three things to respect:
- **Skip what you already know.** Mine the conversation, the account data, and previous offers in the repo first. Re-asking is the fastest way to make the user stop using the skill.
- **Ask what changes the output.** If both answers lead to the same offer, don't ask.
- **Ask, don't interrogate.** ~8 questions total across both rounds is the target. If you're reaching for a 12th, you're collecting trivia.

When the user answers "je ne sais pas" on something load-bearing (margin above all), don't quietly substitute an assumption. Carry it into the offer as a stated assumption — `references/components.md` has the `.assumption` block for exactly this — and flag it in the internal brief as a question for the call.

---

## Round 1 — before the data

### 1. Deal type
> Ce client, c'est quoi exactement ?

`Nouveau prospect (jamais travaillé ensemble)` · `Client actuel — renouvellement` · `Client actuel — upsell / extension de scope` · `Ancien client — reconquête` · `Client en difficulté / risque de churn`

**Changes:** the entire offer architecture, the tone, whether you can quote your own past results, and whether price can go up. See `references/typologies.md`.

### 2. Access to their data
> Qu'est-ce que j'ai comme accès pour analyser ?

`Compte Meta + Triple Whale/Shopify` · `Meta seulement` · `Screenshots / exports fournis par le client` · `Aucun accès — prospect froid`

**Changes:** which audit path in `data-audit.md`, and how strong the offer's claims can be. Get the ad account name/ID and the Shopify domain here — with 50+ accounts on this Meta user, guessing is a real risk.

### 3. Their objective, in their words
> L'objectif principal du client sur les 6–12 prochains mois ?

`Scaler le volume (plus de CA)` · `Améliorer la rentabilité (marge/MER)` · `Baisser le CAC / acquérir mieux` · `Lancer un produit / un marché` · `Sortir d'une mauvaise passe`

**Changes:** which findings you lead with. A profitability-driven client doesn't want to hear about scaling budgets, even if the account can take it.

### 4. Current spend and what they pay today
> Budget média mensuel actuel, et ce qu'ils paient en frais d'agence/freelance aujourd'hui ?

Free-form is fine here. **Changes:** everything about pricing. An offer that lands 3× above their current agency fee needs a different structure (and a much stronger diagnostic) than one that lands 20% above. Not knowing the incumbent's price is the single most common reason an offer gets rejected without a counter.

### 5. Decision process — ask when the deal is more than a routine renewal
> Qui signe, et sur quoi ils vont juger ?

`Le fondateur, décision rapide` · `Fondateur + associé/CFO` · `Comité / plusieurs parties prenantes` · `Je ne sais pas encore`

**Changes:** length and shape. A CFO wants payback and downside; a founder wants the plan and the person. Multiple stakeholders means the PDF must stand alone without the user in the room to narrate it.

---

## Round 2 — after the data, before pricing

Now the questions are specific. Quote the number you found in the question itself — that's what turns an interview into a consultation.

### 6. Gross margin — always ask, never assume
> Marge brute moyenne (après COGS, avant pub) ? J'en ai besoin pour parler profit et pas juste CA.

`> 70% (services / digital / cosmétique premium)` · `50–70%` · `30–50%` · `< 30% (retail, revente, marketplace)` · `Je dois demander au client`

**Changes:** breakeven MER, payback, and whether the offer can make profit claims at all. Without it, `offer_math.py` refuses profit-level outputs and every projection stays at revenue level — which is a much weaker offer. Fight for this number.

### 7. The anomaly you found
> [Mois X], le [CPA/ROAS/spend] a [bougé de Y%] — tu sais ce qui s'est passé ?

Free-form. **Changes:** whether a dip is a structural problem you're selling a fix for, or a stock-out/seasonal event you'd look foolish diagnosing as a targeting failure. This question also catches the trap where the user's own agency caused the anomaly.

### 8. Capacity to absorb growth
> Si on double le volume, ils suivent ? (stock, logistique, SAV, capacité de production)

`Oui, sans problème` · `Oui avec du délai de prod` · `Stock limité / précommandes` · `Non — c'est le vrai goulot`

**Changes:** whether the offer sells *more volume* or *more margin on the same volume*. Selling scaling to a client who can't ship it is how a signed contract becomes a churn in month three.

### 9. Budget appetite for the fee
> Ils ont un budget en tête pour l'accompagnement ? Ou un plafond à ne pas dépasser ?

Free-form, and it is fine to answer "aucune idée" — the guardrails in `offer_math.py` will bound the fee against the client's own economics instead.

### 10. Commitment and start date
> Engagement envisagé, et démarrage souhaité ?

`Mensuel sans engagement` · `3 mois` · `6 mois` · `12 mois` · `Projet ponctuel`

**Changes:** price (commitment buys a discount, see `pricing.md`), how the roadmap is phased, and whether the offer must show results inside a trial window. Cross-check the start date against `seasonality.md` — starting a Q4 ecom mandate on October 20 means the ramp-up is already too late to sell as a Q4 play, and pretending otherwise sets up a failure.

---

## When the user won't do the interview

Sometimes the answer is "j'ai pas le temps, sors-moi l'offre". Respect it: pull whatever data access allows, build the offer on the data plus explicit assumptions, and hand back a short list — "j'ai supposé X, Y, Z ; corrige-moi et je régénère". Assumptions in an offer are recoverable. Waiting for answers that never come is not.
