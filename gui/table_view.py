from PyQt5.QtWidgets import QTableView, QMenu, QAction
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal


class TwoDATable(QTableView):
    requestInsertAbove = pyqtSignal()
    requestInsertBelow = pyqtSignal()
    requestDuplicate = pyqtSignal()
    requestDelete = pyqtSignal()

    DEFAULT_BG = QColor("#2b2b2b")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAlternatingRowColors(False)
        self.setSortingEnabled(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def currentRow(self):
        idx = self.currentIndex()
        return idx.row() if idx.isValid() else -1

    def open_context_menu(self, pos):
        idx = self.indexAt(pos)
        if not idx.isValid():
            return

        self.setCurrentIndex(idx)

        menu = QMenu(self)

        act_insert_above = QAction("Insert Row Above", self)
        act_insert_below = QAction("Insert Row Below", self)
        act_duplicate = QAction("Duplicate Row", self)
        act_delete = QAction("Delete Row", self)

        act_insert_above.triggered.connect(self.requestInsertAbove.emit)
        act_insert_below.triggered.connect(self.requestInsertBelow.emit)
        act_duplicate.triggered.connect(self.requestDuplicate.emit)
        act_delete.triggered.connect(self.requestDelete.emit)

        menu.addAction(act_insert_above)
        menu.addAction(act_insert_below)
        menu.addAction(act_duplicate)
        menu.addSeparator()
        menu.addAction(act_delete)

        menu.exec_(self.viewport().mapToGlobal(pos))
