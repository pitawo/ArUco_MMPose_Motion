from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class FramePacket:
    frame_index: int
    timestamp_sec: float
    image_path: str


def iter_image_files(image_dir: str) -> Iterator[FramePacket]:
    """Treat sorted images as pseudo-frames for STEP B dry-run/validation."""
    directory = Path(image_dir)
    for idx, path in enumerate(sorted(directory.glob("*"))):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        yield FramePacket(frame_index=idx, timestamp_sec=float(idx), image_path=str(path))
