import sys
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG_PATH = os.path.join(ROOT, "debug")
if DEBUG_PATH not in sys.path:
    sys.path.append(DEBUG_PATH)

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QUndoStack
from PyQt5.QtWidgets import QUndoCommand
from PyQt5.QtCore import QSettings
from .table_view import TwoDATable
from .table_model import TwoDATableModel
from .dialogs import SearchReplaceDialog
from data.twoda import load_2da, save_2da
from gui.error_handler import show_error
from gui.styles import LIGHT_STYLE, DARK_STYLE, MIDNIGHT_STYLE, TABLE_LIGHT_STYLE, TABLE_DARK_STYLE, TABLE_MIDNIGHT_STYLE


class CellEditCommand(QUndoCommand):
    def __init__(self, model, row, col, old_text, new_text):
        super().__init__()
        self.model = model
        self.row = row
        self.col = col
        self.old_text = old_text
        self.new_text = new_text

    def undo(self):
        self.model.set_cell(self.row, self.col, self.old_text, emit_edit_signal=False)

    def redo(self):
        self.model.set_cell(self.row, self.col, self.new_text, emit_edit_signal=False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Icy 2da Editor")
        self.resize(1200, 700)

        self.table = TwoDATable()
        self.model = TwoDATableModel(self)

        self.table.setModel(self.model)
        self.setCentralWidget(self.table)

        self.undo_stack = QUndoStack(self)
        self.is_dirty = False
        self.current_path = None
        self.current_data = None

        self.last_search_regex = None
        self.last_find_position = (-1, -1)

        # Style management
        self.settings = QSettings("Ice-2DA-Editor", "MainWindow")
        self.current_style = self.settings.value("theme", "dark")  # load saved theme or default to dark
        self.style_map = {
            "light": (LIGHT_STYLE, TABLE_LIGHT_STYLE),
            "dark": (DARK_STYLE, TABLE_DARK_STYLE),
            "midnight": (MIDNIGHT_STYLE, TABLE_MIDNIGHT_STYLE)
        }

        self.model.cellEdited.connect(self._on_model_cell_edited)

        self.table.requestInsertAbove.connect(self.insert_row_above)
        self.table.requestInsertBelow.connect(self.insert_row_below)
        self.table.requestDuplicate.connect(self.duplicate_row)
        self.table.requestDelete.connect(self.delete_selected_row)

        self.update_window_title()
        self.create_actions()
        self.create_menu()

        # Apply saved theme (or default dark theme)
        self.set_style(self.current_style)

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

        # Style actions
        self.act_style_light = QAction("Light Mode", self)
        self.act_style_light.setCheckable(True)
        self.act_style_light.triggered.connect(lambda: self.set_style("light"))

        self.act_style_dark = QAction("Dark Mode", self)
        self.act_style_dark.setCheckable(True)
        self.act_style_dark.triggered.connect(lambda: self.set_style("dark"))

        self.act_style_midnight = QAction("Midnight Mode", self)
        self.act_style_midnight.setCheckable(True)
        self.act_style_midnight.triggered.connect(lambda: self.set_style("midnight"))

        # Set dark as checked by default
        self.act_style_dark.setChecked(True)

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

        view_menu = menubar.addMenu("View")
        style_menu = view_menu.addMenu("Theme")
        style_menu.addAction(self.act_style_light)
        style_menu.addAction(self.act_style_dark)
        style_menu.addAction(self.act_style_midnight)

    def set_style(self, style_name):
        """Switch the application theme"""
        if style_name not in self.style_map:
            return

        # Update current style
        self.current_style = style_name

        # Save theme preference
        self.settings.setValue("theme", style_name)

        # Get the style sheets
        main_style, table_style = self.style_map[style_name]

        # Apply the styles to the application
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        app.setStyleSheet(main_style + table_style)

        # Update action check states
        self.act_style_light.setChecked(style_name == "light")
        self.act_style_dark.setChecked(style_name == "dark")
        self.act_style_midnight.setChecked(style_name == "midnight")

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

            header = [""] + data.header_fields
            rows = data.row_fields

            self.model.set_data(header, rows)

            self.is_dirty = False
            self.update_window_title()

            self.last_search_regex = None
            self.last_find_position = (-1, -1)
            self.undo_stack.clear()

        except Exception as e:
            show_error("Failed to load 2DA file.", e)

    def save_file(self):
        if not self.current_path:
            return self.save_file_as()

        try:
            header, rows = self.model.extract_data()
            self.current_data.header_fields = header[1:]
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

    # ------------------------------------------------------------------ #
    # Dirty flag / title
    # ------------------------------------------------------------------ #
    def update_window_title(self):
        name = self.current_path if self.current_path else "Untitled"
        star = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{name}{star} - Icy 2da Editor")

    # ------------------------------------------------------------------ #
    # Undo hookup
    # ------------------------------------------------------------------ #
    def _on_model_cell_edited(self, row, col, old_text, new_text):
        self.undo_stack.push(CellEditCommand(self.model, row, col, old_text, new_text))
        self.is_dirty = True
        self.update_window_title()

    # ------------------------------------------------------------------ #
    # Row operations
    # ------------------------------------------------------------------ #
    def delete_selected_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.model.removeRows(row, 1)
        self.is_dirty = True
        self.update_window_title()

    def insert_row_above(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.model.insertRows(row, 1)
        self.is_dirty = True
        self.update_window_title()

    def insert_row_below(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.model.insertRows(row + 1, 1)
        self.is_dirty = True
        self.update_window_title()

    def duplicate_row(self):
        row = self.table.currentRow()
        if row < 0:
            return
        self.model.duplicateRow(row)
        self.is_dirty = True
        self.update_window_title()

    # ------------------------------------------------------------------ #
    # Search / Replace / Find Next / Find Previous
    # ------------------------------------------------------------------ #
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

        if rep == "":
            self.find_next()
            return

        rows = self.model.rowCount()
        cols = self.model.columnCount()
        for r in range(rows):
            for c in range(cols):
                idx = self.model.index(r, c)
                text = self.model.data(idx) or ""
                new_text, count = regex.subn(rep, text)
                if count > 0:
                    self.model.set_cell(r, c, new_text, emit_edit_signal=True)

    def find_next(self):
        if not self.last_search_regex:
            return

        rows = self.model.rowCount()
        cols = self.model.columnCount()
        if rows == 0 or cols == 0:
            return

        total = rows * cols
        start_r, start_c = self.last_find_position

        idx = 0 if start_r == -1 else (start_r * cols + start_c + 1) % total
        start_idx = idx

        while True:
            r = idx // cols
            c = idx % cols
            mi = self.model.index(r, c)
            text = self.model.data(mi) or ""
            if self.last_search_regex.search(text):
                self.table.setCurrentIndex(mi)
                self.table.scrollTo(mi)
                self.last_find_position = (r, c)
                return

            idx = (idx + 1) % total
            if idx == start_idx:
                return

    def find_previous(self):
        if not self.last_search_regex:
            return

        rows = self.model.rowCount()
        cols = self.model.columnCount()
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
            mi = self.model.index(r, c)
            text = self.model.data(mi) or ""
            if self.last_search_regex.search(text):
                self.table.setCurrentIndex(mi)
                self.table.scrollTo(mi)
                self.last_find_position = (r, c)
                return

            idx -= 1
            if idx < 0:
                idx = total - 1
            if idx == start_idx:
                return
