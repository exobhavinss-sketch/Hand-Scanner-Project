from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from .theme import panel


class MetricCard(QWidget):
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(4)
        caption = QLabel(label.upper())
        caption.setObjectName("eyebrow")
        self.value = QLabel(value)
        self.value.setObjectName("metricValue")
        layout.addWidget(caption)
        layout.addWidget(self.value)


class MetricsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        self.hands = MetricCard("Hands", "0")
        self.fingers = MetricCard("Fingers", "0")
        self.gesture = MetricCard("Gesture", "—")
        self.fps = MetricCard("FPS", "0")
        self.tracking = MetricCard("Tracking", "IDLE")
        for column, card in enumerate((self.hands, self.fingers, self.gesture, self.fps, self.tracking)):
            wrapper = panel()
            inner = QVBoxLayout(wrapper)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.addWidget(card)
            layout.addWidget(wrapper, 0, column)
            layout.setColumnStretch(column, 1)

