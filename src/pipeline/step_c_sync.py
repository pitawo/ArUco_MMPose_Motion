"""STEP C: Multi-camera time synchronization.

設計書: docs/DESIGN.md §STEP C 参照。未実装。

責務:
- 複数カメラの動画を時刻同期（タイムスタンプ／相互相関／手動オフセットの3モード）
- 同期マップ（sync_map.csv）の生成
- フレーム欠落時の NaN 処理
"""
from __future__ import annotations


def synchronize_cameras(*args, **kwargs):
    raise NotImplementedError("STEP C は次セッション以降で実装")


if __name__ == "__main__":
    raise NotImplementedError("STEP C は次セッション以降で実装")
