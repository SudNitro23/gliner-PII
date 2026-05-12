from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_path(raw_value: str, default: Path) -> Path:
    value = os.getenv(raw_value)
    if not value:
        return default

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


@dataclass(frozen=True)
class Settings:
    gliner_model_path: Path | None
    gliner_threshold: float
    data_dir: Path
    sqlite_path: Path
    cors_origins: list[str]


def load_settings() -> Settings:
    model_path_value = os.getenv("GLINER_MODEL_PATH")
    model_path = Path(model_path_value).expanduser() if model_path_value else None

    if model_path and not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path

    data_dir = _resolve_path("APP_DATA_DIR", PROJECT_ROOT / "backend" / "data")
    sqlite_path = _resolve_path("SQLITE_PATH", data_dir / "evaluations.sqlite3")

    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")

    return Settings(
        gliner_model_path=model_path,
        gliner_threshold=float(os.getenv("GLINER_THRESHOLD", "0.5")),
        data_dir=data_dir,
        sqlite_path=sqlite_path,
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )


settings = load_settings()

