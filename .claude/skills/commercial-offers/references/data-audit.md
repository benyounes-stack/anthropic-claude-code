# Data audit — the tool playbook

The audit has one job: produce a handful of numbers strong enough that the offer's price stops being a matter of opinion. Twelve well-chosen figures beat a 40-row dump — you're building an argument, not a dashboard.

Budget roughly 10–20 tool calls. Pull at the granularity the argument needs and stop.

---

## 0. Before anything: which client, which accounts?

This is where audits go wrong in practice. This Meta user has **50+ ad accounts** spread across many businesses, in CAD / USD / EUR / DZD, and a good share are `DISABLED` or `CLOSED`. Triple Whale is authorized for **one store at a time** — whichever the user selected when connecting it.

So, in order:

1. `ads_get_ad_accounts` — match the client name against `ad_account_name` **and** `business_name` (the account name is often blank or an internal codename like "Adam Gagne x DS CC 2"). Paginate with `next_cursor` if you don't find it on page one.
2. Check three fields before using an account: `is_ads_mcp_enabled` (false → not usable via MCP), `is_queryable` (false → surface `not_queryable_reason` instead of calling), `account_status` (`DISABLED`/`CLOSED`/`UNSETTLED` → the account state is itself a finding worth raising).
3. **Confirm ambiguity with the user rather than guessing.** Several accounts under one business, or two plausible name matches, means asking "c'est bien le compte X (ID …, EUR) ?". An audit of the wrong account is worse than no audit.
4. Note the **currency** and never mix currencies in one figure. If the client runs EUR and CAD accounts, report them separately or convert once with an explicitly stated rate.
5. `get-shop-info` (Triple Whale) — **verify the connected store is this client.** If `shopName`/`shopId` is a different client, Triple Whale data is unavailable for this offer: tell the user to reconnect Triple Whale with the right store, and build the offer from Meta + interview instead. Never present another store's numbers.

Two mechanical notes on the Meta tools: every call takes `client_conversation_id` — generate one 20-character alphanumeric id and reuse the identical value for every Meta call in the session. And `advertiser_request` must carry the user's own words, quoted, not your paraphrase.

---

## 1. Meta Ads — what to pull

Default window: **last 12 months** with `time_increment: "monthly"`, so you see seasonality and trend instead of a snapshot. Add a recent 30-day window when the offer hinges on current state.

| Call | Why it earns its place in an offer |
|---|---|
| `ads_get_ad_entities` level `ad_account`, monthly, 12 months | The spine: spend, revenue, ROAS, CPA, CPM, CTR per month. Trend + seasonality + best/worst month in one call. |
| `ads_get_ad_entities` level `campaign`, sorted by spend desc | Where the money actually goes. Budget concentration and the underperformers are the scope of half the offers you'll write. |
| `ads_get_ad_entities` level `campaign`, sorted by the KPI **ascending** | The tool truncates results — to show both the best and the worst you need two calls with opposite sort directions. The worst campaigns are the ones that justify the fee. |
| `ads_get_ad_entities` level `ad`, top spenders | Creative concentration: if 80% of spend sits on 2 ads, creative production is the offer. |
| `ads_get_opportunity_score` | Meta's own account-level recommendations. Independent third-party backup for your diagnostic — useful precisely because it isn't your opinion. |
| `ads_insights_performance_trend` | Direction of CPC/CPM/CPR/ROAS/CTR over time — separates "the account got worse" from "the auction got more expensive". |
| `ads_insights_industry_benchmark` | Peer comparison. Handle with care: only compare cost-per-result between similar optimization goals, and label it as a benchmark, not as the client's number. |
| `ads_get_errors` | Delivery-blocking errors. A rejected ad or a broken pixel is an immediate, concrete, provable finding. |
| `ads_insights_advertiser_context` | Funnel/objective overview when you don't know the account. |

Verify field names with `ads_get_field_context` before a large `fields` list — a rejected call costs more than the check.

**Creative-level detail** (hook rate, hold rate, thumbstop) needs explicit ad-level fields; it isn't in campaign-level output. Only pull it if creative is part of the offer.

---

## 2. Cold prospect — the public path

No account access is not "no audit". It's a narrower one, and saying so plainly is more credible than vagueness:

