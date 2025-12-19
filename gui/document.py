# gui/document.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QUndoStack
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QUndoCommand

from .table_view import TwoDATable
from .table_model import TwoDATableModel


SEARCHABLE_COL_START = 1  # 2DA rule: column 0 is structural (row label/index), do not search/replace


# -----------------------------
# Undo commands for row ops
# -----------------------------
class InsertRowCommand(QUndoCommand):
    def __init__(self, doc, row: int, count: int = 1, label: str = "Insert Row"):
        super().__init__(label)
        self.doc = doc
        self.row = row
        self.count = count
        self._did_redo = False

    def redo(self):
        # Insert empty rows via model so signals/view updates are correct
        self.doc.model.insertRows(self.row, self.count)
        self._did_redo = True

    def undo(self):
        if not self._did_redo:
            return
        self.doc.model.removeRows(self.row, self.count)


class RemoveRowCommand(QUndoCommand):
    def __init__(self, doc, row: int, count: int = 1, label: str = "Delete Row"):
        super().__init__(label)
        self.doc = doc
        self.row = row
        self.count = count
        self._removed_rows = None  # list[list[str]]

    def redo(self):
        # Snapshot rows before deletion so undo can restore them exactly
        rows = self.doc.model._rows
        if self.row < 0 or self.row >= len(rows) or self.count <= 0:
            self._removed_rows = []
            return
        last = min(len(rows), self.row + self.count)
        self._removed_rows = [list(r) for r in rows[self.row:last]]
        self.doc.model.removeRows(self.row, self.count)

    def undo(self):
        if not self._removed_rows:
            return

        m = self.doc.model
        insert_at = max(0, min(self.row, len(m._rows)))
        m.beginInsertRows(QModelIndex(), insert_at, insert_at + len(self._removed_rows) - 1)
        for i, row_data in enumerate(self._removed_rows):
            # Ensure row has at least as many cols as header
            row = list(row_data)
            while len(row) < len(m._header):
                row.append("")
            m._rows.insert(insert_at + i, row)
        m.endInsertRows()


class DuplicateRowCommand(QUndoCommand):
    def __init__(self, doc, row: int, label: str = "Duplicate Row"):
        super().__init__(label)
        self.doc = doc
        self.row = row
        self._copied = None  # list[str]
        self._insert_at = row + 1

    def redo(self):
        m = self.doc.model
        if self.row < 0 or self.row >= len(m._rows):
            self._copied = None
            return

        self._copied = list(m._rows[self.row])
        while len(self._copied) < len(m._header):
            self._copied.append("")

        insert_at = max(0, min(self._insert_at, len(m._rows)))
        m.beginInsertRows(QModelIndex(), insert_at, insert_at)
        m._rows.insert(insert_at, list(self._copied))
        m.endInsertRows()

    def undo(self):
        m = self.doc.model
        if self._copied is None:
            return
        # Remove the row we inserted at redo-time. Clamp in case other ops happened.
        idx = max(0, min(self._insert_at, len(m._rows) - 1))
        m.removeRows(idx, 1)


# -----------------------------
# Undo commands for column ops
# -----------------------------
class InsertColumnCommand(QUndoCommand):
    def __init__(self, doc, col: int, count: int = 1, label: str = "Insert Column"):
        super().__init__(label)
        self.doc = doc
        self.col = col
        self.count = count
        self._did_redo = False

    def redo(self):
        # Insert empty columns via model so signals/view updates are correct
        self.doc.model.insertColumns(self.col, self.count)
        self._did_redo = True

    def undo(self):
        if not self._did_redo:
            return
        self.doc.model.removeColumns(self.col, self.count)


class RemoveColumnCommand(QUndoCommand):
    def __init__(self, doc, col: int, count: int = 1, label: str = "Delete Column"):
        super().__init__(label)
        self.doc = doc
        self.col = col
        self.count = count
        self._removed_header = None  # list[str]
        self._removed_data = None    # list[list[str]]

    def redo(self):
        # Snapshot columns before deletion so undo can restore them exactly
        m = self.doc.model
        if self.col < 0 or self.col >= len(m._header) or self.count <= 0:
            self._removed_header = []
            self._removed_data = []
            return

        last = min(len(m._header), self.col + self.count)
        self._removed_header = m._header[self.col:last]

        # Extract column data from all rows
        self._removed_data = []
        for row in m._rows:
            if self.col < len(row):
                col_data = row[self.col:min(len(row), self.col + self.count)]
                self._removed_data.append(col_data)
            else:
                self._removed_data.append([])

        self.doc.model.removeColumns(self.col, self.count)

    def undo(self):
        if not self._removed_header or not self._removed_data:
            return

        m = self.doc.model
        insert_at = max(0, min(self.col, len(m._header)))
        m.beginInsertColumns(QModelIndex(), insert_at, insert_at + len(self._removed_header) - 1)

        # Insert headers
        for i, header in enumerate(self._removed_header):
            m._header.insert(insert_at + i, header)

        # Insert column data into each row
        for row_idx, row_data in enumerate(self._removed_data):
            if row_idx < len(m._rows):
                row = m._rows[row_idx]
                for i, cell_data in enumerate(row_data):
                    row.insert(insert_at + i, cell_data)

        m.endInsertColumns()


