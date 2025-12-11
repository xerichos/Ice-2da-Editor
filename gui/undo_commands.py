from PyQt5.QtWidgets import QUndoCommand

class CellEditCommand(QUndoCommand):
    def __init__(self, table, row, col, old_text, new_text):
        super().__init__(f"Edit Cell ({row}, {col})")
        self.table = table
        self.row = row
        self.col = col
        self.old = old_text
        self.new = new_text

    def undo(self):
        item = self.table.item(self.row, self.col)
        if item:
            self.table._suspend_dirty = True
            item.setText(self.old)
            self.table._suspend_dirty = False
            self.table.window().is_dirty = True
            self.table.window().update_window_title()

    def redo(self):
        item = self.table.item(self.row, self.col)
        if item:
            self.table._suspend_dirty = True
            item.setText(self.new)
            self.table._suspend_dirty = False
            self.table.window().is_dirty = True
            self.table.window().update_window_title()
