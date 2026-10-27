from __future__ import annotations

from dataclasses import dataclass

import cv2


@dataclass(frozen=True)
class CameraStatus:
    index: int
    connected: bool
    message: str
    width: int | None = None
    height: int | None = None


def _backend() -> int:
    return cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY


def list_cameras(max_index: int = 8) -> list[int]:
    """Probe camera indexes and return only indexes that open successfully."""
    available: list[int] = []
    for index in range(max(0, max_index)):
        capture = None
        try:
            capture = cv2.VideoCapture(index, _backend())
            if capture.isOpened():
                available.append(index)
        except cv2.error:
            continue
        finally:
            if capture is not None:
                capture.release()
    return available


class CameraManager:
    """Own one OpenCV camera handle and expose safe lifecycle/status methods."""

    def __init__(self, index: int = 0, width: int = 960, height: int = 540):
        self.index = index
        self.width = width
        self.height = height
        self.capture: cv2.VideoCapture | None = None
        self._status = CameraStatus(index, False, "Camera has not been opened")

    @property
    def is_connected(self) -> bool:
        return self.capture is not None and self.capture.isOpened()

    @property
    def status(self) -> CameraStatus:
        return self._status

    def open(self) -> bool:
        self.release()
        try:
            capture = cv2.VideoCapture(self.index, _backend())
        except cv2.error as exc:
            self._status = CameraStatus(self.index, False, f"OpenCV could not open camera: {exc}")
            return False
        if not capture.isOpened():
            capture.release()
            self._status = CameraStatus(self.index, False, f"Camera {self.index} is unavailable or permission was denied")
            return False
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.width
        actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.height
        self.capture = capture
        self._status = CameraStatus(self.index, True, "Camera connected", actual_width, actual_height)
        return True

    def read(self):
        """Return ``(success, BGR frame)`` without raising for a disconnected camera."""
        if not self.is_connected:
            self._status = CameraStatus(self.index, False, "Camera is not connected")
            return False, None
        try:
            ok, frame = self.capture.read()
        except cv2.error as exc:
            self._status = CameraStatus(self.index, False, f"Camera read failed: {exc}")
            return False, None
        if not ok or frame is None:
            self._status = CameraStatus(self.index, False, "Camera returned no frame")
            return False, None
        return True, frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
        self.capture = None
        if self._status.connected:
            self._status = CameraStatus(self.index, False, "Camera released")

    def __enter__(self) -> "CameraManager":
        if not self.open():
            raise RuntimeError(self.status.message)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.release()

