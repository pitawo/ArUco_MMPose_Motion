from __future__ import annotations

from src.common.validators import is_valid_xy


def mask_low_confidence(keypoints: list[list[float]], threshold: float) -> list[list[float]]:
    """Replace low-confidence keypoints with NaN placeholders.

    Input format: [[x, y, score], ...]
    """
    filtered: list[list[float]] = []
    for kpt in keypoints:
        if len(kpt) < 3:
            filtered.append(kpt)
            continue
        x, y, score = kpt[0], kpt[1], kpt[2]
        if score < threshold:
            filtered.append([float("nan"), float("nan"), score])
        else:
            filtered.append([x, y, score])
    return filtered


def count_valid_keypoints(keypoints: list[list[float]]) -> int:
    return sum(1 for kpt in keypoints if len(kpt) >= 3 and is_valid_xy(kpt))
