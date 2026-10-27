from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .config import MODEL_PATH, MODEL_URL, ScannerConfig


@dataclass(frozen=True)
class HandObservation:
    """One MediaPipe hand result; gesture classification is intentionally absent in Phase 2."""

    landmarks: tuple[object, ...]
    handedness: str
    handedness_score: float | None = None


class ModelAssetError(RuntimeError):
    """Raised when the verified local MediaPipe model asset cannot be prepared."""


def ensure_model(path: Path = MODEL_PATH) -> Path:
    """Return a valid local model, downloading the official asset when absent."""
    if path.exists() and path.is_file() and path.stat().st_size > 100_000:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(MODEL_URL, path)
    except Exception as exc:
        if path.exists():
            path.unlink(missing_ok=True)
        raise ModelAssetError(
            f"Hand landmark model is unavailable at {path}. "
            f"Download it from {MODEL_URL} or allow the application to download it, then retry."
        ) from exc
    if not path.exists() or path.stat().st_size <= 100_000:
        raise ModelAssetError(f"Downloaded hand landmark model is invalid or empty: {path}")
    return path


class HandTracker:
    """MediaPipe Hand Landmarker Tasks API adapter for video frames."""

    def __init__(self, config: ScannerConfig | None = None):
        self.config = config or ScannerConfig()
        self.landmarker = None
        self._mp = None
        self._timestamp_ms = 0

    @property
    def is_initialized(self) -> bool:
        return self.landmarker is not None

    def start(self) -> None:
        if self.is_initialized:
            return
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
        except ImportError as exc:
            raise RuntimeError("MediaPipe is not installed. Run: python -m pip install -r requirements.txt") from exc

        model_path = ensure_model()
        try:
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=max(1, min(2, self.config.max_hands)),
                min_hand_detection_confidence=self.config.min_detection_confidence,
                min_hand_presence_confidence=self.config.min_presence_confidence,
                min_tracking_confidence=self.config.min_tracking_confidence,
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
        except Exception as exc:
            raise RuntimeError(f"MediaPipe Hand Landmarker could not initialize from {model_path}: {exc}") from exc
        self._mp = mp
        self._timestamp_ms = int(time.monotonic_ns() // 1_000_000)

    def process(self, frame_bgr: np.ndarray) -> list[HandObservation]:
        """Process one valid BGR frame and return zero to two hand observations."""
        if not self.is_initialized or self._mp is None:
            raise RuntimeError("Hand tracker has not been initialized; call start() first")
        if not isinstance(frame_bgr, np.ndarray) or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
            raise ValueError("Expected a non-empty HxWx3 BGR NumPy frame")
        if frame_bgr.size == 0 or frame_bgr.dtype != np.uint8:
            raise ValueError("Expected a non-empty uint8 BGR NumPy frame")

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        timestamp = int(time.monotonic_ns() // 1_000_000)
        self._timestamp_ms = max(self._timestamp_ms + 1, timestamp)
        result = self.landmarker.detect_for_video(image, self._timestamp_ms)

        observations: list[HandObservation] = []
        for index, landmarks in enumerate(result.hand_landmarks or []):
            handedness = "Unknown"
            score: float | None = None
            if result.handedness and index < len(result.handedness) and result.handedness[index]:
                category = result.handedness[index][0]
                handedness = category.category_name or "Unknown"
                score = category.score
            if len(landmarks) == 21:
                observations.append(HandObservation(tuple(landmarks), handedness, score))
        return observations

    def close(self) -> None:
        if self.landmarker is not None:
            self.landmarker.close()
        self.landmarker = None
        self._mp = None

