"""Smoke tests: module imports and placeholder behavior.

mmpose / mmcv / opencv 等の重い依存は import せず、純 Python で完結するモジュールのみを確認する。
本格的なユニットテストは STEP 実装と同時に追加する。
"""
from __future__ import annotations

import importlib

import pytest


PURE_PYTHON_MODULES = [
    "src.common.config",
    "src.common.deps",
    "src.common.jsonl_io",
    "src.common.logger",
    "src.common.output_naming",
    "src.common.validators",
    "src.io.keypoint_io",
    "src.aruco",
    "src.aruco.detector",
    "src.aruco.pose_estimator",
    "src.aruco.world_transform",
    "src.triangulation",
    "src.triangulation.linear_dlt",
    "src.triangulation.ransac",
    "src.smoothing",
    "src.smoothing.savitzky_golay",
    "src.smoothing.one_euro",
    "src.sync",
    "src.sync.time_sync",
    "src.pipeline.step_a_aruco_calibration",
    "src.pipeline.step_c_sync",
    "src.pipeline.step_d_triangulation",
    "src.pipeline.step_e_smoothing",
    "src.visualization.draw_pose3d_world",
]


@pytest.mark.parametrize("module_name", PURE_PYTHON_MODULES)
def test_module_imports(module_name: str) -> None:
    """各モジュールが import 可能であることを確認する。"""
    importlib.import_module(module_name)


def test_step_a_placeholder_raises() -> None:
    from src.pipeline.step_a_aruco_calibration import estimate_world_transforms
    with pytest.raises(NotImplementedError):
        estimate_world_transforms()


def test_step_d_placeholder_raises() -> None:
    from src.pipeline.step_d_triangulation import triangulate_3d_world
    with pytest.raises(NotImplementedError):
        triangulate_3d_world()
