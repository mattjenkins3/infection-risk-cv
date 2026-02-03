from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def _make_image_bytes() -> bytes:
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    image[16:48, 16:48] = [0, 0, 255]
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_assess_happy_path() -> None:
    image_bytes = _make_image_bytes()
    response = client.post(
        "/assess",
        files={"file": ("test.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "risk_score" in payload
    assert "signals" in payload


def test_assess_invalid_file_type() -> None:
    response = client.post(
        "/assess",
        files={"file": ("test.txt", b"notanimage", "text/plain")},
    )
    assert response.status_code == 400
