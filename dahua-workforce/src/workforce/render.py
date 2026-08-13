"""Génération du PDF de fin de journée, aux couleurs TPS Digital Services.

Réutilise la skill `custom-reports` déjà présente dans ce dépôt : son gabarit
HTML, son catalogue de blocs, sa charte (`brand.json`) et son script de rendu
Chromium. On n'invente pas une seconde identité visuelle.

La règle d'honnêteté de la skill s'applique intégralement ici : un poste dont la
couverture de mesure est insuffisante apparaît en `note gap`, jamais avec un
chiffre présenté comme mesuré.
"""

from __future__ import annotations

import html
import json
import logging
import shutil
import subprocess
from datetime import date
from pathlib import Path

from .report import SiteReport, ZoneReport

_LOGGER = logging.getLogger(__name__)

# Racine de la skill custom-reports, relative à la racine du dépôt.
_SKILL_DIR = Path(".claude/skills/custom-reports")

_MONTHS_FR = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)


class RenderError(Exception):
    """Échec de génération du rapport."""


def _skill_dir(repo_root: Path) -> Path:
    directory = repo_root / _SKILL_DIR
    if not directory.is_dir():
        raise RenderError(
            f"skill custom-reports introuvable ({directory}) — lancer la commande "
            f"depuis la racine du dépôt, ou passer --repo-root"
        )
    return directory


def _format_date_fr(value: date) -> str:
    return f"{value.day} {_MONTHS_FR[value.month - 1]} {value.year}"


def _pct(value: float) -> str:
    return f"{value * 100:.0f} %".replace(".", ",")


def _minutes(value: float) -> str:
    if value < 60:
        return f"{value:.0f} min"
    hours, remainder = divmod(int(round(value)), 60)
    return f"{hours} h {remainder:02d}"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


# ------------------------------------------------------------------- sections


def _kpi_row(report: SiteReport) -> str:
    zones = report.zones
    measured = [zone for zone in zones if zone.received_samples > 0]
    reliable = [zone for zone in zones if zone.is_reliable]
    alerts = report.zones_with_alerts
    total_idle = sum(zone.unoccupied_minutes for zone in zones)

    # Sans aucune mesure, l'occupation n'est pas de 0 % : elle est inconnue.
    # Afficher « 0 % · sous le seuil » serait une conclusion tirée du vide.
    if not report.has_data:
        return f"""<div class="kpi-row-4">
  <div class="kpi">
    <div class="kpi-label">Occupation moyenne</div>
    <div class="kpi-val">—</div>
    <div class="kpi-sub">aucune mesure sur la plage</div>
    <div class="tag tag-neutral">Non mesuré</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Postes suivis</div>
    <div class="kpi-val">0/{len(zones)}</div>
    <div class="kpi-sub">aucun poste n'a produit de mesure</div>
    <div class="tag tag-r">Collecte à vérifier</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Inoccupation cumulée</div>
    <div class="kpi-val">—</div>
    <div class="kpi-sub">non calculable sans mesure</div>
    <div class="tag tag-neutral">Non mesuré</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Dépassements de seuil</div>
    <div class="kpi-val">—</div>
    <div class="kpi-sub">non vérifiable sans mesure</div>
    <div class="tag tag-neutral">Non mesuré</div>
  </div>
</div>"""

    occupancy = report.overall_occupancy_rate
    if occupancy >= 0.90:
        occupancy_tag = '<div class="tag tag-g">Conforme</div>'
    elif occupancy >= 0.75:
        occupancy_tag = '<div class="tag tag-o">À surveiller</div>'
    else:
        occupancy_tag = '<div class="tag tag-r">Sous le seuil</div>'

    alert_tag = (
        '<div class="tag tag-g">Aucun dépassement</div>'
        if not alerts
        else f'<div class="tag tag-r">{len(alerts)} à traiter</div>'
    )

    coverage_tag = (
        '<div class="tag tag-g">Mesure fiable</div>'
        if len(reliable) == len(zones)
        else f'<div class="tag tag-o">{len(zones) - len(reliable)} poste(s) partiel(s)</div>'
    )

    return f"""<div class="kpi-row-4">
  <div class="kpi">
    <div class="kpi-label">Occupation moyenne</div>
    <div class="kpi-val">{_pct(occupancy)}</div>
    <div class="kpi-sub">du temps mesuré, tous postes confondus</div>
    {occupancy_tag}
  </div>
  <div class="kpi">
    <div class="kpi-label">Postes suivis</div>
    <div class="kpi-val">{len(measured)}/{len(zones)}</div>
    <div class="kpi-sub">postes ayant produit des mesures</div>
    {coverage_tag}
  </div>
  <div class="kpi">
    <div class="kpi-label">Inoccupation cumulée</div>
    <div class="kpi-val">{_minutes(total_idle)}</div>
    <div class="kpi-sub">somme sur l'ensemble des postes</div>
    <div class="tag tag-b">Indicateur de pilotage</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Dépassements de seuil</div>
    <div class="kpi-val">{len(alerts)}</div>
    <div class="kpi-sub">postes vides au-delà de leur seuil</div>
    {alert_tag}
  </div>
</div>"""


