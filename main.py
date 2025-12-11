import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# --- Global Exception Handler ----------------------------------------------

def global_exception_hook(exc_type, exc_value, exc_traceback):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    app = QApplication.instance()

    # Only show QMessageBox if QApplication already exists
    if app is not None:
        dlg = QMessageBox()
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Unhandled Error")
        dlg.setText(f"An unexpected error occurred:\n\n{exc_value}")
        dlg.setDetailedText(tb)
        dlg.exec_()
    else:
        # QApplication not created yet — fallback to stderr
        print("Unhandled exception before QApplication was created:", file=sys.stderr)
        print(tb, file=sys.stderr)

    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_hook

# --- Application Start -----------------------------------------------------

from gui.styles import DARK_STYLE, TABLE_DARK_STYLE
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE + TABLE_DARK_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
