from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal


class TwoDATableModel(QAbstractTableModel):
    cellEdited = pyqtSignal(int, int, str, str)  # row, col, old, new

    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = []
        self._rows = []
        self._suspend_edit_signal = False

    def set_data(self, header, rows):
        self.beginResetModel()
        self._header = list(header)
        self._rows = [list(r) for r in rows]
        self.endResetModel()

    def extract_data(self):
        header = list(self._header)
        rows = []

        for r in self._rows:
            row = list(r)
            while len(row) < len(header):
                row.append("****")
            rows.append(row)

        return header, rows


    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._header)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if r < 0 or c < 0:
            return None
        if r >= len(self._rows) or c >= len(self._header):
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):
            row = self._rows[r]
            return row[c] if c < len(row) else ""
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False

        r, c = index.row(), index.column()
        if r < 0 or c < 0:
            return False
        if r >= len(self._rows) or c >= len(self._header):
            return False

        new_text = "" if value is None else str(value)
        row = self._rows[r]
        while len(row) < len(self._header):
            row.append("")

        old_text = row[c]
        if new_text == old_text:
            return True

        row[c] = new_text
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])

        if not self._suspend_edit_signal:
            self.cellEdited.emit(r, c, old_text, new_text)

        return True

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._header):
                return self._header[section]
            return ""
        return str(section)

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False
        if not (0 <= section < len(self._header)):
            return False

        old_name = self._header[section]
        new_name = str(value).strip()
        if old_name == new_name:
            return True

        self._header[section] = new_name
        self.headerDataChanged.emit(orientation, section, section)
        return True

    def set_cell(self, row, col, text, *, emit_edit_signal=True):
        if not (0 <= row < len(self._rows)) or not (0 <= col < len(self._header)):
            return
        idx = self.index(row, col)
        prev = self._suspend_edit_signal
        self._suspend_edit_signal = not emit_edit_signal
        try:
            self.setData(idx, text, Qt.EditRole)
        finally:
            self._suspend_edit_signal = prev

    def insertRows(self, row, count, parent=QModelIndex()):
        if count <= 0:
            return False
        row = max(0, min(row, len(self._rows)))
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for _ in range(count):
            self._rows.insert(row, self.make_empty_row())   
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if count <= 0:
            return False
        if row < 0 or row >= len(self._rows):
            return False
        last = min(len(self._rows) - 1, row + count - 1)
        self.beginRemoveRows(QModelIndex(), row, last)
        del self._rows[row:last + 1]
        self.endRemoveRows()
        return True

    def insertColumns(self, column, count, parent=QModelIndex()):
        if count <= 0:
            return False

        column = max(0, min(column, len(self._header)))
        self.beginInsertColumns(QModelIndex(), column, column + count - 1)

        # --- insert headers ---
        for i in range(count):
            name = "NewColumn" if count == 1 else f"NewColumn{i + 1}"
            self._header.insert(column + i, name)

        # --- normalize all rows BEFORE inserting ---
        target_len = len(self._header) - count
        for row in self._rows:
            while len(row) < target_len:
                row.append("****")

        # --- insert placeholder data ---
        for row in self._rows:
            for i in range(count):
                row.insert(column + i, "****")

        self.endInsertColumns()

        if hasattr(self, "_notify_frozen_column_insert"):
            self._notify_frozen_column_insert(column, count)

        return True


    def removeColumns(self, column, count, parent=QModelIndex()):
        if count <= 0:
            return False
        if column < 0 or column >= len(self._header):
            return False

        last = min(len(self._header) - 1, column + count - 1)
        self.beginRemoveColumns(QModelIndex(), column, last)

        # Remove headers
        del self._header[column:last + 1]

        # Remove data from rows
        for row in self._rows:
            del row[column:last + 1]

        # Normalize rows
        for row in self._rows:
            while len(row) < len(self._header):
                row.append("****")

        self.endRemoveColumns()

        if hasattr(self, "_notify_frozen_column_remove"):
            self._notify_frozen_column_remove(column, count)

        return True


    def duplicateRow(self, row):
        if row < 0 or row >= len(self._rows):
            return False
        insert_at = row + 1
        self.beginInsertRows(QModelIndex(), insert_at, insert_at)
        self._rows.insert(insert_at, list(self._rows[row]))
        self.endInsertRows()
        return True

    def make_empty_row(self):
        return [""] * len(self._header)

    def insert_row_data(self, row, rows_data):
        if not rows_data:
            return False

        row = max(0, min(row, len(self._rows)))
        count = len(rows_data)

        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for i, data in enumerate(rows_data):
            r = list(data)
            while len(r) < len(self._header):
                r.append("")
            self._rows.insert(row + i, r)
        self.endInsertRows()
        return True

    def take_rows(self, row, count):
        if count <= 0 or row < 0 or row >= len(self._rows):
            return []

        last = min(len(self._rows), row + count)
        self.beginRemoveRows(QModelIndex(), row, last - 1)
        removed = self._rows[row:last]
        del self._rows[row:last]
        self.endRemoveRows()
        return [list(r) for r in removed]

