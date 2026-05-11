"""STEP D: Multi-view triangulation.

設計書: docs/DESIGN.md §STEP D 参照。未実装。

責務:
- 同期した複数カメラの 2D キーポイントを線形 DLT で 3D 化
- ロバスト化（再投影誤差ベースの外れ値除去、RANSAC 任意）
- 任意で非線形最適化（Levenberg-Marquardt）

入力:
- 各カメラの STEP B 出力（pose2d_keypoints.jsonl）
- STEP A 出力（world_transforms.npz）
- STEP C 出力（sync_map.csv）

出力:
- pose3d_world.jsonl（ワールド座標 3D キーポイント）
- pose3d_summary.json（再投影誤差・有効カメラ数等）
"""
from __future__ import annotations


def triangulate_3d_world(*args, **kwargs):
    raise NotImplementedError("STEP D は次セッション以降で実装")


if __name__ == "__main__":
    raise NotImplementedError("STEP D は次セッション以降で実装")