def _zone_table(report: SiteReport) -> str:
    rows: list[str] = []
    for zone in report.zones:
        if zone.received_samples == 0:
            rows.append(
                f'<tr><td>{_esc(zone.label)}</td><td colspan="5">'
                f"Aucune mesure collectée</td></tr>"
            )
            continue
        row_class = ""
        if zone.breached_idle_threshold:
            row_class = ' class="waste"'
        elif zone.occupancy_rate >= 0.95 and zone.is_reliable:
            row_class = ' class="win"'
        coverage = "" if zone.is_reliable else f" ({_pct(zone.coverage)} mesuré)"
        rows.append(
            f"<tr{row_class}>"
            f"<td>{_esc(zone.label)}</td>"
            f"<td>{_pct(zone.occupancy_rate)}{coverage}</td>"
            f"<td>{_minutes(zone.unoccupied_minutes)}</td>"
            f"<td>{_minutes(zone.longest_idle_minutes)}</td>"
            f"<td>{_esc(zone.first_seen_local or '—')}</td>"
            f"<td>{_esc(zone.last_seen_local or '—')}</td>"
            f"</tr>"
        )

    return f"""<table class="tbl">
  <thead><tr>
    <th>Poste</th><th>Occupation</th><th>Inoccupation cumulée</th>
    <th>Plus longue absence</th><th>1<sup>re</sup> présence</th><th>Dernière présence</th>
  </tr></thead>
  <tbody>
{chr(10).join("    " + row for row in rows)}
  </tbody>
</table>"""


def _alerts_block(report: SiteReport) -> str:
    alerts = report.zones_with_alerts
    unmeasured = [zone for zone in report.zones if zone.received_samples == 0]

    if not report.has_data:
        # Aucune mesure : on ne peut affirmer ni conformité ni dépassement.
        return (
            '<div class="note gap">\n  <strong>Rien à signaler — et rien à confirmer :</strong> '
            "aucune mesure n'a été collectée sur cette plage, il est donc impossible "
            "de dire si les postes ont été tenus. Vérifier l'état du collecteur et la "
            "liaison réseau des caméras (<code>workforce probe</code>) avant de tirer "
            "une conclusion de ce rapport."
            "\n</div>"
        )

    if not alerts:
        caveat = ""
        if unmeasured:
            # Le constat ne vaut que pour les postes réellement mesurés.
            caveat = (
                f"</li>\n    <li><strong>Constat partiel</strong> — "
                f"{len(unmeasured)} poste(s) sans aucune mesure "
                f"({', '.join(_esc(zone.label) for zone in unmeasured)}) sont exclus "
                f"de ce constat."
            )
        return (
            '<div class="wins">\n  <h3>✅ Aucun dépassement</h3>\n  <ul><li>'
            "<strong>Tous les postes mesurés sont restés sous leur seuil "
            "d'inoccupation</strong> sur la plage du quart."
            f"{caveat}</li></ul>\n</div>"
        )

    items = "\n".join(
        f"    <li><strong>{_esc(zone.label)} — {_minutes(zone.longest_idle_minutes)} "
        f"d'absence continue</strong> (seuil fixé à {zone.max_idle_minutes} min ; "
        f"occupation sur le quart : {_pct(zone.occupancy_rate)}).</li>"
        for zone in alerts
    )
    return f'<div class="fixes">\n  <h3>⚠ Postes au-delà du seuil</h3>\n  <ul>\n{items}\n  </ul>\n</div>'


