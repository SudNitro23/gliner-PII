from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EvaluationResponse(BaseModel):
    id: str
    created_at: str | None = None
    pdf_filename: str
    ground_truth_filename: str
    status: str
    metrics: dict[str, Any] | None = None
    predictions: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    model_status: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str

