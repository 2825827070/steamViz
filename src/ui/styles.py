DARK_THEME = """
QMainWindow, QWidget {
    background-color: transparent;
}

#main_central_widget {
    background-color: #18181b;
    color: #fafafa;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    border-radius: 8px;
}

#sidebar {
    background-color: #09090b;
    border-right: 1px solid rgba(255,255,255,0.06);
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    min-width: 180px;
    max-width: 180px;
}

#nav_tree {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 8px;
}

#nav_tree::item {
    color: #71717a;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 1px 0px;
    font-size: 13px;
}

#nav_tree::item:hover {
    background-color: rgba(255, 255, 255, 0.04);
    color: #a1a1aa;
}

#nav_tree::item:selected {
    background-color: rgba(59, 130, 246, 0.12);
    color: #60a5fa;
    font-weight: 500;
}

#content_area {
    background-color: transparent;
}

.stat-card {
    background: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 6px;
}

.stat-card:hover {
    border: 1px solid rgba(255, 255, 255, 0.1);
}

QPushButton {
    background: #3b82f6;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 7px 18px;
    font-size: 13px;
}

QPushButton:hover {
    background: #2563eb;
}

QPushButton:pressed {
    background: #1d4ed8;
}

QPushButton:disabled {
    background: #3f3f46;
    color: #71717a;
}

QLineEdit {
    background-color: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 7px 12px;
    color: #fafafa;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #3b82f6;
}

QComboBox {
    background-color: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 6px 12px;
    color: #fafafa;
    min-width: 100px;
}

QComboBox:hover {
    border-color: rgba(255, 255, 255, 0.12);
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    color: #fafafa;
    selection-background-color: rgba(59, 130, 246, 0.15);
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.2);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(255, 255, 255, 0.2);
}

QStatusBar {
    background-color: transparent;
    color: #52525b;
    border-top: 1px solid rgba(255,255,255,0.05);
    font-size: 11px;
}

QTableWidget {
    background-color: #18181b;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    color: #fafafa;
    selection-background-color: rgba(59, 130, 246, 0.15);
}

QHeaderView::section {
    background-color: #27272a;
    color: #71717a;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px;
}

QMessageBox {
    background-color: #18181b;
}

QMessageBox QLabel {
    color: #fafafa;
    font-size: 14px;
}

QProgressBar {
    background-color: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 4px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}

QSpinBox {
    background-color: #27272a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 6px 10px;
    color: #fafafa;
}

QSpinBox:focus {
    border-color: #3b82f6;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    border: none;
    width: 20px;
}

QTextEdit {
    background-color: #09090b;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    color: #a1a1aa;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: transparent;
}

#main_central_widget {
    background-color: #fafafa;
    color: #18181b;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    border-radius: 8px;
}

#sidebar {
    background-color: #f4f4f5;
    border-right: 1px solid rgba(0,0,0,0.06);
    border-top-left-radius: 8px;
    border-bottom-left-radius: 8px;
    min-width: 180px;
    max-width: 180px;
}

#nav_tree {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 8px;
}

#nav_tree::item {
    color: #71717a;
    padding: 8px 12px;
    border-radius: 6px;
    margin: 1px 0px;
    font-size: 13px;
}

#nav_tree::item:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: #52525b;
}

#nav_tree::item:selected {
    background-color: rgba(59, 130, 246, 0.1);
    color: #2563eb;
    font-weight: 500;
}

#content_area {
    background-color: transparent;
}

.stat-card {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 6px;
}

.stat-card:hover {
    border: 1px solid rgba(0, 0, 0, 0.1);
}

QPushButton {
    background: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 7px 18px;
    font-size: 13px;
}

QPushButton:hover {
    background: #1d4ed8;
}

QPushButton:pressed {
    background: #1e40af;
}

QPushButton:disabled {
    background: #e4e4e7;
    color: #a1a1aa;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 5px;
    padding: 7px 12px;
    color: #18181b;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #2563eb;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 5px;
    padding: 6px 12px;
    color: #18181b;
    min-width: 100px;
}

QComboBox:hover {
    border-color: rgba(0, 0, 0, 0.12);
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 5px;
    color: #18181b;
    selection-background-color: rgba(59, 130, 246, 0.1);
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.25);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-width: 24px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(0, 0, 0, 0.25);
}

QStatusBar {
    background-color: transparent;
    color: #a1a1aa;
    border-top: 1px solid rgba(0,0,0,0.05);
    font-size: 11px;
}

QTableWidget {
    background-color: #fafafa;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 6px;
    color: #18181b;
    selection-background-color: rgba(59, 130, 246, 0.1);
}

QHeaderView::section {
    background-color: #f4f4f5;
    color: #71717a;
    border: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
    padding: 8px;
}

QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #18181b;
    font-size: 14px;
}

QProgressBar {
    background-color: #e4e4e7;
    border: 1px solid rgba(0, 0, 0, 0.05);
    border-radius: 4px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 3px;
}

QSpinBox {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 5px;
    padding: 6px 10px;
    color: #18181b;
}

QSpinBox:focus {
    border-color: #2563eb;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    border: none;
    width: 20px;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 6px;
    color: #52525b;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}
"""