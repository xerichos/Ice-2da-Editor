# gui/styles.py

# Light Theme
LIGHT_STYLE = """
QWidget {
    background-color: #f8f9fa;
    color: #212529;
    font-size: 12px;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #dee2e6;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
    color: #212529;
}

QMenuBar::item:selected {
    background: #e9ecef;
}

QMenuBar::item:pressed {
    background: #dee2e6;
}

QMenu {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #dee2e6;
}

QMenu::item {
    padding: 4px 20px 4px 24px;
    color: #212529;
}

QMenu::item:selected {
    background-color: #e9ecef;
}

QMenu::item:pressed {
    background-color: #dee2e6;
}

QTabWidget::pane {
    border: 1px solid #dee2e6;
    top: -1px;
}

QTabBar::tab {
    background: #f8f9fa;
    color: #6c757d;
    padding: 4px 10px;
    margin-right: 1px;
    border: 1px solid #dee2e6;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #212529;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:hover {
    background: #e9ecef;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #ffffff;
    color: #212529;
    border: 1px solid #ced4da;
    padding: 2px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    padding: 4px 8px;
    color: #212529;
}

QPushButton:hover {
    background-color: #e9ecef;
}

QPushButton:pressed {
    background-color: #dee2e6;
}

QScrollBar:vertical {
    background-color: #f8f9fa;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #adb5bd;
    border-radius: 2px;
}

QScrollBar:horizontal {
    background-color: #f8f9fa;
    height: 18px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #adb5bd;
    border-radius: 2px;
}

QDialog {
    background-color: #f8f9fa;
}
"""

# Dark Theme (Default)
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
    height: 18px;
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

# Midnight Theme (Fancy dark theme with blues and purples)
MIDNIGHT_STYLE = """
QWidget {
    background-color: #0f0f23;
    color: #c8d6e5;
    font-size: 12px;
}

QMenuBar {
    background-color: #1a1a2e;
    border-bottom: 1px solid #16213e;
}

QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
    color: #c8d6e5;
}

QMenuBar::item:selected {
    background: #16213e;
}

QMenuBar::item:pressed {
    background: #0f3460;
}

QMenu {
    background-color: #1a1a2e;
    color: #c8d6e5;
    border: 1px solid #16213e;
}

QMenu::item {
    padding: 4px 20px 4px 24px;
    color: #c8d6e5;
}

QMenu::item:selected {
    background-color: #16213e;
}

QMenu::item:pressed {
    background-color: #0f3460;
}

QTabWidget::pane {
    border: 1px solid #16213e;
    top: -1px;
}

QTabBar::tab {
    background: #1a1a2e;
    color: #8892b0;
    padding: 4px 10px;
    margin-right: 1px;
    border: 1px solid #16213e;
}

QTabBar::tab:selected {
    background: #0f3460;
    color: #e6f1ff;
    border-bottom: 1px solid #0f3460;
}

QTabBar::tab:hover {
    background: #16213e;
}

QLineEdit, QComboBox, QTextEdit {
    background-color: #1a1a2e;
    color: #c8d6e5;
    border: 1px solid #16213e;
    padding: 2px;
}

QPushButton {
    background-color: #1a1a2e;
    border: 1px solid #16213e;
    padding: 4px 8px;
    color: #c8d6e5;
}

QPushButton:hover {
    background-color: #16213e;
}

QPushButton:pressed {
    background-color: #0f3460;
}

QScrollBar:vertical {
    background-color: #0f0f23;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #16213e;
    border-radius: 2px;
}

QScrollBar:horizontal {
    background-color: #0f0f23;
    height: 18px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #16213e;
    border-radius: 2px;
}

QDialog {
    background-color: #0f0f23;
}
"""

# Light Table Style
TABLE_LIGHT_STYLE = """
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    color: #212529;
    gridline-color: #dee2e6;
    selection-background-color: #007bff;
    selection-color: #ffffff;
}

QTableWidget::item {
    background-color: #ffffff;
    color: #212529;
}

QTableWidget::item:alternate {
    background-color: #f8f9fa;
}

QTableWidget::item:selected {
    background-color: #007bff;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #dee2e6;
    padding: 4px;
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

# Midnight Table Style
TABLE_MIDNIGHT_STYLE = """
QTableWidget {
    background-color: #0f0f23;
    alternate-background-color: #1a1a2e;
    color: #c8d6e5;
    gridline-color: #16213e;
    selection-background-color: #0f3460;
    selection-color: #e6f1ff;
}

QTableWidget::item {
    background-color: #0f0f23;
    color: #c8d6e5;
}

QTableWidget::item:alternate {
    background-color: #1a1a2e;
}

QTableWidget::item:selected {
    background-color: #0f3460;
    color: #e6f1ff;
}

QHeaderView::section {
    background-color: #16213e;
    color: #8892b0;
    border: 1px solid #0f3460;
    padding: 4px;
}
"""
