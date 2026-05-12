from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.services.gliner_runner import Prediction
from app.services.taxonomy import map_to_nitro


TEXT_COLUMNS = ("text", "entity_text", "value", "span", "pii_text")
LABEL_COLUMNS = ("label", "entity_type", "type", "taxonomy", "pii_type")


@dataclass(frozen=True)
class GroundTruthEntity:
    text: str
    label: str
    page: int | None = None
    start: int | None = None
    end: int | None = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "label": self.label,
            "page": self.page,
            "start": self.start,
            "end": self.end,
        }


@dataclass(frozen=True)
class EvaluationResult:
    metrics: dict
    matches: list[dict]


def load_ground_truth(csv_path: Path) -> list[GroundTruthEntity]:
    frame = pd.read_csv(csv_path)
    normalized_columns = {column.lower().strip(): column for column in frame.columns}

    text_column = _find_column(normalized_columns, TEXT_COLUMNS)
    label_column = _find_column(normalized_columns, LABEL_COLUMNS)

    if text_column is None or label_column is None:
        raise ValueError(
            "Ground truth CSV must include a text column and a label column. "
            f"Found columns: {', '.join(frame.columns)}"
        )

    entities: list[GroundTruthEntity] = []
    for row in frame.to_dict(orient="records"):
        text = str(row.get(text_column, "")).strip()
        raw_label = str(row.get(label_column, "")).strip()

        if not text or not raw_label:
            continue

        entities.append(
            GroundTruthEntity(
                text=text,
                label=map_to_nitro(raw_label),
                page=_optional_int(row.get("page")),
                start=_optional_int(row.get("start")),
                end=_optional_int(row.get("end")),
            )
        )

    return entities


def compare_predictions(
    predictions: list[Prediction],
    ground_truth: list[GroundTruthEntity],
) -> EvaluationResult:
    unused_ground_truth = set(range(len(ground_truth)))
    matches: list[dict] = []
    true_positive_predictions: set[int] = set()

    for prediction_index, prediction in enumerate(predictions):
        matched_index = _find_exact_match(prediction, ground_truth, unused_ground_truth)

        if matched_index is None:
            matches.append(
                {
                    "status": "false_positive",
                    "prediction": prediction.to_dict(),
                    "ground_truth": None,
                }
            )
            continue

        unused_ground_truth.remove(matched_index)
        true_positive_predictions.add(prediction_index)
        matches.append(
            {
                "status": "true_positive",
                "prediction": prediction.to_dict(),
                "ground_truth": ground_truth[matched_index].to_dict(),
            }
        )

    for ground_truth_index in sorted(unused_ground_truth):
        matches.append(
            {
                "status": "false_negative",
                "prediction": None,
                "ground_truth": ground_truth[ground_truth_index].to_dict(),
            }
        )

    true_positives = len(true_positive_predictions)
    false_positives = len(predictions) - true_positives
    false_negatives = len(unused_ground_truth)

    metrics = {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": _safe_divide(true_positives, true_positives + false_positives),
        "recall": _safe_divide(true_positives, true_positives + false_negatives),
        "f1": _f1(true_positives, false_positives, false_negatives),
        "by_label": _metrics_by_label(predictions, ground_truth, matches),
    }

    return EvaluationResult(metrics=metrics, matches=matches)


def _find_column(normalized_columns: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in normalized_columns:
            return normalized_columns[candidate]
    return None


def _find_exact_match(
    prediction: Prediction,
    ground_truth: list[GroundTruthEntity],
    unused_ground_truth: set[int],
) -> int | None:
    prediction_text = _normalize_text(prediction.text)
    prediction_label = map_to_nitro(prediction.taxonomy_label)

    for ground_truth_index in unused_ground_truth:
        expected = ground_truth[ground_truth_index]
        if _normalize_text(expected.text) == prediction_text and expected.label == prediction_label:
            return ground_truth_index

    return None


def _metrics_by_label(
    predictions: list[Prediction],
    ground_truth: list[GroundTruthEntity],
    matches: list[dict],
) -> dict[str, dict[str, float | int]]:
    labels = {
        *(prediction.taxonomy_label for prediction in predictions),
        *(entity.label for entity in ground_truth),
    }

    by_label: dict[str, dict[str, float | int]] = {}
    for label in sorted(labels):
        tp = sum(1 for match in matches if match["status"] == "true_positive" and _match_label(match) == label)
        fp = sum(1 for match in matches if match["status"] == "false_positive" and _match_label(match) == label)
        fn = sum(1 for match in matches if match["status"] == "false_negative" and _match_label(match) == label)

        by_label[label] = {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": _safe_divide(tp, tp + fp),
            "recall": _safe_divide(tp, tp + fn),
            "f1": _f1(tp, fp, fn),
        }

    return by_label


def _match_label(match: dict) -> str:
    if match["prediction"]:
        return match["prediction"]["taxonomy_label"]
    return match["ground_truth"]["label"]


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _f1(true_positives: int, false_positives: int, false_negatives: int) -> float:
    precision = _safe_divide(true_positives, true_positives + false_positives)
    recall = _safe_divide(true_positives, true_positives + false_negatives)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def _optional_int(value: object) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)