class DuplicateColumnCommand(QUndoCommand):
    def __init__(self, doc, col: int, label: str = "Duplicate Column"):
        super().__init__(label)
        self.doc = doc
        self.col = col
        self._copied_header = None  # str
        self._copied_data = None    # list[str]
        self._insert_at = col + 1

    def redo(self):
        m = self.doc.model
        if self.col < 0 or self.col >= len(m._header):
            self._copied_header = None
            self._copied_data = None
            return

        self._copied_header = m._header[self.col]

        # Extract column data from all rows
        self._copied_data = []
        for row in m._rows:
            if self.col < len(row):
                self._copied_data.append(row[self.col])
            else:
                self._copied_data.append("")

        insert_at = max(0, min(self._insert_at, len(m._header)))
        m.beginInsertColumns(QModelIndex(), insert_at, insert_at)

        # Insert header
        m._header.insert(insert_at, self._copied_header)

        # Insert column data into each row
        for row_idx, cell_data in enumerate(self._copied_data):
            if row_idx < len(m._rows):
                m._rows[row_idx].insert(insert_at, cell_data)

        m.endInsertColumns()

    def undo(self):
        m = self.doc.model
        if self._copied_header is None or self._copied_data is None:
            return
        # Remove the column we inserted at redo-time. Clamp in case other ops happened.
        idx = max(0, min(self._insert_at, len(m._header) - 1))
        m.removeColumns(idx, 1)


