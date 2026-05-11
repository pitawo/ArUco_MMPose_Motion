"""STEP E: 3D pose temporal smoothing & gap filling.

設計書: docs/DESIGN.md §STEP E 参照。未実装。

責務:
- 3D 時系列の平滑化（Savitzky-Golay / OneEuro / Kalman）
- 短区間欠損の補間
- ジッタ抑制と動的応答性のバランス
"""
from __future__ import annotations


def smooth_3d_world(*args, **kwargs):
    raise NotImplementedError("STEP E は次セッション以降で実装")


if __name__ == "__main__":
    raise NotImplementedError("STEP E は次セッション以降で実装")
