# mmpose_3d_pose_aruco

マルチカメラ × ArUco マーカーで絶対座標系の 3D 骨格を復元するパイプライン。

## 状態（2026-05-02）

- **v1**：骨組み構築完了（このコミット）
- **動作可能**：STEP B（2D 姿勢推定）— 既存プロトタイプから移植
- **未実装**：STEP A / C / D / E（プレースホルダ配置済み、`NotImplementedError`）

## 設計

[docs/DESIGN.md](docs/DESIGN.md) を参照。

入出力概略：
- 入力：2〜4 台の固定カメラ動画 + 各カメラ内部パラメータ + ArUco マーカー
- 出力：`pose3d_world.jsonl`（ワールド座標 3D キーポイント）+ 可視化動画

パイプライン：

| Step | 役割 | 状態 |
|---|---|---|
| A | ArUco 検出 → 各カメラ外部パラメータ推定 → ワールド変換マトリクス | 未実装 |
| B | 各カメラで 2D 姿勢推定（COCO17） | **動作可能** |
| C | タイムスタンプ／相互相関で時刻同期 | 未実装 |
| D | 線形 DLT で 3D 化（ロバスト化） | 未実装 |
| E | 3D 時系列平滑化＋短区間欠損補間 | 未実装 |

## セットアップ

[docs/環境構築手順.md](docs/環境構築手順.md) を参照。要点：

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
pip install -r requirements.txt
python scripts/env_check.py   # 依存バージョン確認
```

## 使い方（v1 時点）

```bash
# 単眼での 2D 姿勢推定（動作可能）
python -m src.main --step b --config configs/step_b_pose2d.yaml

# 未実装（次セッション以降）
python -m src.main --step a --config configs/step_a_aruco.yaml
python -m src.main --step d --config configs/step_d_triangulation.yaml
```

## テスト

```bash
python -m pytest tests/test_smoke.py
```

## 次のマイルストーン

1. STEP A 実装（ArUco 外部パラメータ推定）
2. STEP D 実装（線形 DLT 三角測量）
3. 同期入力動画でのエンドツーエンド検証
4. GitHub プライベートリポジトリへの初回 push

## 既存プロトタイプとの関係

本リポジトリは `mmpose_3d_pose_A-main`（単眼 3D 向けプロトタイプ）から派生。
移植経緯：[docs/MIGRATION_NOTES.md](docs/MIGRATION_NOTES.md)。
