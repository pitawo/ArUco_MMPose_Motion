from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Any


# COCO 17-keypoint names
COCO_KEYPOINT_NAMES = [
    "nose", "left_eye", "right_eye", "left_ear", "right_ear",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
]


def write_jsonl(records: Iterable[Mapping[str, Any]], out_path: str) -> int:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_json(data: Mapping[str, Any], out_path: str) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_keypoints_csv(records: Iterable[Mapping[str, Any]], out_path: str) -> int:
    """Write per-frame keypoints to CSV.

    Columns: frame_index, num_person, valid_keypoints,
             {name}_x, {name}_y, {name}_score  for each keypoint.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    kpt_columns: list[str] = []
    for name in COCO_KEYPOINT_NAMES:
        kpt_columns.extend([f"{name}_x", f"{name}_y", f"{name}_score"])

    header = ["frame_index", "num_person", "valid_keypoints"] + kpt_columns

    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for rec in records:
            row: list[Any] = [rec["frame_index"], rec["num_person"], rec["valid_keypoints"]]
            keypoints = rec.get("keypoints", [])
            for i in range(len(COCO_KEYPOINT_NAMES)):
                if i < len(keypoints):
                    kp = keypoints[i]
                    x = kp[0] if not math.isnan(kp[0]) else ""
                    y = kp[1] if not math.isnan(kp[1]) else ""
                    score = kp[2] if len(kp) >= 3 else ""
                    row.extend([x, y, score])
                else:
                    row.extend(["", "", ""])
            writer.writerow(row)
            count += 1
    return count
