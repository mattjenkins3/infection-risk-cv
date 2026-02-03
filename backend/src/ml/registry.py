"""Model registry for swapping heuristic vs learned models."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from .features import FeatureExtractor
from .scoring import RiskResult, RiskScorer


class RiskModel(Protocol):
    """Protocol for risk models."""

    def predict(self, image_bgr: np.ndarray) -> RiskResult:
        ...


@dataclass
class HeuristicRiskModel:
    """Heuristic model using hand-crafted features."""

    weights_path: Path

    def __post_init__(self) -> None:
        self.extractor = FeatureExtractor()
        self.scorer = RiskScorer(self.weights_path)

    def predict(self, image_bgr: np.ndarray) -> RiskResult:
        signals = self.extractor.extract(image_bgr)
        return self.scorer.score(signals)


@dataclass
class TorchModelStub:
    """Placeholder for a future PyTorch model."""

    model_path: Path

    def predict(self, image_bgr: np.ndarray) -> RiskResult:
        raise NotImplementedError(
            "TODO: Load and run a trained PyTorch model, then map outputs to RiskResult."
        )


def load_model(model_name: str, weights_path: Path, model_path: Path | None = None) -> RiskModel:
    """Load a risk model based on configuration.

    Args:
        model_name: Either 'heuristic' or 'torch'.
        weights_path: Path to scoring weights (heuristic).
        model_path: Optional path to a trained model (torch).
    """
    if model_name == "torch":
        if model_path is None:
            raise ValueError("model_path is required for torch model")
        return TorchModelStub(model_path=model_path)
    return HeuristicRiskModel(weights_path=weights_path)
