from __future__ import annotations

import argparse
import math
from typing import Any

from src.common.config import load_config as _load_config
from src.common.deps import import_cv2
from src.common.logger import setup_logger
from src.common.output_naming import append_timestamp_to_path, make_run_timestamp
from src.io.keypoint_io import COCO_KEYPOINT_NAMES, write_json, write_jsonl, write_keypoints_csv
from src.pose.confidence_filter import count_valid_keypoints, mask_low_confidence
from src.pose.pose2d_infer import Pose2DConfig, Pose2DInferencer
from src.visualization.draw_pose2d import PoseVideoWriter


REQUIRED_TOP_LEVEL_KEYS = {"input", "runtime", "postprocess", "output"}


def _import_cv2() -> Any:
    return import_cv2("STEP_B")


def load_config(path: str) -> dict[str, Any]:
    return _load_config(path, REQUIRED_TOP_LEVEL_KEYS)


def _extract_first_person_keypoints(prediction: dict[str, Any]) -> tuple[list[list[float]], int]:
    """Extract first-person keypoints from MMPose inference output.

    Returns (keypoints_with_score, num_person).
    """
    predictions = prediction.get("predictions", [])
    if not predictions:
        return [], 0

    person_instances = predictions[0] if isinstance(predictions[0], list) else predictions
    if not person_instances:
        return [], 0

    first_person = person_instances[0]
    keypoints = first_person.get("keypoints", [])
    keypoint_scores = first_person.get("keypoint_scores", [])
    if not keypoints:
        return [], len(person_instances)

    if not keypoint_scores:
        return [[kp[0], kp[1], 1.0] for kp in keypoints], len(person_instances)

    zipped = [[kp[0], kp[1], float(score)] for kp, score in zip(keypoints, keypoint_scores)]
    return zipped, len(person_instances)


def _collect_rejected_keypoints(keypoints: list[list[float]], threshold: float) -> tuple[list[int], list[str]]:
    rejected_indices: list[int] = []
    rejected_names: list[str] = []
    for idx, kpt in enumerate(keypoints):
        if len(kpt) < 3:
            continue
        if float(kpt[2]) < threshold:
            rejected_indices.append(idx)
            if idx < len(COCO_KEYPOINT_NAMES):
                rejected_names.append(COCO_KEYPOINT_NAMES[idx])
            else:
                rejected_names.append(f"kp_{idx}")
    return rejected_indices, rejected_names


def _joint_names_to_indices(joint_names: list[str]) -> list[int]:
    lookup = {name: idx for idx, name in enumerate(COCO_KEYPOINT_NAMES)}
    return [lookup[name] for name in joint_names if name in lookup]


def _recover_target_joints(
    filtered: list[list[float]],
    recovery_keypoints: list[list[float]],
    target_indices: list[int],
    recovery_threshold: float,
    max_per_frame: int,
) -> tuple[list[list[float]], list[int], list[str]]:
    recovered_indices: list[int] = []
    recovered_names: list[str] = []

    budget = max(0, max_per_frame)
    for idx in target_indices:
        if budget <= 0:
            break
        if idx >= len(filtered) or idx >= len(recovery_keypoints):
            continue

        current = filtered[idx]
        if len(current) < 2 or not math.isnan(float(current[0])):
            continue

        candidate = recovery_keypoints[idx]
        if len(candidate) < 3:
            continue

        x, y, score = float(candidate[0]), float(candidate[1]), float(candidate[2])
        if math.isnan(x) or math.isnan(y) or score < recovery_threshold:
            continue

        filtered[idx] = [x, y, score]
        recovered_indices.append(idx)
        recovered_names.append(COCO_KEYPOINT_NAMES[idx] if idx < len(COCO_KEYPOINT_NAMES) else f"kp_{idx}")
        budget -= 1

    return filtered, recovered_indices, recovered_names


