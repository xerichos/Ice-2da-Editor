# gui/main_window.py

import sys
import os
import re  
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG_PATH = os.path.join(ROOT, "debug")
if DEBUG_PATH not in sys.path:
    sys.path.append(DEBUG_PATH)

from PyQt5.QtWidgets import QMainWindow, QFileDialog, QAction, QMessageBox
from .table_view import TwoDATable
from .dialogs import SearchReplaceDialog
from data.twoda import TwoDAData, load_2da, save_2da
from error_handler import show_error


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("NWN 2DA Editor")
        self.resize(1200, 700)

        self.table = TwoDATable()
        self.setCentralWidget(self.table)

        self.is_dirty = False
        self.current_path = None
        self.current_data = None  # already exists if you followed previous steps
        self.update_window_title()
        self.create_actions()
        self.create_menu()

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

        self.act_search = QAction("Search/Replace", self)
        self.act_search.setShortcut("Ctrl+F")
        self.act_search.triggered.connect(self.search_replace)

    def create_menu(self):
        m = self.menuBar().addMenu("File")
        m.addAction(self.act_open)
        m.addAction(self.act_save)
        m.addAction(self.act_save_as)

        e = self.menuBar().addMenu("Edit")
        e.addAction(self.act_search)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open 2DA", "", "2DA Files (*.2da)")
        if not path:
            return

        try:
            data = load_2da(path)
            self.current_data = data
            self.current_path = path

            # GUI header: add synthetic blank header for the index column
            table_header = [""] + data.header_fields
            table_rows = data.row_fields   # rows already include the index

            self.table.set_data(table_header, table_rows)
            self.is_dirty = False
            self.update_window_title()


        except Exception as e:
            show_error("Failed to load 2DA file.", e)


    def save_file(self):
        if not self.current_path:
            return self.save_file_as()

        try:
            header, rows = self.table.extract_data()

            # Update underlying model
            self.current_data.header_fields = header[1:]   # remove synthetic index header
            self.current_data.row_fields = rows

            save_2da(self.current_path, self.current_data)

            # Mark clean
            self.is_dirty = False
            self.update_window_title()

        except Exception as e:
            show_error("Failed to save 2DA file.", e)


    def update_window_title(self):
        name = self.current_path if self.current_path else "Untitled"
        star = "*" if self.is_dirty else ""
        self.setWindowTitle(f"{name}{star} - 2DA Editor")

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save 2DA", "", "2DA Files (*.2da)")
        if not path:
            return
        self.current_path = path
        self.save_file()

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

        # Build regex
        flags = 0 if match_case else re.IGNORECASE
        escaped = re.escape(pat)
        if whole:
            pattern = r"\b" + escaped + r"\b"
        else:
            pattern = escaped

        regex = re.compile(pattern, flags)

        # Apply to all cells
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if not item:
                    continue

                text = item.text()
                new_text, count = regex.subn(rep, text)

                if count > 0:
                    item.setText(new_text)

