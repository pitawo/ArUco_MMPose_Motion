# マルチアングル 3D 姿勢推定システム設計書（ArUco絶対座標基準）

## 1. 目的
本設計は、既存の単眼ベース MMPose パイプラインを拡張し、**複数カメラ（マルチアングル）入力**から、
**ArUcoマーカーを基準とした絶対座標系**で 3D 骨格を復元・統合するシステムを構築するための指針を示す。

最終的な到達目標は以下。
1. ArUco マーカーにより、各カメラ座標を共通ワールド座標へ登録する
2. 各視点の 2D キーポイント（MMPose）を時刻同期し、三角測量で 3D 化する
3. ワールド座標系で整合した 3D 骨格を出力し、品質指標を記録する

---

## 2. 前提・スコープ（確定版）

### 2.1 スコープ内
- 複数固定カメラ（**2〜4台を選択式**）
- 対象人物はパネラー1名を基本（計測者混入ケースを考慮）
- COCO17 キーポイントベース
- ArUco による外部パラメータ（カメラ姿勢）決定
- 動画ファイルの後同期（オフライン前提）

### 2.2 スコープ外（初版）
- 複数人追跡（IDスイッチ対策込み）
- リアルタイム最適化（低遅延配信）
- 学習ベースの 3D Pose Lifting の大規模導入

---

## 3. システム全体アーキテクチャ

```text
[Multi Camera Video Input]
    ├─ Camera 1
    ├─ Camera 2
    └─ Camera N
            ↓
(1) Time Sync / Frame Alignment
            ↓
(2) Per-Camera 2D Pose (MMPose)
            ↓
(3) ArUco Detection & Camera-to-World Extrinsics
            ↓
(4) Multi-view Triangulation (2D→3D)
            ↓
(5) 3D Temporal Filtering / Gap Fill
            ↓
(6) Output Writer + Visualization + QA Metrics
```

---

## 4. 座標系設計

### 4.1 座標系の定義
- **Camera座標系 C_i**: 各カメラ固有の座標系
- **Marker座標系 M**: ArUcoボード（または基準マーカー）に固定
- **World座標系 W**: 原則 M と一致（`W ≡ M`）
- **Pose座標系 P**: 人体キーポイント群（最終的に W で表現）

### 4.2 変換式
- 各カメラ i について、ArUco検出から `T_WC_i`（Camera→World）を求める
- 2D点 `u_i` と投影行列 `P_i = K_i [R_i|t_i]` を用いて三角測量
- 得られた 3D点は W 座標で保持

### 4.3 実運用ルール
- ワールド原点: 基準 ArUco の中心
- ワールド軸: マーカー面法線 + 辺方向（右手系）
- 単位: メートル（マーカー実寸でスケール固定）

---

## 5. 機能要件

### 5.1 入力
- カメラごとの動画ファイル（同一シーン）
- カメラ内部パラメータ（K, distCoeffs）※初期状態では未取得のため本システムでキャリブレーション実施
- ArUco辞書/ボード定義（**6x6系、複数ID**）、マーカーサイズ（**42mm × 42mm**）
- MMPose 2D 推論設定
- （任意）再投影誤差しきい値を読み込む `npz` 設定ファイル

### 5.2 出力
- `pose3d_world.jsonl`（フレームごとの3Dキーポイント）
- `pose3d_summary.json`（有効率、再投影誤差、欠損率）
- デバッグ可視化（重畳動画 / 3D軌跡）

### 5.3 品質指標（最低限）
- キーポイント別 triangulation 成功率
- マルチビュー再投影誤差（px）
- フレーム間ジッタ（3D）
- 有効カメラ数分布（各点が何視点で再構成されたか）

### 5.4 精度要件の定義メモ
- **再投影誤差（px）**: 3D再構成点を各カメラ画像面に投影し直したときの 2D 誤差（ピクセル単位）
- **3D位置誤差（mm）**: 推定3D座標と真値3D座標の距離誤差（ミリメートル単位）
  - 真値がない運用では直接算出できないため、代替として「再投影誤差」「骨長安定性」「既知距離との整合」で品質管理する

---

## 6. 非機能要件
- 再現性: 同一入力から同一結果（乱数固定）
- 拡張性: カメラ台数増減に設定で対応
- 保守性: 既存 `src/pipeline` のステップ構成を踏襲
- 可観測性: ログと中間成果物を段階ごとに保存

---

## 7. 詳細パイプライン設計

## STEP A: キャリブレーション・座標合わせ

### A-1. 内部パラメータ読込
- `calib/intrinsics/camXX.yaml` から K, dist を読込

### A-2. ArUco検出
- 各フレームで ArUco を検出
- 検出信頼度（ID一致、面積、角点品質）を評価

### A-3. 外部パラメータ推定
- `solvePnP` または `estimatePoseBoard` で `R,t` を推定
- 外れ値フレームは補間（前後時刻）または棄却

### A-4. カメラ姿勢平滑化
- 微小振動低減のため、`R,t` を時系列平滑化
- 固定カメラ前提なら区間中央値で代表値化可能

成果物:
- `camera_poses_world.jsonl`
- `camera_pose_quality.json`

---

## STEP B: マルチ視点 2D 姿勢推定

### B-1. 各カメラで既存 Step1 相当を実行
- `src/pose/pose2d_infer.py` を再利用
- 低信頼点の NaN 化（既存 confidence filter 準拠）

