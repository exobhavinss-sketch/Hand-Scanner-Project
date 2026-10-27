from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from math import hypot, isfinite
from typing import Sequence

LANDMARK_COUNT = 21
WRIST = 0
THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
FINGER_TIPS = (8, 12, 16, 20)
FINGER_PIPS = (6, 10, 14, 18)
FINGER_MCPS = (5, 9, 13, 17)


@dataclass(frozen=True)
class GestureResult:
    """Heuristic gesture output, independent of camera and GUI code."""

    name: str
    finger_count: int
    extended: tuple[bool, bool, bool, bool, bool]
    extension_scores: tuple[float, float, float, float, float] = (0.0,) * 5
    ambiguous: bool = False
    reason: str = ""

    @property
    def label(self) -> str:
        """Alias convenient for UI consumers."""
        return self.name


def _xyz(point: object) -> tuple[float, float, float]:
    """Read MediaPipe NormalizedLandmark-like objects or test tuples."""
    if hasattr(point, "x") and hasattr(point, "y"):
        return float(point.x), float(point.y), float(getattr(point, "z", 0.0))
    values = tuple(float(value) for value in point)  # type: ignore[arg-type]
    if len(values) < 2:
        raise ValueError("landmark must contain at least x and y")
    return values[0], values[1], values[2] if len(values) > 2 else 0.0


def _valid_landmarks(landmarks: Sequence[object]) -> bool:
    if len(landmarks) != LANDMARK_COUNT:
        return False
    try:
        return all(isfinite(value) for point in landmarks for value in _xyz(point))
    except (TypeError, ValueError):
        return False


def _distance(a: object, b: object) -> float:
    ax, ay, _ = _xyz(a)
    bx, by, _ = _xyz(b)
    return hypot(ax - bx, ay - by)


def _alignment(a: object, b: object, c: object) -> float:
    """Cosine of the angle between a→b and b→c in normalized image space."""
    ax, ay, _ = _xyz(a)
    bx, by, _ = _xyz(b)
    cx, cy, _ = _xyz(c)
    first = (bx - ax, by - ay)
    second = (cx - bx, cy - by)
    first_length = hypot(*first)
    second_length = hypot(*second)
    if first_length == 0 or second_length == 0:
        return 0.0
    return (first[0] * second[0] + first[1] * second[1]) / (first_length * second_length)


def _effective_handedness(handedness: str | None, mirrored: bool) -> str | None:
    if not handedness:
        return None
    label = handedness.strip().lower()
    if label not in {"left", "right"}:
        return None
    # MediaPipe's handedness assumes a mirrored/selfie input. Swap only when
    # callers explicitly provide an unmirrored coordinate frame.
    if mirrored:
        return label
    return "left" if label == "right" else "right"


def _finger_analysis(landmarks: Sequence[object], mirrored: bool, handedness: str | None):
    """Return extension flags, scores, and ambiguity flags for five fingers."""
    wrist = landmarks[WRIST]
    flags: list[bool] = []
    scores: list[float] = []
    ambiguous: list[bool] = []

    # Thumb extension combines reach, the MCP->IP->TIP chain direction, and
    # separation from the index base. This handles thumbs-up poses where the
    # thumb is mostly vertical and therefore has little horizontal movement.
    thumb_tip_radius = _distance(wrist, landmarks[THUMB_TIP])
    thumb_ip_radius = _distance(wrist, landmarks[THUMB_IP])
    thumb_reach = thumb_tip_radius / max(thumb_ip_radius, 1e-6)
    thumb_alignment = _alignment(landmarks[THUMB_MCP], landmarks[THUMB_IP], landmarks[THUMB_TIP])
    palm_width = max(_distance(landmarks[FINGER_MCPS[0]], landmarks[FINGER_MCPS[3]]), 1e-6)
    thumb_separation = _distance(landmarks[THUMB_TIP], landmarks[FINGER_MCPS[0]]) / palm_width
    thumb_score = thumb_reach * max(thumb_alignment, 0.0) + min(thumb_separation, 2.0) * 0.20
    # The thumb commonly bends at the IP joint even when fully extended, so
    # use its reach and separation as the strong signals and allow a broad
    # but non-folded chain angle.
    thumb_extended = thumb_reach >= 1.10 and thumb_alignment >= -0.85 and thumb_separation >= 0.22
    thumb_ambiguous = (
        (1.02 < thumb_reach < 1.10)
        or (-0.95 < thumb_alignment < -0.85)
        or (0.15 < thumb_separation < 0.22)
    )
    effective_hand = _effective_handedness(handedness, mirrored)
    if effective_hand:
        tx, ty, _ = _xyz(landmarks[THUMB_TIP])
        ix, iy, _ = _xyz(landmarks[FINGER_MCPS[0]])
        outside = (ix - tx) if effective_hand == "right" else (tx - ix)
        # A thumb pointing upward can be nearly above the index MCP, so use
        # the vertical escape route instead of rejecting it on x alone.
        thumb_side_clear = outside / palm_width > -0.45 or abs(ty - iy) / palm_width > 0.40
        thumb_ambiguous = thumb_ambiguous or (thumb_extended and not thumb_side_clear)
        # Strong geometric evidence wins over a weak side cue because hands
        # can rotate in depth and the thumb can cross the index's x position.
        thumb_extended = thumb_extended and (thumb_side_clear or thumb_reach >= 1.45)
    flags.append(thumb_extended)
    scores.append(thumb_score)
    ambiguous.append(thumb_ambiguous)

    for tip_id, pip_id, mcp_id in zip(FINGER_TIPS, FINGER_PIPS, FINGER_MCPS):
        tip_radius = _distance(wrist, landmarks[tip_id])
        pip_radius = _distance(wrist, landmarks[pip_id])
        radius_ratio = tip_radius / max(pip_radius, 1e-6)
        alignment = _alignment(landmarks[mcp_id], landmarks[pip_id], landmarks[tip_id])
        # Both terms are orientation-tolerant: a finger should extend beyond
        # its PIP joint from the wrist and its two segments should be aligned.
        score = radius_ratio * max(alignment, 0.0)
        extended = radius_ratio >= 1.10 and alignment >= 0.35
        is_ambiguous = (1.02 < radius_ratio < 1.10) or (0.15 < alignment < 0.35)
        flags.append(extended)
        scores.append(score)
        ambiguous.append(is_ambiguous)
    return tuple(flags), tuple(scores), any(ambiguous)


