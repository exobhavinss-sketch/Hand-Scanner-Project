from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np

from .camera_manager import CameraManager
from .config import ScannerConfig
from .hand_tracker import HandObservation, HandTracker


@dataclass(frozen=True)
class TrackingFrame:
    frame: np.ndarray
    hands: tuple[HandObservation, ...]
    fps: float
    mirrored: bool
    camera_connected: bool
    error: str | None = None


ScanFrame = TrackingFrame

HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
    (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


def draw_hand_landmarks(frame_bgr: np.ndarray, hands: list[HandObservation] | tuple[HandObservation, ...]) -> np.ndarray:
    """Draw the 21-point hand skeleton in-place and return the frame."""
    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError("Expected an HxWx3 frame for landmark drawing")
    height, width = frame_bgr.shape[:2]
    for hand in hands:
        if len(hand.landmarks) != 21:
            continue
        points = []
        for landmark in hand.landmarks:
            x = max(0, min(width - 1, int(round(float(landmark.x) * width))))
            y = max(0, min(height - 1, int(round(float(landmark.y) * height))))
            points.append((x, y))
        for start, end in HAND_CONNECTIONS:
            cv2.line(frame_bgr, points[start], points[end], (212, 175, 55), 2, cv2.LINE_AA)
        for point in points:
            cv2.circle(frame_bgr, point, 5, (255, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(frame_bgr, point, 7, (42, 183, 235), 1, cv2.LINE_AA)
    return frame_bgr


class ScannerWorker:
    """Camera/vision loop intended to run outside the GUI thread."""

    def __init__(self, camera_index: int | None = None, config: ScannerConfig | None = None,
                 camera: CameraManager | None = None, tracker: HandTracker | None = None):
        self.config = config or ScannerConfig()
        index = self.config.camera_index if camera_index is None else camera_index
        self.camera = camera or CameraManager(index, self.config.camera_width, self.config.camera_height)
        self.tracker = tracker or HandTracker(self.config)
        self.running = False
        self._last_frame_time = time.monotonic()
        self._fps = 0.0

    def start(self) -> None:
        if not self.camera.open():
            raise RuntimeError(self.camera.status.message)
        try:
            self.tracker.start()
        except Exception:
            self.camera.release()
            raise
        self.running = True
        self._last_frame_time = time.monotonic()

    def process_frame(self, frame_bgr: np.ndarray, mirrored: bool = True,
                      draw_landmarks: bool = True) -> TrackingFrame:
        """Process an already-captured frame; useful for tests and worker integrations."""
        if not isinstance(frame_bgr, np.ndarray) or frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3 or frame_bgr.size == 0:
            return TrackingFrame(np.zeros((360, 640, 3), dtype=np.uint8), tuple(), self._fps, mirrored, False, "Invalid camera frame")
        frame = cv2.flip(frame_bgr, 1) if mirrored else frame_bgr.copy()
        try:
            hands = self.tracker.process(frame)
        except Exception as exc:
            return TrackingFrame(frame, tuple(), self._fps, mirrored, self.camera.is_connected, str(exc))
        if draw_landmarks:
            draw_hand_landmarks(frame, hands)
        now = time.monotonic()
        delta = now - self._last_frame_time
        self._last_frame_time = now
        if delta > 0:
            instant_fps = 1.0 / delta
            self._fps = instant_fps if self._fps == 0 else self._fps * 0.85 + instant_fps * 0.15
        return TrackingFrame(frame, tuple(hands), self._fps, mirrored, self.camera.is_connected)

    def read(self, mirrored: bool = True, draw_landmarks: bool = True) -> TrackingFrame:
        ok, frame = self.camera.read()
        if not ok or frame is None:
            return TrackingFrame(np.zeros((360, 640, 3), dtype=np.uint8), tuple(), self._fps, mirrored, False, self.camera.status.message)
        result = self.process_frame(frame, mirrored, draw_landmarks)
        return TrackingFrame(result.frame, result.hands, result.fps, mirrored, True, result.error)

    def stop(self) -> None:
        self.running = False
        self.camera.release()
        self.tracker.close()

