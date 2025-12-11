# gui/table_view.py

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


class TwoDATable(QTableWidget):

    DEFAULT_BG = QColor("#2b2b2b")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._suspend_dirty = False
        self.itemChanged.connect(self._on_cell_changed)

    def set_data(self, header, rows):
        # Prevent dirty flag from triggering while filling data
        self._suspend_dirty = True

        self.clear()
        self.setColumnCount(len(header))
        self.setHorizontalHeaderLabels(header)
        self.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                item.setBackground(self.DEFAULT_BG)
                self.setItem(r, c, item)

        self._suspend_dirty = False

    def extract_data(self):
        header = []
        for c in range(self.columnCount()):
            item = self.horizontalHeaderItem(c)
            header.append(item.text() if item else "")

        rows = []
        for r in range(self.rowCount()):
            row = []
            for c in range(self.columnCount()):
                item = self.item(r, c)
                row.append(item.text() if item else "")
            rows.append(row)

        return header, rows

    # ------------------------------------------------------------------
    # Mark parent window as dirty on edits
    # ------------------------------------------------------------------
    def _on_cell_changed(self, item):
        if self._suspend_dirty:
            return

        win = self.window()
        if hasattr(win, "is_dirty"):
            win.is_dirty = True
            if hasattr(win, "update_window_title"):
                win.update_window_title()
