#!/usr/bin/env python3
"""
Offer economics + guardrails.

Computes the numbers a commercial offer stands on (MER, breakeven MER, CAC,
contribution, fee load, the uplift needed for the fee to pay for itself, and
three scenarios) and raises flags when the offer as sized isn't defensible.

The point is not convenience. Offer arithmetic done in prose drifts: a fee gets
compared to revenue instead of gross profit, a projection quietly assumes every
dollar of revenue is paid-driven, a "+30% growth" scenario forgets that the
client is already below breakeven. Those mistakes end up in a document someone
signs. This does the arithmetic once, the same way each time, and says so out
loud when the result won't hold up.

Usage:
    python3 offer_math.py inputs.json [-o economics.json]
    python3 offer_math.py --example > inputs.json

Stdlib only.
"""

import argparse
import json
import sys

# Thresholds. They're deliberately conservative: an offer that trips a warning
# can still be right, but it needs a reason stated in the document.
FEE_TO_GROSS_PROFIT_WARN = 0.25
FEE_TO_GROSS_PROFIT_BLOCK = 0.40
FEE_TO_SPEND_WARN = 0.33          # fee above a third of media budget
FEE_TO_SPEND_BLOCK = 1.00         # fee above the media budget itself
UPLIFT_WARN = 0.15                # >15% revenue uplift just to cover the fee
UPLIFT_BLOCK = 0.30
MARGIN_SENSITIVITY = [0.30, 0.50, 0.70]


class Flag:
    def __init__(self, level, code, message, fix=None):
        self.level, self.code, self.message, self.fix = level, code, message, fix

    def as_dict(self):
        d = {"level": self.level, "code": self.code, "message": self.message}
        if self.fix:
            d["fix"] = self.fix
        return d


def div(a, b):
    """Division that returns None instead of exploding — missing inputs are normal here."""
    try:
        if a is None or b in (None, 0):
            return None
        return a / b
    except (TypeError, ZeroDivisionError):
        return None


def r(x, n=2):
    return None if x is None else round(x, n)


