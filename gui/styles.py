# gui/styles.py

DARK_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #dddddd;
    font-size: 12px;
}

/* Menu bar */

QMenuBar {
    background-color: #2b2b2b;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
}

QMenuBar::item:selected {
    background: #3f3f3f; /* hover/active highlight */
}

QMenuBar::item:pressed {
    background: #505050;
}

/* Menus */

QMenu {
    background-color: #2b2b2b;
    color: #dddddd;
    border: 1px solid #444444;
}

QMenu::item {
    padding: 4px 20px 4px 24px;
}

QMenu::item:selected {
    background-color: #3f3f3f; /* hover highlight in menus */
}

QMenu::item:pressed {
    background-color: #505050;
}

/* Tabs */

QTabWidget::pane {
    border: 1px solid #444444;
    top: -1px;
}

QTabBar::tab {
    background: #333333;
    color: #dddddd;
    padding: 4px 10px;
    margin-right: 1px;
}

QTabBar::tab:selected {
    background: #505050;  /* selected tab */
    color: #ffffff;
}

QTabBar::tab:hover {
    background: #3f3f3f;  /* hover tab */
}

/* Line edits, combos, text edits */

QLineEdit, QComboBox, QTextEdit {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
}

/* Buttons */

QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    padding: 4px 8px;
}

QPushButton:hover {
    background-color: #444444;
}

QPushButton:pressed {
    background-color: #555555;
}

/* Scrollbars */

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
}

/* Dialogs */

QDialog {
    background-color: #2b2b2b;
}
"""

TABLE_DARK_STYLE = """
QTableWidget {
    background-color: #2b2b2b;
    alternate-background-color: #252525;
    color: #e0e0e0;
    gridline-color: #444444;
    selection-background-color: #3c3f41;
    selection-color: #ffffff;
}

QTableWidget::item {
    background-color: #2b2b2b;
    color: #e0e0e0;
}

QTableWidget::item:alternate {
    background-color: #242424;
}

QTableWidget::item:selected {
    background-color: #3c3f41;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #444444;
}
"""
