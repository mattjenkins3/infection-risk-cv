from pathlib import Path

from src.ml.features import FeatureSignals
from src.ml.scoring import RiskScorer


def test_scoring_outputs_expected_level() -> None:
    scorer = RiskScorer(Path(__file__).resolve().parents[1] / "config" / "weights.yaml")
    signals = FeatureSignals(0.9, 0.1, 0.1, 0.1)
    result = scorer.score(signals)
    assert result.risk_score >= 0.0
    assert result.risk_level in {"low", "medium", "high"}
    assert result.explanation
