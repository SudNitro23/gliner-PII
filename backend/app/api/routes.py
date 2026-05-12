from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.database import (
    get_evaluation,
    insert_evaluation,
    list_evaluations,
    update_evaluation,
)
from app.schemas import EvaluationResponse, HealthResponse
from app.services.evaluator import compare_predictions, load_ground_truth
from app.services.gliner_runner import GLiNERService
from app.services.pdf_extractor import extract_pdf_text
from app.services.storage import save_upload

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="gliner-pii-evaluation-api")


@router.get("/api/evaluations", response_model=list[EvaluationResponse])
def evaluations() -> list[dict]:
    return list_evaluations(settings.sqlite_path)


@router.get("/api/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def evaluation(evaluation_id: str) -> dict:
    record = get_evaluation(settings.sqlite_path, evaluation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return record


@router.post("/api/evaluations", response_model=EvaluationResponse)
async def create_evaluation(
    pdf: UploadFile = File(...),
    ground_truth: UploadFile = File(...),
    threshold: float | None = Form(default=None),
) -> dict:
    if not pdf.filename or not pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF upload must be a .pdf file")

    if not ground_truth.filename or not ground_truth.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Ground truth upload must be a .csv file")

    evaluation_id = str(uuid4())
    run_dir = settings.data_dir / "runs" / evaluation_id
    insert_evaluation(settings.sqlite_path, evaluation_id, pdf.filename, ground_truth.filename)

    try:
        pdf_path = await save_upload(pdf, run_dir)
        ground_truth_path = await save_upload(ground_truth, run_dir)

        document = extract_pdf_text(pdf_path)
        model = GLiNERService(
            model_path=settings.gliner_model_path,
            threshold=threshold if threshold is not None else settings.gliner_threshold,
        )
        prediction_result = model.predict(document.text)

        ground_truth_entities = load_ground_truth(ground_truth_path)
        evaluation_result = compare_predictions(
            prediction_result.predictions,
            ground_truth_entities,
        )

        update_evaluation(
            settings.sqlite_path,
            evaluation_id,
            status="completed",
            metrics=evaluation_result.metrics,
            predictions=[prediction.to_dict() for prediction in prediction_result.predictions],
            matches=evaluation_result.matches,
            model_status=prediction_result.model_status,
        )
    except Exception as exc:
        update_evaluation(
            settings.sqlite_path,
            evaluation_id,
            status="failed",
            error=str(exc),
        )

    record = get_evaluation(settings.sqlite_path, evaluation_id)
    if record is None:
        raise HTTPException(status_code=500, detail="Evaluation record was not persisted")
    return record

