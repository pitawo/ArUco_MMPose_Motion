"""Entry point for ArUco_MMPose_Motion pipeline.

Usage:
    python -m src.main --step b --config configs/step_b_pose2d.yaml
    python -m src.main --step a --config configs/step_a_aruco.yaml  # 未実装
    ...

設計書: docs/DESIGN.md
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable


def _run_step_a(config_path: str) -> None:
    from src.pipeline.step_a_aruco_calibration import estimate_world_transforms
    estimate_world_transforms(config_path)


def _run_step_b(config_path: str) -> None:
    from src.pipeline.step_b_pose2d import run_step_b
    run_step_b(config_path)


def _run_step_c(config_path: str) -> None:
    from src.pipeline.step_c_sync import synchronize_cameras
    synchronize_cameras(config_path)


def _run_step_d(config_path: str) -> None:
    from src.pipeline.step_d_triangulation import triangulate_3d_world
    triangulate_3d_world(config_path)


def _run_step_e(config_path: str) -> None:
    from src.pipeline.step_e_smoothing import smooth_3d_world
    smooth_3d_world(config_path)


_STEP_RUNNERS: dict[str, Callable[[str], None]] = {
    "a": _run_step_a,
    "b": _run_step_b,
    "c": _run_step_c,
    "d": _run_step_d,
    "e": _run_step_e,
}

_DEFAULT_CONFIGS: dict[str, str] = {
    "a": "configs/step_a_aruco.yaml",
    "b": "configs/step_b_pose2d.yaml",
    "c": "configs/step_c_sync.yaml",
    "d": "configs/step_d_triangulation.yaml",
    "e": "configs/step_e_smoothing.yaml",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ArUco_MMPose_Motion entry point")
    parser.add_argument(
        "--step",
        required=True,
        choices=["a", "b", "c", "d", "e", "all"],
        help="Pipeline step to execute (a/b/c/d/e or all)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Config YAML path (default: configs/step_<step>_*.yaml)",
    )
    args = parser.parse_args(argv)

    if args.step == "all":
        if args.config is not None:
            parser.error("--config cannot be used with --step all; use each step default config or run steps individually")
        for step_key in ["a", "b", "c", "d", "e"]:
            _STEP_RUNNERS[step_key](_DEFAULT_CONFIGS[step_key])
    else:
        cfg = args.config or _DEFAULT_CONFIGS[args.step]
        _STEP_RUNNERS[args.step](cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
