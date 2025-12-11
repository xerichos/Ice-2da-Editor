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
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)


    def set_data(self, header, rows):
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

        # NEW: sync left frozen column with index column
        self.sync_index_header()

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


    def _on_cell_changed(self, item):
        if self._suspend_dirty:
            return

        win = self.window()
        if not hasattr(win, "undo_stack"):
            return

        row = item.row()
        col = item.column()
        new_text = item.text()

        # Keep vertical header in sync if index column changed
        if col == 0:
            header_item = self.verticalHeaderItem(row)
            if header_item is None:
                from PyQt5.QtWidgets import QTableWidgetItem
                header_item = QTableWidgetItem(new_text)
                self.setVerticalHeaderItem(row, header_item)
            else:
                header_item.setText(new_text)

        old_text = getattr(item, "_old_value", "")

        from gui.undo_commands import CellEditCommand
        cmd = CellEditCommand(self, row, col, old_text, new_text)
        win.undo_stack.push(cmd)

        if hasattr(win, "is_dirty"):
            win.is_dirty = True
            win.update_window_title()



    def _create_empty_item(self):
        item = QTableWidgetItem("")
        item.setBackground(self.DEFAULT_BG)
        return item

    def _create_item(self, text):
        item = QTableWidgetItem(text)
        item.setBackground(self.DEFAULT_BG)
        return item
        
    def open_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid():
            return

        row = index.row()
        self.selectRow(row)

        from PyQt5.QtWidgets import QMenu, QAction

        menu = QMenu(self)

        act_insert_above = QAction("Insert Row Above", self)
        act_insert_below = QAction("Insert Row Below", self)
        act_duplicate = QAction("Duplicate Row", self)
        act_delete = QAction("Delete Row", self)

        # Forward calls to MainWindow
        main = self.window()
        act_insert_above.triggered.connect(main.insert_row_above)
        act_insert_below.triggered.connect(main.insert_row_below)
        act_duplicate.triggered.connect(main.duplicate_row)
        act_delete.triggered.connect(main.delete_selected_row)

        menu.addAction(act_insert_above)
        menu.addAction(act_insert_below)
        menu.addAction(act_duplicate)
        menu.addSeparator()
        menu.addAction(act_delete)

        menu.exec_(self.viewport().mapToGlobal(pos))


    def sync_index_header(self):
        """Make the frozen left header show the values of column 0."""
        from PyQt5.QtWidgets import QTableWidgetItem

        for r in range(self.rowCount()):
            item = self.item(r, 0)
            text = item.text() if item else ""
            header_item = self.verticalHeaderItem(r)
            if header_item is None:
                header_item = QTableWidgetItem(text)
                self.setVerticalHeaderItem(r, header_item)
            else:
                header_item.setText(text)
