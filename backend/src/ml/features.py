"""Image feature extraction for wound risk estimation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import cv2
import numpy as np


@dataclass
class FeatureSignals:
    """Container for heuristic feature signals."""

    periwound_redness: float
    exudate_proxy: float
    dark_tissue_proxy: float
    swelling_proxy: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "periwound_redness": self.periwound_redness,
            "exudate_proxy": self.exudate_proxy,
            "dark_tissue_proxy": self.dark_tissue_proxy,
            "swelling_proxy": self.swelling_proxy,
        }


class FeatureExtractor:
    """Extracts heuristic features from a wound image."""

    def extract(self, image_bgr: np.ndarray) -> FeatureSignals:
        """Extract signals from a BGR image.

        Args:
            image_bgr: Image as a BGR uint8 numpy array.
        """
        wound_mask = self._segment_wound(image_bgr)
        periwound_mask = self._periwound_ring(wound_mask, ring_width=18)

        redness = self._periwound_redness(image_bgr, periwound_mask)
        exudate = self._exudate_proxy(image_bgr, wound_mask)
        dark = self._dark_tissue_proxy(image_bgr, wound_mask)
        swelling = self._swelling_proxy(image_bgr, periwound_mask)

        return FeatureSignals(
            periwound_redness=redness,
            exudate_proxy=exudate,
            dark_tissue_proxy=dark,
            swelling_proxy=swelling,
        )

    def _segment_wound(self, image_bgr: np.ndarray) -> np.ndarray:
        """Approximate wound segmentation using GrabCut with fallback."""
        height, width = image_bgr.shape[:2]
        mask = np.zeros((height, width), np.uint8)
        rect = (int(width * 0.1), int(height * 0.1), int(width * 0.8), int(height * 0.8))
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(image_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            wound_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype("uint8")
        except cv2.error:
            wound_mask = self._fallback_otsu(image_bgr)

        wound_mask = cv2.morphologyEx(wound_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        return wound_mask

    def _fallback_otsu(self, image_bgr: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return (thresh == 0).astype("uint8")

    def _periwound_ring(self, wound_mask: np.ndarray, ring_width: int) -> np.ndarray:
        kernel = np.ones((ring_width, ring_width), np.uint8)
        dilated = cv2.dilate(wound_mask, kernel, iterations=1)
        eroded = cv2.erode(wound_mask, kernel, iterations=1)
        ring = np.clip(dilated - eroded, 0, 1).astype("uint8")
        return ring

    def _periwound_redness(self, image_bgr: np.ndarray, periwound_mask: np.ndarray) -> float:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        h, s, _ = cv2.split(hsv)
        red_mask = ((h < 10) | (h > 160)) & (s > 80)
        region = periwound_mask.astype(bool)
        if region.sum() == 0:
            return 0.0
        return float(red_mask[region].mean())

    def _exudate_proxy(self, image_bgr: np.ndarray, wound_mask: np.ndarray) -> float:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        exudate_mask = (h > 20) & (h < 90) & (s > 60) & (v > 80)
        region = wound_mask.astype(bool)
        if region.sum() == 0:
            return 0.0
        return float(exudate_mask[region].mean())

    def _dark_tissue_proxy(self, image_bgr: np.ndarray, wound_mask: np.ndarray) -> float:
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
        _, _, v = cv2.split(hsv)
        dark_mask = v < 40
        region = wound_mask.astype(bool)
        if region.sum() == 0:
            return 0.0
        return float(dark_mask[region].mean())

    def _swelling_proxy(self, image_bgr: np.ndarray, periwound_mask: np.ndarray) -> float:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 120)
        region = periwound_mask.astype(bool)
        if region.sum() == 0:
            return 0.0
        return float((edges > 0)[region].mean())
