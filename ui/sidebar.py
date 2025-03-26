"""
Sidebar module for the Spring Test App.
Contains the sidebar widget for API key and command reference.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QTableView, QHeaderView, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from utils.constants import COMMANDS
from models.table_models import CommandTableModel


class SidebarWidget(QWidget):
    """Sidebar widget for the Spring Test App."""
    
    # Define signals
    api_key_changed = pyqtSignal(str)
    clear_chat_clicked = pyqtSignal()
    
    def __init__(self, settings_service):
        """Initialize the sidebar widget.
        
        Args:
            settings_service: Settings service.
        """
        super().__init__()
        
        # Store settings service
        self.settings_service = settings_service
        
        # Set up the UI
        self.init_ui()
        
        # Load settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel("Spring Test App")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Settings group box
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()
        
        # API key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        settings_layout.addRow("API Key:", self.api_key_input)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Command reference
        cmd_label = QLabel("Command Reference")
        cmd_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(cmd_label)
        
        # Command reference table
        self.cmd_table = QTableView()
        self.cmd_table.setModel(CommandTableModel(COMMANDS))
        self.cmd_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Make the table sortable
        self.cmd_table.setSortingEnabled(True)
        
        # Set a reasonable height
        self.cmd_table.setMinimumHeight(300)
        
        layout.addWidget(self.cmd_table)
        
        # Action buttons
        self.clear_chat_btn = QPushButton("Clear Chat")
        self.clear_chat_btn.clicked.connect(self.clear_chat_clicked)
        layout.addWidget(self.clear_chat_btn)
        
        # Add some stretch to push everything up
        layout.addStretch()
        
        # Set the layout
        self.setLayout(layout)
        
        # Set a fixed width for the sidebar
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
    
    def load_settings(self):
        """Load settings from the settings service."""
        # Don't load API key by default to avoid consuming credits
        # Let user enter it manually when needed
        self.api_key_input.setText("")
    
    def on_api_key_changed(self, api_key):
        """Handle API key changes.
        
        Args:
            api_key: New API key.
        """
        # Update settings
        self.settings_service.set_api_key(api_key)
        
        # Emit signal
        self.api_key_changed.emit(api_key) 