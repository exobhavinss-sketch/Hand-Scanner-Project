"""Centralized visual tokens for the quiet, macOS-inspired scanner shell."""

from PySide6.QtWidgets import QFrame

# Surfaces: matte graphite instead of a collection of unrelated gradients.
WINDOW_BG = "#101113"
SURFACE = "#17181B"
SURFACE_ELEVATED = "#202124"
SURFACE_SOFT = "#1C1D20"
TEXT = "#F5F5F7"
TEXT_SECONDARY = "#A1A1AA"
TEXT_TERTIARY = "#71717A"
ACCENT = "#64D8FF"
ACCENT_SOFT = "#173541"
SUCCESS = "#8BD8A2"
WARNING = "#F2C879"
DANGER = "#FF8C96"
BORDER = "#2B2D31"
BORDER_STRONG = "#3A3D42"

# Backwards-compatible aliases for existing UI imports.
BACKGROUND = WINDOW_BG
PANEL = SURFACE
PANEL_ALT = SURFACE_ELEVATED
MUTED = TEXT_SECONDARY
ACCENT_DARK = ACCENT_SOFT

SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 24
RADIUS_SMALL = 8
RADIUS_PANEL = 14
CONTROL_HEIGHT = 34

STYLESHEET = f"""
QWidget {{
    background: {WINDOW_BG};
    color: {TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow {{ background: {WINDOW_BG}; }}
QFrame#panel {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_PANEL}px;
}}
QFrame#metricsPanel {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_PANEL}px;
}}
QLabel#eyebrow {{
    color: {TEXT_TERTIARY};
    font-size: 11px;
    font-weight: 600;
}}
QLabel#title {{
    color: {TEXT};
    font-size: 21px;
    font-weight: 600;
}}
QLabel#pageTitle {{
    color: {TEXT};
    font-size: 18px;
    font-weight: 600;
}}
QLabel#metricValue {{
    color: {TEXT};
    font-size: 20px;
    font-weight: 600;
}}
QLabel#gestureValue {{
    color: {TEXT};
    font-size: 28px;
    font-weight: 600;
}}
QLabel#muted {{ color: {TEXT_SECONDARY}; }}
QLabel#statusLabel {{ font-weight: 600; }}
QLabel#statePill {{
    background: {SURFACE_SOFT};
    border: 1px solid {BORDER};
    border-radius: 12px;
    color: {TEXT_SECONDARY};
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QPushButton {{
    background: {SURFACE_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SMALL}px;
    color: {TEXT};
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 12px;
    font-weight: 500;
}}
QPushButton:hover {{ background: #27292D; border-color: {BORDER_STRONG}; }}
QPushButton:pressed {{ background: #2D3035; }}
QPushButton:focus {{ border: 1px solid {ACCENT}; }}
QPushButton:disabled {{ color: {TEXT_TERTIARY}; background: #151619; border-color: #242529; }}
QPushButton:checked {{ background: {ACCENT_SOFT}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; border: 1px solid {ACCENT}; color: #071014; font-weight: 600; }}
QPushButton#primary:hover {{ background: #86E2FF; }}
QPushButton#quiet {{ background: transparent; border-color: transparent; color: {TEXT_SECONDARY}; }}
QPushButton#quiet:hover {{ background: {SURFACE_ELEVATED}; color: {TEXT}; }}
QComboBox {{
    background: {SURFACE_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SMALL}px;
    color: {TEXT};
    min-height: {CONTROL_HEIGHT}px;
    padding: 0 10px;
}}
QComboBox:hover {{ border-color: {BORDER_STRONG}; }}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {SURFACE_ELEVATED}; color: {TEXT}; selection-background-color: {ACCENT_SOFT}; }}
QListWidget {{ background: transparent; border: none; outline: none; color: {TEXT_SECONDARY}; }}
QListWidget::item {{ padding: 8px 2px; border-bottom: 1px solid {BORDER}; }}
QListWidget::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}
QStatusBar {{ color: {TEXT_SECONDARY}; background: {WINDOW_BG}; }}
QToolTip {{ background: {SURFACE_ELEVATED}; color: {TEXT}; border: 1px solid {BORDER_STRONG}; padding: 6px; }}
"""


def panel() -> QFrame:
    frame = QFrame()
    frame.setObjectName("panel")
    return frame

