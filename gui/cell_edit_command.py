from PyQt5.QtWidgets import QUndoCommand


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
