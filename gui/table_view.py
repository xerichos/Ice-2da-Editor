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
        self.itemActivated.connect(self.prepare_for_edit) 
        self.itemClicked.connect(self.prepare_for_edit)

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
                item._old_value = val

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
        
    def prepare_for_edit(self, item):
        # store the value before editing
        item._old_value = item.text()


    # ------------------------------------------------------------------
    # Mark parent window as dirty on edits
    # ------------------------------------------------------------------
    def _on_cell_changed(self, item):
        if self._suspend_dirty:
            return

        win = self.window()
        if not hasattr(win, "undo_stack"):
            return

        row = item.row()
        col = item.column()
        new_text = item.text()

        # Retrieve old text stored before edit
        old_text = getattr(item, "_old_value", "")

        # Push undo command
        from gui.undo_commands import CellEditCommand
        cmd = CellEditCommand(self, row, col, old_text, new_text)
        win.undo_stack.push(cmd)

        # Mark document dirty
        if hasattr(win, "is_dirty"):
            win.is_dirty = True
            win.update_window_title()
