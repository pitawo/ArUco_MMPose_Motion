from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from src.common.validators import is_valid_xy


BBox = tuple[float, float, float, float]  # (x1, y1, x2, y2)


# COCO OKS sigmas (normalized), same order as COCO 17 keypoints.
_OKS_SIGMAS: tuple[float, ...] = (
    0.026, 0.025, 0.025, 0.035, 0.035,
    0.079, 0.079, 0.072, 0.072, 0.062, 0.062,
    0.107, 0.107, 0.087, 0.087, 0.089, 0.089,
)


def bbox_from_keypoints(keypoints: Sequence[Sequence[float]], pad: float = 0.05) -> BBox | None:
    xs = [kp[0] for kp in keypoints if is_valid_xy(kp)]
    ys = [kp[1] for kp in keypoints if is_valid_xy(kp)]
    if not xs or not ys:
        return None
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    w, h = x2 - x1, y2 - y1
    return (x1 - w * pad, y1 - h * pad, x2 + w * pad, y2 + h * pad)


def iou(a: BBox, b: BBox) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return inter / union


def oks(
    kps_a: Sequence[Sequence[float]],
    kps_b: Sequence[Sequence[float]],
    bbox_b: BBox | None = None,
) -> float:
    """Object Keypoint Similarity between two keypoint sets."""
    n = min(len(kps_a), len(kps_b), len(_OKS_SIGMAS))
    if n == 0:
        return 0.0
    if bbox_b is None:
        bbox_b = bbox_from_keypoints(kps_b)
    if bbox_b is None:
        return 0.0
    area = max(1e-6, (bbox_b[2] - bbox_b[0]) * (bbox_b[3] - bbox_b[1]))
    scores: list[float] = []
    for i in range(n):
        a, b = kps_a[i], kps_b[i]
        if not (is_valid_xy(a) and is_valid_xy(b)):
            continue
        d2 = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
        var = (_OKS_SIGMAS[i] * 2) ** 2
        scores.append(math.exp(-d2 / (2.0 * area * var + 1e-9)))
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


@dataclass
class _Track:
    track_id: int
    bbox: BBox
    keypoints: list[list[float]] = field(default_factory=list)
    missed: int = 0


class IoUTracker:
    """Greedy IoU/OKS tracker with unmatched-frame tolerance."""

    def __init__(
        self,
        iou_threshold: float = 0.3,
        oks_threshold: float = 0.3,
        max_missed_frames: int = 10,
        use_oks: bool = False,
    ) -> None:
        self.iou_threshold = iou_threshold
        self.oks_threshold = oks_threshold
        self.max_missed = max_missed_frames
        self.use_oks = use_oks
        self._next_id = 0
        self._tracks: list[_Track] = []

    def _new_track(self, bbox: BBox, keypoints: list[list[float]]) -> _Track:
        track = _Track(track_id=self._next_id, bbox=bbox, keypoints=keypoints)
        self._next_id += 1
        return track

    def update(
        self,
        detections: list[dict],
    ) -> list[dict]:
        """Assign track_id to each detection.

        Each detection must have 'keypoints' (list[list[float]]); 'bbox' optional.
        Returns a new list with added 'track_id' key.
        """
        # Build bboxes
        det_bboxes: list[BBox | None] = []
        for det in detections:
            bbox = det.get("bbox")
            if bbox is None:
                bbox = bbox_from_keypoints(det.get("keypoints", []))
            det_bboxes.append(bbox)

        # Greedy matching: for each existing track, find best-matching detection.
        assigned: dict[int, int] = {}  # det_idx -> track_id
        used_tracks: set[int] = set()
        candidates: list[tuple[float, int, int]] = []  # (score, track_idx, det_idx)
        for t_idx, track in enumerate(self._tracks):
            for d_idx, bbox in enumerate(det_bboxes):
                if bbox is None:
                    continue
                if self.use_oks:
                    score = oks(track.keypoints, detections[d_idx].get("keypoints", []), bbox)
                    threshold = self.oks_threshold
                else:
                    score = iou(track.bbox, bbox)
                    threshold = self.iou_threshold
                if score >= threshold:
                    candidates.append((score, t_idx, d_idx))
        candidates.sort(reverse=True)

        matched_dets: set[int] = set()
        for score, t_idx, d_idx in candidates:
            if t_idx in used_tracks or d_idx in matched_dets:
                continue
            used_tracks.add(t_idx)
            matched_dets.add(d_idx)
            assigned[d_idx] = self._tracks[t_idx].track_id
            # Update the matched track
            bbox = det_bboxes[d_idx]
            if bbox is not None:
                self._tracks[t_idx].bbox = bbox
            self._tracks[t_idx].keypoints = detections[d_idx].get("keypoints", [])
            self._tracks[t_idx].missed = 0

        # Unmatched tracks age out
        surviving: list[_Track] = []
        for t_idx, track in enumerate(self._tracks):
            if t_idx in used_tracks:
                surviving.append(track)
                continue
            track.missed += 1
            if track.missed <= self.max_missed:
                surviving.append(track)
        self._tracks = surviving

        # New tracks for unmatched detections
        for d_idx, bbox in enumerate(det_bboxes):
            if d_idx in matched_dets or bbox is None:
                continue
            track = self._new_track(bbox, detections[d_idx].get("keypoints", []))
            self._tracks.append(track)
            assigned[d_idx] = track.track_id

        # Produce output preserving input order
        out: list[dict] = []
        for d_idx, det in enumerate(detections):
            new_det = dict(det)
            new_det["track_id"] = assigned.get(d_idx, -1)
            out.append(new_det)
        return out
