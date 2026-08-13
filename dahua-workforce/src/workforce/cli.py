"""Interface en ligne de commande.

    workforce probe      — teste la liaison et les identifiants des caméras
    workforce calibrate  — enregistre une image pour tracer les polygones de zones
    workforce collect    — lance la boucle de collecte (service continu)
    workforce report     — génère le PDF de fin de journée
    workforce send       — génère le PDF et l'envoie sur WhatsApp
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .collect import probe_cameras, run_collector
from .config import Config, ConfigError, load_config
from .dahua import DahuaClient, DahuaError
from .render import RenderError, render_pdf
from .report import SiteReport, build_reports, report_to_dict, whatsapp_summary
from .store import Store
from .whatsapp import WhatsAppError, WhatsAppSender

_LOGGER = logging.getLogger("workforce")


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    # httpx journalise chaque requête en INFO : à 15 s d'intervalle sur plusieurs
    # caméras, ça noie les messages utiles. Visible seulement en --verbose.
    logging.getLogger("httpx").setLevel(logging.DEBUG if verbose else logging.WARNING)


def _resolve_date(raw: str | None, config: Config, site_id: str | None) -> date:
    """Date du rapport. Par défaut : aujourd'hui dans le fuseau du site."""
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise ConfigError(f"date invalide '{raw}' — format AAAA-MM-JJ attendu") from exc
    site = config.site(site_id) if site_id else config.sites[0]
    return datetime.now(tz=ZoneInfo(site.timezone)).date()


# ------------------------------------------------------------------ commandes


def cmd_probe(args: argparse.Namespace, config: Config) -> int:
    results = asyncio.run(probe_cameras(config, args.site))
    failures = 0
    for entry in results:
        if entry.get("ok"):
            print(
                f"  ✓ {entry['camera']:<20} {entry['host']:<16} "
                f"{entry.get('device_type', '?')} · firmware {entry.get('firmware', '?')} · "
                f"snapshot {entry.get('snapshot_bytes', 0)} o · "
                f"zones: {', '.join(entry.get('zones', []))}"
            )
        else:
            failures += 1
            print(f"  ✗ {entry['camera']:<20} {entry['host']:<16} {entry.get('error')}")
    print(f"\n{len(results) - failures}/{len(results)} caméra(s) joignable(s).")
    return 1 if failures else 0


def cmd_calibrate(args: argparse.Namespace, config: Config) -> int:
    """Enregistre une image pour tracer les polygones de zones.

    C'est la seule commande qui écrit une image sur disque, et uniquement sur
    demande explicite de l'opérateur. Supprimer le fichier après calibration.
    """
    camera = None
    for site in config.sites:
        for candidate in site.cameras:
            if candidate.id == args.camera:
                camera = candidate
                break
    if camera is None:
        print(f"caméra inconnue: {args.camera}", file=sys.stderr)
        return 2

    async def grab() -> bytes:
        async with DahuaClient(
            host=camera.host,
            username=camera.username,
            password=camera.password,
            port=camera.port,
            tls=camera.tls,
        ) as client:
            return await client.snapshot(camera.channel)

    try:
        jpeg = asyncio.run(grab())
    except DahuaError as exc:
        print(f"échec de capture: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(jpeg)
    print(f"Image enregistrée: {output} ({len(jpeg)} octets)")
    print(
        "\nPour définir une zone : ouvrir l'image, relever les coins du poste, puis\n"
        "convertir chaque point en coordonnées normalisées — x = pixel_x / largeur,\n"
        "y = pixel_y / hauteur — et les reporter dans `polygon:` du fichier de config.\n"
        "⚠️ Supprimer cette image une fois la calibration terminée."
    )
    return 0


def cmd_collect(args: argparse.Namespace, config: Config) -> int:
    try:
        asyncio.run(
            run_collector(config, site_id=args.site, max_iterations=args.max_iterations)
        )
    except KeyboardInterrupt:
        _LOGGER.info("arrêt demandé")
    return 0


def _generate(config: Config, args: argparse.Namespace) -> list[tuple[SiteReport, Path]]:
    report_date = _resolve_date(args.date, config, args.site)
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)

    generated: list[tuple[SiteReport, Path]] = []
    with Store(config.database_path) as store:
        reports = build_reports(store, config, report_date, args.site)

    if not reports:
        _LOGGER.warning(
            "aucun quart déclaré le %s (%s) — rien à produire",
            report_date,
            report_date.strftime("%A"),
        )
        return generated

    for report in reports:
        if not report.has_data:
            _LOGGER.warning(
                "%s / %s : aucune mesure sur la plage — le rapport sera produit "
                "et signalera l'absence de données",
                report.site_id,
                report.shift_id,
            )
        pdf_path = render_pdf(report, repo_root, output_dir)
        generated.append((report, pdf_path))
    return generated


