# gui/document.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QUndoStack
from .table_view import TwoDATable
from .table_model import TwoDATableModel

class TwoDADocument(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.table = TwoDATable()
        self.model = TwoDATableModel(self)
        self.table.setModel(self.model)

        self.undo_stack = QUndoStack(self)
        self.current_path = None
        self.current_data = None
        self.is_dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

        # Connect context menu signals
        self.table.requestInsertAbove.connect(self.insert_row_above)
        self.table.requestInsertBelow.connect(self.insert_row_below)
        self.table.requestDuplicate.connect(self.duplicate_row)
        self.table.requestDelete.connect(self.delete_row)

    def insert_row_above(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if self.model.insertRows(row, 1):
            self._mark_dirty()

    def insert_row_below(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if self.model.insertRows(row + 1, 1):
            self._mark_dirty()

    def duplicate_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if self.model.duplicateRow(row):
            self._mark_dirty()

    def delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        if self.model.removeRows(row, 1):
            self._mark_dirty()

    def _mark_dirty(self):
        self.is_dirty = True
        mw = self.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self)