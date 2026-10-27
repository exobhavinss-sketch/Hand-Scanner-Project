from src.volume_control import VolumeController


class FakeEndpoint:
    def __init__(self, level=0.5):
        self.level = level
        self.calls = []

    def GetMasterVolumeLevelScalar(self):
        return self.level

    def SetMasterVolumeLevelScalar(self, level, _context):
        self.level = level
        self.calls.append(level)


def test_open_palm_raises_and_closed_fist_lowers_volume_once_per_transition():
    endpoint = FakeEndpoint()
    controller = VolumeController(step=0.1, cooldown=0, endpoint=endpoint)
    up = controller.handle_gesture("Open Palm")
    assert up is not None
    assert up.direction == "up"
    assert endpoint.level == 0.6
    assert controller.handle_gesture("Open Palm") is None
    down = controller.handle_gesture("Closed Fist")
    assert down is not None
    assert down.direction == "down"
    assert endpoint.level == 0.5
    assert len(endpoint.calls) == 2


def test_unknown_gestures_do_not_change_volume():
    endpoint = FakeEndpoint()
    controller = VolumeController(step=0.1, cooldown=0, endpoint=endpoint)
    assert controller.handle_gesture("Peace Sign") is None
    assert endpoint.calls == []


def test_volume_is_clamped():
    endpoint = FakeEndpoint(level=0.98)
    controller = VolumeController(step=0.1, cooldown=0, endpoint=endpoint)
    controller.handle_gesture("Open Palm")
    assert endpoint.level == 1.0
    controller.handle_gesture(None)
    controller.handle_gesture("Closed Fist")
    assert endpoint.level == 0.9

