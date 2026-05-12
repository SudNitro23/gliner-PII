from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="GLiNER-PII Evaluation API",
        version="0.1.0",
        description="Local MVP API for evaluating GLiNER-PII predictions against PDF ground truth.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_db(settings.sqlite_path)
    app.include_router(router)
    return app


app = create_app()

