"""Détection de personnes et affectation aux zones de travail.

Deux responsabilités, séparées pour rester testables sans modèle ni caméra :

* `point_in_polygon` / `assign_to_zones` — la géométrie, pure et déterministe.
* `OnnxPersonDetector` — l'inférence, isolée derrière le protocole `PersonDetector`.

Le détecteur ne renvoie que des boîtes englobantes. Il ne fait aucune
reconnaissance faciale et n'extrait aucun gabarit biométrique : il répond
« combien de personnes », jamais « qui ». C'est une contrainte de conception, pas
une limitation temporaire — voir README, section Conformité.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np

_LOGGER = logging.getLogger(__name__)

# Classe « person » dans le jeu de données COCO, sur lequel les modèles YOLO
# pré-entraînés sont fournis.
_COCO_PERSON_CLASS = 0


@dataclass(frozen=True)
class Detection:
    """Une personne détectée, en coordonnées normalisées (0.0–1.0)."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float

    @property
    def anchor(self) -> tuple[float, float]:
        """Point de référence pour l'affectation à une zone : les pieds.

        Le centre de la boîte se retrouve à mi-hauteur du torse et « déborde »
        sur les zones voisines quand les postes sont rapprochés. Le milieu du
        bord inférieur correspond à l'endroit où la personne se tient réellement,
        ce qui est ce qu'on veut mesurer sur un plan d'usine.
        """
        return ((self.x1 + self.x2) / 2.0, self.y2)


class PersonDetector(Protocol):
    """Contrat minimal d'un détecteur, pour pouvoir en substituer un en test."""

    def detect(self, jpeg: bytes) -> list[Detection]:  # pragma: no cover - protocole
        ...


def point_in_polygon(point: tuple[float, float], polygon: Sequence[tuple[float, float]]) -> bool:
    """Test d'appartenance par lancer de rayon (algorithme pair-impair).

    Gère les polygones concaves, ce qui compte : contourner une machine ou un
    convoyeur produit rarement un rectangle.
    """
    x, y = point
    inside = False
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        # Le segment croise-t-il la demi-droite horizontale partant du point ?
        if (y1 > y) != (y2 > y):
            # Abscisse de l'intersection ; y2 != y1 est garanti par le test ci-dessus.
            crossing_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < crossing_x:
                inside = not inside
    return inside


def assign_to_zones(
    detections: Sequence[Detection],
    zones: Sequence[tuple[str, Sequence[tuple[float, float]]]],
) -> dict[str, int]:
    """Compte les personnes par zone.

    Une détection est affectée à *au plus une* zone : si des polygones se
    chevauchent, la première zone dans l'ordre de la configuration gagne. Sans
    cette règle une personne postée à une intersection serait comptée deux fois
    et le taux d'occupation dépasserait 100 %.

    Retourne un compte pour *chaque* zone, y compris celles à zéro — un zéro est
    une information (poste vide), pas une absence de donnée.
    """
    counts = {zone_id: 0 for zone_id, _ in zones}
    for detection in detections:
        anchor = detection.anchor
        for zone_id, polygon in zones:
            if point_in_polygon(anchor, polygon):
                counts[zone_id] += 1
                break
    return counts


def non_max_suppression(
    boxes: np.ndarray, scores: np.ndarray, iou_threshold: float
) -> list[int]:
    """NMS classique. `boxes` en (N, 4) format xyxy. Retourne les indices gardés."""
    if boxes.size == 0:
        return []
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size > 0:
        current = int(order[0])
        keep.append(current)
        if order.size == 1:
            break
        rest = order[1:]
        # Intersection entre la boîte courante et toutes les restantes.
        inter_x1 = np.maximum(boxes[current, 0], boxes[rest, 0])
        inter_y1 = np.maximum(boxes[current, 1], boxes[rest, 1])
        inter_x2 = np.minimum(boxes[current, 2], boxes[rest, 2])
        inter_y2 = np.minimum(boxes[current, 3], boxes[rest, 3])
        inter = np.clip(inter_x2 - inter_x1, 0, None) * np.clip(
            inter_y2 - inter_y1, 0, None
        )
        iou = inter / (areas[current] + areas[rest] - inter + 1e-9)
        order = rest[iou <= iou_threshold]
    return keep