- `ads_library_search` — their live ads: how many, which formats, which angles, **how long each has been running** (a creative live for 8 months in a scaling account usually means creative production has stalled — a finding you can build an offer on). Also run it on 2–3 competitors the user names: "voici ce que font X et Y, voici ce que vous ne faites pas" is the strongest cold-prospect page you can write.
- `ads_get_ad_accounts` — worth a check anyway; the user may already have partner access without realizing.
- Their storefront (WebFetch): product range, price points, offer structure, whether there's a bundle/subscription, what the PDP promises. Price point × plausible margin tells you what fee the business can carry.
- Public signals: review counts as a proxy for order volume, job posts, recent launches.

State the basis explicitly in the PDF: *"Audit réalisé sans accès au compte publicitaire, à partir de la bibliothèque publicitaire Meta et du site."* Then make the audit itself the first deliverable of the offer — it converts a weakness into a paid step.

---

## 3. Triple Whale — attribution, blended economics, and the Shopify layer

There is **no direct Shopify connector** in this session. Shopify data reaches you through the Triple Whale warehouse (`orders_table`, `customers_table`, `products_table`, `refunds_table`, `subscriptions_table`, …). If Triple Whale isn't connected for this client, Shopify-level facts must come from the client (export, screenshot) or be left out — do not infer them.

Sequence:

1. `get-shop-info` — store, currency, timezone, attribution model/window, industry, GMV segment. Everything downstream depends on these.
2. `get-summary-kpis` with `compareStartDate`/`compareEndDate` — **prefer this over SQL for topline**: Blended ROAS, MER, Net Profit, new-customer CPA, total sales, blended spend, computed with the shop's own configured formulas and costs. SQL cannot reproduce those, and a number that matches what the client sees in their own dashboard is worth far more in a negotiation than one you derived yourself.
3. `pixel-attribution` broken down by `channel` or `source` — the blended picture: what Meta is really worth next to email, organic, Google. This is where "vous surpayez l'acquisition et sous-exploitez la rétention" gets proven.
4. `explain-metric-change` for any anomaly worth diagnosing ("pourquoi le ROAS a chuté en mars ?"). Slower than other calls; use it once, on the anomaly that matters to the offer.
5. Only then SQL, and only for what the purpose-built tools can't give you: `get-available-tables` → `get-table-schemas` (never reference a column whose schema you haven't fetched) → `find-sql-examples` → `get-date-range` for any relative date → `run-sql`.

Two SQL rules that bite: **every table needs an explicit `event_date` filter** or results silently default to the last 7 days, and results are capped (200 rows default, 500 max) — aggregate with `GROUP BY` rather than trying to page.

Questions worth one query each, when they're load-bearing for the offer:
- New vs returning revenue split and AOV per group (`orders_table`) — the retention argument.
- Repeat rate and time-to-second-order — sizes the retention/CRM opportunity in dollars.
- Revenue concentration by product (`product_analytics_tvf`) — one-product dependency is a risk you can price against.
- Refund rate (`refunds_table`) — quietly destroys apparent ROAS, and clients rarely factor it in.
- Email/SMS share of revenue (`email_sms_table`) — the most common cheap win in a DTC offer.
- Subscription/LTV signals (`subscriptions_table`) when relevant.

---

## 4. Attribution — the trap that voids an offer

Meta's reported ROAS and Triple Whale's attributed ROAS **are not the same metric** and are structurally different in magnitude. Blending them, or comparing a target set in one to a result measured in the other, produces claims that fall apart the moment the client checks.

In the offer: keep them in separate labeled lines ("ROAS Meta déclaré 4,2× · ROAS attribué Triple Whale 2,6×"). Better yet, **anchor objectives on MER / blended ROAS** — it is the one figure both parties can verify without arguing about attribution windows, which makes it the safest thing to sign a performance clause against.

---

## 5. Closing the audit

Before moving to the diagnostic, write down — in chat, for yourself — the **6 to 10 numbers** the offer will actually stand on, each with its source and period. Everything else was reconnaissance. If a number can't survive the client asking "where does this come from?", it doesn't go in the PDF.

Also note what you couldn't see. That list becomes the `.note.gap` block in the offer and the "à confirmer" section of the internal brief.
