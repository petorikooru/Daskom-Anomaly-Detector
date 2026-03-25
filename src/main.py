import sys
from PyQt6.QtWidgets import QApplication
import qdarkstyle

from controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="pyqt6"))
    widget = MainController()
    widget.setWindowTitle("Anomaly Tracker")
    widget.show()
    sys.exit(app.exec())
