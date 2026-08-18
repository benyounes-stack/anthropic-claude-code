#!/usr/bin/env python3
"""Charts for the TPS Meta Ads client report — Immense.

All figures are built from the Meta Ads API values pulled in this session
(last 30 days: 2026-07-19 -> 2026-08-17). Chart 3 is explicitly a projection
and is hatched + captioned as such.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# --- palette -----------------------------------------------------------
# Sequential/categorical blue from the dataviz reference palette; status
# colours match the report template (green/red/orange) so the PDF reads as
# one system.
BLUE      = "#2a78d6"
BLUE_LT   = "#86b6ef"
BLUE_DK   = "#184f95"
GREEN     = "#16a34a"
RED       = "#dc2626"
ORANGE    = "#d97706"
SURFACE   = "#ffffff"
INK       = "#111827"
INK2      = "#4b5563"
MUTED     = "#9ca3af"
GRID      = "#e0e0e3"

plt.rcParams.update({
    "font.family": ["DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "text.color": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def strip(ax, keep_left=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if not keep_left:
        ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)


# =======================================================================
# 1. Où le tunnel casse — 3 étapes, chacune face à sa norme e-commerce
# =======================================================================
steps = [
    ("Impression → clic sortant\n(qualité créative)", 5.99, (1.0, 2.0), "au-dessus"),
    ("Clic → visite du site\n(qualité technique)",   95.3, (70.0, 85.0), "au-dessus"),
    ("Visite → achat\n(conversion du site)",          0.178, (1.0, 2.5), "en-dessous"),
]

fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.5))
for ax, (label, val, (lo, hi), verdict) in zip(axes, steps):
    good = verdict == "au-dessus"
    colour = GREEN if good else RED
    top = max(val, hi) * 1.45

    # benchmark band
    ax.axhspan(lo, hi, color=MUTED, alpha=0.16, zorder=0)
    ax.text(0.62, (lo + hi) / 2, "norme\ne-commerce", fontsize=7.5, color=INK2,
            va="center", ha="left", linespacing=1.3)

    ax.bar([0], [val], width=0.5, color=colour, zorder=3)
    ax.text(0, val + top * 0.045, f"{val:.2f} %".replace(".", ","),
            ha="center", va="bottom", fontsize=13, fontweight="bold", color=colour)

    ax.set_title(label, fontsize=9.5, color=INK, pad=10, linespacing=1.5)
    ax.set_xlim(-0.55, 1.35)
    ax.set_ylim(0, top)
    ax.set_xticks([])
    ax.set_yticks([])
    strip(ax)
    ax.spines["bottom"].set_visible(True)

axes[0].set_ylabel("Taux (échelles indépendantes)", fontsize=8, color=MUTED)
fig.suptitle("Les deux premières étapes du tunnel sont excellentes. La troisième casse tout.",
             fontsize=12.5, fontweight="bold", y=1.0, color=INK)
fig.text(0.5, -0.04,
         "Immense · compte Meta Ads · 30 derniers jours (19 juil. → 17 août 2026) · source : Meta Ads. "
         "Chaque panneau a sa propre échelle — la bande grise est la norme e-commerce apparel.",
         ha="center", fontsize=7.5, color=MUTED)
fig.tight_layout()
fig.savefig("chart1-tunnel.png", dpi=190, bbox_inches="tight")
plt.close(fig)


# =======================================================================
# 2. Placements — où va le budget vs ce qu'il rapporte
# =======================================================================
placements = [
    ("Fil d'actualité (Feed)",  2363.02, 2.05),
    ("Instagram Stories",        804.99, 0.86),
    ("Instagram Reels",          405.07, 0.69),
    ("Facebook Reels",           187.09, 7.40),
    ("Marketplace",               33.39, 9.43),
]
names  = [p[0] for p in placements]
spends = [p[1] for p in placements]
roas   = [p[2] for p in placements]
y = range(len(names))[::-1]
y = list(y)

fig, (axl, axr) = plt.subplots(1, 2, figsize=(11.4, 3.6),
                               gridspec_kw={"width_ratios": [1, 1], "wspace": 0.55})

# --- left: budget
axl.barh(y, spends, height=0.6, color=BLUE, zorder=3)
for yi, v in zip(y, spends):
    axl.text(v + 60, yi, f"{v:,.0f} $".replace(",", " "), va="center",
             fontsize=9, color=INK, fontweight="bold")
axl.set_yticks(y)
axl.set_yticklabels(names, fontsize=8.5, color=INK)
axl.set_xlim(0, max(spends) * 1.30)
axl.set_ylim(-1.15, len(names) - 0.45)
axl.set_xticks([])
axl.set_title("Budget dépensé (30 j)", fontsize=10, fontweight="bold",
              color=INK, loc="left", pad=14)
strip(axl)
axl.spines["bottom"].set_visible(False)

# --- right: ROAS, coloured by profitability status
colours = [GREEN if r >= 1.0 else RED for r in roas]
axr.barh(y, roas, height=0.6, color=colours, zorder=3)
axr.axvline(1.0, color=INK2, lw=1.4, ls="--", zorder=4)
axr.text(1.05, -0.62, "seuil de rentabilité (1,0×)",
         fontsize=7.5, color=INK2, va="center", ha="left")
for yi, r in zip(y, roas):
    axr.text(r + 0.24, yi, f"{r:.2f}×".replace(".", ","), va="center",
             fontsize=9, color=INK, fontweight="bold")
axr.set_yticks(y)
axr.set_yticklabels(["" for _ in names])
axr.set_xlim(0, max(roas) * 1.26)
axr.set_ylim(-1.15, len(names) - 0.45)
axr.set_xticks([])
axr.set_title("Retour sur dépense (ROAS)", fontsize=10, fontweight="bold",
              color=INK, loc="left", pad=14)
strip(axr)
axr.spines["bottom"].set_visible(False)
axr.legend(handles=[Patch(facecolor=GREEN, label="Rentable"),
                    Patch(facecolor=RED, label="À perte")],
           loc="lower right", bbox_to_anchor=(1.02, -0.04), frameon=False,
           fontsize=8, handlelength=1.1, ncol=2, columnspacing=1.2)

fig.suptitle("31 % du budget part dans les deux placements qui perdent de l'argent.",
             fontsize=12.5, fontweight="bold", y=1.03, color=INK, x=0.05, ha="left")
fig.text(0.05, -0.06,
         "30 derniers jours · source : Meta Ads. Facebook Reels et Marketplace, les deux placements les plus "
         "rentables, ne reçoivent que 5,7 % du budget.",
         ha="left", fontsize=7.5, color=MUTED)
fig.savefig("chart2-placements.png", dpi=190, bbox_inches="tight")
plt.close(fig)


# =======================================================================
# 3. Projection — ce que vaut le même budget selon le taux de conversion
# =======================================================================
SPEND = 3910.46
AOV = 250.40           # panier moyen mesuré sur les 30 derniers jours
VISITS = 16811

scenarios = [
    ("Aujourd'hui\n0,18 %", 0.00178, False),
    ("Objectif court terme\n0,50 %", 0.005, True),
    ("Norme du secteur\n1,00 %", 0.010, True),
]
labels  = [s[0] for s in scenarios]
revenue = [VISITS * s[1] * AOV for s in scenarios]
orders  = [VISITS * s[1] for s in scenarios]
roas_p  = [r / SPEND for r in revenue]
bar_col = [BLUE_DK, BLUE, BLUE_LT]

def fr_int(n):
    return f"{n:,.0f}".replace(",", " ")


def fr_dec(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


fig, ax = plt.subplots(figsize=(10.6, 4.1))
bars = ax.bar(range(len(labels)), revenue, width=0.5, color=bar_col, zorder=3)
for b, (_, _, hyp) in zip(bars, scenarios):
    if hyp:
        b.set_hatch("///")
        b.set_edgecolor(SURFACE)
        b.set_linewidth(0)

for b, rev in zip(bars, revenue):
    ax.text(b.get_x() + b.get_width() / 2, rev + max(revenue) * 0.03,
            fr_int(rev) + " \\$", ha="center", va="bottom",
            fontsize=13.5, fontweight="bold", color=INK)

ax.axhline(SPEND, color=RED, lw=1.4, ls="--", zorder=4)
ax.text(-0.92, SPEND + max(revenue) * 0.015,
        "budget dépensé\n" + fr_int(SPEND) + " \\$",
        fontsize=8, color=RED, va="bottom", ha="left", linespacing=1.4)

ax.set_xticks(range(len(labels)))
ax.set_xticklabels(
    [f"{lab}\n{fr_int(o)} commandes · ROAS {fr_dec(r)}×"
     for lab, o, r in zip(labels, orders, roas_p)],
    fontsize=9, linespacing=1.85)
ax.set_xlim(-0.95, len(labels) - 0.45)
ax.set_ylim(0, max(revenue) * 1.22)
ax.set_yticks([])
strip(ax)
ax.legend(handles=[Patch(facecolor=BLUE_DK, label="Mesuré"),
                   Patch(facecolor=BLUE, hatch="///", edgecolor=SURFACE, label="Projection")],
          loc="upper left", bbox_to_anchor=(-0.02, 1.02), frameon=False,
          fontsize=8.5, handlelength=1.3)

fig.suptitle("Même budget, même trafic : ce que débloque le taux de conversion du site.",
             fontsize=12.5, fontweight="bold", y=1.03, color=INK, x=0.02, ha="left")
fig.text(0.02, -0.24,
         "Projection — hypothèse à budget (3 910 \\$), trafic (16 811 visites) et panier moyen (250 \\$) constants, "
         "mesurés sur les 30 derniers jours.\nLes barres hachurées ne sont pas des résultats observés.",
         ha="left", fontsize=7.5, color=MUTED, linespacing=1.5)
fig.savefig("chart3-projection.png", dpi=190, bbox_inches="tight")
plt.close(fig)

print("charts written")
for label, val in [("visites/mois", VISITS), ("panier moyen", AOV)]:
    print(f"  {label}: {val}")
