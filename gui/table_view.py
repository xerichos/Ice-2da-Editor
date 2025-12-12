from PyQt5.QtWidgets import QTableView, QMenu, QAction, QHeaderView, QAbstractItemView, QPushButton
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QModelIndex, QAbstractTableModel, QEvent


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

        self._frozen_column = None
        self._frozen_view = QTableView(self)
        self._frozen_view.setFocusPolicy(Qt.NoFocus)
        self._frozen_view.verticalHeader().hide()
        self._frozen_view.horizontalHeader().show()
        self._frozen_view.horizontalHeader().setSectionsMovable(False)
        self._frozen_view.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._frozen_view.setSelectionBehavior(self.selectionBehavior())
        self._frozen_view.setSelectionMode(self.selectionMode())
        self._frozen_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setEditTriggers(self.editTriggers())
        self._frozen_view.hide()

        self._frozen_col_sizes = {}
        self._frozen_proxy = None
        self._main_selection_connected = False
        self._unpin_column_btn = QPushButton("?", self._frozen_view)
        self._unpin_column_btn.setFixedSize(28, 20)
        self._unpin_column_btn.setToolTip("Unpin column")
        self._unpin_column_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #cc5555; font-weight: bold; } QPushButton:hover { background-color: #ff5252; }")
        self._unpin_column_btn.clicked.connect(self._unpin_column)
        self._unpin_column_btn.hide()

        self._frozen_row = None
        self._frozen_row_view = QTableView(self)
        self._frozen_row_view.setFocusPolicy(Qt.NoFocus)
        self._frozen_row_view.setAlternatingRowColors(False)
        self._frozen_row_view.verticalHeader().hide()
        self._frozen_row_view.horizontalHeader().show()
        self._frozen_row_view.verticalHeader().setSectionsMovable(False)
        self._frozen_row_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._frozen_row_view.setSelectionBehavior(self.selectionBehavior())
        self._frozen_row_view.setSelectionMode(self.selectionMode())
        self._frozen_row_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_row_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_row_view.setEditTriggers(self.editTriggers())
        self._frozen_row_view.hide()

        self._frozen_row_sizes = {}
        self._frozen_row_proxy = None
        self._main_row_selection_connected = False
        self._unpin_row_btn = QPushButton("?", self._frozen_row_view)
        self._unpin_row_btn.setFixedSize(28, 20)
        self._unpin_row_btn.setToolTip("Unpin row")
        self._unpin_row_btn.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #cc5555; font-weight: bold; } QPushButton:hover { background-color: #ff5252; }")
        self._unpin_row_btn.clicked.connect(self._unpin_row)
        self._unpin_row_btn.hide()

        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._frozen_view.horizontalHeader().sectionClicked.connect(self._on_frozen_header_clicked)
        self.horizontalHeader().sectionResized.connect(self._on_section_resized)
        self.verticalScrollBar().valueChanged.connect(self._sync_frozen_vertical_value)
        self.verticalScrollBar().rangeChanged.connect(self._sync_frozen_vertical_range)
        self._frozen_view.viewport().installEventFilter(self)

        self.verticalHeader().sectionClicked.connect(self._on_row_header_clicked)
        self._frozen_row_view.horizontalHeader().sectionClicked.connect(self._on_frozen_row_header_clicked)
        self.verticalHeader().sectionResized.connect(self._on_row_section_resized)
        self.horizontalScrollBar().valueChanged.connect(self._sync_frozen_horizontal_value)
        self.horizontalScrollBar().rangeChanged.connect(self._sync_frozen_horizontal_range)
        self._frozen_row_view.viewport().installEventFilter(self)

    def currentRow(self):
        idx = self.currentIndex()
        return idx.row() if idx.isValid() else -1

    def setModel(self, model):
        super().setModel(model)
        if self._frozen_view:
            try:
                self._frozen_view.setItemDelegate(self.itemDelegate())
            except Exception:
                pass
            try:
                self._frozen_view.setEditTriggers(self.editTriggers())
            except Exception:
                pass
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

    def freeze_toggle_column(self, idx: int):
        if self._frozen_column == idx:
            self._frozen_column = None
        else:
            self._frozen_column = idx
        self._update_frozen_columns()

    def freeze_toggle_row(self, idx: int):
        if self._frozen_row == idx:
            self._frozen_row = None
        else:
            self._frozen_row = idx
        self._update_frozen_rows()

    def _update_frozen_columns(self):
        if not self._frozen_view or not self.model():
            return

        model = self.model()
        cols = model.columnCount()

        if self._frozen_column is None:
            for c in range(cols):
                self.setColumnHidden(c, False)
            self._frozen_view.hide()
            self._unpin_column_btn.hide()
            if self._frozen_row_view and self._frozen_row is not None:
                for c in range(cols):
                    self._frozen_row_view.setColumnHidden(c, False)
                self._resize_frozen_row_view()
            return

        header = self.horizontalHeader()
        col_sizes = [header.sectionSize(c) for c in range(cols)]
        self._frozen_col_sizes = {c: col_sizes[c] for c in range(cols)}

        for c in range(cols):
            self.setColumnHidden(c, c == self._frozen_column)
        if self._frozen_row_view and self._frozen_row is not None:
            for c in range(cols):
                self._frozen_row_view.setColumnHidden(c, c == self._frozen_column)
            self._resize_frozen_row_view()

        frozen_sorted = [self._frozen_column]

        class FrozenModel(QAbstractTableModel):
            def __init__(self, source, cols, parent=None):
                super().__init__(parent)
                self._source = source
                self._cols = list(cols)

            def setColumns(self, cols):
                self.beginResetModel()
                self._cols = list(cols)
                self.endResetModel()

            def setSource(self, source):
                self.beginResetModel()
                self._source = source
                self.endResetModel()

            def rowCount(self, parent=QModelIndex()):
                return 0 if self._source is None else self._source.rowCount()

            def columnCount(self, parent=QModelIndex()):
                return len(self._cols)

            def data(self, index, role=Qt.DisplayRole):
                if not index.isValid() or self._source is None:
                    return None
                src_idx = self._source.index(index.row(), self._cols[index.column()])
                return self._source.data(src_idx, role)

            def setData(self, index, value, role=Qt.EditRole):
                if not index.isValid() or self._source is None:
                    return False
                src_idx = self._source.index(index.row(), self._cols[index.column()])
                return self._source.setData(src_idx, value, role)

            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if self._source is None:
                    return None
                if orientation == Qt.Horizontal:
                    src_col = self._cols[section]
                    return self._source.headerData(src_col, orientation, role)
                return self._source.headerData(section, orientation, role)

            def flags(self, index):
                if not index.isValid() or self._source is None:
                    return Qt.NoItemFlags
                src_idx = self._source.index(index.row(), self._cols[index.column()])
                return self._source.flags(src_idx)

        if self._frozen_proxy is None:
            self._frozen_proxy = FrozenModel(self.model(), frozen_sorted, self)
        else:
            self._frozen_proxy.setSource(self.model())
            self._frozen_proxy.setColumns(frozen_sorted)

        self._frozen_view.setModel(self._frozen_proxy)

        for pos, src_col in enumerate(frozen_sorted):
            try:
                self._frozen_view.setColumnWidth(pos, col_sizes[src_col])
            except Exception:
                pass

        try:
            if getattr(self, '_main_selection_connected', False):
                try:
                    self.selectionModel().currentChanged.disconnect(self._on_main_current_changed)
                except Exception:
                    pass
            self.selectionModel().currentChanged.connect(self._on_main_current_changed)
            self._main_selection_connected = True
        except Exception:
            pass

        self._frozen_view.horizontalHeader().show()
        self._frozen_view.show()
        try:
            self._frozen_view.raise_()
        except Exception:
            pass
        self._resize_frozen_view()
        self._update_unpin_column_button()

        try:
            self._sync_frozen_vertical_range(self.verticalScrollBar().minimum(), self.verticalScrollBar().maximum())
            self._sync_frozen_vertical_value(self.verticalScrollBar().value())
        except Exception:
            pass

    def _update_frozen_rows(self):
        if not self._frozen_row_view or not self.model():
            return

        model = self.model()
        rows = model.rowCount()

        if self._frozen_row is None:
            for r in range(rows):
                self.setRowHidden(r, False)
            self._frozen_row_view.hide()
            if hasattr(self, '_unpin_row_btn') and self._unpin_row_btn:
                self._unpin_row_btn.hide()
            return

        header = self.verticalHeader()
        row_sizes = [header.sectionSize(r) for r in range(rows)]
        self._frozen_row_sizes = {r: row_sizes[r] for r in range(rows)}

        for r in range(rows):
            self.setRowHidden(r, r == self._frozen_row)

        cols = model.columnCount()
        for c in range(cols):
            if self._frozen_column is not None:
                self._frozen_row_view.setColumnHidden(c, c == self._frozen_column)
            else:
                self._frozen_row_view.setColumnHidden(c, False)

        frozen_sorted = [self._frozen_row]

        class FrozenRowModel(QAbstractTableModel):
            def __init__(self, source, rows, parent=None):
                super().__init__(parent)
                self._source = source
                self._rows = list(rows)

            def setRows(self, rows):
                self.beginResetModel()
                self._rows = list(rows)
                self.endResetModel()

            def setSource(self, source):
                self.beginResetModel()
                self._source = source
                self.endResetModel()

            def rowCount(self, parent=QModelIndex()):
                return len(self._rows)

            def columnCount(self, parent=QModelIndex()):
                return 0 if self._source is None else self._source.columnCount()

            def data(self, index, role=Qt.DisplayRole):
                if not index.isValid() or self._source is None:
                    return None
                src_idx = self._source.index(self._rows[index.row()], index.column())
                return self._source.data(src_idx, role)

            def setData(self, index, value, role=Qt.EditRole):
                if not index.isValid() or self._source is None:
                    return False
                src_idx = self._source.index(self._rows[index.row()], index.column())
                return self._source.setData(src_idx, value, role)

            def headerData(self, section, orientation, role=Qt.DisplayRole):
                if self._source is None:
                    return None
                if orientation == Qt.Vertical:
                    src_row = self._rows[section]
                    return self._source.headerData(src_row, orientation, role)
                return self._source.headerData(section, orientation, role)

            def flags(self, index):
                if not index.isValid() or self._source is None:
                    return Qt.NoItemFlags
                src_idx = self._source.index(self._rows[index.row()], index.column())
                return self._source.flags(src_idx)

        if self._frozen_row_proxy is None:
            self._frozen_row_proxy = FrozenRowModel(self.model(), frozen_sorted, self)
        else:
            self._frozen_row_proxy.setSource(self.model())
            self._frozen_row_proxy.setRows(frozen_sorted)

        self._frozen_row_view.setModel(self._frozen_row_proxy)

        for pos, src_row in enumerate(frozen_sorted):
            try:
                self._frozen_row_view.setRowHeight(pos, row_sizes[src_row])
            except Exception:
                pass

        # Set column widths to match main table
        for c in range(cols):
            try:
                width = self.columnWidth(c)
                if width > 0:
                    self._frozen_row_view.setColumnWidth(c, width)
            except Exception:
                pass

        try:
            if getattr(self, '_main_row_selection_connected', False):
                try:
                    self.selectionModel().currentChanged.disconnect(self._on_main_row_current_changed)
                except Exception:
                    pass
            self.selectionModel().currentChanged.connect(self._on_main_row_current_changed)
            self._main_row_selection_connected = True
        except Exception:
            pass

        self._frozen_row_view.show()
        try:
            self._frozen_row_view.raise_()
        except Exception:
            pass
        self._resize_frozen_row_view()
        self._update_unpin_row_button()

        try:
            self._sync_frozen_horizontal_range(self.horizontalScrollBar().minimum(), self.horizontalScrollBar().maximum())
            self._sync_frozen_horizontal_value(self.horizontalScrollBar().value())
        except Exception:
            pass

        # Force update of the frozen row view
        try:
            self._frozen_row_view.update()
            self._frozen_row_view.viewport().update()
        except Exception:
            pass

    def _sync_frozen_vertical_range(self, minimum, maximum):
        if not self._frozen_view:
            return
        sb_main = self.verticalScrollBar()
        sb_frozen = self._frozen_view.verticalScrollBar()
        try:
            sb_frozen.setRange(minimum, maximum)
            sb_frozen.setPageStep(sb_main.pageStep())
            sb_frozen.setSingleStep(sb_main.singleStep())
        except Exception:
            pass
        try:
            sb_frozen.setValue(sb_main.value())
        except Exception:
            pass

    def _sync_frozen_vertical_value(self, value):
        if not self._frozen_view:
            return
        try:
            self._frozen_view.verticalScrollBar().setValue(value)
        except Exception:
            pass
        self._frozen_view.viewport().update()

    def _sync_frozen_horizontal_range(self, minimum, maximum):
        if not self._frozen_row_view or self._frozen_row is None:
            return
        sb_main = self.horizontalScrollBar()
        sb_frozen = self._frozen_row_view.horizontalScrollBar()
        try:
            sb_frozen.setRange(minimum, maximum)
            sb_frozen.setPageStep(sb_main.pageStep())
            sb_frozen.setSingleStep(sb_main.singleStep())
            sb_frozen.setValue(sb_main.value())
        except Exception:
            pass

    def _sync_frozen_horizontal_value(self, value):
        if not self._frozen_row_view or self._frozen_row is None:
            return
        try:
            sb_frozen = self._frozen_row_view.horizontalScrollBar()
            if sb_frozen.value() != value:
                sb_frozen.setValue(value)
        except Exception:
            pass
        self._frozen_row_view.viewport().update()

    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        if logicalIndex == self._frozen_column:
            self._resize_frozen_view()
        if self._frozen_row_view and self._frozen_row is not None:
            try:
                if logicalIndex < self._frozen_row_view.model().columnCount():
                    self._frozen_row_view.setColumnWidth(logicalIndex, newSize)
            except Exception:
                pass

    def _on_row_section_resized(self, logicalIndex, oldSize, newSize):
        if logicalIndex == self._frozen_row:
            self._resize_frozen_row_view()
        if self._frozen_row_view and self._frozen_row is not None:
            try:
                self._frozen_row_view.setRowHeight(0, newSize)
            except Exception:
                pass

    def _on_header_clicked(self, logicalIndex):
        self.freeze_toggle_column(logicalIndex)

    def _on_frozen_header_clicked(self, logicalIndex):
        pass

    def _unpin_column(self):
        if self._frozen_column is not None:
            self._frozen_column = None
            self._update_frozen_columns()

    def _on_row_header_clicked(self, logicalIndex):
        if self._frozen_row is not None and self._frozen_row == logicalIndex:
            self._frozen_row = None
            self._update_frozen_rows()
            return
        self.freeze_toggle_row(logicalIndex)

    def _on_frozen_row_header_clicked(self, logicalIndex):
        pass

    def _unpin_row(self):
        if self._frozen_row is not None:
            self._frozen_row = None
            self._update_frozen_rows()

    def _on_main_current_changed(self, current, previous):
        if not current.isValid() or not getattr(self, '_frozen_proxy', None):
            return
        src_col = current.column()
        try:
            if src_col == self._frozen_column:
                idx = self._frozen_view.model().index(current.row(), 0)
                self._frozen_view.setCurrentIndex(idx)
        except Exception:
            pass

    def _resize_frozen_view(self):
        if not self._frozen_view or not self.model() or self._frozen_column is None:
            return
        width = self._frozen_col_sizes.get(self._frozen_column, self.columnWidth(self._frozen_column))
        vp = self.viewport().geometry()
        header_height = self.horizontalHeader().height()
        x = vp.x()
        y = vp.y() - header_height
        h = header_height + vp.height()
        self._frozen_view.setGeometry(QRect(x, y, width, h))
        for r in range(self.model().rowCount()):
            self._frozen_view.setRowHeight(r, self.rowHeight(r))

    def _update_unpin_column_button(self):
        if self._frozen_column is None:
            self._unpin_column_btn.hide()
            return
        self._unpin_column_btn.show()
        self._unpin_column_btn.raise_()
        btn_x = self._frozen_view.width() - 32
        btn_y = 2
        self._unpin_column_btn.move(btn_x, btn_y)

    def _resize_frozen_row_view(self):
        if not self._frozen_row_view or not self.model() or self._frozen_row is None:
            return
        height = self._frozen_row_sizes.get(self._frozen_row, self.rowHeight(self._frozen_row))
        vp = self.viewport().geometry()
        x = vp.x()
        y = vp.y()
        w = vp.width()
        h = height
        self._frozen_row_view.setGeometry(QRect(x, y, w, h))
        cols = self.model().columnCount()
        for c in range(cols):
            try:
                width = self.columnWidth(c)
                if width > 0:
                    self._frozen_row_view.setColumnWidth(c, width)
            except Exception:
                pass
        try:
            self._frozen_row_view.horizontalScrollBar().setValue(self.horizontalScrollBar().value())
        except Exception:
            pass

    def _update_unpin_row_button(self):
        if not hasattr(self, '_unpin_row_btn') or self._frozen_row is None or not self._frozen_row_view.isVisible():
            if hasattr(self, '_unpin_row_btn') and self._unpin_row_btn:
                self._unpin_row_btn.hide()
            return
        self._unpin_row_btn.show()
        self._unpin_row_btn.raise_()
        btn_x = max(2, self._frozen_row_view.width() - 32)
        btn_y = 2
        self._unpin_row_btn.move(btn_x, btn_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_frozen_view()
        self._resize_frozen_row_view()
        if hasattr(self, '_unpin_column_btn'):
            self._update_unpin_column_button()
        if hasattr(self, '_unpin_row_btn'):
            self._update_unpin_row_button()

    def scrollTo(self, index, hint=QAbstractItemView.EnsureVisible):
        super().scrollTo(index, hint)
        if index.isValid() and index.column() == self._frozen_column and self._frozen_view:
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

    def _on_main_row_current_changed(self, current, previous):
        if not current.isValid() or not getattr(self, '_frozen_row_proxy', None):
            return
        src_row = current.row()
        try:
            if src_row == self._frozen_row:
                idx = self._frozen_row_view.model().index(0, current.column())
                self._frozen_row_view.setCurrentIndex(idx)
        except Exception:
            pass

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
                if dy != 0:
                    step = -int(dy / 120) * sb.singleStep()
                else:
                    step = 0
            except Exception:
                step = 0
            sb.setValue(sb.value() + step)
            return True
        return super().eventFilter(obj, event)
