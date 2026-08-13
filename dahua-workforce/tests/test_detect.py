"""Tests de la géométrie d'affectation aux zones."""

from __future__ import annotations

import numpy as np
import pytest

from workforce.detect import (
    Detection,
    assign_to_zones,
    non_max_suppression,
    point_in_polygon,
)

SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
# Polygone en L : le cas réel d'un poste qui contourne une machine.
L_SHAPE = [(0.0, 0.0), (0.6, 0.0), (0.6, 0.4), (1.0, 0.4), (1.0, 1.0), (0.0, 1.0)]


class TestPointInPolygon:
    def test_point_inside(self):
        assert point_in_polygon((0.5, 0.5), SQUARE)

    def test_point_outside(self):
        assert not point_in_polygon((1.5, 0.5), SQUARE)
        assert not point_in_polygon((-0.1, 0.5), SQUARE)

    def test_concave_notch_is_excluded(self):
        # (0.8, 0.2) tombe dans l'encoche du L : dehors, malgré une boîte
        # englobante qui le contiendrait.
        assert not point_in_polygon((0.8, 0.2), L_SHAPE)
        assert point_in_polygon((0.3, 0.2), L_SHAPE)
        assert point_in_polygon((0.8, 0.7), L_SHAPE)

    def test_triangle(self):
        triangle = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        assert point_in_polygon((0.5, 0.3), triangle)
        assert not point_in_polygon((0.05, 0.9), triangle)


class TestAssignToZones:
    def test_anchor_is_the_feet_not_the_centre(self):
        # Personne debout dans la moitié basse de l'image. Le centre de la boîte
        # est à y=0.6, les pieds à y=0.9 : seule la zone « basse » doit compter.
        detection = Detection(x1=0.4, y1=0.3, x2=0.6, y2=0.9, confidence=0.9)
        haute = [(0.0, 0.0), (1.0, 0.0), (1.0, 0.7), (0.0, 0.7)]
        basse = [(0.0, 0.7), (1.0, 0.7), (1.0, 1.0), (0.0, 1.0)]
        counts = assign_to_zones([detection], [("haute", haute), ("basse", basse)])
        assert counts == {"haute": 0, "basse": 1}

    def test_empty_zones_report_zero_not_missing(self):
        # Un poste vide doit apparaître à 0 : c'est une mesure, pas un trou.
        counts = assign_to_zones([], [("poste-01", SQUARE)])
        assert counts == {"poste-01": 0}

    def test_detection_counted_once_when_zones_overlap(self):
        detection = Detection(x1=0.4, y1=0.4, x2=0.6, y2=0.5, confidence=0.9)
        overlapping = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        counts = assign_to_zones(
            [detection], [("a", overlapping), ("b", overlapping)]
        )
        # Sans cette garantie, le taux d'occupation pourrait dépasser 100 %.
        assert sum(counts.values()) == 1
        assert counts["a"] == 1

    def test_multiple_people_in_one_zone(self):
        detections = [
            Detection(0.1, 0.5, 0.2, 0.9, 0.9),
            Detection(0.3, 0.5, 0.4, 0.9, 0.8),
            Detection(0.8, 0.5, 0.9, 0.9, 0.7),
        ]
        left = [(0.0, 0.0), (0.5, 0.0), (0.5, 1.0), (0.0, 1.0)]
        right = [(0.5, 0.0), (1.0, 0.0), (1.0, 1.0), (0.5, 1.0)]
        counts = assign_to_zones(detections, [("gauche", left), ("droite", right)])
        assert counts == {"gauche": 2, "droite": 1}

    def test_person_outside_every_zone_is_dropped(self):
        detection = Detection(0.9, 0.05, 0.95, 0.1, 0.9)
        zone = [(0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0)]
        assert assign_to_zones([detection], [("poste", zone)]) == {"poste": 0}


class TestNonMaxSuppression:
    def test_suppresses_overlapping_boxes(self):
        boxes = np.array([[0.0, 0.0, 10.0, 10.0], [1.0, 1.0, 11.0, 11.0]])
        scores = np.array([0.9, 0.8])
        assert non_max_suppression(boxes, scores, 0.45) == [0]

    def test_keeps_distinct_boxes(self):
        boxes = np.array([[0.0, 0.0, 10.0, 10.0], [50.0, 50.0, 60.0, 60.0]])
        scores = np.array([0.9, 0.8])
        assert sorted(non_max_suppression(boxes, scores, 0.45)) == [0, 1]

    def test_empty_input(self):
        assert non_max_suppression(np.empty((0, 4)), np.empty(0), 0.45) == []

    def test_highest_score_wins(self):
        boxes = np.array([[0.0, 0.0, 10.0, 10.0], [0.5, 0.5, 10.5, 10.5]])
        scores = np.array([0.4, 0.95])
        assert non_max_suppression(boxes, scores, 0.45) == [1]


def test_detection_anchor():
    detection = Detection(x1=0.2, y1=0.1, x2=0.4, y2=0.8, confidence=0.5)
    assert detection.anchor == pytest.approx((0.3, 0.8))
