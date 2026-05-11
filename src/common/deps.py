from __future__ import annotations

from typing import Any


def import_cv2(feature_name: str) -> Any:
    """Import cv2 with a consistent, actionable error message."""
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        message = str(exc)
        if "libGL.so.1" in message:
            raise RuntimeError(
                "OpenCV import failed because libGL.so.1 is missing.\n"
                "Install OS package: Ubuntu/Debian='libgl1', Amazon Linux/RHEL='mesa-libGL'.\n"
                "If you cannot install OS packages (e.g., managed notebook), uninstall opencv-python and install opencv-python-headless.\n"
                "Then retry this command."
            ) from exc
        raise RuntimeError(
            f"OpenCV (cv2) is required for {feature_name}. Install opencv-python or opencv-python-headless."
        ) from exc
    return cv2
