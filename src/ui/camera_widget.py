from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from .theme import ACCENT, BORDER, DANGER, TEXT_SECONDARY


class CameraWidget(QWidget):
    """The visual center of the app: a quiet, aspect-ratio-safe camera canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._state = "idle"
        self._message = "Press Start Scan to begin"
        self.setMinimumSize(520, 320)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_frame(self, frame) -> None:
        height, width, channels = frame.shape
        if channels != 3:
            self.set_state("error", "Unsupported camera frame")
            return
        image = QImage(frame.data, width, height, channels * width, QImage.Format.Format_BGR888).copy()
        self._pixmap = QPixmap.fromImage(image)
        self._state = "scanning"
        self.update()

    def set_state(self, state: str, message: str) -> None:
        self._state = state
        self._message = message
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#0C0D0F"))

        if not self._pixmap.isNull() and self._state == "scanning":
            scaled = self._pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.setPen(QPen(QColor(BORDER), 1))
            painter.drawRect(x, y, scaled.width() - 1, scaled.height() - 1)
            return

        inset = 20
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawRoundedRect(inset, inset, self.width() - inset * 2, self.height() - inset * 2, 12, 12)
        state_color = DANGER if self._state == "error" else ACCENT
        painter.setPen(QColor(state_color))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._message)
        painter.setPen(QColor(TEXT_SECONDARY))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(0, self.height() // 2 + 28, self.width(), 22, Qt.AlignmentFlag.AlignCenter, "Local camera processing")

