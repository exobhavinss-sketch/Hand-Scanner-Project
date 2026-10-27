from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VolumeAction:
    gesture: str
    direction: str
    level: float
    delta: float

    @property
    def message(self) -> str:
        direction = "up" if self.direction == "up" else "down"
        return f"Volume {direction} → {round(self.level * 100):d}%"


class VolumeController:
    """Rate-limited Windows master-volume control driven by gesture transitions."""

    def __init__(self, step: float = 0.08, cooldown: float = 0.65, endpoint: Any | None = None):
        self.step = max(0.01, min(1.0, step))
        self.cooldown = max(0.0, cooldown)
        self.endpoint = endpoint if endpoint is not None else self._create_endpoint()
        self.status = "Volume control ready" if self.endpoint is not None else self._unavailable_reason()
        self._last_gesture: str | None = None
        self._last_action_at = 0.0

    @property
    def available(self) -> bool:
        return self.endpoint is not None

    def _unavailable_reason(self) -> str:
        if os.name != "nt":
            return "Gesture volume control is only available on Windows"
        return "Windows audio control unavailable; install project requirements and check audio permissions"

    @staticmethod
    def _create_endpoint():
        if os.name != "nt":
            return None
        try:
            from comtypes import CLSCTX_ALL, POINTER, cast
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            device = AudioUtilities.GetSpeakers()
            endpoint = getattr(device, "EndpointVolume", None)
            if endpoint is not None:
                return endpoint
            interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception:
            return None

    def handle_gesture(self, gesture: str | None) -> VolumeAction | None:
        """Apply one volume step only when a supported gesture becomes active."""
        if gesture not in {"Open Palm", "Closed Fist"}:
            self._last_gesture = None
            return None
        if gesture == self._last_gesture:
            return None
        self._last_gesture = gesture
        if self.endpoint is None:
            return None
        now = time.monotonic()
        if now - self._last_action_at < self.cooldown:
            return None
        direction = "up" if gesture == "Open Palm" else "down"
        try:
            current = float(self.endpoint.GetMasterVolumeLevelScalar())
            delta = self.step if direction == "up" else -self.step
            target = max(0.0, min(1.0, current + delta))
            self.endpoint.SetMasterVolumeLevelScalar(target, None)
            self._last_action_at = now
            self.status = "Volume control ready"
            return VolumeAction(gesture, direction, target, delta)
        except Exception as exc:
            self.status = f"Volume update failed: {exc}"
            return None