def build(cfg):
    flags = []
    base = cfg.get("baseline", {}) or {}
    offer = cfg.get("offer", {}) or {}
    months = base.get("period_months") or cfg.get("period_months") or 1
    if not months or months <= 0:
        months = 1

    # ---------- baseline, normalised to one month ----------
    revenue_m = div(base.get("revenue"), months)
    spend_m = div(base.get("ad_spend"), months)
    orders_m = div(base.get("orders"), months)
    new_cust_m = div(base.get("new_customers"), months)
    gm = base.get("gross_margin_pct")

    if gm is not None and gm > 1:  # tolerate "62" meaning 62%
        gm = gm / 100.0

    aov = div(base.get("revenue"), base.get("orders"))
    mer = div(revenue_m, spend_m)
    breakeven_mer = div(1.0, gm)
    gross_profit_m = revenue_m * gm if (revenue_m is not None and gm is not None) else None
    contribution_m = (gross_profit_m - spend_m) if (gross_profit_m is not None and spend_m is not None) else None
    cac = div(spend_m, new_cust_m)
    first_order_profit = aov * gm if (aov is not None and gm is not None) else None

    # Paid vs non-paid split decides whether scaling spend can scale all revenue.
    paid_revenue_m = div(base.get("paid_revenue"), months)
    if paid_revenue_m is None:
        paid_revenue_m = revenue_m
        non_paid_m = 0.0
        all_revenue_assumed_paid = True
    else:
        non_paid_m = max((revenue_m or 0) - paid_revenue_m, 0.0)
        all_revenue_assumed_paid = False

    paid_mer = div(paid_revenue_m, spend_m)

    baseline_out = {
        "period_months": months,
        "monthly_revenue": r(revenue_m),
        "monthly_ad_spend": r(spend_m),
        "monthly_orders": r(orders_m, 1),
        "aov": r(aov),
        "gross_margin_pct": gm,
        "mer_blended": r(mer, 3),
        "paid_mer": r(paid_mer, 3),
        "breakeven_mer": r(breakeven_mer, 3),
        "monthly_gross_profit": r(gross_profit_m),
        "monthly_contribution_after_ads": r(contribution_m),
        "blended_new_customer_cac": r(cac),
        "first_order_gross_profit": r(first_order_profit),
        "paid_revenue_share": r(div(paid_revenue_m, revenue_m), 3),
    }

    # ---------- the fee ----------
    monthly_fee = offer.get("monthly_fee") or 0.0
    model = (offer.get("model") or "retainer").lower()
    term = offer.get("term_months") or 0
    setup = offer.get("setup_fee") or 0.0
    planned_spend_m = offer.get("planned_monthly_spend") or spend_m

    if model == "percent_spend":
        pct = offer.get("percent_of_spend")
        if pct is not None and planned_spend_m is not None:
            if pct > 1:
                pct = pct / 100.0
            computed = planned_spend_m * pct
            floor = offer.get("monthly_floor")
            ceiling = offer.get("monthly_ceiling")
            if floor:
                computed = max(computed, floor)
            if ceiling:
                computed = min(computed, ceiling)
            monthly_fee = computed

    # Setup amortised over the term so comparisons are like-for-like.
    amortised_setup = div(setup, term) if term else None
    effective_fee_m = monthly_fee + (amortised_setup or 0.0)

    fee_to_revenue = div(effective_fee_m, revenue_m)
    fee_to_gross_profit = div(effective_fee_m, gross_profit_m)
    fee_to_spend = div(effective_fee_m, planned_spend_m)

    # The most persuasive number in the offer: how much extra revenue makes the
    # fee free. Needs margin — without it, give a sensitivity table instead.
    uplift_revenue = div(effective_fee_m, gm)
    uplift_pct = div(uplift_revenue, revenue_m)
    sensitivity = None
    if gm is None and revenue_m:
        sensitivity = [
            {
                "assumed_gross_margin_pct": m,
                "required_incremental_revenue_monthly": r(effective_fee_m / m),
                "required_uplift_pct": r((effective_fee_m / m) / revenue_m, 4),
            }
            for m in MARGIN_SENSITIVITY
        ]

    fee_out = {
        "model": model,
        "monthly_fee": r(monthly_fee),
        "setup_fee": r(setup),
        "term_months": term or None,
        "amortised_setup_per_month": r(amortised_setup),
        "effective_monthly_cost_to_client": r(effective_fee_m),
        "total_engagement_cost": r(monthly_fee * term + setup) if term else None,
        "fee_as_pct_of_revenue": r(fee_to_revenue, 4),
        "fee_as_pct_of_gross_profit": r(fee_to_gross_profit, 4),
        "fee_as_pct_of_ad_spend": r(fee_to_spend, 4),
        "breakeven_uplift": {
            "incremental_revenue_needed_monthly": r(uplift_revenue),
            "as_pct_of_current_revenue": r(uplift_pct, 4),
            "note": "Revenu additionnel mensuel a partir duquel l'accompagnement s'autofinance, a marge constante.",
        },
        "margin_sensitivity": sensitivity,
    }

    # ---------- scenarios ----------
    scen_cfg = cfg.get("scenarios") or {
        "conservative": {"spend_change_pct": 0.0, "efficiency_change_pct": 0.0},
        "base": {"spend_change_pct": 0.15, "efficiency_change_pct": 0.05},
        "ambitious": {"spend_change_pct": 0.30, "efficiency_change_pct": 0.10},
    }
    scenarios = {}
    for name, s in scen_cfg.items():
        ds = s.get("spend_change_pct", 0.0) or 0.0
        de = s.get("efficiency_change_pct", 0.0) or 0.0
        if abs(ds) > 1.5:
            ds = ds / 100.0
        if abs(de) > 1.5:
            de = de / 100.0

        if spend_m is None or paid_mer is None:
            scenarios[name] = {"error": "insufficient baseline (need revenue and ad_spend)"}
            continue

        new_spend = spend_m * (1 + ds)
        new_paid_mer = paid_mer * (1 + de)
        new_paid_rev = new_spend * new_paid_mer
        new_rev = new_paid_rev + non_paid_m
        new_gp = new_rev * gm if gm is not None else None
        new_contrib = (new_gp - new_spend) if new_gp is not None else None
        new_contrib_after_fee = (new_contrib - effective_fee_m) if new_contrib is not None else None
        base_contrib_after_fee = (contribution_m - effective_fee_m) if contribution_m is not None else None

        scenarios[name] = {
            "assumptions": {
                "ad_spend_change_pct": r(ds, 4),
                "paid_efficiency_change_pct": r(de, 4),
                "gross_margin_held_at": gm,
            },
            "monthly_ad_spend": r(new_spend),
            "monthly_revenue": r(new_rev),
            "revenue_delta_vs_baseline": r(new_rev - revenue_m) if revenue_m is not None else None,
            "revenue_delta_pct": r(div(new_rev - revenue_m, revenue_m), 4) if revenue_m else None,
            "monthly_gross_profit": r(new_gp),
            "monthly_contribution_after_ads": r(new_contrib),
            "monthly_contribution_after_ads_and_fee": r(new_contrib_after_fee),
            "contribution_gain_vs_doing_nothing": (
                r(new_contrib_after_fee - contribution_m)
                if (new_contrib_after_fee is not None and contribution_m is not None) else None
            ),
            "worth_it": (
                None if (new_contrib_after_fee is None or contribution_m is None)
                else new_contrib_after_fee > contribution_m
            ),
            "_baseline_contribution_after_fee": r(base_contrib_after_fee),
        }

        if ds > 0 and de >= 0:
            flags.append(Flag(
                "warning", f"no_diminishing_returns_{name}",
                f"Scenario '{name}': +{ds:.0%} de budget avec une efficacite egale ou meilleure. "
                "Scaler degrade presque toujours le MER.",
                "Passer efficiency_change_pct en negatif sur au moins le scenario ambitieux, "
                "ou justifier pourquoi ce compte a de la marge (headroom d'audience, budget bride).",
            ))

    # ---------- guardrails ----------
    if gm is None:
        flags.append(Flag(
            "warning", "missing_gross_margin",
            "Marge brute inconnue : aucune affirmation de profit n'est soutenable.",
            "Demander la marge au client. En attendant, projections au niveau CA uniquement, "
            "et poser l'hypothese explicitement dans le PDF (bloc .assumption).",
        ))

    if mer is not None and breakeven_mer is not None and mer < breakeven_mer:
        flags.append(Flag(
            "blocker", "unprofitable_before_fee",
            f"MER actuel {mer:.2f} sous le seuil de rentabilite {breakeven_mer:.2f} : "
            "le client perd de l'argent sur le paid avant meme les honoraires.",
            "Ne pas vendre du scaling. Vendre une phase de redressement des unit economics "
            "avec un point de decision (voir diagnostic.md).",
        ))

    if fee_to_gross_profit is not None:
        if fee_to_gross_profit >= FEE_TO_GROSS_PROFIT_BLOCK:
            flags.append(Flag(
                "blocker", "fee_too_heavy",
                f"Les honoraires representent {fee_to_gross_profit:.0%} de la marge brute mensuelle.",
                "Reduire le scope, allonger la montee en charge, ou passer sur un modele "
                "base + performance.",
            ))
        elif fee_to_gross_profit >= FEE_TO_GROSS_PROFIT_WARN:
            flags.append(Flag(
                "warning", "fee_heavy",
                f"Les honoraires representent {fee_to_gross_profit:.0%} de la marge brute mensuelle : "
                "tenable, mais fragile au premier mois creux.",
                "Justifier explicitement par le gain chiffre, ou proposer une option plus legere.",
            ))

    if fee_to_spend is not None:
        if fee_to_spend >= FEE_TO_SPEND_BLOCK:
            flags.append(Flag(
                "blocker", "fee_exceeds_media",
                f"Les honoraires ({r(effective_fee_m)}) depassent le budget media "
                f"({r(planned_spend_m)}).",
                "Requalifier en prestation projet/conseil, ou revoir le budget media a la hausse "
                "avec le client avant de chiffrer.",
            ))
        elif fee_to_spend >= FEE_TO_SPEND_WARN:
            flags.append(Flag(
                "warning", "fee_large_vs_media",
                f"Les honoraires representent {fee_to_spend:.0%} du budget media.",
                "Le client aura l'impression de payer la gestion plutot que les resultats. "
                "Ancrer le prix sur le gain identifie, pas sur le budget.",
            ))

    if uplift_pct is not None:
        if uplift_pct >= UPLIFT_BLOCK:
            flags.append(Flag(
                "blocker", "uplift_unrealistic",
                f"Il faut +{uplift_pct:.0%} de CA juste pour autofinancer les honoraires.",
                "Redimensionner l'offre : a ce niveau, l'offre n'est pas defendable devant un CFO.",
            ))
        elif uplift_pct >= UPLIFT_WARN:
            flags.append(Flag(
                "warning", "uplift_demanding",
                f"Il faut +{uplift_pct:.0%} de CA pour autofinancer les honoraires.",
                "Verifier que le diagnostic identifie bien un gain de cet ordre, sinon descendre en gamme.",
            ))

    if contribution_m is not None and effective_fee_m and (contribution_m - effective_fee_m) < 0:
        flags.append(Flag(
            "blocker", "negative_contribution_after_fee",
            "Apres honoraires, la contribution mensuelle du client devient negative a volume constant.",
            "L'offre ne tient que si la croissance est acquise d'avance — ce qui n'est jamais le cas. "
            "Redimensionner.",
        ))

    if cac is not None and first_order_profit is not None and cac > first_order_profit:
        flags.append(Flag(
            "info", "cac_above_first_order_profit",
            f"CAC nouveau client ({r(cac)}) superieur a la marge brute de la 1ere commande "
            f"({r(first_order_profit)}) : la rentabilite depend du reachat.",
            "Argument fort pour une ligne retention/CRM dans le scope — a chiffrer sur le taux de reachat reel.",
        ))

    if all_revenue_assumed_paid and revenue_m:
        flags.append(Flag(
            "warning", "all_revenue_assumed_paid",
            "Aucun 'paid_revenue' fourni : les projections supposent que 100% du CA suit le budget media, "
            "ce qui surestime l'effet du scaling.",
            "Renseigner baseline.paid_revenue (attribution Triple Whale) pour une projection defendable.",
        ))

    if model == "retainer_plus_perf":
        if not offer.get("performance_cap_monthly"):
            flags.append(Flag(
                "warning", "uncapped_performance",
                "Clause de performance sans plafond mensuel.",
                "Plafonner : un mois exceptionnel produit une facture que le client refusera de payer.",
            ))
        if not offer.get("performance_baseline_definition"):
            flags.append(Flag(
                "warning", "undefined_performance_baseline",
                "Clause de performance sans definition ecrite de la baseline.",
                "Definir la periode de reference et la metrique (MER ou ROAS blende, verifiable des deux cotes).",
            ))

    if model == "percent_spend":
        flags.append(Flag(
            "info", "spend_model_incentive",
            "Modele au % du budget : le client objectera l'incitation a depenser plus.",
            "Prevoir la reponse — plancher, plafond, et un garde-fou de rentabilite dans la meme clause.",
        ))

    if new_cust_m is None:
        flags.append(Flag(
            "info", "missing_new_customers",
            "Nombre de nouveaux clients absent : pas de CAC ni de payback calculables.",
            "Recuperable via Triple Whale (get-summary-kpis / orders_table).",
        ))

    levels = [f.level for f in flags]
    verdict = ("blocked" if "blocker" in levels
               else "review" if "warning" in levels
               else "ok")

    return {
        "client": cfg.get("client"),
        "currency": cfg.get("currency"),
        "period_label": cfg.get("period_label"),
        "baseline": baseline_out,
        "offer": fee_out,
        "scenarios": scenarios,
        "flags": [f.as_dict() for f in flags],
        "verdict": verdict,
    }


