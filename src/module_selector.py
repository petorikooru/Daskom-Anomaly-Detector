from PyQt6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QDialogButtonBox,
    QLabel,
    QAbstractItemView,
    QDialog,
)


class ModuleSelector(QDialog):
    """Custom Dialog to let the user select which modules to analyze."""

    def __init__(self, modules, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Modules")
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select modules to check for anomalies:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self.list_widget.addItems(modules)

        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)

        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_selected_modules(self):
        return [item.text() for item in self.list_widget.selectedItems()]
