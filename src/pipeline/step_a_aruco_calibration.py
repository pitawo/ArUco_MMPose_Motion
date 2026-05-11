"""STEP A: ArUco-based extrinsic calibration (multi-camera).

設計書: docs/DESIGN.md §STEP A 参照。
未実装。次セッション以降で実装着手。

責務:
- 各カメラ動画から ArUco マーカー（6x6系、42mm × 42mm 想定）を検出
- solvePnP / estimatePoseBoard で各カメラの外部パラメータ（rvec, tvec）を推定
- 外れ値フレームを除外し区間中央値で安定化
- ワールド座標系（マーカー基準）への変換マトリクスを生成

入力:
- 各カメラ動画ファイル（同一シーンを撮影、固定カメラ前提）
- カメラ内部パラメータ（intrinsics: K, distCoeffs）
- ArUco 辞書 ID とマーカー物理サイズ

出力:
- world_transforms.npz（カメラ毎の R, t, K, distCoeffs を一括保存）
- 検出ログ（成功率・外れ値統計）
"""
from __future__ import annotations


def estimate_world_transforms(*args, **kwargs):
    """ArUco 検出 → 外部パラメータ推定 → ワールド変換マトリクス生成。

    入出力スキーマは docs/DESIGN.md §STEP A 参照。
    """
    raise NotImplementedError("STEP A は次セッション以降で実装")


if __name__ == "__main__":
    raise NotImplementedError("STEP A は次セッション以降で実装")
