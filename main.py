from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
    except ImportError as exc:
        print("A required desktop dependency is not available. Install the project dependencies with:")
        print("  python -m pip install -r requirements.txt")
        print(f"Details: {exc}")
        return 1
    app = QApplication(sys.argv)
    app.setApplicationName("AI Hand Scanner")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

