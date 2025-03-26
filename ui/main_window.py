"""
Main window module for the Spring Test App.
Contains the main window class and initialization.
"""
import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QMessageBox, QApplication, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from utils.constants import APP_TITLE, APP_VERSION, APP_WINDOW_SIZE
from models.data_models import TestSequence

# These will be implemented in separate files
from ui.chat_results_container import ChatResultsContainer
from ui.specifications_panel import SpecificationsPanel


class MainWindow(QMainWindow):
    """Main window for the Spring Test App."""
    
    def __init__(self, settings_service, sequence_generator, chat_service, export_service):
        """Initialize the main window.
        
        Args:
            settings_service: Settings service.
            sequence_generator: Sequence generator service.
            chat_service: Chat service.
            export_service: Export service.
        """
        super().__init__()
        
        # Store services
        self.settings_service = settings_service
        self.sequence_generator = sequence_generator
        self.chat_service = chat_service
        self.export_service = export_service
        
        # Set up the UI
        self.init_ui()
        
        # Set up signals and slots
        self.connect_signals()
        
    def init_ui(self):
        """Initialize the UI."""
        # Set window properties
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        self.setGeometry(100, 100, *APP_WINDOW_SIZE)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create the central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create content panels
        self.chat_results_container = ChatResultsContainer(
            self.chat_service, 
            self.sequence_generator,
            self.export_service
        )
        self.specs_panel = SpecificationsPanel(
            self.settings_service, 
            self.sequence_generator, 
            self.chat_service
        )
        
        # Add specifications panel to the sidebar
        self.chat_results_container.sidebar.add_specifications_panel(self.specs_panel)
        
        # Add chat results container to main layout
        main_layout.addWidget(self.chat_results_container)
        
        # Set the central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Apply theme
        self.apply_theme()
    
    def connect_signals(self):
        """Connect signals and slots."""
        # Connect chat results container signals
        self.chat_results_container.sequence_generated.connect(self.on_sequence_generated)
        
        # Connect specifications panel signals
        self.specs_panel.specifications_changed.connect(self.on_specifications_changed)
        self.specs_panel.api_key_changed.connect(self.on_api_key_changed)
        self.specs_panel.clear_chat_clicked.connect(self.on_clear_chat)
    
    def on_api_key_changed(self, api_key):
        """Handle API key changes.
        
        Args:
            api_key: New API key.
        """
        # Update the API key in the sequence generator
        self.sequence_generator.set_api_key(api_key)
        
        # Only validate the API key if it's not empty
        if api_key.strip():
            # Validate the API key
            self.chat_results_container.validate_api_key()
    
    def on_clear_chat(self):
        """Handle clear chat button clicks."""
        # Clear chat history
        self.chat_service.clear_history()
        
        # Update chat panel
        self.chat_results_container.refresh_chat_display()
    
    def on_sequence_generated(self, sequence):
        """Handle sequence generation.
        
        Args:
            sequence: Generated sequence.
        """
        # The sequence is already displayed in the sidebar
        # No need to do anything here
        pass
    
    def on_specifications_changed(self, specifications):
        """Handle specifications changes.
        
        Args:
            specifications: New specifications.
        """
        # The sequence generator is already updated by the specifications panel,
        # so we don't need to do anything here.
        pass
    
    def apply_theme(self):
        """Apply the theme."""
        from ui.styles import apply_theme
        apply_theme(self)
    
    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Save settings
        self.settings_service.save_settings()
        
        # Save chat history
        self.chat_service.save_history()
        
        # Accept the event
        event.accept()


def create_main_window(settings_service, sequence_generator, chat_service, export_service):
    """Create and configure the main window.
    
    Args:
        settings_service: Settings service.
        sequence_generator: Sequence generator service.
        chat_service: Chat service.
        export_service: Export service.
        
    Returns:
        Configured MainWindow instance.
    """
    # Create the main window
    window = MainWindow(
        settings_service=settings_service,
        sequence_generator=sequence_generator,
        chat_service=chat_service,
        export_service=export_service
    )
    
    # Configure window (maximize, etc.)
    window.show()
    
    return window 