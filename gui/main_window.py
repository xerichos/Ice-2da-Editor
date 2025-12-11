# gui/main_window.py

import sys
import os
import re

# Ensure debug/ is on sys.path before importing error_handler
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG_PATH = os.path.join(ROOT, "debug")
if DEBUG_PATH not in sys.path:
    sys.path.append(DEBUG_PATH)

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QUndoStack
from .table_view import TwoDATable
from .dialogs import SearchReplaceDialog
from data.twoda import load_2da, save_2da
from error_handler import show_error


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Icy 2da Editor")
        self.resize(1200, 700)

        self.table = TwoDATable()
        self.setCentralWidget(self.table)

        self.undo_stack = QUndoStack(self)
        self.is_dirty = False
        self.current_path = None
        self.current_data = None

        self.last_search_regex = None
        self.last_find_position = (-1, -1)  # (row, col)

        self.update_window_title()
        self.create_actions()
        self.create_menu()

    # ------------------------------------------------------------------ #
    # Actions / Menus
    # ------------------------------------------------------------------ #
    def create_actions(self):
        self.act_open = QAction("Open", self)
        self.act_open.setShortcut("Ctrl+O")
        self.act_open.triggered.connect(self.open_file)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.save_file)

        self.act_save_as = QAction("Save As", self)
        self.act_save_as.setShortcut("Ctrl+Shift+S")
        self.act_save_as.triggered.connect(self.save_file_as)

        self.act_search = QAction("Search / Replace", self)
        self.act_search.setShortcut("Ctrl+F")
        self.act_search.triggered.connect(self.search_replace)

        self.act_find_next = QAction("Find Next", self)
        self.act_find_next.setShortcut("F3")
        self.act_find_next.triggered.connect(self.find_next)
        self.addAction(self.act_find_next)

        self.act_find_prev = QAction("Find Previous", self)
        self.act_find_prev.setShortcut("Shift+F3")
        self.act_find_prev.triggered.connect(self.find_previous)
        self.addAction(self.act_find_prev)

        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(self.undo_stack.undo)

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(self.undo_stack.redo)

        self.act_select_all = QAction("Select All", self)
        self.act_select_all.setShortcut("Ctrl+A")
        self.act_select_all.triggered.connect(self.table.selectAll)

        self.act_delete_row = QAction("Delete Row", self)
        self.act_delete_row.setShortcut("Del")
        self.act_delete_row.triggered.connect(self.delete_selected_row)

        self.act_exit = QAction("Exit", self)
        self.act_exit.triggered.connect(self.close)

    def create_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        edit_menu = menubar.addMenu("Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_search)
        edit_menu.addAction(self.act_find_next)
        edit_menu.addAction(self.act_find_prev)
        edit_menu.addAction(self.act_select_all)
        edit_menu.addAction(self.act_delete_row)

    # ------------------------------------------------------------------ #
    # File operations
    # ------------------------------------------------------------------ #
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open 2DA", "", "2DA Files (*.2da)")
        if not path:
            return

        try:
            data = load_2da(path)
            self.current_data = data
            self.current_path = path

            header = data.header_fields
            rows = data.row_fields

            self.table.set_data(header, rows)
            self.is_dirty = False
            self.update_window_title()

        except Exception as e:
            show_error("Failed to load 2DA file.", e)

    def save_file(self):
        if not self.current_path:
            return self.save_file_as()

        try:
            header, rows = self.table.extract_data()
            self.current_data.header_fields = header      
            self.current_data.row_fields = rows           

            save_2da(self.current_path, self.current_data)

            self.is_dirty = False
            self.update_window_title()

        except Exception as e:
            show_error("Failed to save 2DA file.", e)

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save 2DA", "", "2DA Files (*.2da)")
        if not path:
            return
        self.current_path = path
        self.save_file()

    def update_window_title(self):
        name = self.current_path if self.current_path else "Untitled"
        star = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{name}{star} - Icy 2da Editor")

    def search_replace(self):
        dlg = SearchReplaceDialog(self)
        if dlg.exec_() != dlg.Accepted:
            return

        vals = dlg.values()
        pat = vals["pattern"]
        rep = vals["replacement"]
        match_case = vals["match_case"]
        whole = vals["whole_word"]

        if not pat:
            return

        flags = 0 if match_case else re.IGNORECASE
        escaped = re.escape(pat)
        pattern = r"\b" + escaped + r"\b" if whole else escaped
        regex = re.compile(pattern, flags)

        self.last_search_regex = regex
        self.last_find_position = (-1, -1)

        # Find-only mode if replacement is empty
        if rep == "":
            self.find_next()
            return

        # Replace-all mode
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if not item:
                    continue
                text = item.text()
                new_text, count = regex.subn(rep, text)
                if count > 0:
                    item.setText(new_text)

    def find_next(self):
        if not self.last_search_regex:
            return

        table = self.table
        rows = table.rowCount()
        cols = table.columnCount()
        if rows == 0 or cols == 0:
            return

        total = rows * cols
        start_r, start_c = self.last_find_position

        if start_r == -1:
            idx = 0
        else:
            idx = (start_r * cols + start_c + 1) % total

        start_idx = idx

        while True:
            r = idx // cols
            c = idx % cols

            item = table.item(r, c)
            if item and self.last_search_regex.search(item.text()):
                table.setCurrentCell(r, c)
                table.scrollToItem(item)
                self.last_find_position = (r, c)
                return

            idx = (idx + 1) % total
            if idx == start_idx:
                return

    def find_previous(self):
        if not self.last_search_regex:
            return

        table = self.table
        rows = table.rowCount()
        cols = table.columnCount()
        if rows == 0 or cols == 0:
            return

        total = rows * cols
        start_r, start_c = self.last_find_position

        if start_r == -1:
            idx = total - 1
        else:
            idx = start_r * cols + start_c - 1
            if idx < 0:
                idx = total - 1

        start_idx = idx

        while True:
            r = idx // cols
            c = idx % cols

            item = table.item(r, c)
            if item and self.last_search_regex.search(item.text()):
                table.setCurrentCell(r, c)
                table.scrollToItem(item)
                self.last_find_position = (r, c)
                return

            idx -= 1
            if idx < 0:
                idx = total - 1
            if idx == start_idx:
                return
                
    def delete_selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)
        self.table.sync_index_header()
        self.is_dirty = True
        self.update_window_title()

    def insert_row_above(self):
        table = self.table
        row = table.currentRow()
        if row < 0:
            return

        cols = table.columnCount()
        table.insertRow(row)
        for c in range(cols):
            table.setItem(row, c, table._create_empty_item())

        table.sync_index_header()
        self.is_dirty = True
        self.update_window_title()

    def insert_row_below(self):
        table = self.table
        row = table.currentRow()
        if row < 0:
            return

        cols = table.columnCount()
        new_row = row + 1
        table.insertRow(new_row)
        for c in range(cols):
            table.setItem(new_row, c, table._create_empty_item())

        table.sync_index_header()
        self.is_dirty = True
        self.update_window_title()

    def duplicate_row(self):
        table = self.table
        row = table.currentRow()
        if row < 0:
            return

        cols = table.columnCount()
        new_row = row + 1
        table.insertRow(new_row)
        for c in range(cols):
            item = table.item(row, c)
            value = item.text() if item else ""
            table.setItem(new_row, c, table._create_item(value))

        table.sync_index_header()
        self.is_dirty = True
        self.update_window_title()

