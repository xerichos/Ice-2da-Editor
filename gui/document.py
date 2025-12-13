# gui/document.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QUndoStack
from .table_view import TwoDATable
from .table_model import TwoDATableModel

class TwoDADocument(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.table = TwoDATable()
        self.model = TwoDATableModel(self)
        self.table.setModel(self.model)

        self.undo_stack = QUndoStack(self)
        self.current_path = None
        self.current_data = None
        self.is_dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
