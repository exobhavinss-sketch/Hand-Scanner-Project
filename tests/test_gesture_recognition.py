from types import SimpleNamespace

from src.gesture_recognition import GestureSmoother, count_extended_fingers, recognize_gesture


def landmarks(extended=(False, False, False, False, False), thumb_side="right", rotate=False):
    """MediaPipe-shaped normalized landmarks with optional 90-degree rotation."""
    points = [(0.50, 0.85, 0.0) for _ in range(21)]
    points[0] = (0.50, 0.85, 0.0)
    for x, mcp in zip((0.35, 0.45, 0.50, 0.55, 0.60), (2, 5, 9, 13, 17)):
        points[mcp] = (x, 0.55, 0.0)
    for index, (tip, pip, mcp, x) in enumerate(zip((4, 8, 12, 16, 20), (3, 6, 10, 14, 18), (2, 5, 9, 13, 17), (0.35, 0.45, 0.50, 0.55, 0.60))):
        if index == 0:
            points[pip] = (0.42, 0.65, 0.0) if not extended[0] else (0.42, 0.65, 0.0)
            folded_x = 0.35 if thumb_side == "right" else 0.55
            extended_x = 0.25 if thumb_side == "right" else 0.70
            points[tip] = (folded_x, 0.72, 0.0) if not extended[0] else (extended_x, 0.60, 0.0)
        else:
            points[pip] = (x, 0.40 if extended[index] else 0.65, 0.0)
            points[tip] = (x, 0.25 if extended[index] else 0.72, 0.0)
    if rotate:
        points = [(1.0 - y, x, z) for x, y, z in points]
    return [SimpleNamespace(x=x, y=y, z=z) for x, y, z in points]


def test_expected_gestures_with_both_handedness_labels():
    cases = [
        ((True, True, True, True, True), "Open Palm"),
        ((False, False, False, False, False), "Closed Fist"),
        ((False, True, True, False, False), "Peace Sign"),
        ((False, True, False, False, False), "Pointing Finger"),
        ((True, False, False, False, False), "Thumbs Up"),
        ((False, True, True, True, False), "Three Fingers"),
        ((False, True, True, True, True), "Four Fingers"),
    ]
    for handedness in ("Left", "Right"):
        for pose, expected in cases:
            result = recognize_gesture(landmarks(pose, thumb_side=handedness.lower()), handedness)
            assert result.name == expected, (handedness, pose, result)


def test_rotation_does_not_depend_on_vertical_screen_direction():
    assert recognize_gesture(landmarks((False, True, True, False, False), rotate=True), "Right").name == "Peace Sign"


def test_unmirrored_input_swaps_handedness_for_thumb_geometry():
    pose = landmarks((True, False, False, False, False))
    assert recognize_gesture(pose, "Right", mirrored=True).name == "Thumbs Up"
    assert recognize_gesture(pose, "Left", mirrored=False).name == "Thumbs Up"


def test_ambiguous_and_missing_landmarks_are_unknown():
    ambiguous = landmarks((False, True, False, False, False))
    ambiguous[8] = SimpleNamespace(x=0.45, y=0.37, z=0.0)
    result = recognize_gesture(ambiguous, "Right")
    assert result.name == "Unknown"
    assert result.ambiguous
    missing = recognize_gesture([], "Right")
    assert missing.name == "Unknown"
    assert missing.finger_count == 0


def test_count_is_structured_and_scores_are_available():
    result = recognize_gesture(landmarks((False, True, True, False, False)), "Left")
    assert count_extended_fingers(landmarks((False, True, True, False, False)), "Left") == (False, True, True, False, False)
    assert result.finger_count == 2
    assert len(result.extension_scores) == 5


def test_smoother_debounces_single_frame_flicker():
    smoother = GestureSmoother(window_size=5, min_consistent=3)
    assert smoother.update("Open Palm") == "Open Palm"
    assert smoother.update("Unknown") == "Open Palm"
    assert smoother.update("Unknown") == "Open Palm"
    assert smoother.update("Unknown") == "Unknown"

