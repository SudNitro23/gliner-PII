# GLiNER-PII Evaluation Platform

Local MVP for evaluating NVIDIA GLiNER-PII predictions against manually annotated PDF ground truth.

## What This Repo Contains

- `backend/`: FastAPI service for PDF extraction, model inference, taxonomy mapping, evaluation, and SQLite persistence.
- `frontend/`: Next.js UI for uploading a PDF and ground-truth CSV, running an evaluation, and viewing metrics.
- `scripts/`: local helper scripts.

This is intentionally local-first. Docker, AWS, S3, DynamoDB, and production deployment are future scope.

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

