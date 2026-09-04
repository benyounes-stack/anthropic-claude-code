---
name: azm-weekly-report
description: Produce the Friday weekly report for AZ Motorsport (client "azm") — pull the week's Meta Ads numbers, log them, render the client-facing recap, and post it to Slack and Alfredify. Use when the user asks for the AZM weekly report, the AZ Motorsport recap, "le report de la semaine" for azm, or asks to log/refresh AZM's weekly metrics. The same procedure works as a template for another client's weekly report — change the account id, the channel and the log directory.
---

# AZM weekly report

A Friday ritual with a memory. Every week's numbers land in an append-only log
first, and the report is rendered from that log — so week-over-week deltas are
computed from recorded data instead of being re-derived by hand, and last
week's report is still readable next month.

## Fixed facts

| | |
| - | - |
| Client | AZ Motorsport (`azm`), contact Tommy / Loveon |
| Meta ad account | `1442672066309406` (business `azmotorsport`), USD, **Pacific time** |
| Client Slack channel | `#client-az-motorsport` (`C0AM95WBXFD`) — written in English or French, the client reads both |
| Internal Slack channel | `#tps-az-motorsport` (`C0AMDFXKQKG`) |
| Alfredify | board linked to the AZM Meta ads account (marketing tasks; dev/site tasks live on the AZ Motorsport *project* board) |
| Log | `logs/azm/weekly-metrics.jsonl`, `logs/azm/reports/`, `logs/azm/run-log.md` |
| Script | `scripts/azm_weekly_log.py` |

**Reporting week runs Friday → Thursday.** The Friday report covers the seven
completed days before it, so a report produced on Friday 2026-09-04 covers
2026-08-28 → 2026-09-03. A week is identified by its `period_end`.

⚠️ Check today's real date before choosing the window. Don't infer it from the
last Slack message you read — that mistake shipped a week-old report once
already (see `logs/azm/run-log.md`, 2026-08-28).

## Procedure

1. **Pull the week** with the Meta Ads MCP tools. Account level for the
   headline, then campaign and ad level to explain it:

   ```
   ads_get_ad_entities(ad_account_id="1442672066309406", level="ad_account",
     time_range='{"since":"<start>","until":"<end>"}',
     fields=["amount_spent","impressions","reach","frequency","clicks","ctr",
             "cpc","cpm","purchase_roas","omni_purchase","link_click",
             "landing_page_view"])
   ```

   Field names are not guessable — `spend` resolves to `amount_spent`,
   purchases are `omni_purchase`, and `purchases`/`purchase_value` don't exist.
   Run `ads_get_field_context` on anything new before querying.

   `purchase_roas` comes back `null` when nothing was attributed. Revenue is
   derived: `spend × purchase_roas` (record it as derived, it is not a field).

2. **Log it** — build the record and append:

   ```bash
   python3 scripts/azm_weekly_log.py add --file week.json
   python3 scripts/azm_weekly_log.py table     # sanity-check the deltas
   ```

   Re-running a week is refused unless you pass `--replace`, so a re-pull can't
   silently create two versions of the same week.

3. **Render and write the report**:

   ```bash
   python3 scripts/azm_weekly_log.py report --write   # -> logs/azm/reports/<period_end>.md
   ```

   The script fills the metrics table, the créatifs list and the tracking
   caveat, and leaves `<!-- TODO -->` markers for the narrative sections. Fill
   those from the internal channel and the connectors — Google Ads status, Nate's
   Search Console numbers, creative deliveries, dev tasks, Klaviyo. Never leave a
   TODO in what you send.

4. **Post to Slack** — `slack_send_message_draft` on `#client-az-motorsport`,
   never `slack_send_message`. The report goes out only once a human has read
   it. Tell the user it's in drafts and let them send.

5. **Post to Alfredify** — see below.

6. **Append a row to `logs/azm/run-log.md`**, including the weeks where the
   report did not go out and why. A missing row reads as "nobody did it".

## Tone

The client reads plainly and dislikes filler. Short lines, contractions, no
agency vocabulary — `on la coupe` beats `nous procédons à une désactivation`.
Say the bad week out loud in the first two lines; a recap that buries a zero
under a good CTR is the one that destroys trust.

Never send a number the log can't back. And every time you show pixel revenue,
repeat that DM and manual-invoice sales aren't in it — for this store that's
roughly two thirds of the revenue, so the pixel number is a floor, not a result.

## Alfredify

Alfredify (`alfredify.com`) is where the team's logs and kanban boards live, and
Zack pulls his data from it: what isn't logged there didn't happen. An API
exists (Zack: it can create tasks but not projects), but:

**⚠️ This session has no Alfredify credentials and no Alfredify MCP connector,
and no public API surface is reachable at `alfredify.com/api*` unauthenticated.**
Until that's provided, produce the payload and hand it over instead of pretending
it posted:

```bash
python3 scripts/azm_weekly_log.py payload > /tmp/azm-week.json
```

The payload carries the period, metrics, previous week, computed deltas, top ads,
notes and the rendered markdown body, under generic key names (`title`, `body_markdown`,
`metrics`, `period`) so they can be mapped onto whatever the endpoint expects.

To wire the posting up, what's needed is: the base URL, the auth method (API key
header / bearer token / session), the board or project id for AZM, and the task
or log-entry endpoint shape. Add them as environment variables (never commit a
token) and extend `scripts/azm_weekly_log.py` with a `post` subcommand.

## Files

- `scripts/azm_weekly_log.py` — add / table / report / payload. Stdlib only, no network.
- `logs/azm/weekly-metrics.jsonl` — one record per week, append-only.
- `logs/azm/reports/<period_end>.md` — the report as sent, with front-matter status.
- `logs/azm/run-log.md` — one row per weekly cycle + the standing measurement gaps.
