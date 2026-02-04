"""Scoring logic for infection risk estimation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml

from .features import FeatureSignals


@dataclass
class SymptomInputs:
    """Container for user-reported symptom inputs."""

    reported_pain: bool
    reported_warmth: bool
    reported_swelling: bool
    reported_drainage: bool
    reported_spreading_redness: bool

    def as_dict(self) -> Dict[str, float]:
        return {
            "reported_pain": 1.0 if self.reported_pain else 0.0,
            "reported_warmth": 1.0 if self.reported_warmth else 0.0,
            "reported_swelling": 1.0 if self.reported_swelling else 0.0,
            "reported_drainage": 1.0 if self.reported_drainage else 0.0,
            "reported_spreading_redness": 1.0 if self.reported_spreading_redness else 0.0,
        }


@dataclass
class SignalDetail:
    name: str
    value: float
    weight: float
    note: str


@dataclass
class RiskResult:
    risk_score: float
    risk_level: str
    signals: List[SignalDetail]
    explanation: str
    disclaimer: str
    recommended_next_steps: List[str]


class RiskScorer:
    """Combine feature signals into a risk score using configured weights."""

    def __init__(self, weights_path: Path) -> None:
        self.weights = self._load_weights(weights_path)

    def score(self, signals: FeatureSignals, symptoms: SymptomInputs | None = None) -> RiskResult:
        signals_dict = signals.as_dict()
        weighted_sum = self.weights.get("bias", 0.0)
        details: List[SignalDetail] = []
        for name, value in signals_dict.items():
            weight = float(self.weights.get(name, 0.0))
            weighted_sum += weight * value
            details.append(
                SignalDetail(
                    name=name,
                    value=float(value),
                    weight=weight,
                    note=self._signal_note(name, value),
                )
            )

        if symptoms is not None:
            for name, value in symptoms.as_dict().items():
                weight = float(self.weights.get(name, 0.0))
                weighted_sum += weight * value
                details.append(
                    SignalDetail(
                        name=name,
                        value=float(value),
                        weight=weight,
                        note=self._signal_note(name, value),
                    )
                )

        risk_score = min(max(weighted_sum, 0.0), 1.0)
        risk_level = self._risk_level(risk_score)
        explanation = self._explanation(details, risk_level)
        return RiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            signals=details,
            explanation=explanation,
            disclaimer=(
                "This output is a non-diagnostic risk estimation for triage support only. "
                "It cannot diagnose infection and should not replace clinical evaluation."
            ),
            recommended_next_steps=self._recommended_steps(risk_level),
        )

    def _load_weights(self, weights_path: Path) -> Dict[str, float]:
        with weights_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return {key: float(value) for key, value in data.items()}

    def _risk_level(self, score: float) -> str:
        if score >= 0.66:
            return "high"
        if score >= 0.33:
            return "medium"
        return "low"

    def _signal_note(self, name: str, value: float) -> str:
        notes = {
            "periwound_redness": "Higher redness near the wound boundary may be associated with irritation.",
            "exudate_proxy": "Yellow/green coloration can be a proxy for exudate-like appearance.",
            "dark_tissue_proxy": "Darker regions may indicate non-viable tissue presence.",
            "swelling_proxy": "Edge sharpness can be a proxy for localized swelling cues.",
            "reported_pain": "Pain or tenderness near the wound can be a reported symptom of irritation.",
            "reported_warmth": "A warm or hot sensation around the wound can indicate inflammation.",
            "reported_swelling": "Swelling around the wound can be a sign of irritation or inflammation.",
            "reported_drainage": "Drainage or pus-like fluid can be a reported sign of infection.",
            "reported_spreading_redness": "Redness spreading beyond the wound may indicate inflammation.",
        }
        base = notes.get(name, "Signal observed in the image.")
        return f"{base} Signal intensity: {value:.2f}."

    def _explanation(self, details: List[SignalDetail], level: str) -> str:
        visual_details = [detail for detail in details if detail.name in self._visual_signal_names()]
        symptom_details = [
            detail for detail in details if detail.name in self._symptom_signal_names() and detail.value > 0.5
        ]

        visual_summary = self._visual_summary(visual_details)
        symptom_summary = self._symptom_summary(symptom_details)

        return (
            f"Estimated risk level: {level}. {visual_summary} {symptom_summary} "
            "This is a triage support estimate, not a diagnosis."
        )

    def _visual_signal_names(self) -> List[str]:
        return ["periwound_redness", "exudate_proxy", "dark_tissue_proxy", "swelling_proxy"]

    def _symptom_signal_names(self) -> List[str]:
        return [
            "reported_pain",
            "reported_warmth",
            "reported_swelling",
            "reported_drainage",
            "reported_spreading_redness",
        ]

    def _visual_summary(self, details: List[SignalDetail]) -> str:
        cues: List[str] = []
        signal_map = {detail.name: detail.value for detail in details}
        if signal_map.get("periwound_redness", 0.0) >= 0.35:
            cues.append("notable redness around the wound edges")
        if signal_map.get("exudate_proxy", 0.0) >= 0.25:
            cues.append("yellow/green drainage or pus-like coloration")
        if signal_map.get("dark_tissue_proxy", 0.0) >= 0.2:
            cues.append("darkened tissue inside the wound")
        if signal_map.get("swelling_proxy", 0.0) >= 0.2:
            cues.append("edge texture changes consistent with swelling")

        if cues:
            return f"Visual cues suggest {', '.join(cues)}."
        return "No strong visual cues like redness, drainage, or swelling were detected."

    def _symptom_summary(self, details: List[SignalDetail]) -> str:
        if not details:
            return "No concerning symptoms were reported in the questionnaire."

        symptom_phrases = {
            "reported_pain": "pain or tenderness",
            "reported_warmth": "warmth around the wound",
            "reported_swelling": "swelling",
            "reported_drainage": "drainage/pus",
            "reported_spreading_redness": "spreading redness",
        }
        cues = [symptom_phrases.get(detail.name, detail.name.replace("_", " ")) for detail in details]
        return f"Reported symptoms include {', '.join(cues)}."

    def _recommended_steps(self, level: str) -> List[str]:
        if level == "high":
            return [
                "Consider scheduling a clinical check if symptoms persist or worsen.",
                "Monitor for changes such as increasing redness, swelling, or drainage.",
            ]
        if level == "medium":
            return [
                "Continue monitoring and recheck if the appearance changes.",
                "Seek clinical advice if you are concerned about progression.",
            ]
        return [
            "Keep monitoring for noticeable changes over time.",
            "If you have concerns, seek clinical guidance.",
        ]
