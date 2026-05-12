from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.services.taxonomy import map_to_nitro, model_labels


@dataclass(frozen=True)
class Prediction:
    text: str
    label: str
    taxonomy_label: str
    start: int | None = None
    end: int | None = None
    score: float | None = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "label": self.label,
            "taxonomy_label": self.taxonomy_label,
            "start": self.start,
            "end": self.end,
            "score": self.score,
        }


@dataclass(frozen=True)
class PredictionResult:
    predictions: list[Prediction]
    model_status: str


class GLiNERService:
    def __init__(self, model_path: Path | None, threshold: float = 0.5) -> None:
        self.model_path = model_path
        self.threshold = threshold

    def predict(self, text: str) -> PredictionResult:
        if not text:
            return PredictionResult(predictions=[], model_status="empty-document")

        if self.model_path is not None:
            try:
                return self._predict_with_gliner(text)
            except Exception as exc:
                fallback = self._regex_fallback(text)
                return PredictionResult(
                    predictions=fallback,
                    model_status=f"regex-dev-fallback: GLiNER unavailable ({exc})",
                )

        return PredictionResult(
            predictions=self._regex_fallback(text),
            model_status="regex-dev-fallback: GLINER_MODEL_PATH is not configured",
        )

    def _predict_with_gliner(self, text: str) -> PredictionResult:
        try:
            from gliner import GLiNER
        except ImportError as exc:
            raise RuntimeError("gliner package is not installed") from exc

        if self.model_path is None:
            raise RuntimeError("GLINER_MODEL_PATH is not configured")

        model = GLiNER.from_pretrained(str(self.model_path), local_files_only=True)
        entities = model.predict_entities(
            text,
            labels=model_labels(),
            threshold=self.threshold,
        )

        predictions = [
            Prediction(
                text=str(entity.get("text", "")),
                label=str(entity.get("label", "")),
                taxonomy_label=map_to_nitro(str(entity.get("label", ""))),
                start=_optional_int(entity.get("start")),
                end=_optional_int(entity.get("end")),
                score=_optional_float(entity.get("score")),
            )
            for entity in entities
            if entity.get("text")
        ]
        return PredictionResult(predictions=predictions, model_status="gliner")

    def _regex_fallback(self, text: str) -> list[Prediction]:
        patterns = [
            ("email", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            ("phone", r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
            ("ssn", r"\b\d{3}-\d{2}-\d{4}\b"),
        ]

        predictions: list[Prediction] = []
        for label, pattern in patterns:
            for match in re.finditer(pattern, text):
                predictions.append(
                    Prediction(
                        text=match.group(0),
                        label=label,
                        taxonomy_label=map_to_nitro(label),
                        start=match.start(),
                        end=match.end(),
                        score=1.0,
                    )
                )

        return sorted(predictions, key=lambda prediction: prediction.start or 0)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)

