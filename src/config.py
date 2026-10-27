from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
MODEL_PATH = ASSETS_DIR / "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


@dataclass(frozen=True)
class ScannerConfig:
    camera_index: int = 0
    max_hands: int = 2
    min_detection_confidence: float = 0.55
    min_presence_confidence: float = 0.55
    min_tracking_confidence: float = 0.55
    camera_width: int = 960
    camera_height: int = 540
    target_fps: int = 30
    volume_step: float = 0.08

