# GLiNER-PII Evaluation Platform

Local MVP for evaluating NVIDIA GLiNER-PII predictions against manually annotated PDF ground truth.

## What This Repo Contains

- `backend/`: FastAPI service for PDF extraction, model inference, taxonomy mapping, evaluation, and SQLite persistence.
- `frontend/`: Next.js UI for uploading a PDF and ground-truth CSV, running an evaluation, and viewing metrics.
- `scripts/`: local helper scripts.

This is intentionally local-first. Docker, AWS, S3, DynamoDB, and production deployment are future scope.

## MVP Architecture

```text
User
  -> Next.js frontend
  -> Dataset ingestion API
  -> Local dataset storage
  -> FastAPI backend
  -> PyMuPDF PDF text extraction
  -> GLiNER-PII prediction
  -> Nitro taxonomy mapping
  -> Ground truth CSV comparison
  -> SQLite evaluation record
  -> Next.js results view
```

The frontend is responsible for selecting a PDF, selecting a ground-truth CSV, choosing a model threshold, and displaying evaluation output.

The backend owns the evaluation pipeline. It extracts text from the PDF, runs GLiNER predictions, maps model labels into Nitro's PII taxonomy, loads the manually annotated CSV, computes metrics, and stores the run locally.

## Project Flow

1. Start the FastAPI service.
2. Start the Next.js app.
3. Upload one or more source PDFs and one ground-truth CSV.
4. The dataset ingestion API validates the CSV columns and stores all uploaded files locally.
5. A later evaluation run extracts PDF text and runs the PII detector.
6. Predictions are normalized into Nitro taxonomy labels.
7. Predictions are compared with the CSV annotations.
8. Precision, recall, F1, TP, FP, and FN results are returned to the UI.

## Dataset Ingestion

The dataset ingestion endpoint is:

```text
POST /api/datasets
```

It accepts:

- multiple PDF files under `pdfs`
- one ground-truth CSV under `ground_truth`
- an optional dataset name under `name`

For the MVP, uploaded files are stored under:

```text
backend/data/datasets/<dataset_id>/
```

The CSV is validated before the dataset is recorded. At minimum, the file must contain:

- one supported text column such as `text` or `entity_text`
- one supported label column such as `label` or `entity_type`

## Expected Ground Truth CSV

The evaluator accepts flexible column names, but the simplest format is:

```csv
text,label
"Jane Smith",PERSON_NAME
"jane@example.com",EMAIL_ADDRESS
```

Supported text columns include `text`, `entity_text`, `value`, `span`, and `pii_text`.
Supported label columns include `label`, `entity_type`, `type`, `taxonomy`, and `pii_type`.

## Local Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Set `GLINER_MODEL_PATH` to the local Hugging Face model checkout. If this repo sits next to the model folder, that path will usually be something like:

```text
/Users/you/projects/gliner-PII
```

Install and run the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Install and run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

## Current MVP Behavior

The backend will use the configured GLiNER model when the `gliner` package and model path are available. If the model cannot be loaded, the service falls back to a small regex-based development detector for emails, phone numbers, and SSN-like values so the UI and evaluation flow can still be tested.

Evaluation is currently exact normalized `text + label` matching. That keeps the MVP transparent and easy to inspect before adding span overlap, page-aware matching, or fuzzy matching.
