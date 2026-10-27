from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class CameraWidget(QWidget):
    """Responsive camera canvas with explicit idle and error states."""

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
        painter.fillRect(self.rect(), QColor("#070b10"))
        if not self._pixmap.isNull() and self._state == "scanning":
            scaled = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.setPen(QPen(QColor("#39c7ee"), 1))
            painter.drawRect(x, y, scaled.width() - 1, scaled.height() - 1)
            return

        painter.setPen(QPen(QColor("#243342"), 1))
        painter.drawRect(18, 18, self.width() - 36, self.height() - 36)
        painter.setPen(QColor("#39c7ee" if self._state != "error" else "#ef8d8d"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._message)