class RenameColumnCommand(QUndoCommand):
    def __init__(self, doc, col: int, old_name: str, new_name: str, label: str = "Rename Column"):
        super().__init__(label)
        self.doc = doc
        self.col = col
        self.old_name = old_name
        self.new_name = new_name

    def redo(self):
        self.doc.model.setHeaderData(self.col, Qt.Horizontal, self.new_name, Qt.EditRole)
        # Also update the document's current_data immediately
        header, _ = self.doc.model.extract_data()
        self.doc.current_data.header_fields = header[1:]

    def undo(self):
        self.doc.model.setHeaderData(self.col, Qt.Horizontal, self.old_name, Qt.EditRole)
        # Also update the document's current_data
        header, _ = self.doc.model.extract_data()
        self.doc.current_data.header_fields = header[1:]


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

        # Connect to undo stack clean state changes
        self.undo_stack.cleanChanged.connect(self._on_clean_changed)

        # Search state
        self._search_regex = None
        self._search_last_row = -1
        self._search_last_col = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)

        # Connect context menu signals (row ops must go through undo commands)
        self.table.requestInsertAbove.connect(self.insert_row_above)
        self.table.requestInsertBelow.connect(self.insert_row_below)
        self.table.requestDuplicate.connect(self.duplicate_row)
        self.table.requestDelete.connect(self.delete_row)

        # Connect column context menu signals (column ops must go through undo commands)
        self.table.requestInsertColumnLeft.connect(self.insert_column_left)
        self.table.requestInsertColumnRight.connect(self.insert_column_right)
        self.table.requestDuplicateColumn.connect(self.duplicate_column)
        self.table.requestDeleteColumn.connect(self.delete_column)

    # -----------------------------
    # Row operations (UNDO SAFE)
    # -----------------------------
    def insert_row_above(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.undo_stack.push(InsertRowCommand(self, row, 1, "Insert Row Above"))
        self._mark_dirty()

    def insert_row_below(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.undo_stack.push(InsertRowCommand(self, row + 1, 1, "Insert Row Below"))
        self._mark_dirty()

    def duplicate_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.undo_stack.push(DuplicateRowCommand(self, row))
        self._mark_dirty()

    def delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.undo_stack.push(RemoveRowCommand(self, row, 1))
        self._mark_dirty()

    # -----------------------------
    # Column operations (UNDO SAFE)
    # -----------------------------
    def insert_column_left(self):
        col = self.table.currentColumn()
        if col < 0:
            return
        # Don't insert before the index column (position 0)
        insert_pos = max(1, col)
        self.undo_stack.push(InsertColumnCommand(self, insert_pos, 1, "Insert Column Left"))
        self._mark_dirty()

    def insert_column_right(self):
        col = self.table.currentColumn()
        if col < 0:
            return
        # Insert after the current column, but ensure we're not inserting before index column
        insert_pos = max(1, col + 1)
        self.undo_stack.push(InsertColumnCommand(self, insert_pos, 1, "Insert Column Right"))
        self._mark_dirty()

    def duplicate_column(self):
        col = self.table.currentColumn()
        if col < 0 or col == 0:
            return  # Don't duplicate the index column
        self.undo_stack.push(DuplicateColumnCommand(self, col))
        self._mark_dirty()

    def delete_column(self):
        col = self.table.currentColumn()
        if col < 0 or col == 0:
            return  # Don't delete the index column
        self.undo_stack.push(RemoveColumnCommand(self, col, 1))
        self._mark_dirty()

    # -----------------------------
    # Search / navigation
    # -----------------------------
    def set_search_pattern(self, regex):
        self._search_regex = regex
        self._search_last_row = -1
        self._search_last_col = -1

    def find_next(self):
        if not self._search_regex or not self.model:
            return

        rows = self.model._rows

        # If no prior match, start at top-left (searchable region)
        if self._search_last_row < 0 or self._search_last_col < 0:
            start_row = 0
            start_col = SEARCHABLE_COL_START
        else:
            start_row = self._search_last_row
            start_col = self._search_last_col + 1

        # Forward scan
        for r in range(start_row, len(rows)):
            row = rows[r]
            col_start = start_col if r == start_row else SEARCHABLE_COL_START
            col_start = max(SEARCHABLE_COL_START, col_start)

            for c in range(col_start, len(row)):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    self._search_last_row = r
                    self._search_last_col = c
                    idx = self.model.index(r, c)
                    self.table.setCurrentIndex(idx)
                    self.table.scrollTo(idx)
                    return

        # Wrap around to beginning
        for r in range(0, min(start_row + 1, len(rows))):
            row = rows[r]
            # if r == start_row, only search up to (but not including) start_col
            col_end = start_col if r == start_row else len(row)
            col_end = max(SEARCHABLE_COL_START, col_end)

            for c in range(SEARCHABLE_COL_START, min(col_end, len(row))):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    self._search_last_row = r
                    self._search_last_col = c
                    idx = self.model.index(r, c)
                    self.table.setCurrentIndex(idx)
                    self.table.scrollTo(idx)
                    return

    def find_previous(self):
        if not self._search_regex or not self.model:
            return

        rows = self.model._rows
        if not rows:
            return

        # If no prior match, start at bottom-right (searchable region)
        if self._search_last_row < 0 or self._search_last_col < 0:
            start_row = len(rows) - 1
            start_col = len(rows[start_row]) - 1
        else:
            start_row = self._search_last_row
            start_col = self._search_last_col - 1

        # Backward scan
        for r in range(start_row, -1, -1):
            row = rows[r]
            col_start = start_col if r == start_row else len(row) - 1
            col_start = min(col_start, len(row) - 1)

            for c in range(col_start, SEARCHABLE_COL_START - 1, -1):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    self._search_last_row = r
                    self._search_last_col = c
                    idx = self.model.index(r, c)
                    self.table.setCurrentIndex(idx)
                    self.table.scrollTo(idx)
                    return

        # Wrap around to end
        for r in range(len(rows) - 1, start_row - 1, -1):
            row = rows[r]
            col_start = (len(row) - 1) if r != start_row else start_col
            col_start = min(col_start, len(row) - 1)

            for c in range(col_start, SEARCHABLE_COL_START - 1, -1):
                cell_value = row[c]
                if isinstance(cell_value, str) and self._search_regex.search(cell_value):
                    self._search_last_row = r
                    self._search_last_col = c
                    idx = self.model.index(r, c)
                    self.table.setCurrentIndex(idx)
                    self.table.scrollTo(idx)
                    return

    # -----------------------------
    # Replace
    # -----------------------------
    def replace_current(self, replacement: str):
        r, c = self._search_last_row, self._search_last_col
        if r < 0 or c < 0:
            return
        if c < SEARCHABLE_COL_START:
            return
        if not self._search_regex:
            return

        cell = self.model._rows[r][c]
        if not isinstance(cell, str):
            return

        match = self._search_regex.search(cell)
        if not match:
            return

        new = cell[:match.start()] + replacement + cell[match.end():]
        self.model.set_cell(r, c, new)
        self._mark_dirty()

    def replace_all(self, regex, replacement: str):
        if not regex or not self.model:
            return

        rows = self.model._rows
        modified = False

        # Replace in searchable region only
        for r, row in enumerate(rows):
            for c in range(SEARCHABLE_COL_START, len(row)):
                cell_value = row[c]
                if isinstance(cell_value, str) and regex.search(cell_value):
                    new_value = regex.sub(replacement, cell_value)
                    if new_value != cell_value:
                        # emit_edit_signal=False to avoid generating per-cell undo commands
                        self.model.set_cell(r, c, new_value, emit_edit_signal=False)
                        modified = True

        if modified:
            self._mark_dirty()

    # -----------------------------
    # Dirty flag / title
    # -----------------------------
    def _mark_dirty(self):
        self.is_dirty = True
        mw = self.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self)

    def _on_clean_changed(self, clean):
        """Handle undo stack clean state changes."""
        self.is_dirty = not clean
        mw = self.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self)
