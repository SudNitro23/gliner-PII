from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def init_db(sqlite_path: Path) -> None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                pdf_filenames_json TEXT NOT NULL,
                pdf_count INTEGER NOT NULL,
                ground_truth_filename TEXT NOT NULL,
                csv_text_column TEXT NOT NULL,
                csv_label_column TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                pdf_filename TEXT NOT NULL,
                ground_truth_filename TEXT NOT NULL,
                status TEXT NOT NULL,
                metrics_json TEXT,
                predictions_json TEXT,
                matches_json TEXT,
                model_status TEXT,
                error TEXT
            )
            """
        )


def insert_dataset(
    sqlite_path: Path,
    dataset_id: str,
    *,
    name: str,
    pdf_filenames: list[str],
    ground_truth_filename: str,
    csv_text_column: str,
    csv_label_column: str,
    storage_path: str,
) -> None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            INSERT INTO datasets (
                id,
                created_at,
                name,
                pdf_filenames_json,
                pdf_count,
                ground_truth_filename,
                csv_text_column,
                csv_label_column,
                storage_path,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                datetime.now(UTC).isoformat(),
                name,
                json.dumps(pdf_filenames),
                len(pdf_filenames),
                ground_truth_filename,
                csv_text_column,
                csv_label_column,
                storage_path,
                "uploaded",
            ),
        )


def get_dataset(sqlite_path: Path, dataset_id: str) -> dict[str, Any] | None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM datasets WHERE id = ?",
            (dataset_id,),
        ).fetchone()

    return _dataset_row_to_record(row) if row else None


def list_datasets(sqlite_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT *
            FROM datasets
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_dataset_row_to_record(row) for row in rows]


def insert_evaluation(
    sqlite_path: Path,
    evaluation_id: str,
    pdf_filename: str,
    ground_truth_filename: str,
) -> None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            INSERT INTO evaluations (
                id,
                created_at,
                pdf_filename,
                ground_truth_filename,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                datetime.now(UTC).isoformat(),
                pdf_filename,
                ground_truth_filename,
                "running",
            ),
        )


def update_evaluation(
    sqlite_path: Path,
    evaluation_id: str,
    *,
    status: str,
    metrics: dict[str, Any] | None = None,
    predictions: list[dict[str, Any]] | None = None,
    matches: list[dict[str, Any]] | None = None,
    model_status: str | None = None,
    error: str | None = None,
) -> None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            UPDATE evaluations
            SET status = ?,
                metrics_json = ?,
                predictions_json = ?,
                matches_json = ?,
                model_status = ?,
                error = ?
            WHERE id = ?
            """,
            (
                status,
                json.dumps(metrics) if metrics is not None else None,
                json.dumps(predictions) if predictions is not None else None,
                json.dumps(matches) if matches is not None else None,
                model_status,
                error,
                evaluation_id,
            ),
        )


def get_evaluation(sqlite_path: Path, evaluation_id: str) -> dict[str, Any] | None:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM evaluations WHERE id = ?",
            (evaluation_id,),
        ).fetchone()

    return _row_to_record(row) if row else None


def list_evaluations(sqlite_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    with sqlite3.connect(sqlite_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT *
            FROM evaluations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_row_to_record(row) for row in rows]


def _row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "pdf_filename": row["pdf_filename"],
        "ground_truth_filename": row["ground_truth_filename"],
        "status": row["status"],
        "metrics": json.loads(row["metrics_json"]) if row["metrics_json"] else None,
        "predictions": json.loads(row["predictions_json"]) if row["predictions_json"] else [],
        "matches": json.loads(row["matches_json"]) if row["matches_json"] else [],
        "model_status": row["model_status"],
        "error": row["error"],
    }


def _dataset_row_to_record(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "name": row["name"],
        "pdf_filenames": json.loads(row["pdf_filenames_json"]),
        "pdf_count": row["pdf_count"],
        "ground_truth_filename": row["ground_truth_filename"],
        "csv_text_column": row["csv_text_column"],
        "csv_label_column": row["csv_label_column"],
        "storage_path": row["storage_path"],
        "status": row["status"],
        "error": row["error"],
    }