def cmd_report(args: argparse.Namespace, config: Config) -> int:
    generated = _generate(config, args)
    if not generated:
        return 1
    for report, pdf_path in generated:
        print(f"  {report.site_label} / {report.shift_label} → {pdf_path}")
        if args.json:
            print(json.dumps(report_to_dict(report), ensure_ascii=False, indent=2))
    return 0


def cmd_send(args: argparse.Namespace, config: Config) -> int:
    if config.whatsapp.include_employee_names:
        _LOGGER.warning(
            "include_employee_names est actif : le message sortant contiendra des "
            "données personnelles et transitera par les serveurs Meta, hors "
            "d'Algérie. Vérifier la base légale du transfert (loi 25-11) avant "
            "de laisser ce réglage en production."
        )

    generated = _generate(config, args)
    if not generated:
        return 1

    exit_code = 0
    with WhatsAppSender(config.whatsapp) as sender:
        for report, pdf_path in generated:
            try:
                media_id = sender.upload_document(pdf_path)
                results = sender.send_report(
                    media_id=media_id,
                    filename=pdf_path.name,
                    body_parameters=[
                        report.site_label,
                        report.report_date.isoformat(),
                        whatsapp_summary(report),
                    ],
                )
            except WhatsAppError as exc:
                _LOGGER.error("%s / %s : %s", report.site_id, report.shift_id, exc)
                exit_code = 1
                continue
            for result in results:
                print(f"  ✓ {result.recipient} — message {result.message_id}")
    return exit_code


# ---------------------------------------------------------------------- parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workforce",
        description=(
            "Suivi d'occupation des postes de travail à partir de caméras Dahua, "
            "avec rapport de fin de journée."
        ),
    )
    parser.add_argument(
        "--config", default="config/sites.yaml", help="chemin du fichier de configuration"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="journalisation détaillée")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="teste la liaison avec les caméras")
    probe.add_argument("--site", help="limiter à un site")
    probe.set_defaults(handler=cmd_probe)

    calibrate = subparsers.add_parser(
        "calibrate", help="enregistre une image pour tracer les zones"
    )
    calibrate.add_argument("--camera", required=True, help="identifiant de caméra")
    calibrate.add_argument("--output", default="calibration.jpg", help="fichier de sortie")
    calibrate.set_defaults(handler=cmd_calibrate)

    collect = subparsers.add_parser("collect", help="lance la boucle de collecte")
    collect.add_argument("--site", help="limiter à un site")
    collect.add_argument(
        "--max-iterations",
        type=int,
        help="s'arrêter après N tours (test d'installation)",
    )
    collect.set_defaults(handler=cmd_collect)

    for name, help_text, handler in (
        ("report", "génère le PDF de fin de journée", cmd_report),
        ("send", "génère le PDF et l'envoie sur WhatsApp", cmd_send),
    ):
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("--site", help="limiter à un site")
        sub.add_argument("--date", help="date du rapport (AAAA-MM-JJ), défaut aujourd'hui")
        sub.add_argument(
            "--yesterday",
            action="store_true",
            help="raccourci pour la veille (quarts de nuit terminés le matin)",
        )
        sub.add_argument("--output-dir", default="out", help="répertoire de sortie")
        sub.add_argument(
            "--repo-root",
            default=".",
            help="racine du dépôt, pour localiser la skill custom-reports",
        )
        if name == "report":
            sub.add_argument(
                "--json", action="store_true", help="afficher aussi les données brutes"
            )
        sub.set_defaults(handler=handler)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"configuration invalide: {exc}", file=sys.stderr)
        return 2

    if getattr(args, "yesterday", False):
        if args.date:
            print("--date et --yesterday sont exclusifs", file=sys.stderr)
            return 2
        site = config.site(args.site) if args.site else config.sites[0]
        args.date = (
            datetime.now(tz=ZoneInfo(site.timezone)).date() - timedelta(days=1)
        ).isoformat()

    try:
        return args.handler(args, config)
    except (ConfigError, RenderError, WhatsAppError, DahuaError) as exc:
        print(f"erreur: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
