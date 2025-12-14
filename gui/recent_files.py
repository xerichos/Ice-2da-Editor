# gui/recent_files.py
"""
Recent files management for the 2DA editor.
Handles storing, retrieving, and displaying recently opened files.
"""
import os
from PyQt5.QtWidgets import QAction

MAX_RECENT_FILES = 10


class RecentFilesManager:
    """Manages recent files list and menu."""
    
    def __init__(self, main_window):
        """
        Initialize recent files manager.
        
        Args:
            main_window: Reference to MainWindow instance
        """
        self.main_window = main_window
        self.recent_menu = None
    
    def add_recent_file(self, path):
        """Add a file to the recent files list."""
        files = self.main_window.settings.value("recent/files", [])
        if path in files:
            files.remove(path)
        files.insert(0, path)
        files = files[:MAX_RECENT_FILES]
        self.main_window.settings.setValue("recent/files", files)
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """Update the recent files menu with current list."""
        if not self.recent_menu:
            return
            
        self.recent_menu.clear()

        files = self.main_window.settings.value("recent/files", [])
        # Normalize + prune missing
        cleaned = []
        for p in files:
            if isinstance(p, str) and os.path.exists(p):
                cleaned.append(p)

        # Persist cleaned list if changed
        if cleaned != files:
            self.main_window.settings.setValue("recent/files", cleaned)

        for path in cleaned:
            act = QAction(path, self.main_window)
            act.triggered.connect(lambda _, p=path: self.open_recent_file(p))
            self.recent_menu.addAction(act)

        if not cleaned:
            empty = QAction("(No recent files)", self.main_window)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)
    
    def open_recent_file(self, path):
        """Open a file from the recent files list."""
        if not os.path.exists(path):
            return
        doc = self.main_window.file_manager.create_document_from_path(
            path, add_to_recent=False, set_current=False
        )
        if doc:
            self.main_window.tabs.setCurrentWidget(doc)
    
    def get_recent_files(self):
        """Get list of recent file paths."""
        files = self.main_window.settings.value("recent/files", [])
        cleaned = []
        for p in files:
            if isinstance(p, str) and os.path.exists(p):
                cleaned.append(p)
        return cleaned