class OnnxPersonDetector:
    """Détecteur de personnes basé sur un modèle YOLO exporté en ONNX.

    Tourne sur CPU via onnxruntime. À la cadence d'échantillonnage visée (une
    image toutes les 10–15 s par caméra), un `yolov8n` suffit largement sur un
    petit serveur ou un mini-PC — aucun GPU nécessaire.

    Le modèle n'est pas embarqué dans ce dépôt (licence + poids). Exporter par
    exemple :

        pip install ultralytics
        yolo export model=yolov8n.pt format=onnx imgsz=640
    """

    def __init__(
        self,
        model_path: str,
        confidence: float = 0.35,
        nms_iou: float = 0.45,
        input_size: int = 640,
    ) -> None:
        try:
            import onnxruntime  # import différé : le CLI doit rester utilisable sans
        except ImportError as exc:  # pragma: no cover - dépend de l'installation
            raise RuntimeError(
                "onnxruntime n'est pas installé — `pip install onnxruntime`"
            ) from exc
        self._session = onnxruntime.InferenceSession(
            model_path, providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        self.confidence = confidence
        self.nms_iou = nms_iou
        self.input_size = input_size

    def detect(self, jpeg: bytes) -> list[Detection]:
        image, original_size = self._decode(jpeg)
        tensor, scale, padding = self._letterbox(image)
        outputs = self._session.run(None, {self._input_name: tensor})
        return self._decode_predictions(outputs[0], scale, padding, original_size)

    # ------------------------------------------------------------ prétraitement

    @staticmethod
    def _decode(jpeg: bytes) -> tuple[np.ndarray, tuple[int, int]]:
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - dépend de l'installation
            raise RuntimeError("Pillow n'est pas installé — `pip install pillow`") from exc
        with Image.open(io.BytesIO(jpeg)) as handle:
            rgb = handle.convert("RGB")
            return np.asarray(rgb), (rgb.width, rgb.height)

    def _letterbox(self, image: np.ndarray) -> tuple[np.ndarray, float, tuple[float, float]]:
        """Redimensionne en conservant le ratio, complète en gris neutre."""
        size = self.input_size
        height, width = image.shape[:2]
        scale = min(size / width, size / height)
        new_width, new_height = round(width * scale), round(height * scale)

        from PIL import Image  # déjà validé par _decode

        resized = np.asarray(
            Image.fromarray(image).resize((new_width, new_height), Image.BILINEAR)
        )
        canvas = np.full((size, size, 3), 114, dtype=np.uint8)
        pad_x = (size - new_width) / 2
        pad_y = (size - new_height) / 2
        top, left = int(pad_y), int(pad_x)
        canvas[top : top + new_height, left : left + new_width] = resized

        # NCHW, float32 normalisé — convention YOLO.
        tensor = canvas.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[np.newaxis, ...]
        return tensor, scale, (pad_x, pad_y)

    # ------------------------------------------------------------ postraitement

    def _decode_predictions(
        self,
        raw: np.ndarray,
        scale: float,
        padding: tuple[float, float],
        original_size: tuple[int, int],
    ) -> list[Detection]:
        # Sortie YOLOv8 : (1, 4 + nb_classes, nb_ancres). On transpose pour
        # obtenir une ligne par ancre.
        predictions = np.squeeze(raw, axis=0).T
        if predictions.shape[1] < 5:
            raise RuntimeError(
                f"sortie de modèle inattendue: {raw.shape} — un export YOLOv8 "
                f"(1, 4+classes, ancres) est attendu"
            )
        scores = predictions[:, 4 + _COCO_PERSON_CLASS]
        keep_mask = scores >= self.confidence
        if not keep_mask.any():
            return []
        boxes_cxcywh = predictions[keep_mask, :4]
        scores = scores[keep_mask]

        # cx,cy,w,h → x1,y1,x2,y2 dans l'espace lettreboxé.
        half = boxes_cxcywh[:, 2:4] / 2.0
        boxes = np.concatenate(
            [boxes_cxcywh[:, 0:2] - half, boxes_cxcywh[:, 0:2] + half], axis=1
        )

        # Retour vers l'image d'origine : retirer le padding puis l'échelle.
        pad_x, pad_y = padding
        boxes[:, [0, 2]] -= pad_x
        boxes[:, [1, 3]] -= pad_y
        boxes /= scale

        width, height = original_size
        boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, width)
        boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, height)

        kept = non_max_suppression(boxes, scores, self.nms_iou)
        return [
            Detection(
                x1=float(boxes[index, 0] / width),
                y1=float(boxes[index, 1] / height),
                x2=float(boxes[index, 2] / width),
                y2=float(boxes[index, 3] / height),
                confidence=float(scores[index]),
            )
            for index in kept
        ]


class NullDetector:
    """Détecteur inerte : renvoie toujours zéro personne.

    Sert à valider la connectivité caméra, la boucle d'échantillonnage et le
    pipeline de rapport avant d'installer un modèle.
    """

    def detect(self, jpeg: bytes) -> list[Detection]:
        return []


def build_detector(model_path: str, confidence: float, nms_iou: float, input_size: int):
    """Retourne un `OnnxPersonDetector`, ou un `NullDetector` si aucun modèle."""
    if not model_path:
        _LOGGER.warning(
            "Aucun modèle configuré (detector.model_path vide) : le collecteur "
            "tourne en mode NullDetector et enregistrera une occupation nulle."
        )
        return NullDetector()
    return OnnxPersonDetector(model_path, confidence, nms_iou, input_size)
