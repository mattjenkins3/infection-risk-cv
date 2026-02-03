import numpy as np

from src.ml.features import FeatureExtractor


def test_feature_extraction_returns_ranges() -> None:
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image[32:96, 32:96, :] = [10, 10, 200]

    extractor = FeatureExtractor()
    signals = extractor.extract(image)

    for value in signals.as_dict().values():
        assert 0.0 <= value <= 1.0