### B-2. 人物選択ロジック
- 初版は「最大 bbox の 1 人」を採用
- 将来は tracking ID を導入

成果物:
- `interim/camXX/pose2d_keypoints.jsonl`

---

## STEP C: 時刻同期

### C-1. 同期モード（確定）
1. タイムスタンプ同期（第一選択）
2. 相互相関ベース補正（補助）
3. 手動オフセット指定（最終フォールバック）

### C-2. 同期後インデックス
- 共通 `frame_index_world` を採番
- 各カメラの欠落は `missing` として保持

成果物:
- `sync_map.csv`

---

## STEP D: 三角測量（2D→3D）

### D-1. 対応点収集
- 同一 `frame_index_world`・同一関節IDの2D点を収集
- 有効視点数 `>=2` を必須条件

### D-2. 幾何復元
- 線形三角測量（DLT）を基本
- 任意: 再投影誤差最小化で非線形最適化

### D-3. ロバスト化
- RANSAC または誤差しきい値で外れ視点を除外
- 失敗関節は NaN を維持

成果物:
- `pose3d_raw_world.jsonl`

---

## STEP E: 3D後処理

### E-1. 時系列平滑化
- Savitzky-Golay / OneEuro / Kalman いずれか

### E-2. 欠損補間
- 短区間のみ線形補間（例: 最大5フレーム）

### E-3. 人体制約（任意）
- 骨長の急変抑制
- 解剖学的に不自然な角度を軽減

成果物:
- `pose3d_world.jsonl`
- `pose3d_qc.json`

---

## 8. データモデル（提案）

### 8.1 2D（カメラ別）
```json
{
  "frame_index": 123,
  "camera_id": "cam01",
  "num_person": 1,
  "keypoints": [[x,y,score], ...],
  "bbox": [x1,y1,x2,y2],
  "timestamp_ms": 4567
}
```

### 8.2 カメラ姿勢
```json
{
  "frame_index": 123,
  "camera_id": "cam01",
  "R": [[...],[...],[...]],
  "t": [...],
  "aruco_detected": true,
  "aruco_reproj_error": 0.83
}
```

### 8.3 3D骨格（最終）
```json
{
  "frame_index_world": 120,
  "keypoints_3d_world": [[X,Y,Z,conf], ...],
  "num_valid_joints": 15,
  "mean_reproj_error": 1.92
}
```

---

## 9. 推奨ディレクトリ構成（既存リポジトリ踏襲）

```text
configs/
  stepA_calib_aruco.yaml
  stepB_pose2d_multicam.yaml
  stepC_sync.yaml
  stepD_triangulation.yaml
  stepE_postprocess3d.yaml

src/
  calib/
    aruco_detector.py
    pose_estimation.py
  sync/
    frame_sync.py
  triangulation/
    dlt.py
    reprojection.py
  pipeline/
    stepA_run_calib_aruco.py
    stepB_run_pose2d_multicam.py
    stepC_run_sync.py
    stepD_run_triangulation.py
    stepE_run_postprocess3d.py
```

---

## 10. 実装フェーズ計画

### Phase 1（最小実装）
- 2台カメラ（設定で3〜4台へ拡張可能な設計）
- 複数ID ArUco（6x6系）
- 線形三角測量のみ
- オフライン処理

### Phase 2（品質向上）
- 3台以上対応
- 再投影誤差ベース外れ値除去
- 3D時系列平滑化

### Phase 3（運用対応）
- 複数人対応
- 自動同期補正
- 準リアルタイム化

---

## 11. リスクと対策
- **ArUcoが見えないフレーム**: 複数マーカー配置・過去姿勢補間
- **カメラ同期ずれ**: 明示同期信号 or タイムスタンプ補正
- **被写体遮蔽**: カメラ台数を増やし、2視点未満時は欠損保持
- **2D誤検出**: 関節別信頼度しきい値 + 再投影誤差監視
- **計測者の映り込み**: ROIマスクで除外するか、2名検出モードを選択可能にする（設定切替）

---

## 12. 受け入れ基準（初版）
1. 任意フレームで15点以上の3D復元率が80%以上
2. 平均再投影誤差がしきい値以下（固定値または `npz` から読込）
3. ワールド座標のスケール誤差が ±2% 以内（既知長さ計測）
4. 全ステップが設定ファイル駆動で再実行可能

---

## 13. 要件確定内容（今回回答反映）
1. **カメラ台数・配置**: 2〜4台の選択式、固定設置
2. **同期条件**: 動画ファイルの後同期
3. **ArUco運用**: 複数ID、6x6系辞書、42mm × 42mm
4. **精度要件**: 再投影誤差しきい値は `npz` 読み込み方式
5. **対象人物数**: パネラー1名を基本、計測者混入時の運用を要検討
6. **出力用途**: オフライン解析専用
7. **既存資産**: カメラ内部パラメータ未取得（Step Aで取得）

## 14. 未確定事項（次回合意ポイント）
1. **計測者の扱い**
   - A案: 画角マスクで計測者を除外（単一人物運用を維持）
   - B案: 2名検出・1名選別ルール（中央優先/ROI内優先）を導入
2. **再投影誤差しきい値 `npz` のスキーマ**
   - 例: `global_thresh_px` / `joint_thresh_px[17]` / `camera_pair_thresh_px`
