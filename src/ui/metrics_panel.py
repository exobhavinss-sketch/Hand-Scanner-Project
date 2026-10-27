from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .theme import BORDER, SURFACE


class MetricCard(QWidget):
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 11, 16, 11)
        layout.setSpacing(3)
        caption = QLabel(label)
        caption.setObjectName("eyebrow")
        self.value = QLabel(value)
        self.value.setObjectName("metricValue")
        layout.addWidget(caption)
        layout.addWidget(self.value)


class MetricsPanel(QFrame):
    """A stable, low-noise metric strip; values never reflow the camera area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metricsPanel")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.hands = MetricCard("Hands", "0")
        self.fingers = MetricCard("Fingers", "0")
        self.gesture = MetricCard("Gesture", "—")
        self.fps = MetricCard("FPS", "0")
        self.tracking = MetricCard("Tracking", "IDLE")
        cards = (self.hands, self.fingers, self.gesture, self.fps, self.tracking)
        for index, card in enumerate(cards):
            if index:
                divider = QFrame()
                divider.setFrameShape(QFrame.Shape.VLine)
                divider.setStyleSheet(f"color: {BORDER};")
                layout.addWidget(divider)
            layout.addWidget(card, 1)

