"""Envoi du rapport via WhatsApp Business Cloud API (Meta).

Deux étapes imposées par l'API :

1. `POST /{phone_number_id}/media` — téléverser le PDF, récupérer un `media_id`.
2. `POST /{phone_number_id}/messages` — envoyer un message `template` dont
   l'en-tête référence ce `media_id`.

Le passage par un *template approuvé* n'est pas optionnel : un rapport quotidien
est un message à l'initiative de l'entreprise, donc hors de la fenêtre de service
de 24 h. Voir README pour le gabarit à déclarer dans WhatsApp Manager.

⚠️ Ce transport sort les données d'Algérie (serveurs Meta). Le corps du message
doit rester agrégé et non nominatif — c'est pourquoi `WhatsAppConfig`
verrouille `include_employee_names` à `False` par défaut.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from .config import WhatsAppConfig

_LOGGER = logging.getLogger(__name__)

_MAX_ATTEMPTS = 4
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
# Plafond Meta pour un document WhatsApp.
_MAX_DOCUMENT_BYTES = 100 * 1024 * 1024


class WhatsAppError(Exception):
    """Échec d'un appel à la Cloud API."""


@dataclass(frozen=True)
class SendResult:
    recipient: str
    message_id: str


class WhatsAppSender:
    def __init__(self, config: WhatsAppConfig, timeout: float = 60.0) -> None:
        missing = [
            name
            for name, value in (
                ("phone_number_id", config.phone_number_id),
                ("access_token", config.access_token),
            )
            if not value
        ]
        if missing:
            raise WhatsAppError(
                "configuration WhatsApp incomplète: " + ", ".join(missing)
            )
        if not config.recipients:
            raise WhatsAppError("aucun destinataire dans whatsapp.recipients")
        self.config = config
        self._base = f"https://graph.facebook.com/{config.graph_version}/{config.phone_number_id}"
        self._client = httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Bearer {config.access_token}"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WhatsAppSender":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ étape 1

    def upload_document(self, pdf_path: str | Path) -> str:
        """Téléverse le PDF et retourne son `media_id`.

        Le média est conservé 30 jours par Meta puis expire ; on en téléverse un
        nouveau à chaque rapport plutôt que d'en réutiliser un.
        """
        path = Path(pdf_path)
        if not path.is_file():
            raise WhatsAppError(f"PDF introuvable: {path}")
        size = path.stat().st_size
        if size == 0:
            raise WhatsAppError(f"PDF vide: {path}")
        if size > _MAX_DOCUMENT_BYTES:
            raise WhatsAppError(
                f"PDF trop volumineux ({size} octets, max {_MAX_DOCUMENT_BYTES})"
            )

        with path.open("rb") as handle:
            response = self._request(
                "POST",
                f"{self._base}/media",
                data={"messaging_product": "whatsapp", "type": "application/pdf"},
                files={"file": (path.name, handle, "application/pdf")},
            )
        media_id = response.get("id")
        if not media_id:
            raise WhatsAppError(f"réponse d'upload sans `id`: {response}")
        _LOGGER.info("PDF téléversé (%d octets), media_id=%s", size, media_id)
        return str(media_id)

    # ------------------------------------------------------------------ étape 2

    def send_report(
        self,
        media_id: str,
        filename: str,
        body_parameters: list[str],
    ) -> list[SendResult]:
        """Envoie le template à tous les destinataires configurés.

        `body_parameters` alimente les variables `{{1}}`, `{{2}}`… du gabarit,
        dans l'ordre. Elles doivent être agrégées et non nominatives.

        Un échec sur un destinataire n'empêche pas les autres : on tente tout le
        monde puis on lève si personne n'a reçu le rapport.
        """
        results: list[SendResult] = []
        failures: list[str] = []
        for recipient in self.config.recipients:
            try:
                results.append(
                    self._send_to(recipient, media_id, filename, body_parameters)
                )
            except WhatsAppError as exc:
                _LOGGER.error("envoi échoué vers %s: %s", recipient, exc)
                failures.append(f"{recipient}: {exc}")

        if failures and not results:
            raise WhatsAppError("aucun envoi n'a abouti — " + " | ".join(failures))
        if failures:
            _LOGGER.warning(
                "%d/%d envoi(s) en échec", len(failures), len(self.config.recipients)
            )
        return results

    def _send_to(
        self, recipient: str, media_id: str, filename: str, body_parameters: list[str]
    ) -> SendResult:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": self.config.template_name,
                "language": {"code": self.config.language_code},
                "components": [
                    {
                        "type": "header",
                        "parameters": [
                            {
                                "type": "document",
                                "document": {"id": media_id, "filename": filename},
                            }
                        ],
                    },
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": value} for value in body_parameters
                        ],
                    },
                ],
            },
        }
        response = self._request("POST", f"{self._base}/messages", json=payload)
        messages = response.get("messages") or []
        message_id = messages[0].get("id", "") if messages else ""
        _LOGGER.info("rapport envoyé à %s (message_id=%s)", recipient, message_id)
        return SendResult(recipient=recipient, message_id=str(message_id))

    # ------------------------------------------------------------------- réseau

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Appel HTTP avec réessais exponentiels sur les erreurs transitoires."""
        last_error = ""
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = self._client.request(method, url, **kwargs)
            except httpx.HTTPError as exc:
                last_error = str(exc)
                if attempt == _MAX_ATTEMPTS:
                    raise WhatsAppError(f"échec réseau: {last_error}") from exc
            else:
                if response.status_code < 400:
                    return response.json()
                last_error = _describe_error(response)
                if response.status_code not in _RETRYABLE_STATUS:
                    raise WhatsAppError(last_error)
                if attempt == _MAX_ATTEMPTS:
                    raise WhatsAppError(last_error)

            backoff = 2 ** (attempt - 1)
            _LOGGER.warning(
                "tentative %d/%d échouée (%s) — nouvelle tentative dans %ds",
                attempt,
                _MAX_ATTEMPTS,
                last_error,
                backoff,
            )
            # `files=` contient un handle déjà consommé après un POST : rouvrir.
            _rewind_files(kwargs)
            time.sleep(backoff)
        raise WhatsAppError(last_error or "échec inconnu")


def _rewind_files(kwargs: dict) -> None:
    """Remet les flux de fichiers à zéro avant un réessai d'upload."""
    for entry in (kwargs.get("files") or {}).values():
        handle = entry[1] if isinstance(entry, (tuple, list)) and len(entry) > 1 else entry
        if hasattr(handle, "seek"):
            handle.seek(0)


def _describe_error(response: httpx.Response) -> str:
    """Extrait le message d'erreur Meta, qui est bien plus parlant que le code."""
    try:
        error = response.json().get("error") or {}
    except ValueError:
        return f"HTTP {response.status_code}: {response.text[:200]}"
    parts = [f"HTTP {response.status_code}"]
    for key in ("message", "error_user_title", "error_user_msg", "code", "error_subcode"):
        value = error.get(key)
        if value:
            parts.append(f"{key}={value}")
    return " ".join(str(part) for part in parts)
