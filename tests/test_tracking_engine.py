from types import SimpleNamespace

import numpy as np

from src.camera_manager import CameraManager
from src.hand_tracker import HandObservation
from src.scanner import ScannerWorker, draw_hand_landmarks


class EmptyTracker:
    def process(self, frame):
        assert frame.dtype == np.uint8
        return []

    def close(self):
        return None


def test_no_hands_on_synthetic_frame():
    worker = ScannerWorker(camera_index=99, tracker=EmptyTracker())
    result = worker.process_frame(np.zeros((120, 160, 3), dtype=np.uint8), mirrored=False)
    assert result.hands == ()
    assert result.error is None
    assert result.frame.shape == (120, 160, 3)


def test_invalid_frame_is_reported_without_inference():
    worker = ScannerWorker(camera_index=99, tracker=EmptyTracker())
    result = worker.process_frame(np.zeros((0, 0, 3), dtype=np.uint8))
    assert result.error == "Invalid camera frame"
    assert result.hands == ()


def test_landmark_visualization_draws_expected_skeleton():
    points = tuple(SimpleNamespace(x=0.5, y=0.5) for _ in range(21))
    hand = HandObservation(points, "Right", 0.98)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    output = draw_hand_landmarks(frame, [hand])
    assert output is frame
    assert int(output.sum()) > 0


def test_unavailable_camera_is_reported_cleanly():
    camera = CameraManager(index=99)
    assert camera.open() is False
    assert camera.is_connected is False
    assert "unavailable" in camera.status.message or "permission" in camera.status.message
    camera.release()

