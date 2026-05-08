from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QDialog,
)
import pandas as pd
from enum import Enum

from main_ui import Ui_MainWindow
from module_selector import ModuleSelector
from process_anomaly import ProcessAnomaly, Prak

APP_VERSION = "1.0.1"


class Page(Enum):
    ORIGINAL = "original"
    LOADED = "loaded"
    ANOMALY = "anomaly"
    EMPTY = "empty"


class MainController(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.process = ProcessAnomaly()
        self.first_run: bool = True
        self.page_state: Page = Page.ORIGINAL
        self.praktikans_state: Prak = Prak.TE

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_maps()

        self.route()
        self.load_page(self.page_state)
        self.load_praktikans(self.praktikans_state)

    def route(self):
        self.ui.search_bar.textChanged.connect(self.filter_table)
        self.ui.label_version.setText(APP_VERSION)
        self.ui.btn_logo.clicked.connect(lambda: self.about_us())

        self.ui.btn_original.clicked.connect(lambda: self.load_page(Page.ORIGINAL))
        self.ui.btn_loaded.clicked.connect(lambda: self.load_page(Page.LOADED))
        self.ui.btn_anomaly.clicked.connect(lambda: self.load_page(Page.ANOMALY))

        self.ui.btn_praktikans_te.clicked.connect(lambda: self.load_praktikans(Prak.TE))
        self.ui.btn_praktikans_te_int.clicked.connect(
            lambda: self.load_praktikans(Prak.TE_INT)
        )
        self.ui.btn_praktikans_tt.clicked.connect(lambda: self.load_praktikans(Prak.TT))
        self.ui.btn_praktikans_tt_int.clicked.connect(
            lambda: self.load_praktikans(Prak.TT_INT)
        )
        self.ui.btn_praktikans_tf.clicked.connect(lambda: self.load_praktikans(Prak.TF))
        self.ui.btn_praktikans_tb.clicked.connect(lambda: self.load_praktikans(Prak.TB))
        self.ui.btn_praktikans_tse.clicked.connect(
            lambda: self.load_praktikans(Prak.TSE)
        )
        self.ui.btn_praktikans_others.clicked.connect(
            lambda: self.load_praktikans(Prak.OTHERS)
        )

        self.ui.btn_analyze.clicked.connect(self.analyze_anomaly)
        self.ui.btn_import.clicked.connect(self.import_praktikans)
        self.ui.btn_export.clicked.connect(self.export_anomaly)
        self.ui.btn_load_original.clicked.connect(self.import_praktikans_original)
        self.ui.btn_reset.clicked.connect(self.reset)

    def setup_maps(self):
        self.page_widgets = {
            Page.ORIGINAL: self.ui.page_original,
            Page.LOADED: self.ui.page_loaded,
            Page.ANOMALY: self.ui.page_anomaly,
            Page.EMPTY: self.ui.page_empty,
        }

        self.page_tables = {
            Page.ORIGINAL: self.ui.table_original,
            Page.LOADED: self.ui.table_loaded,
            Page.ANOMALY: self.ui.table_anomaly,
        }

        self.page_buttons = {
            Page.ORIGINAL: self.ui.btn_original,
            Page.LOADED: self.ui.btn_loaded,
            Page.ANOMALY: self.ui.btn_anomaly,
        }

        self.praktikans_buttons = {
            Prak.TE: self.ui.btn_praktikans_te,
            Prak.TE_INT: self.ui.btn_praktikans_te_int,
            Prak.TT: self.ui.btn_praktikans_tt,
            Prak.TT_INT: self.ui.btn_praktikans_tt_int,
            Prak.TF: self.ui.btn_praktikans_tf,
            Prak.TB: self.ui.btn_praktikans_tb,
            Prak.TSE: self.ui.btn_praktikans_tse,
            Prak.OTHERS: self.ui.btn_praktikans_others,
        }

    def load_page(self, page: Page):
        for p, btn in self.page_buttons.items():
            btn.setEnabled(p != page)

        if self.page_state == page and not self.first_run:
            return

        self.page_state = page
        self.first_run = False
        self.refresh_display()
        self.ui.stackedWidget.setCurrentWidget(self.page_widgets[page])

    def load_praktikans(self, praktikans: Prak):
        for p, btn in self.praktikans_buttons.items():
            btn.setEnabled(p != praktikans)

        if self.praktikans_state == praktikans and not self.first_run:
            return

        self.praktikans_state = praktikans
        self.first_run = False
        self.refresh_display()

    def import_praktikans_original(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            None, "Select Excel File", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if not file_paths:
            return

        reply = QMessageBox.question(
            self,
            "Import Original Data",
            "Do you want to OVERWRITE the existing original data?\n\nSelect 'Yes' to reset the field, or 'No' to just append, or 'Cancel' to you know, cancel.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        overwrite = reply == QMessageBox.StandardButton.Yes

        self.process.load_batch("original", file_paths, overwrite=overwrite)
        last_category = self.process.categorize_file(file_paths[-1])

        self.load_page(Page.ORIGINAL)
        self.load_praktikans(last_category)

    def import_praktikans(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            None, "Select Excel Files", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if not file_paths:
            return

        reply = QMessageBox.question(
            self,
            "Import Loaded Data",
            "Do you want to OVERWRITE the existing loaded data?\n\nSelect 'Yes' to reset the field, or 'No' to just append, or 'Cancel' to you know, cancel.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        overwrite = reply == QMessageBox.StandardButton.Yes

        self.process.load_batch("loaded", file_paths, overwrite=overwrite)
        last_category = self.process.categorize_file(file_paths[-1])

        self.load_page(Page.LOADED)
        self.load_praktikans(last_category)

    def analyze_anomaly(self):
        if not self.process.loaded_data:
            QMessageBox.warning(
                self, "No Data", "Please load practicing data first before analyzing."
            )
            return

        first_df = next(iter(self.process.loaded_data.values()), pd.DataFrame())
        if first_df.empty:
            QMessageBox.warning(self, "Empty Data", "The loaded data is empty.")
            return

        available_modules = self.process.get_available_modules(first_df)
        if not available_modules:
            QMessageBox.warning(
                self,
                "No Modules",
                "Could not find any modules in the loaded spreadsheets.",
            )
            return

        dialog = ModuleSelector(available_modules, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_modules = dialog.get_selected_modules()
            if not selected_modules:
                QMessageBox.warning(
                    self,
                    "Selection Required",
                    "You must select at least one module to analyze.",
                )
                return

            self.process.analyze(selected_modules)
            self.load_page(Page.ANOMALY)
            self.refresh_display()

    def export_anomaly(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Anomaly Report", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        if not file_path:
            return

        if not file_path.endswith(".xlsx"):
            file_path += ".xlsx"

        self.process.export(file_path)

    def load_dataframe_to_table(self, table, df: pd.DataFrame):
        table.clear()

        if df is None or df.empty:
            table.setRowCount(0)
            table.setColumnCount(0)
            return

        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])

        headers = []
        for col in df.columns:
            if isinstance(col, tuple):
                headers.append(" - ".join([str(c) for c in col if str(c).strip()]))
            else:
                headers.append(str(col))

        table.setHorizontalHeaderLabels(headers)

        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                value = df.iat[row, col]

                item = QTableWidgetItem()
                if pd.isna(value):
                    item.setData(Qt.ItemDataRole.DisplayRole, "")
                else:
                    item.setData(Qt.ItemDataRole.DisplayRole, value)
                table.setItem(row, col, item)

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        if table.columnCount() > 0:
            table.horizontalHeader().setSectionResizeMode(
                table.columnCount() - 1,
                QHeaderView.ResizeMode.Stretch,
            )
        table.setSortingEnabled(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def refresh_display(self):
        match self.page_state:
            case Page.ORIGINAL:
                df = self.process.get_original(self.praktikans_state)
                table = self.ui.table_original
            case Page.LOADED:
                df = self.process.get_loaded(self.praktikans_state)
                table = self.ui.table_loaded
            case Page.ANOMALY:
                df = self.process.get_anomaly(self.praktikans_state)
                table = self.ui.table_anomaly
            case _:
                return

        if df is None or df.empty:
            self.ui.stackedWidget.setCurrentWidget(self.ui.page_empty)
        else:
            self.load_dataframe_to_table(table, df)
            self.ui.stackedWidget.setCurrentWidget(self.page_widgets[self.page_state])

        self.ui.label_original.setText(str(self.process.get_count_original()))
        self.ui.label_loaded.setText(str(self.process.get_count_loaded()))
        self.ui.label_anomaly.setText(str(self.process.get_count_anomaly()))

    def filter_table(self, text: str):
        text = text.lower()

        match self.page_state:
            case Page.ORIGINAL:
                table = self.ui.table_original
            case Page.LOADED:
                table = self.ui.table_loaded
            case Page.ANOMALY:
                table = self.ui.table_anomaly
            case _:
                return

        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def about_us(self):
        html = f"""
            <table>
                <tr>
                    <td>
                        <img src="../assets/wife.png" width="160">
                    </td>
                    <td style="padding-left:12px;">
                        <p>
                            <b style="font-size: 18px;">Anomaly Checker</b> &nbsp;&nbsp;&nbsp;
                            {APP_VERSION}
                        </p>
                        <p>Find the anomalies within the sea of grades</p>
                        <p><b>Developed by:</b> petorikooru <b>@ GitHub</b></p>
                        <p>On behalf of <b>ATC 2025/2026</b> Team</p>
                        <p><i>The "A" in ATC stands for "Anomaly"</i></p>
                    </td>
                </tr>
            </table>
        """
        QMessageBox.about(self, "About", html)

    def reset(self):
        result = QMessageBox.warning(
            self,
            "Reset Data",
            "Are you sure to reset all of the data?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )

        if result == QMessageBox.StandardButton.Cancel:
            return

        self.process.reset()
        self.refresh_display()
        self.load_page(Page.ORIGINAL)
