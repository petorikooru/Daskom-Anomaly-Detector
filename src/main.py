import sys
from PyQt6.QtWidgets import QApplication

try:
    import qdarkstyle
except ImportError:
    print("Using default styling...")

from controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt6"))
    except NameError:
        pass

    widget = MainController()
    widget.setWindowTitle("Anomaly Tracker")
    widget.show()
    sys.exit(app.exec())
