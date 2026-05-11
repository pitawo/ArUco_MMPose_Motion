"""Time synchronization across multiple cameras.

未実装。docs/DESIGN.md §STEP C 参照。

3 modes:
- timestamp: ファイル / EXIF / NTP のタイムスタンプベース
- xcorr: 相互相関（音声 or 同期信号フラッシュ）
- manual: 手動オフセット入力
"""
from __future__ import annotations


def build_sync_map(*args, **kwargs):
    raise NotImplementedError("time_sync は次セッション以降で実装")
