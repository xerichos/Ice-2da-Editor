# gui/styles.py

# ------------------------------------------------------------
# Base table normalization (safe)
# ------------------------------------------------------------
TABLE_VIEW_BASE = """
QTableView {
    outline: 0;
}
"""

# ------------------------------------------------------------
# Light theme
# ------------------------------------------------------------
LIGHT_STYLE = """
QWidget {
    background-color: #f8f9fa;
    color: #212529;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #dee2e6;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #f8f9fa;
    color: #495057;
    padding: 6px 12px;
    border: 1px solid #dee2e6;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #212529;
    border-bottom: 1px solid #ffffff;
}

QTabBar::tab:hover {
    background-color: #e9ecef;
}

"""

TABLE_LIGHT_STYLE = TABLE_VIEW_BASE + """
QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8f9fa;
    color: #212529;
    selection-background-color: #007bff;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #dee2e6;
    padding: 4px;
}

/* Pinned column (clearly visible, solid) */
QTableView#FrozenColumnView {
    background-color: #e6e9ee;
}
"""

# ------------------------------------------------------------
# Dark theme
# ------------------------------------------------------------
DARK_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #dddddd;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #444444;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #333333;
    color: #cccccc;
    padding: 6px 12px;
    border: 1px solid #444444;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #3c3f41;
    color: #ffffff;
    border-bottom: 1px solid #3c3f41;
}

QTabBar::tab:hover {
    background-color: #3a3a3a;
}

"""

TABLE_DARK_STYLE = TABLE_VIEW_BASE + """
QTableView {
    background-color: #2b2b2b;
    alternate-background-color: #252525;
    color: #e0e0e0;
    selection-background-color: #3c3f41;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #3a3a3a;
    color: #e0e0e0;
    border: 1px solid #444444;
    padding: 4px;
}

/* Pinned column (clearly visible, solid) */
QTableView#FrozenColumnView {
    background-color: #383838;
}
"""

# ------------------------------------------------------------
# Midnight theme
# ------------------------------------------------------------
MIDNIGHT_STYLE = """
QWidget {
    background-color: #0f0f23;
    color: #c8d6e5;
    font-size: 12px;
}

QTabWidget::pane {
    border: 1px solid #16213e;
    background-color: #0f0f23;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #8892b0;
    padding: 6px 12px;
    border: 1px solid #16213e;
    border-bottom: none;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0f3460;
    color: #e6f1ff;
    border-bottom: 1px solid #0f3460;
}

QTabBar::tab:hover {
    background-color: #16213e;
}

"""

TABLE_MIDNIGHT_STYLE = TABLE_VIEW_BASE + """
QTableView {
    background-color: #0f0f23;
    alternate-background-color: #1a1a2e;
    color: #c8d6e5;
    selection-background-color: #0f3460;
    selection-color: #e6f1ff;
}

QHeaderView::section {
    background-color: #16213e;
    color: #8892b0;
    border: 1px solid #0f3460;
    padding: 4px;
}

/* Pinned column (stronger contrast, still safe) */
QTableView#FrozenColumnView {
    background-color: #1d1d3f;
}
"""
