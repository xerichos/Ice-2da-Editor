# gui/file_manager.py
"""
File operations for the 2DA editor.
Handles opening, saving, and external modification checking.
"""
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from gui.document import TwoDADocument
from gui.cell_edit_command import CellEditCommand
from data.twoda import load_2da, save_2da
from gui.error_handler import show_error


class FileManager:
    """Manages file operations for the main window."""
    
    def __init__(self, main_window):
        """
        Initialize file manager.
        
        Args:
            main_window: Reference to MainWindow instance
        """
        self.main_window = main_window
    
    def create_document_from_path(self, path, add_to_recent=False, set_current=True):
        """Create and setup a document from a file path."""
        try:
            data = load_2da(path)
            doc = TwoDADocument()
            doc.current_path = path
            doc.current_data = data

            header = [""] + data.header_fields
            rows = data.row_fields
            doc.model.set_data(header, rows)

            doc.model.cellEdited.connect(
                lambda r, c, o, n, d=doc:
                    d.undo_stack.push(CellEditCommand(d, r, c, o, n))
            )

            index = self.main_window.tabs.addTab(doc, os.path.basename(path))
            if set_current:
                self.main_window.tabs.setCurrentIndex(index)

            self.main_window.update_tab_title(doc)
            if add_to_recent:
                self.main_window.recent_files_manager.add_recent_file(path)
            doc._last_mtime = os.path.getmtime(path)
            return doc
        except Exception as e:
            show_error("Failed to load 2DA file.", e)
            return None
    
    def open_file(self):
        """Open a file dialog and load the selected 2DA file."""
        path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open 2DA", "", "2DA Files (*.2da)"
        )
        if not path:
            return
        self.create_document_from_path(path, add_to_recent=True, set_current=True)
    
    def save_file(self):
        """Save the current document."""
        doc = self.main_window.current_doc()
        if not doc:
            return

        if self.check_external_modification(doc):
            return

        if not doc.current_path:
            return self.save_file_as()

        try:
            header, rows = doc.model.extract_data()
            doc.current_data.header_fields = header[1:]
            doc.current_data.row_fields = rows

            save_2da(doc.current_path, doc.current_data)
            doc.is_dirty = False
            self.main_window.update_tab_title(doc)
            doc._last_mtime = os.path.getmtime(doc.current_path)
        except Exception as e:
            show_error("Failed to save 2DA file.", e)
    
    def save_file_as(self):
        """Save the current document with a new filename."""
        doc = self.main_window.current_doc()
        if not doc:
            return

        path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save 2DA", "", "2DA Files (*.2da)"
        )
        if not path:
            return

        doc.current_path = path
        self.save_file()
    
    def save_all(self):
        """Save all dirty documents."""
        for i in range(self.main_window.tabs.count()):
            doc = self.main_window.tabs.widget(i)
            if isinstance(doc, TwoDADocument) and doc.is_dirty:
                self.main_window.tabs.setCurrentIndex(i)
                self.save_file()
    
    def check_external_modification(self, doc):
        """
        Check if the file was modified externally and prompt to reload.
        
        Returns:
            True if external modification was detected and handled, False otherwise
        """
        # Reentrancy guard: QMessageBox triggers activation changes
        if getattr(self.main_window, "_checking_external_change", False):
            return False

        if not doc or not doc.current_path or not os.path.exists(doc.current_path):
            return False

        try:
            current_mtime = os.path.getmtime(doc.current_path)
        except OSError:
            return False

        last_mtime = getattr(doc, "_last_mtime", None)
        if last_mtime is None or current_mtime == last_mtime:
            return False

        # Suppress re-entry while the dialog is open
        self.main_window._checking_external_change = True
        try:
            res = QMessageBox.question(
                self.main_window,
                "File Modified",
                "This file was modified outside the editor.\n\nReload from disk?",
                QMessageBox.Yes | QMessageBox.No
            )
        finally:
            self.main_window._checking_external_change = False

        if res == QMessageBox.Yes:
            try:
                data = load_2da(doc.current_path)
                doc.current_data = data
                header = [""] + data.header_fields
                rows = data.row_fields
                doc.model.set_data(header, rows)
                doc.is_dirty = False
                self.main_window.update_tab_title(doc)
            except Exception as e:
                show_error("Failed to reload file.", e)

        # IMPORTANT: acknowledge the external change in all cases
        doc._last_mtime = current_mtime
        return True

