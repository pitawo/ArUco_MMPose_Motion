from __future__ import annotations

import math
from typing import Sequence


def is_valid_xy(kp: Sequence[float]) -> bool:
    """Keypoint has usable x, y (non-NaN)."""
    if len(kp) < 2:
        return False
    x, y = kp[0], kp[1]
    return not (math.isnan(x) or math.isnan(y))


def is_valid_xyz(kp: Sequence[float]) -> bool:
    """3D keypoint has usable x, y, z (non-NaN)."""
    if len(kp) < 3:
        return False
    x, y, z = kp[0], kp[1], kp[2]
    return not (math.isnan(x) or math.isnan(y) or math.isnan(z))


def count_valid_xy(keypoints: Sequence[Sequence[float]]) -> int:
    return sum(1 for kp in keypoints if is_valid_xy(kp))


def count_valid_xyz(keypoints: Sequence[Sequence[float]]) -> int:
    return sum(1 for kp in keypoints if is_valid_xyz(kp))