def run_step_b(config_path: str, inferencer_cls: type[Pose2DInferencer] = Pose2DInferencer) -> dict[str, Any]:
    cv2 = _import_cv2()
    cfg = load_config(config_path)
    logger = setup_logger("step-b-pose2d")
    logger.info("STEP B: 2D pose inference started")

    runtime = cfg["runtime"]
    in_cfg = cfg["input"]
    out_cfg = cfg["output"]
    post_cfg = cfg["postprocess"]
    run_timestamp = make_run_timestamp()

    vis_path = append_timestamp_to_path(out_cfg["vis_video_path"], run_timestamp)
    keypoints_jsonl_path = append_timestamp_to_path(out_cfg["keypoints_jsonl"], run_timestamp)
    csv_base_path = out_cfg.get("keypoints_csv", out_cfg["keypoints_jsonl"].replace(".jsonl", ".csv"))
    keypoints_csv_path = append_timestamp_to_path(csv_base_path, run_timestamp)
    summary_json_path = append_timestamp_to_path(out_cfg["summary_json"], run_timestamp)

    pose_cfg = Pose2DConfig(
        pose2d_model=runtime.get("pose2d_model", "human"),
        pose2d_weights=runtime.get("pose2d_weights"),
        det_model=runtime.get("det_model"),
        det_weights=runtime.get("det_weights"),
        device=runtime.get("device", "cpu"),
        bbox_thr=float(runtime.get("bbox_thr", 0.3)),
        kpt_thr=float(runtime.get("kpt_thr", 0.3)),
    )

    inferencer = inferencer_cls(pose_cfg)
    threshold = float(post_cfg.get("confidence_threshold", 0.6))
    recovery_cfg = post_cfg.get("recovery", {}) if isinstance(post_cfg.get("recovery", {}), dict) else {}
    recovery_enabled = bool(recovery_cfg.get("enabled", False))
    recovery_threshold = float(recovery_cfg.get("confidence_threshold", 0.3))
    recovery_infer_kpt_thr = float(recovery_cfg.get("infer_kpt_thr", min(threshold, pose_cfg.kpt_thr)))
    target_joint_names = recovery_cfg.get("target_joints", [])
    if not isinstance(target_joint_names, list):
        target_joint_names = []
    target_joint_indices = _joint_names_to_indices([str(name) for name in target_joint_names])
    max_recover_per_frame = int(recovery_cfg.get("max_recover_per_frame", len(target_joint_indices)))

    recovery_iter = None
    if recovery_enabled and target_joint_indices:
        recovery_pose_cfg = Pose2DConfig(
            pose2d_model=pose_cfg.pose2d_model,
            pose2d_weights=pose_cfg.pose2d_weights,
            det_model=pose_cfg.det_model,
            det_weights=pose_cfg.det_weights,
            device=pose_cfg.device,
            bbox_thr=pose_cfg.bbox_thr,
            kpt_thr=recovery_infer_kpt_thr,
        )
        recovery_inferencer = inferencer_cls(recovery_pose_cfg)
        recovery_iter = recovery_inferencer.infer_video(in_cfg["video_path"])
        logger.info(
            "Recovery inference enabled for joints=%s recovery_threshold=%.2f infer_kpt_thr=%.2f",
            target_joint_names,
            recovery_threshold,
            recovery_infer_kpt_thr,
        )

    video_path = in_cfg["video_path"]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    vis_writer = PoseVideoWriter(vis_path, fps, width, height)
    logger.info("Visualization video writer opened: %s (%dx%d @ %.1ffps)", vis_path, width, height, fps)

    records: list[dict[str, Any]] = []
    frame_count = 0
    total_valid = 0
    zero_person_frames = 0
    total_rejected = 0
    total_recovered = 0

    for item in inferencer.infer_video(video_path):
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        keypoints_with_score, num_person = _extract_first_person_keypoints(item["prediction"])
        rejected_indices, rejected_names = _collect_rejected_keypoints(keypoints_with_score, threshold)
        filtered = mask_low_confidence(keypoints_with_score, threshold)

        recovered_indices: list[int] = []
        recovered_names: list[str] = []
        if recovery_iter is not None:
            try:
                recovery_item = next(recovery_iter)
                recovery_keypoints_with_score, _ = _extract_first_person_keypoints(recovery_item["prediction"])
                filtered, recovered_indices, recovered_names = _recover_target_joints(
                    filtered,
                    recovery_keypoints_with_score,
                    target_joint_indices,
                    recovery_threshold,
                    max_recover_per_frame,
                )
            except StopIteration:
                logger.warning("Recovery inferencer exhausted before primary inferencer")

        valid_count = count_valid_keypoints(filtered)
        total_rejected += len(rejected_indices)
        total_recovered += len(recovered_indices)
        total_valid += valid_count
        if num_person == 0:
            zero_person_frames += 1

        records.append(
            {
                "frame_index": item["frame_index"],
                "num_person": num_person,
                "valid_keypoints": valid_count,
                "keypoints": filtered,
                "rejected_keypoint_indices": rejected_indices,
                "rejected_keypoint_names": rejected_names,
                "recovered_keypoint_indices": recovered_indices,
                "recovered_keypoint_names": recovered_names,
            }
        )

        vis_writer.write_frame(frame, filtered, recovered_indices=set(recovered_indices))

    cap.release()
    vis_writer.release()
    logger.info("Visualization video saved: %s", vis_path)

    written = write_jsonl(records, keypoints_jsonl_path)
    logger.info("Keypoints JSONL saved: %s (%d rows)", keypoints_jsonl_path, written)

    csv_written = write_keypoints_csv(records, keypoints_csv_path)
    logger.info("CSV saved: %s (%d rows)", keypoints_csv_path, csv_written)

    summary = {
        "frames": frame_count,
        "records_written": written,
        "zero_person_frames": zero_person_frames,
        "mean_valid_keypoints": (total_valid / frame_count) if frame_count else 0.0,
        "total_rejected_keypoints": total_rejected,
        "total_recovered_keypoints": total_recovered,
        "config": {
            "confidence_threshold": threshold,
            "recovery": {
                "enabled": recovery_iter is not None,
                "target_joints": target_joint_names if recovery_iter is not None else [],
                "confidence_threshold": recovery_threshold if recovery_iter is not None else None,
                "infer_kpt_thr": recovery_infer_kpt_thr if recovery_iter is not None else None,
                "max_recover_per_frame": max_recover_per_frame if recovery_iter is not None else None,
            },
        },
    }
    summary["output_files"] = {
        "keypoints_jsonl": keypoints_jsonl_path,
        "keypoints_csv": keypoints_csv_path,
        "summary_json": summary_json_path,
        "vis_video_path": vis_path,
    }
    write_json(summary, summary_json_path)

    logger.info(
        "STEP B completed: frames=%d, records=%d, zero_person_frames=%d",
        frame_count,
        written,
        zero_person_frames,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run STEP B 2D pose inference pipeline")
    parser.add_argument("--config", default="configs/step_b_pose2d.yaml")
    args = parser.parse_args()
    run_step_b(args.config)


if __name__ == "__main__":
    main()
