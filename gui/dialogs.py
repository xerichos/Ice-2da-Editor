# gui/dialogs.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QDialogButtonBox, QComboBox
)

class SearchReplaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pattern = QLineEdit()
        self.replacement = QLineEdit()
        self.case = QCheckBox("Match case")
        self.whole = QCheckBox("Whole word")

        layout = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Find:"))
        row1.addWidget(self.pattern)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Replace:"))
        row2.addWidget(self.replacement)
        layout.addLayout(row2)

        layout.addWidget(self.case)
        layout.addWidget(self.whole)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def values(self):
        return {
            "pattern": self.pattern.text(),
            "replacement": self.replacement.text(),
            "match_case": self.case.isChecked(),
            "whole_word": self.whole.isChecked()
        }