def summarise(out):
    cur = out.get("currency") or ""
    b, o = out["baseline"], out["offer"]

    def money(x):
        if x is None:
            return "n/a"
        return f"{x:,.0f} {cur}".replace(",", " ").strip()

    def pct(x):
        return "n/a" if x is None else f"{x:.1%}"

    lines = [
        f"=== {out.get('client') or 'Client'} — {out.get('period_label') or ''} ===",
        "",
        "BASELINE (mensuel)",
        f"  CA                        {money(b['monthly_revenue'])}",
        f"  Budget media              {money(b['monthly_ad_spend'])}",
        f"  MER blende                {b['mer_blended'] if b['mer_blended'] is not None else 'n/a'}"
        f"   (seuil rentabilite: {b['breakeven_mer'] if b['breakeven_mer'] is not None else 'marge inconnue'})",
        f"  Marge brute               {money(b['monthly_gross_profit'])}",
        f"  Contribution apres pub    {money(b['monthly_contribution_after_ads'])}",
        f"  CAC nouveau client        {money(b['blended_new_customer_cac'])}",
        "",
        "OFFRE",
        f"  Modele                    {o['model']}",
        f"  Cout mensuel effectif     {money(o['effective_monthly_cost_to_client'])}",
        f"  % du CA / marge / media   {pct(o['fee_as_pct_of_revenue'])} / "
        f"{pct(o['fee_as_pct_of_gross_profit'])} / {pct(o['fee_as_pct_of_ad_spend'])}",
    ]

    uplift = o["breakeven_uplift"]["incremental_revenue_needed_monthly"]
    if uplift is not None:
        lines.append(
            f"  Autofinancement a         +{money(uplift)} de CA/mois "
            f"({pct(o['breakeven_uplift']['as_pct_of_current_revenue'])})"
        )

    if o.get("margin_sensitivity"):
        lines.append("  Autofinancement            marge inconnue — sensibilite:")
        for s in o["margin_sensitivity"]:
            lines.append(
                f"    marge {s['assumed_gross_margin_pct']:.0%} -> "
                f"+{money(s['required_incremental_revenue_monthly'])}/mois "
                f"({pct(s['required_uplift_pct'])})"
            )

    lines += ["", "SCENARIOS (mensuel)"]
    for name, s in out["scenarios"].items():
        if "error" in s:
            lines.append(f"  {name:<14} {s['error']}")
            continue
        a = s["assumptions"]
        lines.append(
            f"  {name:<14} budget {a['ad_spend_change_pct']:+.0%} / efficacite "
            f"{a['paid_efficiency_change_pct']:+.0%}  ->  CA {money(s['monthly_revenue'])} "
            f"({s['revenue_delta_pct']:+.1%})" if s.get("revenue_delta_pct") is not None
            else f"  {name:<14} CA {money(s['monthly_revenue'])}"
        )
        if s.get("contribution_gain_vs_doing_nothing") is not None:
            verdict = "OK" if s.get("worth_it") else "NON RENTABLE"
            lines.append(
                f"                 contribution nette apres honoraires "
                f"{money(s['monthly_contribution_after_ads_and_fee'])} "
                f"(gain vs statu quo {money(s['contribution_gain_vs_doing_nothing'])}) [{verdict}]"
            )

    lines += ["", f"VERDICT: {out['verdict'].upper()}"]
    if out["flags"]:
        lines.append("")
        for f in out["flags"]:
            lines.append(f"  [{f['level'].upper()}] {f['message']}")
            if f.get("fix"):
                lines.append(f"          -> {f['fix']}")
    else:
        lines.append("  Aucun garde-fou declenche.")

    return "\n".join(lines)


