from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QThread, Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
                               QListWidget, QMainWindow, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)

from ..camera_manager import list_cameras
from ..config import ScannerConfig
from ..gesture_recognition import GestureResult, GestureSmoother, recognize_gesture
from ..history_manager import HistoryManager
from ..scanner import ScannerWorker, TrackingFrame
from ..volume_control import VolumeAction, VolumeController
from .camera_widget import CameraWidget
from .metrics_panel import MetricsPanel
from .theme import ACCENT, ACCENT_DARK, BORDER, MUTED, PANEL_ALT, STYLESHEET, panel


@dataclass(frozen=True)
class ScanPayload:
    tracking: TrackingFrame
    gestures: tuple[GestureResult, ...]
    volume_action: VolumeAction | None = None


class ScanThread(QThread):
    """Owns the camera and inference loop; all UI updates happen via signals."""

    frame_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, camera_index: int, mirrored: bool, landmarks: bool, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.mirrored = mirrored
        self.landmarks = landmarks

    def run(self) -> None:
        worker = ScannerWorker(camera_index=self.camera_index, config=ScannerConfig())
        smoothers: dict[str, GestureSmoother] = {}
        volume = VolumeController(step=ScannerConfig().volume_step)
        try:
            worker.start()
            while not self.isInterruptionRequested():
                tracking = worker.read(self.mirrored, self.landmarks)
                gestures: list[GestureResult] = []
                for index, hand in enumerate(tracking.hands):
                    key = f"{hand.handedness}:{index}"
                    smoother = smoothers.setdefault(key, GestureSmoother())
                    gestures.append(smoother.update_result(
                        recognize_gesture(hand.landmarks, hand.handedness, self.mirrored)
                    ))
                primary = gestures[0].name if gestures else None
                volume_action = volume.handle_gesture(primary)
                self.frame_ready.emit(ScanPayload(tracking, tuple(gestures), volume_action))
                if tracking.error and not tracking.camera_connected:
                    self.failed.emit(tracking.error)
                    break
                self.msleep(15)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            worker.stop()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Hand Scanner")
        self.resize(1380, 850)
        self.setMinimumSize(1060, 700)
        self.setStyleSheet(STYLESHEET)
        self.thread: ScanThread | None = None
        self.available_cameras: list[int] = []
        self.history = HistoryManager(max_entries=30)
        self._build_ui()
        self._connect_shortcuts()
        self._discover_cameras()

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(22, 22, 22, 18)
        outer.setSpacing(18)
        self.setCentralWidget(root)

        outer.addWidget(self._build_sidebar())
        outer.addLayout(self._build_workspace(), 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = panel()
        sidebar.setFixedWidth(260)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 18)
        layout.setSpacing(10)

        identity = QLabel("AI HAND\nSCANNER")
        identity.setObjectName("title")
        layout.addWidget(identity)
        label = self._label("REAL-TIME COMPUTER VISION", "eyebrow")
        layout.addWidget(label)
        layout.addSpacing(24)

        layout.addWidget(self._label("CAMERA SOURCE", "eyebrow"))
        camera_row = QHBoxLayout()
        self.camera_combo = QComboBox()
        self.camera_combo.setToolTip("Select an available camera")
        self.refresh_camera_button = QPushButton("Refresh")
        self.refresh_camera_button.setToolTip("Rescan camera devices")
        camera_row.addWidget(self.camera_combo, 1)
        camera_row.addWidget(self.refresh_camera_button)
        layout.addLayout(camera_row)

        self.start_button = QPushButton("Start Scan")
        self.start_button.setObjectName("primary")
        self.stop_button = QPushButton("Stop Scan")
        self.stop_button.setEnabled(False)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.start_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.refresh_camera_button.clicked.connect(self._discover_cameras)
        self.camera_combo.currentIndexChanged.connect(self._camera_selection_changed)

        layout.addSpacing(18)
        layout.addWidget(self._label("VIEW SETTINGS", "eyebrow"))
        self.mirror_button = QPushButton("Mirrored Preview")
        self.mirror_button.setCheckable(True)
        self.mirror_button.setChecked(True)
        self.landmark_button = QPushButton("Landmark Overlay")
        self.landmark_button.setCheckable(True)
        self.landmark_button.setChecked(True)
        self.mirror_button.setToolTip("Flip the preview horizontally for a selfie-style view")
        self.landmark_button.setToolTip("Show or hide the 21-point hand skeleton")
        layout.addWidget(self.mirror_button)
        layout.addWidget(self.landmark_button)

        layout.addStretch(1)
        status_box = QFrame()
        status_box.setStyleSheet(f"QFrame {{ background: {PANEL_ALT}; border: 1px solid {BORDER}; border-radius: 9px; }}")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.addWidget(self._label("CONNECTION", "eyebrow"))
        self.connection_label = QLabel("●  READY")
        self.connection_label.setObjectName("statusLabel")
        status_layout.addWidget(self.connection_label)
        layout.addWidget(status_box)
        layout.addWidget(self._label("Frames are processed locally.\nNo camera data leaves this device.", "muted"))
        return sidebar

    def _build_workspace(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(self._label("LIVE SCAN", "eyebrow"))
        header.addStretch(1)
        self.header_state = QLabel("IDLE")
        self.header_state.setObjectName("statePill")
        header.addWidget(self.header_state)
        layout.addLayout(header)

        preview_panel = panel()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        self.camera_widget = CameraWidget()
        preview_layout.addWidget(self.camera_widget, 1)
        layout.addWidget(preview_panel, 1)

        self.metrics = MetricsPanel()
        layout.addWidget(self.metrics)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        bottom.addWidget(self._build_gesture_panel(), 1)
        bottom.addWidget(self._build_history_panel(), 1)
        layout.addLayout(bottom)
        return layout

    def _build_gesture_panel(self) -> QFrame:
        widget = panel()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.addWidget(self._label("CURRENT GESTURE", "eyebrow"))
        self.gesture_label = QLabel("No hand detected")
        self.gesture_label.setObjectName("gestureValue")
        self.gesture_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.gesture_label)
        self.gesture_detail = self._label("Start a scan to analyze hand landmarks.", "muted")
        layout.addWidget(self.gesture_detail)
        return widget

    def _build_history_panel(self) -> QFrame:
        widget = panel()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(18, 14, 18, 10)
        heading = QHBoxLayout()
        heading.addWidget(self._label("RECENT GESTURE EVENTS", "eyebrow"))
        heading.addStretch(1)
        self.clear_history_button = QPushButton("Clear")
        self.export_history_button = QPushButton("Export CSV")
        self.clear_history_button.setToolTip("Clear recognized gesture events")
        self.export_history_button.setToolTip("Export gesture events to a CSV file")
        heading.addWidget(self.clear_history_button)
        heading.addWidget(self.export_history_button)
        layout.addLayout(heading)
        self.history_list = QListWidget()
        layout.addWidget(self.history_list)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.export_history_button.clicked.connect(self.export_history)
        self._render_history()
        return widget

    def _connect_shortcuts(self):
        self._add_shortcut("Space", self._toggle_scan)
        self._add_shortcut("Escape", self.stop_scan)
        self._add_shortcut("Ctrl+R", self._discover_cameras)
        self._add_shortcut("Ctrl+Q", self.close)

    def _add_shortcut(self, sequence: str, callback):
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.activated.connect(callback)

    def _discover_cameras(self):
        if self.thread is not None and self.thread.isRunning():
            return
        self.available_cameras = list_cameras()
        self.camera_combo.clear()
        if not self.available_cameras:
            self.camera_combo.addItem("No camera detected", -1)
            self.start_button.setEnabled(False)
            self._set_connection("NO CAMERA", False)
            self.camera_widget.set_state("error", "No accessible webcam detected")
            return
        for index in self.available_cameras:
            self.camera_combo.addItem(f"Camera {index}", index)
        self.start_button.setEnabled(True)
        self._set_connection("READY", True)
        self.camera_widget.set_state("idle", "Press Start Scan to begin")

    def _camera_selection_changed(self, index: int):
        """Never swap a camera handle while the worker is reading a frame."""
        if self.thread is not None and self.thread.isRunning():
            self.stop_scan()

    @Slot()
    def start_scan(self):
        if self.thread is not None and self.thread.isRunning():
            return
        index = self.camera_combo.currentData()
        if index is None or index < 0:
            self._set_connection("NO CAMERA", False)
            return
        self.thread = ScanThread(index, self.mirror_button.isChecked(), self.landmark_button.isChecked(), self)
        self.thread.frame_ready.connect(self._on_frame)
        self.thread.failed.connect(self._on_worker_error)
        self.thread.finished.connect(self._on_thread_finished)
        self.thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.camera_combo.setEnabled(False)
        self.refresh_camera_button.setEnabled(False)
        self.mirror_button.setEnabled(False)
        self.landmark_button.setEnabled(False)
        self.camera_widget.set_state("idle", "Initializing camera and hand model…")
        self._set_connection("STARTING", True)
        self.metrics.tracking.value.setText("STARTING")
        self.header_state.setText("STARTING")

    @Slot()
    def stop_scan(self, wait: bool = False):
        if self.thread is not None:
            self.thread.requestInterruption()
            self.stop_button.setEnabled(False)
            self._set_connection("STOPPING", True)
            if wait:
                self.thread.wait(2000)
                if self.thread.isRunning():
                    self._set_connection("SHUTDOWN DELAYED", False)
                    return
        if self.thread is None or not self.thread.isRunning():
            self._set_idle_state()

    def _toggle_scan(self):
        if self.thread is not None and self.thread.isRunning():
            self.stop_scan()
        else:
            self.start_scan()

    @Slot(object)
    def _on_frame(self, payload: ScanPayload):
        tracking = payload.tracking
        self.camera_widget.set_frame(tracking.frame)
        self.metrics.hands.value.setText(str(len(tracking.hands)))
        self.metrics.fingers.value.setText(str(sum(result.finger_count for result in payload.gestures)))
        self.metrics.fps.value.setText(f"{tracking.fps:.0f}")
        self.metrics.tracking.value.setText("ACTIVE" if tracking.camera_connected else "ERROR")
        self.header_state.setText("SCANNING" if tracking.camera_connected else "ERROR")
        if tracking.error:
            self.camera_widget.set_state("error", tracking.error)
            self._set_connection("ERROR", False)
            return
        if payload.gestures:
            primary = payload.gestures[0]
            self.metrics.gesture.value.setText(primary.name)
            self.gesture_label.setText(primary.name)
            if self.history.record(primary.name):
                self._render_history()
            hand = tracking.hands[0]
            self.gesture_detail.setText(f"{hand.handedness} hand  •  {primary.finger_count} extended fingers")
        else:
            self.metrics.gesture.value.setText("—")
            self.gesture_label.setText("No hand detected")
            self.gesture_detail.setText("Place a hand inside the camera frame.")
        if payload.volume_action:
            self.gesture_detail.setText(self.gesture_detail.text() + f"  /  {payload.volume_action.message}")
        self._set_connection("CONNECTED", True)

    @Slot(str)
    def _on_worker_error(self, message: str):
        self.camera_widget.set_state("error", message)
        self._set_connection("ERROR", False)
        self.header_state.setText("ERROR")

    @Slot()
    def _on_thread_finished(self):
        if self.thread is not None and not self.thread.isRunning():
            self.thread = None
        self._set_idle_state(keep_error=self.connection_label.text().endswith("ERROR"))

    def clear_history(self):
        self.history.clear()
        self._render_history()

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Gesture History", "gesture_history.csv", "CSV files (*.csv)"
        )
        if path:
            self.history.export_csv(path)

    def _render_history(self):
        self.history_list.clear()
        if not self.history.events:
            self.history_list.addItem("No gesture changes recorded yet.")
            return
        for event in reversed(self.history.events):
            self.history_list.addItem(f"{event.time_text}   {event.gesture}")

    def _set_idle_state(self, keep_error: bool = False):
        self.start_button.setEnabled(bool(self.available_cameras) and not keep_error)
        self.stop_button.setEnabled(False)
        self.camera_combo.setEnabled(True)
        self.refresh_camera_button.setEnabled(True)
        self.mirror_button.setEnabled(True)
        self.landmark_button.setEnabled(True)
        self.metrics.tracking.value.setText("IDLE" if not keep_error else "ERROR")
        self.metrics.gesture.value.setText("—")
        self.header_state.setText("IDLE" if not keep_error else "ERROR")
        if not keep_error:
            self._set_connection("READY" if self.available_cameras else "NO CAMERA", bool(self.available_cameras))
            self.camera_widget.set_state("idle" if self.available_cameras else "error", "Press Start Scan to begin" if self.available_cameras else "No accessible webcam detected")

    def _set_connection(self, text: str, healthy: bool):
        self.connection_label.setText("●  " + text)
        self.connection_label.setStyleSheet(f"color: {ACCENT if healthy else '#ef8d8d'};")

    @staticmethod
    def _label(text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def closeEvent(self, event):
        self.stop_scan(wait=True)
        if self.thread is not None and self.thread.isRunning():
            event.ignore()
            return
        event.accept()

