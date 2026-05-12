from __future__ import annotations

import shutil
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.database import (
    get_dataset,
    get_evaluation,
    insert_dataset,
    insert_evaluation,
    list_datasets,
    list_evaluations,
    update_evaluation,
)
from app.schemas import DatasetResponse, EvaluationResponse, HealthResponse
from app.services.evaluator import compare_predictions, load_ground_truth, validate_ground_truth_csv
from app.services.gliner_runner import GLiNERService
from app.services.pdf_extractor import extract_pdf_text
from app.services.storage import save_upload, save_uploads

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="gliner-pii-evaluation-api")


@router.get("/api/evaluations", response_model=list[EvaluationResponse])
def evaluations() -> list[dict]:
    return list_evaluations(settings.sqlite_path)


@router.get("/api/datasets", response_model=list[DatasetResponse])
def datasets() -> list[dict]:
    return list_datasets(settings.sqlite_path)


@router.get("/api/datasets/{dataset_id}", response_model=DatasetResponse)
def dataset(dataset_id: str) -> dict:
    record = get_dataset(settings.sqlite_path, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return record


@router.post("/api/datasets", response_model=DatasetResponse)
async def create_dataset(
    pdfs: list[UploadFile] = File(...),
    ground_truth: UploadFile = File(...),
    name: str | None = Form(default=None),
) -> dict:
    if not pdfs:
        raise HTTPException(status_code=400, detail="At least one PDF must be uploaded")

    invalid_pdf_names = [
        upload.filename or "unnamed"
        for upload in pdfs
        if not upload.filename or not upload.filename.lower().endswith(".pdf")
    ]
    if invalid_pdf_names:
        raise HTTPException(
            status_code=400,
            detail=f"All uploaded PDFs must be .pdf files. Invalid files: {', '.join(invalid_pdf_names)}",
        )

    if not ground_truth.filename or not ground_truth.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Ground truth upload must be a .csv file")

    dataset_id = str(uuid4())
    dataset_name = (name or f"Dataset {dataset_id[:8]}").strip()
    storage_dir = settings.data_dir / "datasets" / dataset_id
    pdf_dir = storage_dir / "pdfs"
    ground_truth_dir = storage_dir / "ground_truth"

    try:
        pdf_paths = await save_uploads(pdfs, pdf_dir)
        ground_truth_path = await save_upload(ground_truth, ground_truth_dir)
        validation = validate_ground_truth_csv(ground_truth_path)
    except ValueError as exc:
        shutil.rmtree(storage_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    insert_dataset(
        settings.sqlite_path,
        dataset_id,
        name=dataset_name,
        pdf_filenames=[path.name for path in pdf_paths],
        ground_truth_filename=ground_truth_path.name,
        csv_text_column=validation.text_column,
        csv_label_column=validation.label_column,
        storage_path=str(storage_dir),
    )

    record = get_dataset(settings.sqlite_path, dataset_id)
    if record is None:
        raise HTTPException(status_code=500, detail="Dataset record was not persisted")
    return record


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
