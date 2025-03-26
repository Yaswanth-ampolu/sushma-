"""
Collapsible sidebar module for the Spring Test App.
Contains the collapsible sidebar widget for displaying result details.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                           QPushButton, QHeaderView, QTableView, QSizePolicy, QGroupBox,
                           QTextEdit, QToolButton, QFrame, QStackedWidget, QScrollArea,
                           QComboBox, QFileDialog, QMessageBox, QMenu, QAction, QApplication)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

import pandas as pd
import json
from models.table_models import PandasModel
from utils.constants import FILE_FORMATS


class CollapsibleSidebar(QWidget):
    """Collapsible sidebar widget for results details."""
    
    # Define signals
    collapsed_changed = pyqtSignal(bool)  # Emitted when sidebar is collapsed/expanded
    
    def __init__(self, parent=None, export_service=None):
        """Initialize the collapsible sidebar.
        
        Args:
            parent: Parent widget.
            export_service: Export service for exporting sequences.
        """
        super().__init__(parent)
        
        # Store services
        self.export_service = export_service
        
        # Store current state
        self.is_collapsed = False
        self.default_width = 500
        self.collapsed_width = 40
        self.animation_duration = 200  # ms
        self.current_sequence = None
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Set up the UI
        self.init_ui()
        
        # Set up animations
        self.setup_animations()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout (horizontal)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create toggle button container (always visible)
        toggle_container = QFrame()
        toggle_container.setFrameShape(QFrame.NoFrame)
        toggle_container.setFixedWidth(40)
        toggle_container.setObjectName("SidebarToggleContainer")
        toggle_layout = QVBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 10, 0, 0)
        toggle_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        
        # Toggle/Menu button using menubutton.svg
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(QIcon("resources/menubutton.svg"))
        self.toggle_btn.setIconSize(QSize(24, 24))
        self.toggle_btn.setToolTip("Menu (Right-click) & Toggle Sidebar (Left-click)")
        self.toggle_btn.setFixedSize(30, 30)
        self.toggle_btn.setObjectName("SidebarToggleButton")
        # Click will show menu which includes toggle option
        self.toggle_btn.clicked.connect(self.on_toggle_btn_clicked)
        toggle_layout.addWidget(self.toggle_btn)
        
        # Add toggle container to main layout
        self.main_layout.addWidget(toggle_container)
        
        # Create content container
        self.content_container = QFrame()
        self.content_container.setFrameShape(QFrame.StyledPanel)
        self.content_container.setObjectName("SidebarContentContainer")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Results table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        
        # Results table label
        table_label = QLabel("Generated Test Sequence")
        table_label.setFont(QFont("Arial", 12, QFont.Bold))
        table_layout.addWidget(table_label)
        
        # Results table
        self.results_table = QTableView()
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSortingEnabled(True)
        table_layout.addWidget(self.results_table)
        
        table_tab.setLayout(table_layout)
        self.tab_widget.addTab(table_tab, "Sequence")
        
        # Parameters tab
        params_tab = QWidget()
        params_layout = QVBoxLayout()
        
        # Parameters label
        params_label = QLabel("Spring Parameters")
        params_label.setFont(QFont("Arial", 12, QFont.Bold))
        params_layout.addWidget(params_label)
        
        # Parameters display
        self.parameters_display = QTextEdit()
        self.parameters_display.setReadOnly(True)
        params_layout.addWidget(self.parameters_display)
        
        params_tab.setLayout(params_layout)
        self.tab_widget.addTab(params_tab, "Parameters")
        
        # JSON view tab
        json_tab = QWidget()
        json_layout = QVBoxLayout()
        
        # JSON label
        json_label = QLabel("JSON Representation")
        json_label.setFont(QFont("Arial", 12, QFont.Bold))
        json_layout.addWidget(json_label)
        
        # JSON display
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(QFont("Courier New", 10))
        json_layout.addWidget(self.json_display)
        
        json_tab.setLayout(json_layout)
        self.tab_widget.addTab(json_tab, "JSON")
        
        # Specifications tab placeholder - will be populated from MainWindow
        self.specs_tab = QWidget()
        self.specs_layout = QVBoxLayout(self.specs_tab)
        self.tab_widget.addTab(self.specs_tab, "Specifications")
        
        # Add tab widget to content layout
        content_layout.addWidget(self.tab_widget)
        
        # Add export controls
        if self.export_service:
            # Export group
            export_group = QGroupBox("Export Options")
            export_layout = QVBoxLayout()
            
            # Export format selection
            format_layout = QHBoxLayout()
            format_layout.addWidget(QLabel("Format:"))
            
            self.format_combo = QComboBox()
            for format_name in self.export_service.get_supported_formats():
                self.format_combo.addItem(format_name)
            format_layout.addWidget(self.format_combo)
            
            export_layout.addLayout(format_layout)
            
            # Export buttons
            export_btn_layout = QHBoxLayout()
            
            self.export_btn = QPushButton("Export Sequence")
            self.export_btn.clicked.connect(self.on_export_clicked)
            self.export_btn.setEnabled(False)  # Disabled until a sequence is available
            export_btn_layout.addWidget(self.export_btn)
            
            self.save_template_btn = QPushButton("Save as Template")
            self.save_template_btn.clicked.connect(self.on_save_template_clicked)
            self.save_template_btn.setEnabled(False)  # Disabled until a sequence is available
            export_btn_layout.addWidget(self.save_template_btn)
            
            export_layout.addLayout(export_btn_layout)
            
            export_group.setLayout(export_layout)
            content_layout.addWidget(export_group)
        
        # Add content container to main layout
        self.main_layout.addWidget(self.content_container)
        
        # Set default sizes
        self.setFixedWidth(self.default_width)
    
    def setup_animations(self):
        """Set up animations for collapsing/expanding."""
        # Width animation
        self.width_animation = QPropertyAnimation(self, b"sidebar_width")
        self.width_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.width_animation.setDuration(self.animation_duration)
        self.width_animation.finished.connect(self.on_animation_finished)
    
    def toggle_collapsed(self):
        """Toggle collapsed state."""
        if self.width_animation.state() == QPropertyAnimation.Running:
            return  # Don't toggle if animation is running
        
        self.is_collapsed = not self.is_collapsed
        
        # Start animation
        target_width = self.collapsed_width if self.is_collapsed else self.default_width
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(target_width)
        self.width_animation.start()
        
        # Hide content immediately when collapsing starts
        if self.is_collapsed:
            self.content_container.hide()
        
        # Emit signal
        self.collapsed_changed.emit(self.is_collapsed)
    
    def on_animation_finished(self):
        """Handle animation finished event."""
        # Show content when expansion is complete
        if not self.is_collapsed:
            self.content_container.show()
    
    # Property for animation
    def get_sidebar_width(self):
        """Get sidebar width for animation property."""
        return self.width()
    
    def set_sidebar_width(self, width):
        """Set sidebar width for animation property."""
        self.setFixedWidth(width)
    
    sidebar_width = pyqtProperty(int, get_sidebar_width, set_sidebar_width)
    
    def display_sequence(self, sequence):
        """Display a sequence in the sidebar.
        
        Args:
            sequence: TestSequence object.
        """
        # Store the sequence
        self.current_sequence = sequence
        
        # If the sidebar is collapsed, expand it
        if self.is_collapsed:
            self.toggle_collapsed()
        
        # Display in table
        df = pd.DataFrame(sequence.rows)
        model = PandasModel(df)
        self.results_table.setModel(model)
        
        # Update parameters display
        params_text = ""
        for key, value in sequence.parameters.items():
            # Skip timestamp and other metadata
            if key in ["Timestamp"]:
                continue
            params_text += f"<b>{key}:</b> {value}<br>"
        self.parameters_display.setHtml(params_text)
        
        # Update JSON display
        json_text = json.dumps(sequence.to_dict(), indent=2)
        self.json_display.setText(json_text)
        
        # Enable export buttons if they exist
        if hasattr(self, 'export_btn'):
            self.export_btn.setEnabled(True)
        if hasattr(self, 'save_template_btn'):
            self.save_template_btn.setEnabled(True)
        
        # Switch to sequence tab
        self.tab_widget.setCurrentIndex(0)
    
    def clear_display(self):
        """Clear the display."""
        # Clear table
        self.results_table.setModel(None)
        
        # Clear parameters display
        self.parameters_display.clear()
        
        # Clear JSON display
        self.json_display.clear()
        
        # Clear current sequence
        self.current_sequence = None
        
        # Disable export buttons if they exist
        if hasattr(self, 'export_btn'):
            self.export_btn.setEnabled(False)
        if hasattr(self, 'save_template_btn'):
            self.save_template_btn.setEnabled(False)
    
    def on_export_clicked(self):
        """Handle export button clicks."""
        # Check if a sequence is available
        if not self.current_sequence or not self.export_service:
            QMessageBox.warning(self, "No Sequence", "No test sequence available to export.")
            return
        
        # Get selected format
        format_name = self.format_combo.currentText()
        file_extension = FILE_FORMATS.get(format_name, ".csv")
        
        # Get file name from user
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Sequence", "", f"{format_name} Files (*{file_extension})"
        )
        
        if not file_name:
            return  # User cancelled
        
        # Add extension if not present
        if not file_name.endswith(file_extension):
            file_name += file_extension
        
        # Export the sequence
        success, error_msg = self.export_service.export_sequence(
            self.current_sequence, file_name, format_name
        )
        
        if success:
            QMessageBox.information(self, "Export Successful", f"Sequence exported to {file_name}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export sequence: {error_msg}")
    
    def on_save_template_clicked(self):
        """Handle save template button clicks."""
        # Check if a sequence is available
        if not self.current_sequence:
            QMessageBox.warning(self, "No Sequence", "No test sequence available to save as a template.")
            return
        
        # Not implemented yet
        QMessageBox.information(self, "Not Implemented", "This feature is not yet implemented.")
    
    def on_toggle_btn_clicked(self):
        """Handle toggle button clicks by toggling sidebar and showing context menu on right-click."""
        # Get mouse button from event
        modifiers = QApplication.keyboardModifiers()
        
        # If right-click or holding Ctrl key (for context menu)
        if QApplication.mouseButtons() & Qt.RightButton or modifiers & Qt.ControlModifier:
            # Create context menu
            menu = QMenu(self)
            
            # Add toggle sidebar action
            if self.is_collapsed:
                toggle_action = QAction("Expand Sidebar", self)
            else:
                toggle_action = QAction("Collapse Sidebar", self)
            toggle_action.triggered.connect(self.toggle_collapsed)
            menu.addAction(toggle_action)
            
            menu.addSeparator()
            
            # Add clear display action
            clear_action = QAction("Clear Display", self)
            clear_action.triggered.connect(self.clear_display)
            menu.addAction(clear_action)
            
            # Add export actions if export service exists and there's a sequence
            if self.export_service and self.current_sequence:
                menu.addSeparator()
                
                export_action = QAction("Quick Export (CSV)", self)
                export_action.triggered.connect(self.quick_export)
                menu.addAction(export_action)
                
                export_dialog_action = QAction("Export with Options...", self)
                export_dialog_action.triggered.connect(self.on_export_clicked)
                menu.addAction(export_dialog_action)
            
            # Show menu at button position
            pos = self.toggle_btn.mapToGlobal(self.toggle_btn.rect().bottomRight())
            menu.exec_(pos)
        else:
            # Direct toggle on left-click
            self.toggle_collapsed()
    
    def quick_export(self):
        """Quickly export the current sequence to CSV without dialog."""
        if not self.current_sequence or not self.export_service:
            return
        
        try:
            # Get a default filename based on timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"spring_sequence_{timestamp}.csv"
            
            # Use the documents folder as default location
            import os
            documents_path = os.path.expanduser("~/Documents")
            if not os.path.exists(documents_path):
                documents_path = os.path.expanduser("~")
            
            file_path = os.path.join(documents_path, default_filename)
            
            # Export the sequence
            success, error_msg = self.export_service.export_sequence(
                self.current_sequence, file_path, "CSV"
            )
            
            if success:
                QMessageBox.information(self, "Quick Export Successful", 
                                       f"Sequence exported to {file_path}")
            else:
                QMessageBox.critical(self, "Export Failed", 
                                    f"Failed to export sequence: {error_msg}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error during export: {str(e)}")

    def add_specifications_panel(self, specs_panel):
        """Add the specifications panel to the sidebar.
        
        Args:
            specs_panel: Specifications panel to add.
        """
        # Clear any existing widgets
        while self.specs_layout.count():
            item = self.specs_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Add the specifications panel
        self.specs_layout.addWidget(specs_panel)
        
        # Switch to the specifications tab (optional)
        self.tab_widget.setCurrentWidget(self.specs_tab) 