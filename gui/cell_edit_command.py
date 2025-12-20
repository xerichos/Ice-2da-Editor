from PyQt5.QtWidgets import QUndoCommand
from PyQt5.QtCore import Qt
from typing import List, Tuple


class CellEditCommand(QUndoCommand):
    def __init__(self, document, row, col, old_text, new_text):
        super().__init__(f"Edit Cell ({row}, {col})")

        self.document = document
        self.model = document.model
        self.row = row
        self.col = col
        self.old_text = old_text
        self.new_text = new_text

    def undo(self):
        self.model.set_cell(
            self.row,
            self.col,
            self.old_text,
            emit_edit_signal=False
        )
        self._mark_dirty()

    def redo(self):
        self.model.set_cell(
            self.row,
            self.col,
            self.new_text,
            emit_edit_signal=False
        )
        self._mark_dirty()

    def _mark_dirty(self):
        self.document.is_dirty = True
        mw = self.document.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self.document)


class MultiCellClearCommand(QUndoCommand):
    """Command for clearing multiple selected cells."""

    def __init__(self, document, cells_to_clear: List[Tuple[int, int]]):
        super().__init__(f"Clear {len(cells_to_clear)} Cells")

        self.document = document
        self.model = document.model
        self.cells_to_clear = cells_to_clear
        self.old_values = []  # List of (row, col, old_value)

        # Capture old values
        for row, col in self.cells_to_clear:
            old_value = self.model.data(self.model.index(row, col), Qt.DisplayRole)
            if old_value is None:
                old_value = ""
            self.old_values.append((row, col, str(old_value)))

    def undo(self):
        for row, col, old_value in self.old_values:
            self.model.set_cell(row, col, old_value, emit_edit_signal=False)
        self._mark_dirty()

    def redo(self):
        for row, col, _ in self.old_values:
            self.model.set_cell(row, col, "", emit_edit_signal=False)
        self._mark_dirty()

    def _mark_dirty(self):
        self.document.is_dirty = True
        mw = self.document.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self.document)


class MultiCellFillCommand(QUndoCommand):
    """Command for filling multiple selected cells with a value."""

    def __init__(self, document, cells_to_fill: List[Tuple[int, int]], fill_value: str):
        super().__init__(f"Fill {len(cells_to_fill)} Cells with '{fill_value}'")

        self.document = document
        self.model = document.model
        self.cells_to_fill = cells_to_fill
        self.fill_value = fill_value
        self.old_values = []  # List of (row, col, old_value)

        # Capture old values
        for row, col in self.cells_to_fill:
            old_value = self.model.data(self.model.index(row, col), Qt.DisplayRole)
            if old_value is None:
                old_value = ""
            self.old_values.append((row, col, str(old_value)))

    def undo(self):
        for row, col, old_value in self.old_values:
            self.model.set_cell(row, col, old_value, emit_edit_signal=False)
        self._mark_dirty()

    def redo(self):
        for row, col, _ in self.old_values:
            self.model.set_cell(row, col, self.fill_value, emit_edit_signal=False)
        self._mark_dirty()

    def _mark_dirty(self):
        self.document.is_dirty = True
        mw = self.document.window()
        if mw and hasattr(mw, "update_tab_title"):
            mw.update_tab_title(self.document)


