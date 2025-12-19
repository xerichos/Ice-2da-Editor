from PyQt5.QtWidgets import (
    QTableView,
    QMenu,
    QAction,
    QHeaderView,
    QAbstractItemView,
    QScroller,
    QFrame,
    QApplication,
)
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QModelIndex,
    QEvent,
    QTimer,
)
from PyQt5.QtGui import QKeySequence, QClipboard
from .frozen_view import FrozenViewMixin

PAN_START_THRESHOLD = 8  # pixels


class TwoDATable(QTableView, FrozenViewMixin):
    requestInsertAbove = pyqtSignal()
    requestInsertBelow = pyqtSignal()
    requestDuplicate = pyqtSignal()
    requestDelete = pyqtSignal()

    requestInsertColumnLeft = pyqtSignal()
    requestInsertColumnRight = pyqtSignal()
    requestDuplicateColumn = pyqtSignal()
    requestDeleteColumn = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Row metrics on the MAIN view ---
        vh = self.verticalHeader()
        vh.setSectionResizeMode(QHeaderView.Fixed)
        vh.setDefaultSectionSize(22)

        # NOTE: frames/borders can subtly affect layout; remove them for consistency
        self.setFrameShape(QFrame.NoFrame)
        self.setLineWidth(0)
        self.setMidLineWidth(0)

        self._panning = False
        self._pan_last_pos = None
        self._pan_dx = 0.0
        self._pan_dy = 0.0

        self._pan_timer = QTimer(self)
        self._pan_timer.setInterval(33)  # ~30 Hz
        self._pan_timer.timeout.connect(self._apply_pan)

        QScroller.grabGesture(self.viewport(), QScroller.LeftMouseButtonGesture)

        self.setAlternatingRowColors(False)
        self.setSortingEnabled(False)

        # Enable extended selection for multi-row/cell selection
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

        # Hide the empty column 0
        self.setColumnHidden(0, True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

        # Column header context menu
        # Set column resize mode to resize to contents
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeToContents)
        hh.setContextMenuPolicy(Qt.CustomContextMenu)
        hh.customContextMenuRequested.connect(self.open_column_context_menu)

        # Keep scroll modes identical across views (needed for proper frozen view sync)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        # Initialize frozen views
        self._init_frozen_views()

        self.setEditTriggers(
            QAbstractItemView.EditKeyPressed |
            QAbstractItemView.DoubleClicked |
            QAbstractItemView.SelectedClicked
        )

    def currentRow(self):
        idx = self.currentIndex()
        return idx.row() if idx.isValid() else -1

    def currentColumn(self):
        idx = self.currentIndex()
        return idx.column() if idx.isValid() else -1

    def setModel(self, model):
        super().setModel(model)

        # Connect frozen column notifications if model supports it
        if model and hasattr(model, '_notify_frozen_column_insert'):
            model._notify_frozen_column_insert = self._on_frozen_column_insert
            model._notify_frozen_column_remove = self._on_frozen_column_remove

        if self._frozen_view:
            try:
                self._frozen_view.setItemDelegate(self.itemDelegate())
            except Exception:
                pass
            try:
                self._frozen_view.setEditTriggers(self.editTriggers())
            except Exception:
                pass
            # Ensure frozen view stays metric-compatible with main view
            self._frozen_view.setShowGrid(self.showGrid())
            self._update_frozen_columns()

        if self._frozen_row_view:
            try:
                self._frozen_row_view.setItemDelegate(self.itemDelegate())
            except Exception:
                pass
            try:
                self._frozen_row_view.setEditTriggers(self.editTriggers())
            except Exception:
                pass
            self._frozen_row_view.setShowGrid(self.showGrid())
            self._update_frozen_rows()

    def setItemDelegate(self, delegate):
        super().setItemDelegate(delegate)
        if self._frozen_view:
            try:
                self._frozen_view.setItemDelegate(delegate)
            except Exception:
                pass
        if self._frozen_row_view:
            try:
                self._frozen_row_view.setItemDelegate(delegate)
            except Exception:
                pass

    def setEditTriggers(self, triggers):
        super().setEditTriggers(triggers)
        if self._frozen_view:
            try:
                self._frozen_view.setEditTriggers(triggers)
            except Exception:
                pass
        if self._frozen_row_view:
            try:
                self._frozen_row_view.setEditTriggers(triggers)
            except Exception:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_frozen_view()
        self._resize_frozen_row_view()
        if hasattr(self, "_unpin_column_btn"):
            self._update_unpin_column_button()
        if hasattr(self, "_unpin_row_btn"):
            self._update_unpin_row_button()

    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        super().scrollTo(index, hint)
        if (
            index.isValid()
            and index.column() == self._frozen_column
            and self._frozen_view
        ):
            try:
                if self._frozen_proxy:
                    idx = self._frozen_proxy.index(index.row(), 0)
                    self._frozen_view.scrollTo(idx, hint)
                    return
            except Exception:
                pass
            self._frozen_view.scrollTo(index, hint)

    def open_context_menu(self, pos):
        idx = self.indexAt(pos)
        if not idx.isValid():
            return
        self.setCurrentIndex(idx)
        menu = QMenu(self)

        # Row operations
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

        # Column operations
        menu.addSeparator()

        act_insert_left = QAction("Insert Column Left", self)
        act_insert_right = QAction("Insert Column Right", self)
        act_duplicate_col = QAction("Duplicate Column", self)
        act_delete_col = QAction("Delete Column", self)

        act_insert_left.triggered.connect(self.requestInsertColumnLeft.emit)
        act_insert_right.triggered.connect(self.requestInsertColumnRight.emit)
        act_duplicate_col.triggered.connect(self.requestDuplicateColumn.emit)
        act_delete_col.triggered.connect(self.requestDeleteColumn.emit)

        menu.addAction(act_insert_left)
        menu.addAction(act_insert_right)
        menu.addAction(act_duplicate_col)
        menu.addSeparator()
        menu.addAction(act_delete_col)

        menu.exec_(self.viewport().mapToGlobal(pos))

    def open_column_context_menu(self, pos):
        header = self.horizontalHeader()
        col = header.logicalIndexAt(pos)
        if col < 0:
            return

        # Set current column for operations
        if self.model():
            # Set current index to first row of this column
            idx = self.model().index(0, col)
            self.setCurrentIndex(idx)

        menu = QMenu(self)

        # Rename option
        act_rename = QAction("Rename Column", self)
        act_rename.triggered.connect(lambda: self.rename_column(col))

        # Freeze/Unfreeze option
        is_frozen = getattr(self, '_frozen_column', None) == col
        freeze_text = "Unfreeze Column" if is_frozen else "Freeze Column"
        act_freeze = QAction(freeze_text, self)
        act_freeze.triggered.connect(lambda: self.toggle_freeze_column(col))

        act_insert_left = QAction("Insert Column Left", self)
        act_insert_right = QAction("Insert Column Right", self)
        act_duplicate = QAction("Duplicate Column", self)
        act_delete = QAction("Delete Column", self)

        act_insert_left.triggered.connect(self.requestInsertColumnLeft.emit)
        act_insert_right.triggered.connect(self.requestInsertColumnRight.emit)
        act_duplicate.triggered.connect(self.requestDuplicateColumn.emit)
        act_delete.triggered.connect(self.requestDeleteColumn.emit)

        menu.addAction(act_rename)
        menu.addAction(act_freeze)
        menu.addSeparator()
        menu.addAction(act_insert_left)
        menu.addAction(act_insert_right)
        menu.addAction(act_duplicate)
        menu.addSeparator()
        menu.addAction(act_delete)
        menu.exec_(header.mapToGlobal(pos))

    def eventFilter(self, obj, event):
        if self._frozen_view and obj is self._frozen_view.viewport() and event.type() == QEvent.Wheel:
            sb = self.verticalScrollBar()
            try:
                dy = event.angleDelta().y()
                step = -int(dy / 120) * sb.singleStep()
            except Exception:
                step = 0
            sb.setValue(sb.value() + step)
            return True

        if self._frozen_row_view and obj is self._frozen_row_view.viewport() and event.type() == QEvent.Wheel:
            sb = self.verticalScrollBar()
            try:
                dy = event.angleDelta().y()
                step = -int(dy / 120) * sb.singleStep() if dy != 0 else 0
            except Exception:
                step = 0
            sb.setValue(sb.value() + step)
            return True

        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_origin_pos = event.pos()
            self._pan_last_pos = event.pos()
            self._pan_dx = 0.0
            self._pan_dy = 0.0
            self._pan_active = False
            self.setCursor(Qt.OpenHandCursor)
            self._pan_timer.start()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_last_pos is not None:
            delta = event.pos() - self._pan_last_pos
            self._pan_last_pos = event.pos()

            if not self._pan_active:
                total_delta = event.pos() - self._pan_origin_pos
                if (
                    abs(total_delta.x()) < PAN_START_THRESHOLD
                    and abs(total_delta.y()) < PAN_START_THRESHOLD
                ):
                    event.accept()
                    return
                self._pan_active = True
                self.setCursor(Qt.ClosedHandCursor)

            self._pan_dx += delta.x()
            self._pan_dy += delta.y()

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self._pan_active = False
            self._pan_origin_pos = None
            self._pan_last_pos = None
            self._pan_dx = 0.0
            self._pan_dy = 0.0
            self._pan_timer.stop()
            self.unsetCursor()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _apply_pan(self):
        if not self._panning:
            return
        if not (self._pan_dx or self._pan_dy):
            return

        hbar = self.horizontalScrollBar()
        vbar = self.verticalScrollBar()

        viewport = self.viewport()
        vw = max(1, viewport.width())
        vh = max(1, viewport.height())

        DEAD_ZONE = 2.0
        if abs(self._pan_dx) < DEAD_ZONE:
            self._pan_dx = 0.0
        if abs(self._pan_dy) < DEAD_ZONE:
            self._pan_dy = 0.0

        if not (self._pan_dx or self._pan_dy):
            return

        dx = self._pan_dx * (hbar.pageStep() / vw)
        dy = self._pan_dy * (vbar.pageStep() / vh)

        row_h = self.rowHeight(0) if self.model().rowCount() else 1
        min_v_step = max(1, row_h // 2)
        min_h_step = max(4, hbar.pageStep() // 20)

        ix = int(dx / min_h_step) * min_h_step
        iy = int(dy / min_v_step) * min_v_step

        if ix or iy:
            hbar.setValue(hbar.value() - ix)
            vbar.setValue(vbar.value() - iy)

            if ix:
                self._pan_dx = 0.0
            if iy:
                self._pan_dy = 0.0

    def copy_selection(self):
        """Copy all selected cells to clipboard in tab-separated format."""
        if not self.model():
            return

        selected_indexes = self.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        # Group selected cells by row
        rows_data = {}
        min_col = float('inf')
        max_col = 0

        for index in selected_indexes:
            row = index.row()
            col = index.column()
            if row not in rows_data:
                rows_data[row] = {}
            rows_data[row][col] = self.model().data(index, Qt.DisplayRole) or ""
            min_col = min(min_col, col)
            max_col = max(max_col, col)

        if not rows_data:
            return

        # Convert to tab-separated format
        lines = []
        for row in sorted(rows_data.keys()):
            row_data = rows_data[row]
            # Fill in missing columns with empty strings
            row_values = []
            for col in range(min_col, max_col + 1):
                row_values.append(row_data.get(col, ""))
            lines.append("\t".join(row_values))

        clipboard_text = "\n".join(lines)
        QApplication.clipboard().setText(clipboard_text)

    def paste_selection(self):
        """Paste clipboard content starting from current cell."""
        if not self.model():
            return

        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return

        current_index = self.currentIndex()
        if not current_index.isValid():
            return

        start_row = current_index.row()
        start_col = current_index.column()

        # Parse clipboard content (tab-separated rows)
        rows_data = []
        for line in clipboard_text.split('\n'):
            if line.strip():  # Skip empty lines
                row_data = line.split('\t')
                rows_data.append(row_data)

        if not rows_data:
            return

        # Paste data starting from current position
        for row_offset, row_data in enumerate(rows_data):
            target_row = start_row + row_offset
            if target_row >= self.model().rowCount():
                # Add rows if needed
                rows_to_add = target_row - self.model().rowCount() + 1
                self.model().insertRows(self.model().rowCount(), rows_to_add)

            for col_offset, cell_value in enumerate(row_data):
                target_col = start_col + col_offset
                if target_col < self.model().columnCount():
                    index = self.model().index(target_row, target_col)
                    self.model().setData(index, cell_value, Qt.EditRole)

        # Mark document as dirty if we have a parent document
        if hasattr(self.parent(), '_mark_dirty'):
            self.parent()._mark_dirty()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            idx = self.currentIndex()
            if idx.isValid():
                self.edit(idx)
                event.accept()
                return
        elif event.matches(QKeySequence.Copy):
            self.copy_selection()
            event.accept()
            return
        elif event.matches(QKeySequence.Paste):
            self.paste_selection()
            event.accept()
            return
        super().keyPressEvent(event)
