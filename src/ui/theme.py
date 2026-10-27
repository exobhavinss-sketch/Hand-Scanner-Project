from PySide6.QtWidgets import QFrame

BACKGROUND = "#0b1016"
PANEL = "#111923"
PANEL_ALT = "#151f2b"
TEXT = "#f4f7fa"
MUTED = "#8b9aaa"
ACCENT = "#39c7ee"
ACCENT_DARK = "#123b4a"
BORDER = "#243342"

STYLESHEET = f"""
QWidget {{ background: {BACKGROUND}; color: {TEXT}; font-family: 'Segoe UI'; font-size: 13px; }}
QFrame#panel {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 14px; }}
QLabel#eyebrow {{ color: {MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QLabel#title {{ font-size: 25px; font-weight: 700; }}
QLabel#metricValue {{ color: {ACCENT}; font-size: 24px; font-weight: 700; }}
QLabel#gestureValue {{ color: {TEXT}; font-size: 30px; font-weight: 700; }}
QLabel#muted {{ color: {MUTED}; }}
QPushButton {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 9px 12px; font-weight: 600; }}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:checked {{ background: {ACCENT_DARK}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; color: #061017; border: none; }}
QComboBox {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px; }}
QListWidget {{ background: transparent; border: none; outline: none; }}
QListWidget::item {{ padding: 8px 2px; border-bottom: 1px solid {BORDER}; }}
QStatusBar {{ color: {MUTED}; }}
QToolTip {{ background: {PANEL_ALT}; color: {TEXT}; border: 1px solid {BORDER}; padding: 5px; }}
"""


def panel() -> QFrame:
    frame = QFrame()
    frame.setObjectName("panel")
    return frame

