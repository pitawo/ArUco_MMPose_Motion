from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.common.deps import import_cv2

if TYPE_CHECKING:
    import numpy as np


# COCO 17-keypoint skeleton connections (0-indexed)
SKELETON = [
    (0, 1), (0, 2), (1, 3), (2, 4),        # head
    (5, 6),                                   # shoulders
    (5, 7), (7, 9),                           # left arm
    (6, 8), (8, 10),                          # right arm
    (5, 11), (6, 12),                         # torso
    (11, 12),                                 # hips
    (11, 13), (13, 15),                       # left leg
    (12, 14), (14, 16),                       # right leg
]

JOINT_COLOR = (0, 255, 0)
RECOVERED_JOINT_COLOR = (0, 255, 255)
LIMB_COLOR = (255, 128, 0)


def _import_cv2() -> Any:
    return import_cv2("visualization")


def prepare_vis_output(path: str) -> str:
    """Create destination directory for visualization video output."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return str(out)


def draw_skeleton(
    frame: "np.ndarray",
    keypoints: list[list[float]],
    recovered_indices: set[int] | None = None,
    radius: int = 4,
    thickness: int = 2,
) -> "np.ndarray":
    """Draw keypoints and skeleton on a single frame."""
    cv2 = _import_cv2()
    overlay = frame.copy()

    # Draw limbs
    for i, j in SKELETON:
        if i >= len(keypoints) or j >= len(keypoints):
            continue
        kp_i, kp_j = keypoints[i], keypoints[j]
        if math.isnan(kp_i[0]) or math.isnan(kp_j[0]):
            continue
        pt1 = (int(kp_i[0]), int(kp_i[1]))
        pt2 = (int(kp_j[0]), int(kp_j[1]))
        cv2.line(overlay, pt1, pt2, LIMB_COLOR, thickness, cv2.LINE_AA)

    recovered = recovered_indices or set()

    # Draw joints
    for idx, kp in enumerate(keypoints):
        if math.isnan(kp[0]):
            continue
        center = (int(kp[0]), int(kp[1]))
        color = RECOVERED_JOINT_COLOR if idx in recovered else JOINT_COLOR
        cv2.circle(overlay, center, radius, color, -1, cv2.LINE_AA)

    return overlay


class PoseVideoWriter:
    """Writes frames with skeleton overlay to an output video."""

    def __init__(self, out_path: str, fps: float, width: int, height: int) -> None:
        self._path = prepare_vis_output(out_path)
        cv2 = _import_cv2()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(self._path, fourcc, fps, (width, height))
        if not self._writer.isOpened():
            raise RuntimeError(f"Failed to open video writer: {self._path}")

    def write_frame(
        self,
        frame: "np.ndarray",
        keypoints: list[list[float]],
        recovered_indices: set[int] | None = None,
    ) -> None:
        drawn = draw_skeleton(frame, keypoints, recovered_indices=recovered_indices)
        self._writer.write(drawn)

    def release(self) -> str:
        self._writer.release()
        return self._path
