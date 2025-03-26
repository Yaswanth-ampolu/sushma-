"""
Chat results container module for the Spring Test App.
Contains a widget that combines the chat panel with a collapsible sidebar for results.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.chat_panel import ChatPanel
from ui.collapsible_sidebar import CollapsibleSidebar


class ChatResultsContainer(QWidget):
    """Container widget that combines the chat panel with a collapsible sidebar for results."""
    
    # Define signals
    sequence_generated = pyqtSignal(object)  # TestSequence object
    
    def __init__(self, chat_service, sequence_generator, export_service):
        """Initialize the chat results container.
        
        Args:
            chat_service: Chat service.
            sequence_generator: Sequence generator service.
            export_service: Export service.
        """
        super().__init__()
        
        # Store services
        self.chat_service = chat_service
        self.sequence_generator = sequence_generator
        self.export_service = export_service
        
        # Set object name for styling
        self.setObjectName("ChatPanelWithSidebar")
        
        # Set up the UI
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create chat panel
        self.chat_panel = ChatPanel(self.chat_service, self.sequence_generator)
        self.chat_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create sidebar for results
        self.sidebar = CollapsibleSidebar(export_service=self.export_service)
        
        # Add widgets to layout
        layout.addWidget(self.chat_panel, 1)  # Chat panel with stretch factor
        layout.addWidget(self.sidebar, 0)     # Sidebar without stretch (will maintain own width)
    
    def connect_signals(self):
        """Connect signals from child components."""
        # Connect chat panel signals
        self.chat_panel.sequence_generated.connect(self.on_sequence_generated)
        
        # Connect sidebar signals
        self.sidebar.collapsed_changed.connect(self.on_sidebar_collapsed_changed)
    
    def on_sequence_generated(self, sequence):
        """Handle sequence generation.
        
        Args:
            sequence: TestSequence object.
        """
        # Display sequence in sidebar
        self.sidebar.display_sequence(sequence)
        
        # Re-emit signal
        self.sequence_generated.emit(sequence)
    
    def on_sidebar_collapsed_changed(self, is_collapsed):
        """Handle sidebar collapsed state changes.
        
        Args:
            is_collapsed: Whether the sidebar is collapsed.
        """
        # Adjust layout as needed
        # (No specific layout adjustments needed currently)
        pass
    
    def refresh_chat_display(self):
        """Refresh the chat display."""
        self.chat_panel.refresh_chat_display()
    
    def validate_api_key(self):
        """Validate the API key."""
        return self.chat_panel.validate_api_key()
    
    def clear_displays(self):
        """Clear all displays."""
        self.chat_panel.refresh_chat_display()
        self.sidebar.clear_display() 