# gui/frozen_view.py
"""
Frozen column and row functionality for TwoDATable.
This module provides a mixin class that adds frozen column/row capabilities to QTableView.
"""
from PyQt5.QtWidgets import QTableView, QPushButton, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel, QRect


class FrozenColumnModel(QAbstractTableModel):
    """Proxy model for frozen column view."""
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


class FrozenRowModel(QAbstractTableModel):
    """Proxy model for frozen row view."""
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


class FrozenViewMixin:
    """
    Mixin class that adds frozen column and row functionality to QTableView.
    To use, inherit from both QTableView and FrozenViewMixin.
    """
    
    def _init_frozen_views(self):
        """Initialize frozen column and row views. Call this from __init__."""
        from PyQt5.QtWidgets import QFrame

        # Frozen column setup
        self._frozen_column = None

        # Connect to model for frozen column management
        if self.model():
            self.model()._notify_frozen_column_insert = self._on_frozen_column_insert
            self.model()._notify_frozen_column_remove = self._on_frozen_column_remove
        self._frozen_view = QTableView(self)
        self._frozen_view.setFrameShape(QFrame.NoFrame)
        self._frozen_view.setLineWidth(0)
        self._frozen_view.setMidLineWidth(0)
        self._frozen_view.setFocusPolicy(Qt.NoFocus)
        self._frozen_view.verticalHeader().hide()
        self._frozen_view.horizontalHeader().setSectionsMovable(False)
        self._frozen_view.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._frozen_view.horizontalHeader().hide()
        self._frozen_view.setSelectionBehavior(self.selectionBehavior())
        self._frozen_view.setSelectionMode(self.selectionMode())
        self._frozen_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setEditTriggers(self.editTriggers())
        self._frozen_view.hide()
        self._frozen_view.setObjectName("FrozenColumnView")
        self._frozen_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._frozen_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._frozen_view.setShowGrid(self.showGrid())
        
        vh = self.verticalHeader()
        fvh = self._frozen_view.verticalHeader()
        fvh.setSectionResizeMode(QHeaderView.Fixed)
        fvh.setDefaultSectionSize(vh.defaultSectionSize())
        fvh.setMinimumSectionSize(vh.minimumSectionSize())
        
        self._frozen_col_sizes = {}
        self._frozen_proxy = None
        self._main_selection_connected = False
        
        self._unpin_column_btn = QPushButton("?", self._frozen_view)
        self._unpin_column_btn.setFixedSize(28, 20)
        self._unpin_column_btn.setToolTip("Unpin column")
        self._unpin_column_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #cc5555; font-weight: bold; } "
            "QPushButton:hover { background-color: #ff5252; }"
        )
        self._unpin_column_btn.clicked.connect(self._unpin_column)
        self._unpin_column_btn.hide()
        
        # Frozen row setup
        self._frozen_row = None
        self._frozen_row_view = QTableView(self)
        self._frozen_row_view.setFrameShape(QFrame.NoFrame)
        self._frozen_row_view.setLineWidth(0)
        self._frozen_row_view.setMidLineWidth(0)
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
        self._frozen_row_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._frozen_row_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._frozen_row_view.setShowGrid(self.showGrid())
        
        self._frozen_row_sizes = {}
        self._frozen_row_proxy = None
        self._main_row_selection_connected = False
        
        self._unpin_row_btn = QPushButton("?", self._frozen_row_view)
        self._unpin_row_btn.setFixedSize(28, 20)
        self._unpin_row_btn.setToolTip("Unpin row")
        self._unpin_row_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #cc5555; font-weight: bold; } "
            "QPushButton:hover { background-color: #ff5252; }"
        )
        self._unpin_row_btn.clicked.connect(self._unpin_row)
        self._unpin_row_btn.hide()
        
        # Connect signals
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
        self.verticalHeader().sectionResized.connect(
            lambda r, old, new: self._frozen_view.setRowHeight(r, new)
        )
    
    def freeze_toggle_column(self, idx: int):
        """Toggle frozen state of a column."""
        if self._frozen_column == idx:
            self._frozen_column = None
        else:
            self._frozen_column = idx
        self._update_frozen_columns()
    
    def freeze_toggle_row(self, idx: int):
        """Toggle frozen state of a row."""
        if self._frozen_row == idx:
            self._frozen_row = None
        else:
            self._frozen_row = idx
        self._update_frozen_rows()
    
    def _update_frozen_columns(self):
        """Update frozen column view based on current frozen column."""
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
        
        if self._frozen_proxy is None:
            self._frozen_proxy = FrozenColumnModel(self.model(), frozen_sorted, self)
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
            if getattr(self, "_main_selection_connected", False):
                try:
                    self.selectionModel().currentChanged.disconnect(self._on_main_current_changed)
                except Exception:
                    pass
            self.selectionModel().currentChanged.connect(self._on_main_current_changed)
            self._main_selection_connected = True
        except Exception:
            pass
        
        self._frozen_view.horizontalHeader().hide()
        self._frozen_view.show()
        try:
            self._frozen_view.raise_()
        except Exception:
            pass
        
        self._resize_frozen_view()
        self._update_unpin_column_button()
        
        try:
            self._sync_frozen_vertical_range(
                self.verticalScrollBar().minimum(),
                self.verticalScrollBar().maximum(),
            )
            self._sync_frozen_vertical_value(self.verticalScrollBar().value())
        except Exception:
            pass
    
    def _update_frozen_rows(self):
        """Update frozen row view based on current frozen row."""
        if not self._frozen_row_view or not self.model():
            return
        
        model = self.model()
        rows = model.rowCount()
        
        if self._frozen_row is None:
            for r in range(rows):
                self.setRowHidden(r, False)
            self._frozen_row_view.hide()
            if hasattr(self, "_unpin_row_btn") and self._unpin_row_btn:
                self._unpin_row_btn.hide()
            # Force visual refresh
            self.update()
            self.viewport().update()
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
        
        for c in range(cols):
            try:
                width = self.columnWidth(c)
                if width > 0:
                    self._frozen_row_view.setColumnWidth(c, width)
            except Exception:
                pass
        
        try:
            if getattr(self, "_main_row_selection_connected", False):
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
            self._sync_frozen_horizontal_range(
                self.horizontalScrollBar().minimum(),
                self.horizontalScrollBar().maximum(),
            )
            self._sync_frozen_horizontal_value(self.horizontalScrollBar().value())
        except Exception:
            pass
        
        try:
            self._frozen_row_view.update()
            self._frozen_row_view.viewport().update()
        except Exception:
            pass
    
    def _sync_frozen_vertical_range(self, minimum, maximum):
        """Sync vertical scroll range with frozen column view."""
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
        """Sync vertical scroll value with frozen column view."""
        if not self._frozen_view:
            return
        try:
            self._frozen_view.verticalScrollBar().setValue(value)
        except Exception:
            pass
        self._frozen_view.viewport().update()
    
    def _sync_frozen_horizontal_range(self, minimum, maximum):
        """Sync horizontal scroll range with frozen row view."""
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
        """Sync horizontal scroll value with frozen row view."""
        if not self._frozen_row_view or self._frozen_row is None:
            return
        try:
            sb_frozen = self._frozen_row_view.horizontalScrollBar()
            if sb_frozen.value() != value:
                sb_frozen.setValue(value)
        except Exception:
            pass
        self._frozen_row_view.viewport().update()
        self._frozen_row_view.update()
    
    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        """Handle column resize events."""
        if logicalIndex == self._frozen_column:
            self._resize_frozen_view()
        if self._frozen_row_view and self._frozen_row is not None:
            try:
                if logicalIndex < self._frozen_row_view.model().columnCount():
                    self._frozen_row_view.setColumnWidth(logicalIndex, newSize)
            except Exception:
                pass
    
    def _on_row_section_resized(self, logicalIndex, oldSize, newSize):
        """Handle row resize events."""
        if logicalIndex == self._frozen_row:
            self._resize_frozen_row_view()
        if self._frozen_row_view and self._frozen_row is not None:
            try:
                self._frozen_row_view.setRowHeight(0, newSize)
            except Exception:
                pass
    
    def _on_header_clicked(self, logicalIndex):
        """Handle header click - no action."""
        pass

    def rename_column(self, logicalIndex):
        """Rename a column by showing an input dialog."""
        from PyQt5.QtWidgets import QInputDialog

        if not self.model():
            return

        current_name = self.model().headerData(logicalIndex, Qt.Horizontal, Qt.DisplayRole) or ""
        new_name, ok = QInputDialog.getText(
            self, "Rename Column",
            f"Enter new name for column {logicalIndex + 1}:",
            text=current_name
        )

        if ok and new_name.strip():
            # Update the header data
            success = self.model().setHeaderData(logicalIndex, Qt.Horizontal, new_name.strip(), Qt.EditRole)
            if success:
                # Mark document as dirty
                if hasattr(self, 'parent') and hasattr(self.parent(), '_mark_dirty'):
                    self.parent()._mark_dirty()

    def toggle_freeze_column(self, logicalIndex):
        """Toggle frozen state of a column (for context menu)."""
        self.freeze_toggle_column(logicalIndex)

    def _on_frozen_header_clicked(self, logicalIndex):
        """Handle frozen header click (no-op)."""
        pass

    def _unpin_column(self):
        """Unpin the frozen column."""
        if self._frozen_column is not None:
            self._frozen_column = None
            self._update_frozen_columns()
    
    def _on_row_header_clicked(self, logicalIndex):
        """Handle row header click to toggle frozen row."""
        if self._frozen_row is not None and self._frozen_row == logicalIndex:
            self._frozen_row = None
            self._update_frozen_rows()
            return
        self.freeze_toggle_row(logicalIndex)
    
    def _on_frozen_row_header_clicked(self, logicalIndex):
        """Handle frozen row header click (no-op)."""
        pass
    
    def _unpin_row(self):
        """Unpin the frozen row."""
        if self._frozen_row is not None:
            self._frozen_row = None
            self._update_frozen_rows()

    def _on_frozen_column_insert(self, column, count):
        """Handle column insertions by adjusting frozen column index."""
        if self._frozen_column is None:
            return

        if column <= self._frozen_column:
            # Columns inserted before or at frozen column - shift the index
            self._frozen_column += count
            self._update_frozen_columns()

    def _on_frozen_column_remove(self, column, count):
        """Handle column removals by adjusting frozen column index."""
        if self._frozen_column is None:
            return

        removed_end = column + count - 1

        if column <= self._frozen_column <= removed_end:
            # Frozen column is being removed - unpin it
            self._frozen_column = None
            self._update_frozen_columns()
        elif column <= self._frozen_column:
            # Columns removed before frozen column - shift the index
            self._frozen_column -= count
            self._update_frozen_columns()
            self._update_frozen_rows()
    
    def _on_main_current_changed(self, current, previous):
        """Sync current selection with frozen column view."""
        if not current.isValid() or not getattr(self, "_frozen_proxy", None):
            return
        src_col = current.column()
        try:
            if src_col == self._frozen_column:
                idx = self._frozen_view.model().index(current.row(), 0)
                self._frozen_view.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _on_main_row_current_changed(self, current, previous):
        """Sync current selection with frozen row view."""
        if not current.isValid() or not getattr(self, "_frozen_row_proxy", None):
            return
        src_row = current.row()
        try:
            if src_row == self._frozen_row:
                idx = self._frozen_row_view.model().index(0, current.column())
                self._frozen_row_view.setCurrentIndex(idx)
        except Exception:
            pass
    
    def _resize_frozen_view(self):
        """Resize frozen column view to match main view."""
        if not self._frozen_view or not self.model() or self._frozen_column is None:
            return
        
        width = self._frozen_col_sizes.get(
            self._frozen_column, self.columnWidth(self._frozen_column)
        )
        
        vp = self.viewport().geometry()
        x = vp.x()
        y = vp.y()
        h = vp.height()
        
        self._frozen_view.setGeometry(QRect(x, y, width, h))
        
        rows = self.model().rowCount()
        for r in range(rows):
            self._frozen_view.setRowHeight(r, self.rowHeight(r))
    
    def _update_unpin_column_button(self):
        """Update position and visibility of unpin column button."""
        if self._frozen_column is None:
            self._unpin_column_btn.hide()
            return
        self._unpin_column_btn.show()
        self._unpin_column_btn.raise_()
        btn_x = self._frozen_view.width() - 32
        btn_y = 2
        self._unpin_column_btn.move(btn_x, btn_y)
    
    def _resize_frozen_row_view(self):
        """Resize frozen row view to match main view."""
        if not self._frozen_row_view or not self.model() or self._frozen_row is None:
            return
        
        row_height = self._frozen_row_sizes.get(
            self._frozen_row, self.rowHeight(self._frozen_row)
        )
        header_height = self._frozen_row_view.horizontalHeader().height()
        vp = self.viewport().geometry()
        x = vp.x()
        y = vp.y()
        w = vp.width()
        h = header_height + row_height
        
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
            self._frozen_row_view.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value()
            )
        except Exception:
            pass
    
    def _update_unpin_row_button(self):
        """Update position and visibility of unpin row button."""
        if (
            not hasattr(self, "_unpin_row_btn")
            or self._frozen_row is None
            or not self._frozen_row_view.isVisible()
        ):
            if hasattr(self, "_unpin_row_btn") and self._unpin_row_btn:
                self._unpin_row_btn.hide()
            return
        self._unpin_row_btn.show()
        self._unpin_row_btn.raise_()
        # Ensure button is above the frozen row view
        self._frozen_row_view.raise_()
        btn_x = max(2, self._frozen_row_view.width() - 32)
        btn_y = 2
        self._unpin_row_btn.move(btn_x, btn_y)
        # Make sure button is visible and enabled
        self._unpin_row_btn.setEnabled(True)
        self._unpin_row_btn.update()

