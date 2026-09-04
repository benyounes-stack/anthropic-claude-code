#!/usr/bin/env python3
"""Weekly reporting log for the AZ Motorsport (azm) Meta Ads account.

One append-only JSONL file holds one record per reporting week, so every weekly
report is reproducible and week-over-week deltas are computed from logged data
instead of being re-pulled (and re-guessed) by hand each Friday.

Subcommands
-----------
  add      Append a week's metrics (JSON on stdin or --file) to the log.
  table    Print the current week vs. the previous week, with deltas.
  report   Render the Slack report skeleton (metrics filled, narrative TODOs).
  payload  Emit the Alfredify-ready JSON payload for a week.

Reporting week runs Friday -> Thursday: the Friday report covers the seven
completed days before it. A week is identified by its `period_end`.

The Meta numbers themselves come from the Meta Ads MCP tools (see
.claude/skills/azm-weekly-report/SKILL.md) - this script never calls an API, it
only stores, compares and renders what was pulled.
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "logs" / "azm" / "weekly-metrics.jsonl"
REPORTS_DIR = REPO_ROOT / "logs" / "azm" / "reports"

# Metrics rendered in the client table, in order: key -> (label, formatter).
TABLE_ROWS = [
    ("spend", "Dépense pub", "money"),
    ("revenue_pixel", "Revenu attribué", "money"),
    ("roas_pixel", "ROAS (pixel)", "ratio"),
    ("purchases_pixel", "Achats (pixel)", "int"),
    ("reach", "Portée", "int"),
    ("link_clicks", "Clics sur lien", "int"),
    ("landing_page_views", "Visites sur le site", "int"),
    ("ctr_all", "CTR", "pct"),
    ("cpc_all", "CPC", "money"),
    ("cpm", "CPM", "money"),
]

# Metrics where a decrease is the good direction.
LOWER_IS_BETTER = {"cpc_all", "cpm", "cost_per_visit"}

# Metrics that are a decision, not a result - a move is neither good nor bad.
NEUTRAL = {"spend", "frequency"}


# --------------------------------------------------------------------------- io


def load(path: Path = LOG_PATH) -> list[dict]:
    """Read every record, oldest first. Missing file means an empty log."""
    if not path.exists():
        return []
    records = []
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: corrupt JSONL record: {exc}") from exc
    records.sort(key=lambda r: r["period_end"])
    return records


def save(records: list[dict], path: Path = LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for record in sorted(records, key=lambda r: r["period_end"]):
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


REQUIRED_FIELDS = ("client", "period_start", "period_end", "source", "metrics")


def validate(record: dict) -> None:
    missing = [f for f in REQUIRED_FIELDS if f not in record]
    if missing:
        raise SystemExit(f"record is missing required field(s): {', '.join(missing)}")
    start = date.fromisoformat(record["period_start"])
    end = date.fromisoformat(record["period_end"])
    span = (end - start).days + 1
    if span != 7:
        raise SystemExit(
            f"period {start}..{end} spans {span} days; a reporting week must span 7"
        )
    if "spend" not in record["metrics"]:
        raise SystemExit("record.metrics must at least carry `spend`")


def find(records: list[dict], period_end: str | None) -> dict:
    """The record for `period_end`, or the most recent one when it is None."""
    if not records:
        raise SystemExit(f"no records in {LOG_PATH}")
    if period_end is None:
        return records[-1]
    for record in records:
        if record["period_end"] == period_end:
            return record
    known = ", ".join(r["period_end"] for r in records)
    raise SystemExit(f"no record for period_end={period_end}. Known: {known}")


def previous(records: list[dict], record: dict) -> dict | None:
    """The record for the week immediately before `record`, if it was logged."""
    expected = (date.fromisoformat(record["period_start"]) - timedelta(days=1)).isoformat()
    for candidate in records:
        if candidate["period_end"] == expected:
            return candidate
    return None


# --------------------------------------------------------------- formatting


def fmt(value, kind: str) -> str:
    if value is None:
        return "—"
    if kind == "money":
        # 1234.5 -> "1 234,50 $" (thin space thousands, comma decimal)
        return f"{value:,.2f}".replace(",", "\u00a0").replace(".", ",") + " $"
    if kind == "int":
        return f"{value:,}".replace(",", " ")
    if kind == "pct":
        return f"{value:.2f} %".replace(".", ",")
    if kind == "ratio":
        return f"{value:.2f}".replace(".", ",")
    return str(value)


def delta(now, before, key: str) -> str:
    """Human-readable week-over-week move, oriented so + always means better."""
    if now is None or before is None:
        return "—"
    if before == 0:
        return "n/a" if now == 0 else "nouveau"
    pct = (now / before - 1) * 100
    arrow = "▲" if pct > 0 else ("▼" if pct < 0 else "=")
    if key in NEUTRAL:
        return f"{arrow} {abs(pct):.0f} %"
    good = pct < 0 if key in LOWER_IS_BETTER else pct > 0
    mark = "" if abs(pct) < 0.5 else (" ✅" if good else " ⚠️")
    return f"{arrow} {abs(pct):.0f} %{mark}"


def cost_per_visit(metrics: dict) -> float | None:
    visits = metrics.get("landing_page_views")
    if not visits:
        return None
    return round(metrics["spend"] / visits, 2)


# ----------------------------------------------------------------- commands


def cmd_add(args) -> int:
    raw = Path(args.file).read_text() if args.file else sys.stdin.read()
    record = json.loads(raw)
    validate(record)
    record.setdefault("pulled_at", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    records = load()
    existing = [r for r in records if r["period_end"] == record["period_end"]]
    if existing and not args.replace:
        raise SystemExit(
            f"week ending {record['period_end']} is already logged. "
            f"Re-run with --replace to overwrite it."
        )
    records = [r for r in records if r["period_end"] != record["period_end"]]
    records.append(record)
    save(records)
    action = "replaced" if existing else "added"
    print(f"{action} week {record['period_start']}..{record['period_end']} in {LOG_PATH}")
    return 0


def cmd_table(args) -> int:
    records = load()
    record = find(records, args.week)
    prev = previous(records, record)
    metrics, before = record["metrics"], (prev or {}).get("metrics", {})

    header = f"{record['client_name']} — {record['period_start']} → {record['period_end']}"
    print(header)
    print("=" * len(header))
    width = max(len(label) for _, label, _ in TABLE_ROWS)
    for key, label, kind in TABLE_ROWS:
        now_s = fmt(metrics.get(key), kind)
        prev_s = fmt(before.get(key), kind) if prev else "—"
        print(f"{label:<{width}}  {now_s:>14}  {prev_s:>14}  {delta(metrics.get(key), before.get(key), key)}")

    cpv_now, cpv_prev = cost_per_visit(metrics), cost_per_visit(before) if prev else None
    print(f"{'Coût par visite':<{width}}  {fmt(cpv_now, 'money'):>14}  {fmt(cpv_prev, 'money'):>14}  "
          f"{delta(cpv_now, cpv_prev, 'cost_per_visit')}")

    if not prev:
        print("\n⚠️  Aucune semaine précédente dans le log — pas de comparaison possible.")
    for note in record.get("notes", []):
        print(f"\nNote: {note}")
    return 0


def cmd_report(args) -> int:
    records = load()
    record = find(records, args.week)
    prev = previous(records, record)
    metrics, before = record["metrics"], (prev or {}).get("metrics", {})

    lines = [
        f"*{record['client_name']} — Weekly Recap | {record['period_start']} → {record['period_end']}*",
        "",
        "*1. Meta Ads*",
        "",
        f"| Métrique | {record['period_start']} → {record['period_end']} "
        f"| {prev['period_start'] + ' → ' + prev['period_end'] if prev else 'semaine précédente'} |",
        "| - | - | - |",
    ]
    for key, label, kind in TABLE_ROWS:
        lines.append(f"| {label} | {fmt(metrics.get(key), kind)} | {fmt(before.get(key), kind)} |")
    lines += [
        "",
        f"Coût par visite : {fmt(cost_per_visit(metrics), 'money')} "
        f"(semaine précédente {fmt(cost_per_visit(before) if prev else None, 'money')})",
        "",
        "<!-- TODO lecture des chiffres : ce qui bouge, et pourquoi -->",
        "",
        ":warning: Ces chiffres comptent seulement les checkouts trackés sur le site. "
        "Les ventes en DM et les factures manuelles n'y sont pas.",
        "",
    ]

    if record.get("top_ads"):
        lines.append("*Créatifs de la semaine*")
        for ad in record["top_ads"]:
            roas = f"ROAS {fmt(ad.get('roas_pixel'), 'ratio')}" if ad.get("roas_pixel") else "aucune vente trackée"
            lines.append(f"• `{ad['name']}` — {fmt(ad.get('spend'), 'money')} dépensés, "
                         f"CTR {fmt(ad.get('ctr_all'), 'pct')}, {roas}")
        lines.append("")

    lines += [
        "*2. Google Ads* — <!-- TODO -->",
        "*3. SEO / organique* — <!-- TODO (stats Search Console de Nate) -->",
        "*4. Créatifs* — <!-- TODO (livraisons Drive, montages, shoots) -->",
        "*5. Site* — <!-- TODO (tâches dev du mois) -->",
        "*6. Email* — <!-- TODO (taille de liste Klaviyo, opt-in) -->",
        "",
        "*La semaine prochaine*",
        "1. <!-- TODO -->",
        "",
        "C'est tout. Si tu veux creuser quelque chose ou faire un call, dis-nous juste quand.",
    ]

    for note in record.get("notes", []):
        lines.append(f"\n<!-- note du log : {note} -->")

    text = "\n".join(lines)
    if args.write:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORTS_DIR / f"{record['period_end']}.md"
        if out.exists() and not args.force:
            raise SystemExit(
                f"{out} already exists - it is probably the hand-finished report. "
                f"Re-run with --force to overwrite it with a fresh skeleton."
            )
        out.write_text(text + "\n")
        print(f"wrote {out}")
    else:
        print(text)
    return 0


def cmd_payload(args) -> int:
    """Alfredify-ready payload: the log record plus computed deltas.

    Field names are intentionally generic (title/body/metrics/period) so they can
    be mapped onto whatever Alfredify's task/log endpoint expects once the API
    contract and credentials are known.
    """
    records = load()
    record = find(records, args.week)
    prev = previous(records, record)
    metrics, before = record["metrics"], (prev or {}).get("metrics", {})

    payload = {
        "client": record["client"],
        "title": f"Weekly report — {record['client_name']} — "
                 f"{record['period_start']} → {record['period_end']}",
        "period": {"start": record["period_start"], "end": record["period_end"]},
        "source": record["source"],
        "currency": record.get("currency", "USD"),
        "pulled_at": record.get("pulled_at"),
        "metrics": metrics,
        "previous_metrics": before or None,
        "deltas_pct": {
            key: (None if metrics.get(key) is None or not before.get(key)
                  else round((metrics[key] / before[key] - 1) * 100, 1))
            for key, _, _ in TABLE_ROWS
        },
        "top_ads": record.get("top_ads", []),
        "notes": record.get("notes", []),
    }
    report_file = REPORTS_DIR / f"{record['period_end']}.md"
    if report_file.exists():
        payload["body_markdown"] = report_file.read_text()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    # Die quietly on `| head` instead of dumping a BrokenPipeError traceback.
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):  # not POSIX, or not the main thread
        pass

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="append a week's metrics to the log")
    p_add.add_argument("--file", help="JSON file to read (default: stdin)")
    p_add.add_argument("--replace", action="store_true", help="overwrite an already-logged week")
    p_add.set_defaults(func=cmd_add)

    p_table = sub.add_parser("table", help="print a week vs. the previous one")
    p_table.add_argument("--week", help="period_end (YYYY-MM-DD); default: latest")
    p_table.set_defaults(func=cmd_table)

    p_report = sub.add_parser("report", help="render the Slack report skeleton")
    p_report.add_argument("--week", help="period_end (YYYY-MM-DD); default: latest")
    p_report.add_argument("--write", action="store_true",
                          help=f"write to {REPORTS_DIR.relative_to(REPO_ROOT)}/<period_end>.md")
    p_report.add_argument("--force", action="store_true",
                          help="overwrite an existing report file")
    p_report.set_defaults(func=cmd_report)

    p_payload = sub.add_parser("payload", help="emit the Alfredify-ready JSON payload")
    p_payload.add_argument("--week", help="period_end (YYYY-MM-DD); default: latest")
    p_payload.set_defaults(func=cmd_payload)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
