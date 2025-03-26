"""
Styles module for the Spring Test App.
Contains style sheets and theming functions.
"""

# Application style sheet
APP_STYLE = """
QWidget {
    background-color: #F0F0F0;
    color: #333333;
    font-family: Arial, sans-serif;
}

QMainWindow {
    background-color: #F0F0F0;
}

QLabel {
    color: #333333;
}

QGroupBox {
    border: 1px solid #CCCCCC;
    border-radius: 5px;
    margin-top: 1ex;
    padding: 10px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
    color: #555555;
}

QPushButton {
    background-color: #4285F4;
    color: white;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5294FF;
}

QPushButton:pressed {
    background-color: #3060C0;
}

QPushButton:disabled {
    background-color: #AAAAAA;
    color: #DDDDDD;
}

QLineEdit, QTextEdit {
    background-color: white;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px;
}

QTextEdit {
    background-color: white;
}

QTableView {
    background-color: white;
    alternate-background-color: #F9F9F9;
    selection-background-color: #D0D9EA;
    selection-color: #333333;
    border: 1px solid #CCCCCC;
}

QHeaderView::section {
    background-color: #EEEEEE;
    color: #333333;
    padding: 4px;
    border: 1px solid #CCCCCC;
    font-weight: bold;
}

QComboBox {
    background-color: white;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 4px 4px 4px 8px;
    min-width: 6em;
}

QComboBox:hover {
    border: 1px solid #AAAAAA;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid #CCCCCC;
}

QTabWidget::pane {
    border: 1px solid #CCCCCC;
    background-color: white;
}

QTabBar::tab {
    background-color: #E8E8E8;
    border: 1px solid #CCCCCC;
    border-bottom-color: #CCCCCC;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 10px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom-color: white;
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

QProgressBar {
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    text-align: center;
    background-color: white;
}

QProgressBar::chunk {
    background-color: #4285F4;
    width: 20px;
}

QScrollBar:vertical {
    border: 1px solid #CCCCCC;
    background: white;
    width: 15px;
    margin: 22px 0 22px 0;
}

QScrollBar::handle:vertical {
    background: #AAAAAA;
    min-height: 20px;
}

QScrollBar::add-line:vertical {
    border: 1px solid #CCCCCC;
    background: #E1E1E1;
    height: 20px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical {
    border: 1px solid #CCCCCC;
    background: #E1E1E1;
    height: 20px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}

QCheckBox {
    spacing: 5px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}

/* Settings section styling */
QGroupBox#SettingsGroup {
    margin-top: 15px;
    margin-bottom: 10px;
}

QPushButton#ClearChatBtn {
    background-color: #F44336;
}

QPushButton#ClearChatBtn:hover {
    background-color: #FF5252;
}

QPushButton#ClearChatBtn:pressed {
    background-color: #D32F2F;
}

/* Main tab widget styling */
QTabWidget#MainTabs::pane {
    border: none;
    background-color: #F0F0F0;
}

/* Chat and results panel styling */
QWidget#ChatResultsPanel {
    background-color: #FFFFFF;
    border-radius: 5px;
}

/* Collapsible Sidebar Styling */
QWidget#SidebarToggleContainer {
    background-color: #E0E0E0;
    border-right: 1px solid #CCCCCC;
}

QToolButton#SidebarToggleButton {
    background-color: #4285F4;
    border-radius: 15px;
    border: none;
    color: white;
    padding: 4px;
}

QToolButton#SidebarToggleButton:hover {
    background-color: #5294FF;
}

QToolButton#SidebarToggleButton:pressed {
    background-color: #3060C0;
}

QMenu {
    background-color: white;
    border: 1px solid #CCCCCC;
    padding: 5px;
}

QMenu::item {
    padding: 5px 25px 5px 20px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #E0E0FF;
    color: #333333;
}

QMenu::separator {
    height: 1px;
    background-color: #CCCCCC;
    margin: 5px 10px;
}

QFrame#SidebarContentContainer {
    background-color: #FFFFFF;
    border-left: 1px solid #CCCCCC;
}

/* Chat panel with sidebar */
QWidget#ChatPanelWithSidebar {
    background-color: #F0F0F0;
}
"""

def get_style_sheet():
    """Get the application style sheet.
    
    Returns:
        The application style sheet.
    """
    return APP_STYLE

def apply_theme(widget):
    """Apply the theme to a widget.
    
    Args:
        widget: The widget to apply the theme to.
    """
    widget.setStyleSheet(get_style_sheet()) 