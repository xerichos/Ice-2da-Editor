# gui/document.py
import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QUndoStack
from PyQt5.QtCore import QTimer
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

        # Search state
        self._search_regex = None
        self._search_last_row = -1
        self._search_last_col = -1

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

    def set_search(self, regex, replacement):
        """Set the search pattern and perform search/replace."""
        """Search and replace in the table data."""
        if not self.model:
            return

        rows = self.model._rows
        header = self.model._header
        modified = False

        for r, row in enumerate(rows):
            for c, cell_value in enumerate(row):
                if isinstance(cell_value, str) and regex.search(cell_value):
                    new_value = regex.sub(replacement, cell_value)
                    if new_value != cell_value:
                        self.model.set_cell(r, c, new_value)
                        modified = True

        if modified:
            self._mark_dirty()

    def find_next(self):
        """Find next occurrence of search pattern."""
        if not self._search_regex or not self.model:
            return

        rows = self.model._rows
        header = self.model._header

        if self._search_last_row < 0 or self._search_last_col < 0:
            start_row = 0
            start_col = 0
        else:
            start_row = self._search_last_row
            start_col = self._search_last_col + 1

        for r in range(start_row, len(rows)):
            row = rows[r]
            col_start = start_col if r == start_row else 0

            for c in range(max(1, col_start), len(row)):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    # Found match - select it
                    self._search_last_row = r
                    self._search_last_col = c
                    self.table.setCurrentIndex(self.model.index(r, c))
                    self.table.scrollTo(self.model.index(r, c))
                    return

        # Wrap around to beginning
        for r in range(0, start_row + 1):
            row = rows[r]
            col_end = start_col if r == start_row else len(row)

            for c in range(0, col_end):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    # Found match - select it
                    self._search_last_row = r
                    self._search_last_col = c
                    self.table.setCurrentIndex(self.model.index(r, c))
                    self.table.scrollTo(self.model.index(r, c))
                    return

    def find_previous(self):
        """Find previous occurrence of search pattern."""
        if not self._search_regex or not self.model:
            return

        rows = self.model._rows

        if self._search_last_row < 0 or self._search_last_col < 0:
            start_row = len(rows) - 1
            start_col = len(rows[start_row]) - 1 if rows else -1
        else:
            start_row = self._search_last_row
            start_col = self._search_last_col - 1

        for r in range(start_row, -1, -1):
            row = rows[r]
            col_start = start_col if r == start_row else len(row) - 1

            for c in range(col_start, -1, -1):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    # Found match - select it
                    self._search_last_row = r
                    self._search_last_col = c
                    self.table.setCurrentIndex(self.model.index(r, c))
                    self.table.scrollTo(self.model.index(r, c))
                    return

        # Wrap around to end
        for r in range(len(rows) - 1, start_row - 1, -1):
            row = rows[r]
            col_start = len(row) - 1 if r != start_row else start_col

            for c in range(col_start, -1, -1):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    # Found match - select it
                    self._search_last_row = r
                    self._search_last_col = c
                    self.table.setCurrentIndex(self.model.index(r, c))
                    self.table.scrollTo(self.model.index(r, c))
                    return

    def _mark_dirty(self):
        self.is_dirty = True
        mw = self.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self)

    def replace_all(self, regex, replacement):
        self.model.beginResetModel()
        ...
        self.model.endResetModel()
        self._mark_dirty()


    def set_search_pattern(self, regex):
        self._search_regex = regex
        self._search_last_row = -1
        self._search_last_col = -1

    def replace_current(self, replacement):
        r, c = self._search_last_row, self._search_last_col
        if r < 0 or c < 0:
            return

        cell = self.model._rows[r][c]
        match = self._search_regex.search(cell)
        if not match:
            return

        new = cell[:match.start()] + replacement + cell[match.end():]
        self.model.set_cell(r, c, new)
        self._mark_dirty()