EXAMPLE = {
    "client": "Nom du client",
    "currency": "CAD",
    "period_label": "12 derniers mois",
    "baseline": {
        "period_months": 12,
        "revenue": 2400000,
        "paid_revenue": 1560000,
        "ad_spend": 480000,
        "orders": 16000,
        "new_customers": 9800,
        "gross_margin_pct": 0.62,
    },
    "offer": {
        "model": "retainer",
        "monthly_fee": 4500,
        "setup_fee": 3500,
        "term_months": 6,
        "planned_monthly_spend": 46000,
        "performance_cap_monthly": None,
        "performance_baseline_definition": None,
    },
    "scenarios": {
        "conservative": {"spend_change_pct": 0.0, "efficiency_change_pct": 0.0},
        "base": {"spend_change_pct": 0.15, "efficiency_change_pct": -0.03},
        "ambitious": {"spend_change_pct": 0.35, "efficiency_change_pct": -0.08},
    },
}


def main():
    p = argparse.ArgumentParser(description="Offer economics and guardrails.")
    p.add_argument("input", nargs="?", help="JSON input file (see --example)")
    p.add_argument("-o", "--output", help="write full JSON results here")
    p.add_argument("--example", action="store_true", help="print an example input file")
    p.add_argument("--json", action="store_true", help="print JSON to stdout instead of the summary")
    args = p.parse_args()

    if args.example:
        print(json.dumps(EXAMPLE, indent=2, ensure_ascii=False))
        return 0

    if not args.input:
        p.error("an input file is required (or use --example)")

    with open(args.input, encoding="utf-8") as fh:
        cfg = json.load(fh)

    out = build(cfg)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)

    print(json.dumps(out, indent=2, ensure_ascii=False) if args.json else summarise(out))

    # Non-zero exit on a blocker so a scripted run can't quietly sail past it.
    return 2 if out["verdict"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