def count_extended_fingers(landmarks: Sequence[object], handedness: str | None = None,
                           mirrored: bool = True) -> tuple[bool, ...]:
    """Return thumb/index/middle/ring/pinky extension flags.

    Phase 2 passes MediaPipe normalized landmarks from a mirrored frame, so
    ``mirrored=True`` is the default. Set it to False for an unmirrored frame.
    Invalid or incomplete landmarks return five false flags.
    """
    if not _valid_landmarks(landmarks):
        return (False,) * 5
    flags, _, _ = _finger_analysis(landmarks, mirrored, handedness)
    return flags


def recognize_gesture(landmarks: Sequence[object], handedness: str | None = None,
                      mirrored: bool = True) -> GestureResult:
    """Classify a hand pose using conservative geometric rules."""
    if not _valid_landmarks(landmarks):
        return GestureResult("Unknown", 0, (False,) * 5, reason="Expected exactly 21 valid landmarks")
    extended, scores, ambiguous = _finger_analysis(landmarks, mirrored, handedness)
    count = sum(extended)
    if ambiguous:
        name = "Unknown"
        reason = "Landmark geometry is borderline or partially occluded"
    elif extended == (False, False, False, False, False):
        name, reason = "Closed Fist", "All fingers are folded"
    elif extended == (True, True, True, True, True):
        name, reason = "Open Palm", "All five fingers are extended"
    elif extended == (True, False, False, False, False):
        name, reason = "Thumbs Up", "Only the thumb is extended"
    elif extended == (False, True, False, False, False):
        name, reason = "Pointing Finger", "Only the index finger is extended"
    elif extended == (False, True, True, False, False):
        name, reason = "Peace Sign", "Index and middle fingers are extended"
    elif count == 3 and not extended[0]:
        name, reason = "Three Fingers", "Three non-thumb fingers are extended"
    elif count == 4 and not extended[0]:
        name, reason = "Four Fingers", "Four non-thumb fingers are extended"
    else:
        name, reason = "Unknown", "Combination is outside the supported gesture set"
    return GestureResult(name, count, extended, scores, ambiguous, reason)


class GestureSmoother:
    """Majority-window debouncer for frame-by-frame gesture labels."""

    def __init__(self, window_size: int = 5, min_consistent: int = 3):
        self.window_size = max(1, window_size)
        self.min_consistent = max(1, min(min_consistent, self.window_size))
        self._values: deque[str] = deque(maxlen=self.window_size)
        self._stable: str = "Unknown"

    @property
    def stable_label(self) -> str:
        return self._stable

    def update(self, value: str) -> str:
        self._values.append(value or "Unknown")
        candidate, count = Counter(self._values).most_common(1)[0]
        if count >= self.min_consistent or len(self._values) == 1:
            self._stable = candidate
        return self._stable

    def update_result(self, result: GestureResult) -> GestureResult:
        stable = self.update(result.name)
        return result if stable == result.name else GestureResult(
            stable, result.finger_count, result.extended, result.extension_scores,
            result.ambiguous, result.reason,
        )

