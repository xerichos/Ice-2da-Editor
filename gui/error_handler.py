# error_handler.py
import traceback
from PyQt5.QtWidgets import QMessageBox

def show_error(message: str, exc: Exception = None):
    text = message
    if exc:
        text += "\n\n--- Exception ---\n" + repr(exc)
        text += "\n\n--- Traceback ---\n" + traceback.format_exc()

    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle("Error")
    box.setText(text)
    box.exec_()
