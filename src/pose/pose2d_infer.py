from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


@dataclass
class Pose2DConfig:
    pose2d_model: str = "human"
    pose2d_weights: str | None = None
    det_model: str | None = None
    det_weights: str | None = None
    device: str = "cpu"
    bbox_thr: float = 0.3
    kpt_thr: float = 0.3


class Pose2DInferencer:
    """Thin wrapper around MMPoseInferencer for STEP1 pipeline."""

    def __init__(self, cfg: Pose2DConfig) -> None:
        self.cfg = cfg
        self._inferencer = self._build_inferencer()

    def _build_inferencer(self) -> Any:
        try:
            from mmpose.apis import MMPoseInferencer
        except ImportError as exc:
            raise RuntimeError(
                "mmpose is not installed. Install mmpose/mmdet to run STEP1 inference."
            ) from exc

        return MMPoseInferencer(
            pose2d=self.cfg.pose2d_model,
            pose2d_weights=self.cfg.pose2d_weights,
            det_model=self.cfg.det_model,
            det_weights=self.cfg.det_weights,
            device=self.cfg.device,
        )

    def infer_video(self, video_path: str) -> Iterator[dict[str, Any]]:
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        result_iter = self._inferencer(
            video_path,
            bbox_thr=self.cfg.bbox_thr,
            kpt_thr=self.cfg.kpt_thr,
            return_vis=False,
            draw_bbox=False,
            show=False,
        )
        for frame_idx, pred in enumerate(result_iter):
            yield {"frame_index": frame_idx, "prediction": pred}
