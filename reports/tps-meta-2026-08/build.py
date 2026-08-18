#!/usr/bin/env python3
"""Assemble rapport.html from the custom-reports template + body.html.

Run after editing body.html, then render with:
  node ../../.claude/skills/custom-reports/scripts/render_pdf.js rapport.html <out>.pdf
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).parent
SKILL = HERE / ".." / ".." / ".claude" / "skills" / "custom-reports"

CLIENT = "Immense"

tpl = (SKILL / "assets" / "report_template.html").read_text()
tpl = re.sub(r"^<!--.*?-->\s*", "", tpl, flags=re.S)   # drop the template's usage comment
brand = json.loads((SKILL / "references" / "brand.json").read_text())
body = (HERE / "body.html").read_text()

out = (tpl
    .replace("{{TITLE}}", f"Rapport Meta Ads — {CLIENT} — Plan 14 jours")
    .replace("{{COLOR_PRIMARY}}", brand["colors"]["primary"])
    .replace("{{COLOR_ACCENT}}", brand["colors"]["accent"])
    .replace("{{FONT_FAMILY}}", brand["font_family"])
    .replace("{{EYEBROW}}", "Rapport de performance publicitaire · Meta Ads")
    .replace("{{TITLE_LINE1}}", CLIENT)
    .replace("{{TITLE_LINE2}}", "État des lieux et plan d'action sur 14 jours")
    .replace("{{HEADER_SUB}}", "Diagnostic du compte publicitaire, identification des postes "
                              "rentables et déficitaires, et feuille de route opérationnelle "
                              "pour les deux prochaines semaines.")
    .replace("{{HEADER_META_ITEMS}}", """
      <span>Période analysée <strong>19 juil. → 17 août 2026</strong></span>
      <span>Budget sur la période <strong>3 910 $ CAD</strong></span>
      <span>ROAS mesuré <strong>1,92×</strong></span>
      <span>Achats <strong>30</strong></span>
      <span>Émis le <strong>18 août 2026</strong></span>""")
    .replace("{{LOGO_HTML}}", '<img src="logo.png" alt="TPS Digital Services">')
    .replace("{{SECTIONS}}", body)
)

# the renderer draws a running footer on every page — drop the in-page one
out = re.sub(r'<div class="footer">.*?</div>\s*(?=</body>)', "", out, flags=re.S)

# print pagination — keep blocks whole and never end a page on a heading
out = out.replace("</style>", """
@media print{
  .section-header,.divider{break-after:avoid;page-break-after:avoid}
  .tbl,figure,.kpi-row,.kpi-row-4,.kpi-row-3,.month-grid,.plan-grid,
  .wins,.fixes,.actions,.diag,.note,.obj-bar,.creative-card{
    break-inside:avoid;page-break-inside:avoid}
  .tbl tbody tr{break-inside:avoid;page-break-inside:avoid}
}
</style>""", 1)

left = re.findall(r"\{\{\w+\}\}", out)
assert not left, f"unfilled placeholders: {left}"
(HERE / "rapport.html").write_text(out)
print(f"rapport.html written ({len(out)} chars) for client: {CLIENT}")
