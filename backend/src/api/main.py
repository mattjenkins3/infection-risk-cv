"""FastAPI application for wound infection risk estimation."""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.ml.registry import load_model
from src.utils.network import get_lan_ip

LOGGER = logging.getLogger("wound-risk")

MAX_FILE_BYTES = 5 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/heic", "image/heif"}

app = FastAPI(title="Wound Infection Risk API", version="0.1.0")
WEB_DIR = Path(__file__).resolve().parent / "web"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


class Signal(BaseModel):
    name: str
    value: float
    weight: float
    note: str


class AssessResponse(BaseModel):
    risk_score: float
    risk_level: str
    signals: List[Signal]
    explanation: str
    disclaimer: str
    recommended_next_steps: List[str]


@app.on_event("startup")
async def startup_event() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    lan_ip = get_lan_ip()
    LOGGER.info("Backend running. iPhone app can connect at: http://%s:8000", lan_ip)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.post("/assess", response_model=AssessResponse)
async def assess(file: UploadFile = File(...)) -> JSONResponse:
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPG or PNG image.")

    contents = await file.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Limit is 5MB.")

    image = _decode_image(contents)
    if image is None:
        raise HTTPException(status_code=400, detail="Unable to decode image.")

    model = load_model(
        model_name="heuristic",
        weights_path=Path(__file__).resolve().parents[2] / "config" / "weights.yaml",
    )
    result = model.predict(image)
    response = AssessResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        signals=[Signal(**detail.__dict__) for detail in result.signals],
        explanation=result.explanation,
        disclaimer=result.disclaimer,
        recommended_next_steps=result.recommended_next_steps,
    )
    return JSONResponse(content=response.dict())


def _decode_image(contents: bytes) -> np.ndarray | None:
    """Decode image bytes into BGR array and strip metadata."""
    try:
        image_array = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    except Exception:  # noqa: BLE001
        return None

    if image is None:
        return None

    _ = io.BytesIO()
    return image
