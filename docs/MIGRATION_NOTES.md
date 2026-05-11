# 移植ノート（mmpose_3d_pose_A-main → mmpose_3d_pose_aruco）

- 移植日: 2026-05-02
- 担当: Ryo（Engineer、Peter ブートストラップ）
- 関連: Decision #009（組織再編）、Plan：`.claude/plans/ryo-...md`

---

## 移植元

`新しいフォルダー/mmpose_3d_pose_A-main/`（単眼 3D 向けプロトタイプ）

## 移植先

`pitawo_AI_company/projects/mmpose_3d_pose_aruco/`（マルチカメラ × ArUco 向け新リポジトリ、独自 git）

---

## コピーしたファイル（変更なし）

| 移植元 | 移植先 |
|---|---|
| `MULTIANGLE_ArUco_MMPose_Design.md` | `docs/DESIGN.md` |
| `環境構築手順.md` | `docs/環境構築手順.md` |
| `requirements.txt` | `requirements.txt` |
| `configs/base.yaml` | `configs/base.yaml` |
| `src/__init__.py` | `src/__init__.py` |
| `src/common/*` | `src/common/*` |
| `src/io/*` | `src/io/*` |
| `src/pose/__init__.py` | `src/pose/__init__.py` |
| `src/pose/confidence_filter.py` | `src/pose/confidence_filter.py` |
| `src/pose/pose2d_infer.py` | `src/pose/pose2d_infer.py` |
| `src/pose/tracker.py` | `src/pose/tracker.py` |
| `src/pipeline/__init__.py` | `src/pipeline/__init__.py` |
| `src/visualization/__init__.py` | `src/visualization/__init__.py` |
| `src/visualization/draw_pose2d.py` | `src/visualization/draw_pose2d.py` |

## リネーム＋微修正したファイル

| 移植元 | 移植先 | 修正内容 |
|---|---|---|
| `configs/step1_pose2d.yaml` | `configs/step_b_pose2d.yaml` | `step` 値を `step_b_pose2d` に、出力パス `data/interim/step1` を `data/interim/step_b` に変更 |
| `src/pipeline/step1_run_pose2d.py` | `src/pipeline/step_b_pose2d.py` | 関数 `run_step1` → `run_step_b`、ロガー名 `step1-pose2d` → `step-b-pose2d`、ログ／argparse の "STEP1" 表記を "STEP B" に統一、デフォルト config パスを更新 |

## 移植しなかったファイル（理由）

| ファイル | 理由 |
|---|---|
| `src/analysis/*` | 単眼 3D 分析用、新マルチビュー設計と用途違い |
| `src/features/*` | 単眼 3D 特徴量、用途違い |
| `src/pose/pose3d_infer.py` | 単眼 MotionBERT 用、マルチビュー三角測量で代替 |
| `src/pipeline/step2_run_features2d.py` | 単眼パイプライン |
| `src/pipeline/step3_run_pose3d.py` | 単眼パイプライン |
| `src/pipeline/step4_run_analysis3d.py` | 単眼パイプライン |
| `src/visualization/draw_pose3d_video.py` | マルチビュー用に書き直し予定（`draw_pose3d_world.py` プレースホルダ） |
| `src/visualization/plot_step*_metrics.py` | 単眼分析グラフ用 |
| `tests/*`（既存テスト） | 単眼パイプライン前提、新規テスト（`tests/test_smoke.py`）に置き換え |

## 新規追加（プレースホルダ）

- `src/pipeline/step_a_aruco_calibration.py`
- `src/pipeline/step_c_sync.py`
- `src/pipeline/step_d_triangulation.py`
- `src/pipeline/step_e_smoothing.py`
- `src/aruco/{__init__,detector,pose_estimator,world_transform}.py`
- `src/triangulation/{__init__,linear_dlt,ransac}.py`
- `src/smoothing/{__init__,savitzky_golay,one_euro}.py`
- `src/sync/{__init__,time_sync}.py`
- `src/visualization/draw_pose3d_world.py`
- `src/main.py`（エントリポイント）
- `configs/step_a_aruco.yaml`
- `configs/step_c_sync.yaml`
- `configs/step_d_triangulation.yaml`
- `configs/step_e_smoothing.yaml`
- `tests/test_smoke.py`
- `scripts/env_check.py`
- `README.md` / `.gitignore`

## Git 状況

- 新リポジトリは独自 `.git`（このプロジェクト初回コミット）
- 親リポジトリ `pitawo_AI_company` の `.gitignore` に `projects/mmpose_3d_pose_aruco/` を追加済み（ネスト git 競合回避）
- GitHub remote は **未設定**（次セッションで `gh repo create --private` 予定）

## 既知の注意

- 移植した `src/pose/pose2d_infer.py` などは MMPose 等の重い依存が必要。`tests/test_smoke.py` ではこれらを直接 import しない設計（mmpose/cv2/torch 未インストール環境でも smoke test が通る）
- 既存 `mmpose_3d_pose_A-main` は元の場所に残置。実装が安定したら整理を検討
