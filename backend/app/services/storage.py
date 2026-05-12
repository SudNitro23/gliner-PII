from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile


async def save_upload(upload: UploadFile, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "upload.bin").name
    target_path = run_dir / safe_name

    content = await upload.read()
    target_path.write_bytes(content)
    return target_path