def _understaffed_block(report: SiteReport) -> str:
    """Postes tenus, mais avec un effectif inférieur à l'effectif attendu."""
    candidates = [
        zone
        for zone in report.zones
        if zone.expected_headcount > 1
        and zone.received_samples > 0
        and zone.fully_staffed_rate < 0.80
    ]
    if not candidates:
        return ""
    items = "\n".join(
        f"    <li><strong>{_esc(zone.label)}</strong> — effectif complet "
        f"({zone.expected_headcount} personnes) sur seulement "
        f"{_pct(zone.fully_staffed_rate)} du temps mesuré, alors que le poste est "
        f"occupé {_pct(zone.occupancy_rate)} du temps.</li>"
        for zone in candidates
    )
    return f'<div class="diag">\n  <h3>⚡ Diagnostic — sous-effectif</h3>\n  <ul>\n{items}\n  </ul>\n</div>'


def _gap_notes(report: SiteReport) -> str:
    blocks: list[str] = []

    unreliable = report.unreliable_zones
    # Quand rien n'a été mesuré, `_alerts_block` le dit déjà : ne pas répéter la
    # liste complète des postes à 0 %.
    if unreliable and report.has_data:
        detail = " · ".join(
            f"{_esc(zone.label)} ({_pct(zone.coverage)})" for zone in unreliable
        )
        blocks.append(
            f'<div class="note gap">\n  <strong>Mesure partielle :</strong> '
            f"les postes suivants ont produit moins de 90 % des mesures attendues — "
            f"{detail}. Leurs taux d'occupation sont calculés sur le temps "
            f"réellement mesuré et ne doivent pas être lus comme un relevé complet."
            f"\n</div>"
        )

    if report.collection_errors:
        detail = " · ".join(
            f"{_esc(camera)} : {_esc(message[:90])} ({count}×)"
            for camera, message, count in report.collection_errors[:5]
        )
        blocks.append(
            f'<div class="note gap">\n  <strong>Incidents de collecte :</strong> '
            f"{detail}. Une caméra injoignable ne produit aucune mesure — ces "
            f"intervalles ne sont comptés ni comme occupés ni comme vides."
            f"\n</div>"
        )

    blocks.append(
        '<div class="note gap">\n  <strong>Ce que ce rapport ne mesure pas :</strong> '
        "il rend compte de l'occupation de postes de travail, pas des heures "
        "travaillées par personne. Le système détecte une présence humaine dans une "
        "zone ; il n'identifie personne et ne peut donc pas servir de base de calcul "
        "de la paie. Pour un pointage nominatif opposable, un terminal de pointage "
        "par badge reste l'instrument requis."
        "\n</div>"
    )
    return "\n".join(blocks)


def _method_block(report: SiteReport) -> str:
    interval = report.sample_interval_seconds
    return (
        '<div class="diag">\n  <h3>⚡ Méthode de mesure</h3>\n  <ul>\n'
        f"    <li><strong>Échantillonnage toutes les {interval} secondes</strong> — "
        f"une image est analysée en mémoire par caméra, la présence humaine est "
        f"comptée par zone, puis l'image est détruite. Aucune image n'est conservée."
        f"</li>\n"
        f"    <li><strong>Aucune identification</strong> — le détecteur répond "
        f"« combien de personnes dans cette zone », jamais « qui ». Aucun gabarit "
        f"biométrique n'est calculé ni stocké.</li>\n"
        f"    <li><strong>Fuseau de référence</strong> — {_esc(report.timezone)}.</li>\n"
        "  </ul>\n</div>"
    )


