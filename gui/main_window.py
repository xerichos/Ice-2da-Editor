import os
import re

from PyQt5.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QAction,
    QTabWidget,
    QMessageBox,
    QMenu,
    QApplication

)
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QIcon
from gui.document import TwoDADocument
from gui.cell_edit_command import CellEditCommand
from data.twoda import load_2da, save_2da
from gui.dialogs import SearchReplaceDialog
from gui.error_handler import show_error
from gui.styles import (
    LIGHT_STYLE, DARK_STYLE, MIDNIGHT_STYLE,
    TABLE_LIGHT_STYLE, TABLE_DARK_STYLE, TABLE_MIDNIGHT_STYLE
)

MAX_RECENT_FILES = 10


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Icy 2DA Editor")
        self.resize(1200, 700)
        self._checking_external_change = False

        # ------------------------------------------------------------
        # Tabs
        # ------------------------------------------------------------
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.open_tab_context_menu)
        self.tabs.tabBar().installEventFilter(self)
        self.tabs.setMovable(True)
        




        # ------------------------------------------------------------
        # Style management
        # ------------------------------------------------------------
        self.settings = QSettings("Ice-2DA-Editor", "MainWindow")
        self.current_style = self.settings.value("theme", "dark")

        self.style_map = {
            "light": (LIGHT_STYLE, TABLE_LIGHT_STYLE),
            "dark": (DARK_STYLE, TABLE_DARK_STYLE),
            "midnight": (MIDNIGHT_STYLE, TABLE_MIDNIGHT_STYLE),
        }

        # ------------------------------------------------------------
        # Actions / menus
        # ------------------------------------------------------------
        self.create_actions()
        self.create_menu()
        self.create_toolbar()
        self.set_style(self.current_style)
        self.restore_session()


    # ==============================================================
    # Helpers
    # ==============================================================
    def current_doc(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, TwoDADocument) else None

    # ==============================================================
    # Actions / Menus
    # ==============================================================
    def create_actions(self):
        self.act_open = QAction("Open", self)
        self.act_open.setShortcut("Ctrl+O")
        self.act_open.triggered.connect(self.open_file)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.save_file)

        self.act_save_as = QAction("Save As", self)
        self.act_save_as.setShortcut("Ctrl+Alt+S")
        self.act_save_as.triggered.connect(self.save_file_as)

        self.act_exit = QAction("Exit", self)
        self.act_exit.triggered.connect(self.close)

        self.act_undo = QAction("Undo", self)
        self.act_undo.setShortcut("Ctrl+Z")
        self.act_undo.triggered.connect(lambda: self._with_doc(lambda d: d.undo_stack.undo()))

        self.act_redo = QAction("Redo", self)
        self.act_redo.setShortcut("Ctrl+Y")
        self.act_redo.triggered.connect(lambda: self._with_doc(lambda d: d.undo_stack.redo()))

        self.act_search = QAction("Search / Replace", self)
        self.act_search.setShortcut("Ctrl+F")
        self.act_search.triggered.connect(self.search_replace)

        self.act_find_next = QAction("Find Next", self)
        self.act_find_next.setShortcut("F3")
        self.act_find_next.triggered.connect(lambda: self._with_doc(lambda d: d.find_next()))
        self.addAction(self.act_find_next)

        self.act_find_prev = QAction("Find Previous", self)
        self.act_find_prev.setShortcut("Shift+F3")
        self.act_find_prev.triggered.connect(lambda: self._with_doc(lambda d: d.find_previous()))
        self.addAction(self.act_find_prev)

        self.act_save_all = QAction("Save All", self)
        self.act_save_all.setShortcut("Ctrl+Shift+S")
        self.act_save_all.triggered.connect(self.save_all)

        self.act_next_tab = QAction(self)
        self.act_next_tab.setShortcut("Ctrl+Tab")
        self.act_next_tab.triggered.connect(self.next_tab)
        self.addAction(self.act_next_tab)

        self.act_prev_tab = QAction(self)
        self.act_prev_tab.setShortcut("Ctrl+Shift+Tab")
        self.act_prev_tab.triggered.connect(self.previous_tab)
        self.addAction(self.act_prev_tab)


        # Theme actions
        self.act_style_light = QAction("Light Mode", self, checkable=True)
        self.act_style_dark = QAction("Dark Mode", self, checkable=True)
        self.act_style_midnight = QAction("Midnight Mode", self, checkable=True)

        self.act_style_light.triggered.connect(lambda: self.set_style("light"))
        self.act_style_dark.triggered.connect(lambda: self.set_style("dark"))
        self.act_style_midnight.triggered.connect(lambda: self.set_style("midnight"))

    def create_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("File")
        file_menu.addAction(self.act_open)
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_menu()

        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)
        file_menu.addAction(self.act_save_all)


        edit_menu = mb.addMenu("Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.act_search)
        edit_menu.addAction(self.act_find_next)
        edit_menu.addAction(self.act_find_prev)

        view_menu = mb.addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        theme_menu.addAction(self.act_style_light)
        theme_menu.addAction(self.act_style_dark)
        theme_menu.addAction(self.act_style_midnight)

        self.act_close_tab = QAction("Close Tab", self)
        self.act_close_tab.setShortcut("Ctrl+W")
        self.act_close_tab.triggered.connect(
            lambda: self._with_doc(lambda d: self.close_tab(self.tabs.currentIndex()))
        )
        self.addAction(self.act_close_tab)

        self.act_close_others = QAction("Close Other Tabs", self)
        self.act_close_others.setShortcut("Ctrl+Shift+W")
        self.act_close_others.triggered.connect(
            lambda: self.close_other_tabs(self.tabs.currentIndex())
        )
        self.addAction(self.act_close_others)

        self.act_close_all = QAction("Close All Tabs", self)
        self.act_close_all.setShortcut("Ctrl+Alt+W")
        self.act_close_all.triggered.connect(self.close_all_tabs)
        self.addAction(self.act_close_all)


    # ==============================================================
    # Style
    # ==============================================================
    def set_style(self, style_name):
        if style_name not in self.style_map:
            return

        self.current_style = style_name
        self.settings.setValue("theme", style_name)

        main_style, table_style = self.style_map[style_name]
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(main_style + table_style)

        self.act_style_light.setChecked(style_name == "light")
        self.act_style_dark.setChecked(style_name == "dark")
        self.act_style_midnight.setChecked(style_name == "midnight")

    # ==============================================================
    # File handling
    # ==============================================================
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open 2DA", "", "2DA Files (*.2da)")
        if not path:
            return

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

            index = self.tabs.addTab(doc, os.path.basename(path))
            self.tabs.setCurrentIndex(index)

            self.update_tab_title(doc)
            self.add_recent_file(path)
            doc._last_mtime = os.path.getmtime(path)



        except Exception as e:
            show_error("Failed to load 2DA file.", e)

    def save_file(self):
        doc = self.current_doc()
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
            self.update_tab_title(doc)
            doc._last_mtime = os.path.getmtime(doc.current_path)


        except Exception as e:
            show_error("Failed to save 2DA file.", e)

    def save_file_as(self):
        doc = self.current_doc()
        if not doc:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save 2DA", "", "2DA Files (*.2da)")
        if not path:
            return

        doc.current_path = path
        self.save_file()

    # ==============================================================
    # Tabs
    # ==============================================================
    def update_tab_title(self, doc):
        idx = self.tabs.indexOf(doc)
        if idx < 0:
            return

        name = os.path.basename(doc.current_path) if doc.current_path else "Untitled"
        self.tabs.setTabText(idx, name)

        if doc.is_dirty:
            self.tabs.setTabIcon(idx, self.style().standardIcon(self.style().SP_DialogApplyButton))
        else:
            self.tabs.setTabIcon(idx, QIcon())




    def close_tab(self, index):
        doc = self.tabs.widget(index)

        if doc.is_dirty:
            res = QMessageBox.question(
                self,
                "Unsaved Changes",
                "This file has unsaved changes. Close anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res != QMessageBox.Yes:
                return

        self.tabs.removeTab(index)

    def on_tab_changed(self, index):
        pass

    # ==============================================================
    # Search / Replace
    # ==============================================================
    def search_replace(self):
        doc = self.current_doc()
        if not doc:
            return

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

        doc.set_search(regex, rep)

    # ==============================================================
    # Utilities
    # ==============================================================
    def _with_doc(self, fn):
        doc = self.current_doc()
        if doc:
            fn(doc)

    def open_tab_context_menu(self, pos):
        tab_bar = self.tabs.tabBar()
        index = tab_bar.tabAt(pos)
        if index < 0:
            return

        doc = self.tabs.widget(index)
        if not isinstance(doc, TwoDADocument):
            return

        menu = QMenu(self)

        act_close = menu.addAction("Close")

        act_close_others = menu.addAction("Close Others")
        act_close_all = menu.addAction("Close All")
        menu.addSeparator()

        act_save = menu.addAction("Save")
        act_save_as = menu.addAction("Save As?")
        menu.addSeparator()

        act_reveal = menu.addAction("Reveal in File Explorer")
        act_copy_path = menu.addAction("Copy Full Path")
        menu.addSeparator()

        action = menu.exec_(tab_bar.mapToGlobal(pos))
        if not action:
            return

        self.tabs.setCurrentIndex(index)

        if action == act_close:
            self.close_tab(index)

        elif action == act_close_others:
            self.close_other_tabs(index)

        elif action == act_close_all:
            self.close_all_tabs()

        elif action == act_save:
            self.save_file()

        elif action == act_save_as:
            self.save_file_as()

        elif action == act_reveal:
            if doc.current_path:
                os.startfile(os.path.dirname(doc.current_path))

        elif action == act_copy_path:
            if doc.current_path:
                QApplication.clipboard().setText(doc.current_path)


        menu = QMenu(self)

        act_close = menu.addAction("Close")
        act_close_others = menu.addAction("Close Others")
        act_close_all = menu.addAction("Close All")
        menu.addSeparator()
        act_save = menu.addAction("Save")
        act_save_as = menu.addAction("Save As?")

        action = menu.exec_(tab_bar.mapToGlobal(pos))
        if not action:
            return

        if action == act_close:
            self.close_tab(index)

        elif action == act_close_others:
            self.close_other_tabs(index)

        elif action == act_close_all:
            self.close_all_tabs()

        elif action == act_save:
            self.tabs.setCurrentIndex(index)
            self.save_file()

        elif action == act_save_as:
            self.tabs.setCurrentIndex(index)
            self.save_file_as()

    def close_other_tabs(self, keep_index):
        for i in reversed(range(self.tabs.count())):
            if i != keep_index:
                self.close_tab(i)

    def close_all_tabs(self):
        for i in reversed(range(self.tabs.count())):
            self.close_tab(i)

    def eventFilter(self, obj, event):
        if obj is self.tabs.tabBar() and event.type() == event.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                index = obj.tabAt(event.pos())
                if index >= 0:
                    self.close_tab(index)
                    return True
        return super().eventFilter(obj, event)

    def save_all(self):
        for i in range(self.tabs.count()):
            doc = self.tabs.widget(i)
            if isinstance(doc, TwoDADocument) and doc.is_dirty:
                self.tabs.setCurrentIndex(i)
                self.save_file()

    def closeEvent(self, event):
        dirty_docs = [
            self.tabs.widget(i)
            for i in range(self.tabs.count())
            if getattr(self.tabs.widget(i), "is_dirty", False)
        ]

        if dirty_docs:
            res = QMessageBox.question(
                self,
                "Unsaved Changes",
                "There are unsaved files. Exit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res != QMessageBox.Yes:
                event.ignore()
                return
            
        paths = []
        for i in range(self.tabs.count()):
            doc = self.tabs.widget(i)
            if doc.current_path:
                paths.append(doc.current_path)
        self.settings.setValue("session/files", paths)

        super().closeEvent(event)


    def restore_session(self):
        paths = self.settings.value("session/files", [])
        if not paths:
            return

        for path in paths:
            if isinstance(path, str) and os.path.exists(path):
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

                    self.tabs.addTab(doc, os.path.basename(path))
                    self.update_tab_title(doc)

                except Exception:
                    pass

    def next_tab(self):
        count = self.tabs.count()
        if count < 2:
            return
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % count)

    def previous_tab(self):
        count = self.tabs.count()
        if count < 2:
            return
        self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1) % count)


    def add_recent_file(self, path):
        files = self.settings.value("recent/files", [])
        if path in files:
            files.remove(path)
        files.insert(0, path)
        files = files[:MAX_RECENT_FILES]
        self.settings.setValue("recent/files", files)
        self.update_recent_menu()

    def update_recent_menu(self):
        self.recent_menu.clear()

        files = self.settings.value("recent/files", [])
        # Normalize + prune missing
        cleaned = []
        for p in files:
            if isinstance(p, str) and os.path.exists(p):
                cleaned.append(p)

        # Persist cleaned list if changed
        if cleaned != files:
            self.settings.setValue("recent/files", cleaned)

        for path in cleaned:
            act = QAction(path, self)
            act.triggered.connect(lambda _, p=path: self.open_recent_file(p))
            self.recent_menu.addAction(act)

        if not cleaned:
            empty = QAction("(No recent files)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)


    def open_recent_file(self, path):
        if not os.path.exists(path):
            return
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

            self.tabs.addTab(doc, os.path.basename(path))
            self.update_tab_title(doc)
            self.tabs.setCurrentWidget(doc)

        except Exception as e:
            show_error("Failed to open recent file.", e)


    def check_external_modification(self, doc):
        # Reentrancy guard: QMessageBox triggers activation changes
        if getattr(self, "_checking_external_change", False):
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
        self._checking_external_change = True
        try:
            res = QMessageBox.question(
                self,
                "File Modified",
                "This file was modified outside the editor.\n\nReload from disk?",
                QMessageBox.Yes | QMessageBox.No
            )
        finally:
            self._checking_external_change = False

        if res == QMessageBox.Yes:
            try:
                data = load_2da(doc.current_path)
                doc.current_data = data

                header = [""] + data.header_fields
                rows = data.row_fields
                doc.model.set_data(header, rows)

                doc.is_dirty = False
                self.update_tab_title(doc)

            except Exception as e:
                show_error("Failed to reload file.", e)

        # IMPORTANT: acknowledge the external change in all cases
        doc._last_mtime = current_mtime
        return True


    
    def changeEvent(self, event):
        if event.type() == event.ActivationChange and self.isActiveWindow():
            doc = self.current_doc()
            if doc:
                self.check_external_modification(doc)
        super().changeEvent(event)


    def create_toolbar(self):
        tb = self.addToolBar("Main")
        tb.setMovable(False)

        # File actions
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addAction(self.act_save_all)

        tb.addSeparator()

        # Edit actions
        tb.addAction(self.act_undo)
        tb.addAction(self.act_redo)

        tb.addSeparator()

        tb.addAction(self.act_search)
