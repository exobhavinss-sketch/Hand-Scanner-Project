# AI Hand Scanner — Phase 5 Full Integration

AI Hand Scanner is a local desktop computer-vision project using MediaPipe Hand Landmarker, OpenCV, NumPy, and PySide6. Phase 5 integrates the tracking engine, gesture recognition, premium dashboard, and bounded gesture history.

## Recent changes

- Improved thumb detection using thumb reach, thumb-chain geometry, thumb-to-index separation, handedness, and mirrored-preview handling.
- Added regression coverage for Open Palm and Thumbs Up detection with both Left and Right handedness.
- Added Windows gesture volume control:
  - Open Palm raises master volume by one 8% step.
  - Closed Fist lowers master volume by one 8% step.
  - Repeated frames do not repeatedly change the volume.
- Added `src/volume_control.py` using `pycaw` and `comtypes`, with graceful fallback when Windows audio control is unavailable.
- Added volume-control unit tests and updated the dependency list.

## Features

- MediaPipe Tasks Hand Landmarker integration with an explicit local model asset path.
- Up to two hands and 21 landmarks per hand, with handedness and handedness score.
- Thread-ready camera/vision pipeline with mirroring, FPS smoothing, structured results, and skeleton drawing.
- Safe camera selection, lifecycle, connection status, invalid-frame handling, and actionable errors.
- Startup status screen for dependencies, model asset, and webcam availability.
- Conservative classification for Open Palm, Closed Fist, Peace Sign, Pointing Finger, Thumbs Up, Three Fingers, Four Fingers, and Unknown.
- Majority-window gesture debouncing through `GestureSmoother`.
- Premium dark dashboard with sidebar controls, live preview, metrics, gesture panel, status indicators, and gesture history.
- Background camera/inference processing through `QThread` signals; widgets are updated only on the GUI thread.
- Keyboard shortcuts: Space starts/stops, Escape stops, Ctrl+R rescans cameras, Ctrl+Q exits.
- Windows volume control: a stabilized Open Palm raises master volume by one step; a stabilized Closed Fist lowers it. Repeated frames do not repeatedly change volume.
- All planned computer-vision processing is local; frames are not uploaded.

## Architecture

`camera_manager.py` owns webcam lifecycle; `hand_tracker.py` initializes the MediaPipe Tasks API and model; `gesture_recognition.py` contains geometry rules and smoothing primitives; `scanner.py` runs the processing loop; `history_manager.py` handles bounded deduplication/timestamps/CSV export; `volume_control.py` provides rate-limited Windows master-volume actions; and `src/ui/` contains the PySide6 presentation layer. The UI receives frames through a `QThread` signal and never updates widgets from the camera thread.

## Prerequisites and setup

Python 3.11 is recommended. A webcam and permission for the Python process are required for live scanning.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

The tracker resolves the official `hand_landmarker.task` asset to `assets/hand_landmarker.task` and can download it from the official MediaPipe model URL. The current workspace does not contain the asset yet; the first live-tracking start will download it or show an actionable error. On Windows, `pycaw` and `comtypes` provide system-volume control; on unsupported systems or unavailable audio endpoints, scanning continues without volume actions.

## Foundation gesture module

`src/gesture_recognition.py` consumes the actual Phase 2 `HandObservation.landmarks` tuple: 21 MediaPipe normalized landmark objects with `.x`, `.y`, and optional `.z`, plus the Phase 2 handedness label. Finger extension uses wrist-relative tip/PIP distances and joint-vector alignment, not fixed screen coordinates. The `mirrored` argument keeps thumb-side interpretation consistent with MediaPipe's selfie-image handedness convention.

The recognizer is heuristic geometry, not a trained accuracy model. Extreme rotations, occlusion, motion blur, unusual finger poses, and landmarks near decision thresholds may produce `Unknown`. The result exposes extension flags, finger count, extension scores, ambiguity, and a reason so the UI can present this honestly.

The worker passes each `HandObservation.landmarks` and `HandObservation.handedness` to `recognize_gesture()`, then applies `GestureSmoother.update_result()` before emitting results to the GUI. The GUI renders `result.name`, `result.finger_count`, tracking metrics, and records only gesture changes through `HistoryManager`. History can be cleared or exported as CSV.

## Testing

```powershell
python -m pytest -q
```

The automated suite uses synthetic landmarks and does not require a webcam, MediaPipe model, or GUI display. The current suite contains 17 passing tests. Manual camera and gesture-volume testing requires installing dependencies, granting camera permission, and running `python main.py`.

For a direct engine check, instantiate `ScannerWorker` from a worker thread, call `start()`, repeatedly call `read()`, and inspect `TrackingFrame.hands`, `TrackingFrame.fps`, and `TrackingFrame.camera_connected`. The helper `process_frame()` accepts an already-captured BGR NumPy frame for integration tests.

## Troubleshooting

- **No camera detected:** close other applications using the webcam, check Windows camera privacy settings, or select another camera after reconnecting it.
- **MediaPipe/model error:** reinstall requirements and confirm the model asset can be downloaded into `assets/`.
- **Black preview:** verify the camera is not covered and that the selected camera index is correct.
- **GUI import error:** activate the virtual environment and run `python -m pip install -r requirements.txt`.

## Limitations and future improvements

Gesture rules are intentionally transparent rather than a learned classifier, and unusual rotations or occlusions may be reported as Unknown. Future work could add calibration profiles, configurable gesture mappings, richer multi-hand summaries, and optional recording of anonymized metrics (never raw frames).