def build_sections(report: SiteReport) -> str:
    """Compose le corps du rapport avec les blocs du catalogue de la skill."""
    understaffed = _understaffed_block(report)

    sections = [
        f"""<div class="section">
  <div class="section-header">
    <span class="s-num">01</span>
    <span class="s-title">Le quart en un coup d'œil</span>
  </div>
{_kpi_row(report)}
</div>""",
        f"""<div class="section">
  <div class="section-header">
    <span class="s-num">02</span>
    <span class="s-title">Occupation poste par poste</span>
  </div>
{_zone_table(report)}
</div>""",
        f"""<div class="section">
  <div class="section-header">
    <span class="s-num">03</span>
    <span class="s-title">Ce qui demande une action</span>
  </div>
{_alerts_block(report)}
{understaffed}
</div>""",
        f"""<div class="section">
  <div class="section-header">
    <span class="s-num">04</span>
    <span class="s-title">Portée et limites de la mesure</span>
  </div>
{_method_block(report)}
{_gap_notes(report)}
</div>""",
    ]
    return "\n\n".join(sections)


# --------------------------------------------------------------------- rendu


def render_html(report: SiteReport, repo_root: Path, output_dir: Path) -> Path:
    """Écrit le HTML du rapport dans `output_dir` et y copie le logo."""
    skill = _skill_dir(repo_root)
    template = (skill / "assets" / "report_template.html").read_text(encoding="utf-8")
    brand = json.loads((skill / "references" / "brand.json").read_text(encoding="utf-8"))
    colors = brand["colors"]

    output_dir.mkdir(parents=True, exist_ok=True)
    logo_source = skill / brand["logo_path"]
    logo_html = ""
    if logo_source.is_file():
        # Le HTML est ouvert en file:// : le logo doit être à côté de lui.
        shutil.copy2(logo_source, output_dir / logo_source.name)
        logo_html = f'<img src="{logo_source.name}" alt="{_esc(brand["company_name"])}">'

    date_label = _format_date_fr(report.report_date)
    title = f"Rapport de fin de journée — {report.site_label} — {report.report_date.isoformat()}"

    replacements = {
        "{{TITLE}}": _esc(title),
        "{{COLOR_PRIMARY}}": colors["primary"],
        "{{COLOR_ACCENT}}": colors["accent"],
        "{{FONT_FAMILY}}": brand["font_family"],
        "{{EYEBROW}}": "Rapport de fin de journée",
        "{{TITLE_LINE1}}": _esc(report.site_label),
        "{{TITLE_LINE2}}": _esc(report.shift_label),
        "{{HEADER_SUB}}": _esc(
            f"Occupation des postes de travail mesurée sur la plage "
            f"{report.window_start_local}–{report.window_end_local}. "
            f"Données agrégées par poste — aucun suivi nominatif."
        ),
        "{{HEADER_META_ITEMS}}": (
            f"<span>Date <strong>{_esc(date_label)}</strong></span>\n"
            f"      <span>Plage <strong>{report.window_start_local}–"
            f"{report.window_end_local}</strong></span>\n"
            f"      <span>Postes suivis <strong>{len(report.zones)}</strong></span>"
        ),
        "{{LOGO_HTML}}": logo_html,
        "{{SECTIONS}}": build_sections(report),
        "{{FOOTER_LEFT}}": _esc(brand["footer_text"]),
        "{{FOOTER_RIGHT}}": _esc(brand["company_name"]),
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    html_path = output_dir / f"rapport-{report.site_id}-{report.shift_id}-{report.report_date.isoformat()}.html"
    html_path.write_text(template, encoding="utf-8")
    return html_path


def render_pdf(report: SiteReport, repo_root: Path, output_dir: Path) -> Path:
    """Rend le PDF via le script Chromium de la skill custom-reports."""
    html_path = render_html(report, repo_root, output_dir)
    pdf_path = html_path.with_suffix(".pdf")
    script = _skill_dir(repo_root) / "scripts" / "render_pdf.js"
    if not script.is_file():
        raise RenderError(f"script de rendu introuvable: {script}")

    try:
        result = subprocess.run(
            ["node", str(script), str(html_path), str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RenderError("node introuvable — Node.js est requis pour le rendu PDF") from exc
    except subprocess.TimeoutExpired as exc:
        raise RenderError("le rendu PDF a dépassé 180 s") from exc

    if result.returncode != 0:
        raise RenderError(
            f"rendu PDF échoué (code {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise RenderError(f"PDF absent ou vide après rendu: {pdf_path}")

    _LOGGER.info("PDF généré: %s (%d octets)", pdf_path, pdf_path.stat().st_size)
    return pdf_path
