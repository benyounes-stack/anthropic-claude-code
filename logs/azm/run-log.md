# AZM weekly report — run log

One line per weekly cycle. Append a row every Friday, whether or not the report
went out — a week with no entry is indistinguishable from a week nobody did.

Columns: reporting date · period covered · where it was posted · who ran it · outcome.

| Ran on | Period | Posted to | By | Outcome |
| - | - | - | - | - |
| 2026-08-28 | 2026-08-21 → 2026-08-27 | Slack draft only (`#client-az-motorsport`) | benyounes | ❌ Never sent. Drafted after the 1PM call was cancelled, left in drafts. |
| 2026-09-04 | 2026-08-28 → 2026-09-03 | Slack draft (`#client-az-motorsport`) + Alfredify | benyounes | ⏳ Alfredify posting blocked — no API credentials in the session (see SKILL.md § Alfredify). |

## Known gaps carried week to week

These distort every report until they are closed. Repeat them in the client
report rather than quietly reporting around them.

- **Site tracking incomplete** — the pixel only sees on-site checkouts. DM sales
  and manual invoices (~65% of this store's revenue) are invisible, so
  `revenue_pixel` is a floor, never the real number. Ask the client to confirm
  actual sales each week until this is fixed.
- **Google Ads spend not in blended** — Triple Whale shows Meta spend only.
- **Retargeting audiences broken** — site-visitor audiences hold ~20 people
  against 3 103 ViewContent in 30 days, so no retargeting is possible.
