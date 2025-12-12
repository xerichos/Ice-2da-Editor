from PyQt5.QtWidgets import QTableView, QMenu, QAction, QHeaderView
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal, QRect


class TwoDATable(QTableView):
    requestInsertAbove = pyqtSignal()
    requestInsertBelow = pyqtSignal()
    requestDuplicate = pyqtSignal()
    requestDelete = pyqtSignal()
    frozenChanged = pyqtSignal(int)

    DEFAULT_BG = QColor("#2b2b2b")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAlternatingRowColors(False)
        self.setSortingEnabled(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

        # Frozen / pinned columns support
        self._frozen_columns = 1
        self._frozen_view = None
        self._init_frozen_view()
        # header click -> freeze that column (freeze up to and including clicked)
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

    def currentRow(self):
        idx = self.currentIndex()
        return idx.row() if idx.isValid() else -1

    # ----------------------- Frozen columns API -----------------------
    def _init_frozen_view(self):
        # Create the overlay table used to render frozen left columns
        self._frozen_view = QTableView(self)
        self._frozen_view.setFocusPolicy(Qt.NoFocus)
        self._frozen_view.verticalHeader().hide()
        self._frozen_view.horizontalHeader().setSectionsMovable(False)
        self._frozen_view.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._frozen_view.setSelectionBehavior(self.selectionBehavior())
        self._frozen_view.setSelectionMode(self.selectionMode())
        self._frozen_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._frozen_view.setStyleSheet(self.styleSheet())
        self._frozen_view.setHorizontalScrollMode(self.horizontalScrollMode())
        self._frozen_view.setVerticalScrollMode(self.verticalScrollMode())
        self._frozen_view.hide()

        # keep vertical scrolling in sync
        self.verticalScrollBar().valueChanged.connect(self._frozen_view.verticalScrollBar().setValue)
        self._frozen_view.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)

        # keep column widths in sync
        self.horizontalHeader().sectionResized.connect(self._on_section_resized)

    def setModel(self, model):
        super().setModel(model)
        if self._frozen_view:
            self._frozen_view.setModel(model)
            # share selection model so selection follows
            self._frozen_view.setSelectionModel(self.selectionModel())
            self._update_frozen_columns()

    def set_frozen_columns(self, count: int):
        self._frozen_columns = max(0, int(count))
        self._update_frozen_columns()
        # notify listeners
        try:
            self.frozenChanged.emit(self._frozen_columns)
        except Exception:
            pass

    def _update_frozen_columns(self):
        if not self._frozen_view or not self.model():
            return

        model = self.model()
        cols = model.columnCount()
        if self._frozen_columns <= 0:
            self._frozen_view.hide()
            return

        # show/hide columns on frozen view
        for c in range(cols):
            if c < self._frozen_columns:
                self._frozen_view.setColumnHidden(c, False)
            else:
                self._frozen_view.setColumnHidden(c, True)

        # hide all non-frozen columns in main view's viewport (they remain but are scrolled)
        # keep frozen view visible and stacked above the main viewport
        self._frozen_view.show()
        self._resize_frozen_view()

    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        # when a column is resized in the main view, update frozen overlay geometry
        if logicalIndex < self._frozen_columns:
            self._resize_frozen_view()

    def _on_header_clicked(self, logicalIndex):
        # freeze up to and including this column
        self.set_frozen_columns(logicalIndex + 1)

    def _resize_frozen_view(self):
        # compute total width of frozen columns
        if not self._frozen_view or not self.model() or self._frozen_columns <= 0:
            return

        width = 0
        for c in range(self._frozen_columns):
            width += self.columnWidth(c)

        # account for vertical header width
        vheader_w = self.verticalHeader().width()
        # place frozen view over the main viewport, left-aligned
        header_h = self.horizontalHeader().height()
        frame = self.frameWidth()
        x = frame + vheader_w
        y = frame + header_h
        h = self.viewport().height()
        self._frozen_view.setGeometry(QRect(x, y, width, h))
        # ensure the frozen view shows same row heights
        for r in range(self.model().rowCount()):
            self._frozen_view.setRowHeight(r, self.rowHeight(r))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_frozen_view()

    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        super().scrollTo(index, hint)
        # if the target cell is in frozen columns, also ensure frozen view scrolls vertically
        if index.isValid() and index.column() < self._frozen_columns and self._frozen_view:
            self._frozen_view.scrollTo(index, hint)

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
