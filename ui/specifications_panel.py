"""
Specifications panel module for the Spring Test App.
Contains the specifications panel for entering and editing spring specifications.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                           QFormLayout, QGroupBox, QPushButton, QScrollArea, 
                           QTabWidget, QComboBox, QDoubleSpinBox, QCheckBox,
                           QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTextEdit,
                           QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import re
import os
import logging

# Import PyPDF2 for PDF parsing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("PyPDF2 not installed. PDF import feature will be disabled.")

from models.data_models import SpringSpecification, SetPoint


class SetPointWidget(QGroupBox):
    """Widget for editing a single set point."""
    
    # Define signals
    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)  # self
    
    def __init__(self, set_point, index):
        """Initialize the set point widget.
        
        Args:
            set_point: Set point to edit.
            index: Index of the set point.
        """
        super().__init__(f"Set Point {index + 1}")
        
        self.set_point = set_point
        self.index = index
        
        # Set up the UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Use a more compact layout
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(5)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Position input
        self.position_input = QDoubleSpinBox()
        self.position_input.setRange(0, 500)
        self.position_input.setValue(self.set_point.position_mm)
        self.position_input.setSuffix(" mm")
        self.position_input.setDecimals(2)
        self.position_input.valueChanged.connect(self.on_position_changed)
        form_layout.addRow("Position:", self.position_input)
        
        # Load input
        self.load_input = QDoubleSpinBox()
        self.load_input.setRange(0, 1000)
        self.load_input.setValue(self.set_point.load_n)
        self.load_input.setSuffix(" N")
        self.load_input.setDecimals(2)
        self.load_input.valueChanged.connect(self.on_load_changed)
        form_layout.addRow("Load:", self.load_input)
        
        # Tolerance input
        self.tolerance_input = QDoubleSpinBox()
        self.tolerance_input.setRange(0, 100)
        self.tolerance_input.setValue(self.set_point.tolerance_percent)
        self.tolerance_input.setSuffix(" %")
        self.tolerance_input.setDecimals(1)
        self.tolerance_input.valueChanged.connect(self.on_tolerance_changed)
        form_layout.addRow("Tolerance:", self.tolerance_input)
        
        layout.addLayout(form_layout)
        
        # Controls in a horizontal layout
        controls_layout = QHBoxLayout()
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(self.set_point.enabled)
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        controls_layout.addWidget(self.enabled_checkbox)
        
        # Add spacer
        controls_layout.addStretch()
        
        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setMaximumWidth(80)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        controls_layout.addWidget(self.delete_button)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def on_position_changed(self, value):
        """Handle position changes.
        
        Args:
            value: New position value.
        """
        self.set_point.position_mm = value
        self.changed.emit()
    
    def on_load_changed(self, value):
        """Handle load changes.
        
        Args:
            value: New load value.
        """
        self.set_point.load_n = value
        self.changed.emit()
    
    def on_tolerance_changed(self, value):
        """Handle tolerance changes.
        
        Args:
            value: New tolerance value.
        """
        self.set_point.tolerance_percent = value
        self.changed.emit()
    
    def on_enabled_changed(self, state):
        """Handle enabled state changes.
        
        Args:
            state: New enabled state.
        """
        self.set_point.enabled = (state == Qt.Checked)
        self.changed.emit()
    
    def on_delete_clicked(self):
        """Handle delete button clicks."""
        self.delete_requested.emit(self)
    
    def update_index(self, new_index):
        """Update the set point index.
        
        Args:
            new_index: New index.
        """
        self.index = new_index
        self.setTitle(f"Set Point {new_index + 1}")


class SpecificationsPanel(QWidget):
    """Panel for entering and editing spring specifications."""
    
    # Define signals
    specifications_changed = pyqtSignal(object)  # SpringSpecification
    api_key_changed = pyqtSignal(str)  # API Key
    clear_chat_clicked = pyqtSignal()  # Clear chat
    
    def __init__(self, settings_service, sequence_generator, chat_service=None):
        """Initialize the specifications panel.
        
        Args:
            settings_service: Settings service.
            sequence_generator: Sequence generator service.
            chat_service: Chat service (optional).
        """
        super().__init__()
        
        # Store services
        self.settings_service = settings_service
        self.sequence_generator = sequence_generator
        self.chat_service = chat_service
        
        # Store specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Store set point widgets
        self.set_point_widgets = []
        
        # Auto-update flag
        self.auto_update_enabled = False
        
        # Set up the UI
        self.init_ui()
        
        # Load specifications
        self.load_specifications()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Spring Specifications")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Tabs
        tabs = QTabWidget()
        
        # Combined Info & Set Points tab
        combined_tab = QWidget()
        combined_layout = QVBoxLayout()
        
        # Create scroll area for the combined tab
        combined_scroll = QScrollArea()
        combined_scroll.setWidgetResizable(True)
        combined_scroll_content = QWidget()
        combined_scroll_layout = QVBoxLayout(combined_scroll_content)
        
        # Basic info section
        basic_info_group = QGroupBox("Basic Info")
        basic_info_layout = QFormLayout()
        
        # Part name input
        self.part_name_input = QLineEdit()
        self.part_name_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part Name:", self.part_name_input)
        
        # Part number input
        self.part_number_input = QLineEdit()
        self.part_number_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part Number:", self.part_number_input)
        
        # Part ID input
        self.part_id_input = QLineEdit()
        self.part_id_input.textChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Part ID:", self.part_id_input)
        
        # Free length input
        self.free_length_input = QDoubleSpinBox()
        self.free_length_input.setRange(0, 1000)
        self.free_length_input.setSuffix(" mm")
        self.free_length_input.setDecimals(2)
        self.free_length_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Free Length:", self.free_length_input)
        
        # Coil count input
        self.coil_count_input = QDoubleSpinBox()
        self.coil_count_input.setRange(0, 100)
        self.coil_count_input.setDecimals(1)
        self.coil_count_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Number of Coils:", self.coil_count_input)
        
        # Wire diameter input
        self.wire_dia_input = QDoubleSpinBox()
        self.wire_dia_input.setRange(0, 100)
        self.wire_dia_input.setSuffix(" mm")
        self.wire_dia_input.setDecimals(2)
        self.wire_dia_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Wire Diameter:", self.wire_dia_input)
        
        # Outer diameter input
        self.outer_dia_input = QDoubleSpinBox()
        self.outer_dia_input.setRange(0, 500)
        self.outer_dia_input.setSuffix(" mm")
        self.outer_dia_input.setDecimals(2)
        self.outer_dia_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Outer Diameter:", self.outer_dia_input)
        
        # Safety limit input
        self.safety_limit_input = QDoubleSpinBox()
        self.safety_limit_input.setRange(0, 10000)
        self.safety_limit_input.setSuffix(" N")
        self.safety_limit_input.setDecimals(2)
        self.safety_limit_input.valueChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Safety Limit:", self.safety_limit_input)
        
        # Unit input
        self.unit_input = QComboBox()
        self.unit_input.addItems(["mm", "inch"])
        self.unit_input.currentTextChanged.connect(self.on_basic_info_changed)
        basic_info_layout.addRow("Unit:", self.unit_input)
        
        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enable Specifications")
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        basic_info_layout.addRow("", self.enabled_checkbox)
        
        basic_info_group.setLayout(basic_info_layout)
        combined_scroll_layout.addWidget(basic_info_group)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        combined_scroll_layout.addWidget(separator)
        
        # Set Points section
        set_points_group = QGroupBox("Set Points")
        set_points_layout = QVBoxLayout()
        
        # Container for set points
        set_points_container = QWidget()
        self.set_points_layout = QVBoxLayout(set_points_container)
        set_points_layout.addWidget(set_points_container)
        
        # Add set point button
        add_button = QPushButton("Add Set Point")
        add_button.clicked.connect(self.on_add_set_point)
        set_points_layout.addWidget(add_button)
        
        set_points_group.setLayout(set_points_layout)
        combined_scroll_layout.addWidget(set_points_group)
        
        # Finalize combined tab
        combined_scroll.setWidget(combined_scroll_content)
        combined_layout.addWidget(combined_scroll)
        combined_tab.setLayout(combined_layout)
        
        # Settings tab - new
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        
        # API Key group
        api_key_group = QGroupBox("API Settings")
        api_key_group.setObjectName("SettingsGroup")
        api_key_layout = QFormLayout()
        api_key_layout.setContentsMargins(15, 20, 15, 20)
        api_key_layout.setSpacing(10)
        
        # API key input with icon
        api_key_container = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API Key")
        self.api_key_input.setMinimumHeight(30)
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        api_key_container.addWidget(self.api_key_input)
        
        # Show/hide password toggle button could be added here
        
        api_key_layout.addRow("API Key:", api_key_container)
        
        # Key description
        key_description = QLabel("Enter your API key from OpenAI or another LLM provider.")
        key_description.setStyleSheet("color: gray; font-style: italic;")
        key_description.setWordWrap(True)
        api_key_layout.addRow("", key_description)
        
        api_key_group.setLayout(api_key_layout)
        settings_layout.addWidget(api_key_group)
        
        # Chat controls group
        chat_controls_group = QGroupBox("Chat Controls")
        chat_controls_group.setObjectName("SettingsGroup")
        chat_controls_layout = QVBoxLayout()
        chat_controls_layout.setContentsMargins(15, 20, 15, 20)
        chat_controls_layout.setSpacing(10)
        
        # Clear chat description
        clear_chat_description = QLabel("Clear the chat history to start a fresh conversation.")
        clear_chat_description.setStyleSheet("color: gray; font-style: italic;")
        clear_chat_description.setWordWrap(True)
        chat_controls_layout.addWidget(clear_chat_description)
        
        # Clear chat button
        self.clear_chat_btn = QPushButton("Clear Chat History")
        self.clear_chat_btn.setObjectName("ClearChatBtn")
        self.clear_chat_btn.setMinimumHeight(40)
        self.clear_chat_btn.clicked.connect(self.on_clear_chat_clicked)
        chat_controls_layout.addWidget(self.clear_chat_btn)
        
        chat_controls_group.setLayout(chat_controls_layout)
        settings_layout.addWidget(chat_controls_group)
        
        # Add spacer at the bottom of settings tab
        settings_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        settings_tab.setLayout(settings_layout)
        
        # Add tabs to tab widget
        tabs.addTab(combined_tab, "Specifications")
        tabs.addTab(self.create_text_input_tab(), "Paste Specifications")
        tabs.addTab(settings_tab, "Settings")
        
        main_layout.addWidget(tabs)
        
        # Save button
        save_button = QPushButton("Save Specifications")
        save_button.clicked.connect(self.on_save_specifications)
        main_layout.addWidget(save_button)
        
        # Spacer
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(main_layout)
    
    def load_specifications(self):
        """Load specifications from the settings service."""
        # Get specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Set basic info values
        self.part_name_input.setText(self.specifications.part_name)
        self.part_number_input.setText(self.specifications.part_number)
        self.part_id_input.setText(str(self.specifications.part_id))
        self.free_length_input.setValue(self.specifications.free_length_mm)
        self.coil_count_input.setValue(self.specifications.coil_count)
        self.wire_dia_input.setValue(self.specifications.wire_dia_mm)
        self.outer_dia_input.setValue(self.specifications.outer_dia_mm)
        self.safety_limit_input.setValue(self.specifications.safety_limit_n)
        self.unit_input.setCurrentText(self.specifications.unit)
        self.enabled_checkbox.setChecked(self.specifications.enabled)
        
        # Load API key
        api_key = self.settings_service.get_api_key()
        if api_key:
            self.api_key_input.setText(api_key)
        
        # Set set points
        self.refresh_set_points()
    
    def refresh_set_points(self):
        """Refresh the set points display."""
        # Clear existing set point widgets
        for widget in self.set_point_widgets:
            self.set_points_layout.removeWidget(widget)
            widget.deleteLater()
        
        self.set_point_widgets = []
        
        # Add set point widgets
        for i, set_point in enumerate(self.specifications.set_points):
            widget = SetPointWidget(set_point, i)
            widget.changed.connect(self.on_specifications_changed)
            widget.delete_requested.connect(self.on_delete_set_point)
            self.set_points_layout.addWidget(widget)
            self.set_point_widgets.append(widget)
        
        # Add a spacer at the end
        self.set_points_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
    
    def on_basic_info_changed(self):
        """Handle changes to basic info."""
        # Update specifications
        try:
            part_id = int(self.part_id_input.text()) if self.part_id_input.text() else 0
        except ValueError:
            part_id = 0
        
        self.settings_service.update_spring_basic_info(
            part_name=self.part_name_input.text(),
            part_number=self.part_number_input.text(),
            part_id=part_id,
            free_length=self.free_length_input.value(),
            coil_count=self.coil_count_input.value(),
            wire_dia=self.wire_dia_input.value(),
            outer_dia=self.outer_dia_input.value(),
            safety_limit=self.safety_limit_input.value(),
            unit=self.unit_input.currentText(),
            enabled=self.enabled_checkbox.isChecked()
        )
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_enabled_changed(self, state):
        """Handle enabled state changes.
        
        Args:
            state: New enabled state.
        """
        # Update specifications
        self.specifications.enabled = (state == Qt.Checked)
        
        # Update settings
        self.settings_service.set_spring_specification(self.specifications)
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_add_set_point(self):
        """Handle add set point button clicks."""
        # Add new set point
        self.settings_service.add_set_point()
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Refresh set points
        self.refresh_set_points()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_delete_set_point(self, widget):
        """Handle delete set point requests.
        
        Args:
            widget: Set point widget to delete.
        """
        # Delete set point
        self.settings_service.delete_set_point(widget.index)
        
        # Refresh specifications
        self.specifications = self.settings_service.get_spring_specification()
        
        # Refresh set points
        self.refresh_set_points()
        
        # Emit signal
        self.on_specifications_changed()
    
    def on_specifications_changed(self):
        """Handle specifications changes."""
        # Update sequence generator
        self.sequence_generator.set_spring_specification(self.specifications)
        
        # Emit signal
        self.specifications_changed.emit(self.specifications)
    
    def on_auto_update_changed(self, state):
        """Handle auto-update checkbox state changes.
        
        Args:
            state: New state (Qt.Checked or Qt.Unchecked).
        """
        self.auto_update_enabled = (state == Qt.Checked)
        
        # Connect/disconnect the textChanged signal based on auto-update state
        if self.auto_update_enabled:
            self.specs_text_input.textChanged.connect(self.on_parse_specifications)
        else:
            try:
                self.specs_text_input.textChanged.disconnect(self.on_parse_specifications)
            except TypeError:
                # Signal was not connected
                pass
    
    def on_parse_specifications(self):
        """Parse specifications from text input and update form fields."""
        # Get text from input
        specs_text = self.specs_text_input.toPlainText()
        
        if not specs_text.strip():
            return
        
        # Parse specifications
        parsed_data = self.parse_specifications_text(specs_text)
        
        # Update form fields with parsed data
        if parsed_data:
            self.populate_form_from_parsed_data(parsed_data)
            
            # Show success message if not auto-updating
            if not self.auto_update_enabled:
                QMessageBox.information(self, "Specifications Parsed", 
                                       "Spring specifications were successfully parsed and updated.")
    
    def parse_specifications_text(self, text):
        """Parse specifications from text.
        
        Args:
            text: Text containing specifications.
            
        Returns:
            Dictionary of parsed values or None if parsing failed.
        """
        parsed_data = {
            "basic_info": {},
            "set_points": []
        }
        
        # Preprocess text to improve parsing
        # Replace common typos and normalize spacing
        preprocessed_text = text
        # Insert newlines before key patterns to help with parsing
        for pattern in ["Part Name:", "Part Number:", "ID:", "Free Length:", "No of ", "Wire ", "Wired ", "OD:", "Set Po", "Safety"]:
            preprocessed_text = re.sub(f"\\s+({pattern})", f"\n\\1", preprocessed_text, flags=re.IGNORECASE)
        
        # Normalize spacing and remove extra whitespace
        preprocessed_text = re.sub(r'\s+', ' ', preprocessed_text).strip()
        
        # Regular expressions for parsing different parts - more flexible now
        patterns = {
            "part_name": r"(?:^|\s+)(?:Part|Spring)\s+Name:?\s*(.+?)(?:\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety)|$)",
            "part_number": r"(?:^|\s+)Part\s+Number:?\s*(.+?)(?:\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety)|$)",
            "part_id": r"(?:^|\s+)ID:?\s*(\d+)",
            "free_length": r"(?:^|\s+)Free\s+Length:?\s*([\d.]+)",
            "coil_count": r"(?:^|\s+)No\s+of\s+(?:Coils|Colis):?\s*([\d.]+)",
            "wire_dia": r"(?:^|\s+)(?:Wire|Wired)\s+Dia(?:meter)?:?\s*([\d.]+)",
            "outer_dia": r"(?:^|\s+)OD:?\s*([\d.]+)",
            "safety_limit": r"(?:^|\s+)[Ss]afety\s+[Ll]imit:?\s*([\d.]+)"
        }
        
        # Extract basic info with improved patterns
        for key, pattern in patterns.items():
            match = re.search(pattern, preprocessed_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Remove trailing text that might have been captured incorrectly
                value = re.sub(r'\s+(?:Part|ID|Free|No|Wire|OD|Set|Safety).*$', '', value, flags=re.IGNORECASE)
                try:
                    if key in ["part_id"]:
                        parsed_data["basic_info"][key] = int(value)
                    elif key in ["free_length", "coil_count", "wire_dia", "outer_dia", "safety_limit"]:
                        parsed_data["basic_info"][key] = float(value)
                    else:
                        parsed_data["basic_info"][key] = value
                except (ValueError, TypeError):
                    # Skip if conversion fails
                    continue
        
        # Extract set points with improved patterns
        # Look for both "Point" and "Poni" typos in the input
        set_point_indices = []
        
        # Find all set point indices mentioned in the text
        for match in re.finditer(r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-(\d+)", preprocessed_text, re.IGNORECASE):
            try:
                index = int(match.group(1))
                if index not in set_point_indices:
                    set_point_indices.append(index)
            except ValueError:
                continue
        
        # Process each set point with more flexible patterns
        for index in set_point_indices:
            set_point = {"index": index - 1}  # Convert to 0-based index
            
            # Position patterns - handle various formats and typos
            position_patterns = [
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"(?:\s+in\s+mm)?:?\s*([\d.]+)",
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"\s+(?:in\s+mm)\s*([\d.]+)",
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"[^L]+?([\d.]+)"  # Catch anything that's not "Load"
            ]
            
            # Try each position pattern
            for pattern in position_patterns:
                position_match = re.search(pattern, preprocessed_text, re.IGNORECASE)
                if position_match:
                    try:
                        set_point["position"] = float(position_match.group(1).strip())
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Load patterns - handle various formats and typos
            load_patterns = [
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"\s+Load\s+In\s+N:?\s*([\d.]+)(?:±([\d.]+)%)?",
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"\s+Load\s+In\s+N\s*([\d.]+)(?:±([\d.]+)%)?",
                r"Set\s+(?:Po(?:i|n)(?:i|t)|Poni)-" + str(index) + r"[^:]*?Load[^:]*?([\d.]+)(?:±([\d.]+)%)?"
            ]
            
            # Try each load pattern
            for pattern in load_patterns:
                load_match = re.search(pattern, preprocessed_text, re.IGNORECASE)
                if load_match:
                    try:
                        set_point["load"] = float(load_match.group(1).strip())
                        
                        # Extract tolerance if present
                        if load_match.group(2):
                            set_point["tolerance"] = float(load_match.group(2).strip())
                        break
                    except (ValueError, TypeError):
                        continue
            
            # Add set point if it has both position and load
            if "position" in set_point and "load" in set_point:
                set_point["enabled"] = True
                if "tolerance" not in set_point:
                    set_point["tolerance"] = 10.0  # Default tolerance
                parsed_data["set_points"].append(set_point)
        
        return parsed_data
    
    def populate_form_from_parsed_data(self, parsed_data):
        """Populate form fields from parsed data.
        
        Args:
            parsed_data: Dictionary of parsed values.
        """
        # Update basic info fields
        basic_info = parsed_data.get("basic_info", {})
        
        if "part_name" in basic_info:
            self.part_name_input.setText(basic_info["part_name"])
        
        if "part_number" in basic_info:
            self.part_number_input.setText(basic_info["part_number"])
        
        if "part_id" in basic_info:
            self.part_id_input.setText(str(basic_info["part_id"]))
        
        if "free_length" in basic_info:
            self.free_length_input.setValue(basic_info["free_length"])
        
        if "coil_count" in basic_info:
            self.coil_count_input.setValue(basic_info["coil_count"])
        
        if "wire_dia" in basic_info:
            self.wire_dia_input.setValue(basic_info["wire_dia"])
        
        if "outer_dia" in basic_info:
            self.outer_dia_input.setValue(basic_info["outer_dia"])
        
        if "safety_limit" in basic_info:
            self.safety_limit_input.setValue(basic_info["safety_limit"])
        
        # Enable specifications checkbox if any basic info was parsed
        if basic_info:
            self.enabled_checkbox.setChecked(True)
        
        # Update settings with basic info changes
        self.on_basic_info_changed()
        
        # Update set points
        set_points = parsed_data.get("set_points", [])
        
        if set_points:
            # First, make sure we have enough set points
            while len(self.specifications.set_points) < len(set_points):
                self.settings_service.add_set_point()
            
            # Update each set point
            for sp_data in set_points:
                index = sp_data["index"]
                
                # Make sure the index is valid
                if index >= len(self.specifications.set_points):
                    continue
                
                # Update set point data
                self.settings_service.update_set_point(
                    index=index,
                    position=sp_data["position"],
                    load=sp_data["load"],
                    tolerance=sp_data["tolerance"],
                    enabled=sp_data["enabled"]
                )
            
            # Refresh specifications
            self.specifications = self.settings_service.get_spring_specification()
            
            # Refresh set points display
            self.refresh_set_points()
            
            # Emit signal for specifications changed
            self.on_specifications_changed()

    def on_save_specifications(self):
        """Handle save specifications button clicks."""
        # Save specifications
        self.settings_service.set_spring_specification(self.specifications)
        
        # Show success message
        QMessageBox.information(self, "Specifications Saved", "Spring specifications saved successfully.")

    def on_upload_pdf(self):
        """Handle upload PDF button clicks."""
        if not PDF_SUPPORT:
            QMessageBox.warning(
                self, 
                "Feature Not Available", 
                "PDF support requires the PyPDF2 package. Please install it and restart the application."
            )
            return
        
        # Open file dialog to select PDF
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            # User cancelled
            return
        
        try:
            # Update status
            self.upload_status.setText(f"Processing {os.path.basename(file_path)}...")
            
            # Extract text from PDF
            extracted_text = self.extract_text_from_pdf(file_path)
            
            if not extracted_text:
                self.upload_status.setText("No text extracted from PDF.")
                return
            
            # Set text in input field
            self.specs_text_input.setPlainText(extracted_text)
            
            # Parse the specifications
            self.on_parse_specifications()
            
            # Update status
            self.upload_status.setText(f"Processed {os.path.basename(file_path)}")
            
        except Exception as e:
            self.upload_status.setText(f"Error: {str(e)}")
            logging.error(f"Error processing PDF: {str(e)}")
            QMessageBox.critical(
                self, 
                "PDF Processing Error", 
                f"An error occurred while processing the PDF file: {str(e)}"
            )
    
    def extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Extracted text.
        """
        extracted_text = ""
        
        # Open the PDF file
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Get the number of pages
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text:
                    extracted_text += page_text + "\n"
        
        # Process extracted text to clean it up
        # This is important as PDF extraction can include various formatting characters
        cleaned_text = self.clean_pdf_text(extracted_text)
        
        return cleaned_text
    
    def clean_pdf_text(self, text):
        """Clean up text extracted from PDF.
        
        Args:
            text: Raw text extracted from PDF.
            
        Returns:
            Cleaned text.
        """
        # Create a new string to build our formatted output
        formatted_output = ""
        
        # Preprocess: insert newlines before key patterns to help with parsing
        preprocessed_text = text
        for pattern in ["Part Name", "Part Number", "ID:", "Free Length", "No of ", "Wire ", "Wired ", "OD:", "Set Po", "Safety"]:
            preprocessed_text = re.sub(f"([^\\n])\\s+({pattern})", f"\\1\n\\2", preprocessed_text, flags=re.IGNORECASE)
        
        # Replace multiple spaces with a single space within lines
        cleaned_lines = []
        for line in preprocessed_text.split('\n'):
            cleaned_lines.append(re.sub(r'\s+', ' ', line).strip())
        cleaned = '\n'.join(cleaned_lines)
        
        # Dictionary to store extracted values
        extracted = {}
        
        # More flexible patterns to match various PDF formats
        patterns = {
            "part_name": [
                r'(?:part|spring)[\s:]+name[\s:]*([^,;\n\d]+)',
                r'(?:^|\n)[\s:]*part[\s:]*name[\s:]*([^,;\n\d]+)'
            ],
            "part_number": [
                r'(?:part|spring)[\s:]+(?:number|no\.?|#)[\s:]*([^,;\n]+)',
                r'(?:^|\n)[\s:]*part[\s:]*number[\s:]*([^,;\n]+)'
            ],
            "part_id": [
                r'(?:part|spring)?[\s:]*id[\s:]*(\d+)',
                r'(?:^|\n)[\s:]*id[\s:]*(\d+)'
            ],
            "free_length": [
                r'free[\s:]+length[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*free[\s:]*length[\s:]*(\d+\.?\d*)'
            ],
            "coil_count": [
                r'(?:number[\s:]+of[\s:]+(?:coils|colis)|no[\s:]+of[\s:]+(?:coils|colis))[\s:]*(\d+\.?\d*)',
                r'(?:^|\n)[\s:]*(?:no\.?|number)[\s:]*of[\s:]*(?:coils|colis)[\s:]*(\d+\.?\d*)'
            ],
            "wire_dia": [
                r'(?:wire|wired)[\s:]+dia(?:meter)?[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*(?:wire|wired)[\s:]*dia(?:meter)?[\s:]*(\d+\.?\d*)'
            ],
            "outer_dia": [
                r'(?:outer[\s:]+dia(?:meter)?|od)[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'(?:^|\n)[\s:]*(?:outer[\s:]*diameter|od)[\s:]*(\d+\.?\d*)'
            ],
            "safety_limit": [
                r'safety[\s:]+limit[\s:]*(\d+\.?\d*)[\s]*(?:n)?',
                r'(?:^|\n)[\s:]*safety[\s:]*limit[\s:]*(\d+\.?\d*)'
            ]
        }
        
        # Try multiple patterns for each parameter
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, cleaned, re.IGNORECASE)
                if match:
                    extracted[key] = match.group(1).strip()
                    break
        
        # Find set points with more flexible patterns
        set_points = {}
        
        # First find all set point indices
        for match in re.finditer(r'set[\s:]+(?:poin?t|poni)[\s\-:]+(\d+)', cleaned, re.IGNORECASE):
            try:
                index = int(match.group(1))
                if index not in set_points:
                    set_points[index] = {"index": index}
            except ValueError:
                continue
        
        # For each set point, find position and load with multiple pattern attempts
        for index in set_points:
            # Position patterns
            pos_patterns = [
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+in[\s:]+mm[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]*(\d+\.?\d*)[\s]*(?:mm)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[^0-9]*?(\d+\.?\d*)[\s]*(?:mm)?'
            ]
            
            for pattern in pos_patterns:
                pos_match = re.search(pattern, cleaned, re.IGNORECASE)
                if pos_match:
                    set_points[index]["position"] = pos_match.group(1).strip()
                    break
            
            # Load patterns
            load_patterns = [
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+load[\s:]+in[\s:]+n[\s:]*(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'[\s:]+load[\s:]*(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?',
                r'set[\s:]+(?:poin?t|poni)[\s\-:]+' + str(index) + r'.*?load.*?(\d+\.?\d*)(?:±([\d.]+)%)?[\s]*(?:n)?'
            ]
            
            for pattern in load_patterns:
                load_match = re.search(pattern, cleaned, re.IGNORECASE)
                if load_match:
                    set_points[index]["load"] = load_match.group(1).strip()
                    set_points[index]["tolerance"] = load_match.group(2).strip() if load_match.group(2) else "10"
                    break
        
        # Build the formatted output with consistent format
        if 'part_name' in extracted:
            formatted_output += f"Part Name: {extracted['part_name']}\n"
        
        if 'part_number' in extracted:
            formatted_output += f"Part Number: {extracted['part_number']}\n"
        
        if 'part_id' in extracted:
            formatted_output += f"ID: {extracted['part_id']}\n"
        
        if 'free_length' in extracted:
            formatted_output += f"Free Length: {extracted['free_length']} mm\n"
        
        if 'coil_count' in extracted:
            formatted_output += f"No of Coils: {extracted['coil_count']}\n"
        
        if 'wire_dia' in extracted:
            formatted_output += f"Wire Dia: {extracted['wire_dia']} mm\n"
        
        if 'outer_dia' in extracted:
            formatted_output += f"OD: {extracted['outer_dia']} mm\n"
        
        # Add set points in order
        for index in sorted(set_points.keys()):
            sp = set_points[index]
            if "position" in sp:
                formatted_output += f"Set Point-{index} in mm: {sp['position']} mm\n"
            if "load" in sp and "tolerance" in sp:
                formatted_output += f"Set Point-{index} Load In N: {sp['load']}±{sp['tolerance']}% N\n"
        
        if 'safety_limit' in extracted:
            formatted_output += f"Safety limit: {extracted['safety_limit']} N\n"
        
        # If we didn't extract anything meaningful, try line-by-line analysis
        if not formatted_output.strip():
            # Split into lines and process each one
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if any(key in line.lower() for key in ['part name', 'part number', 'id:', 'free length', 
                                                      'coils', 'colis', 'wire dia', 'wired', 'od:', 'set point', 'set poni', 'safety']):
                    formatted_output += line + '\n'
            
            # If still empty, return original
            if not formatted_output.strip():
                return text
        
        return formatted_output

    # New methods for API key and clear chat functionality
    def on_api_key_changed(self, api_key):
        """Handle API key changes.
        
        Args:
            api_key: New API key.
        """
        # Update settings
        self.settings_service.set_api_key(api_key)
        
        # Emit signal
        self.api_key_changed.emit(api_key)
    
    def on_clear_chat_clicked(self):
        """Handle clear chat button clicks."""
        # Emit signal
        self.clear_chat_clicked.emit()

    def create_text_input_tab(self):
        """Create the text input tab."""
        text_input_tab = QWidget()
        text_input_layout = QVBoxLayout()
        
        # Instructions
        instructions_label = QLabel("Paste or type spring specifications in the format below:")
        text_input_layout.addWidget(instructions_label)
        
        # Format hint
        format_hint = QLabel(
            "Format: Part Name, Part Number, ID, Free Length, No of Coils, "
            "Wire Dia, OD, Set Points, Safety Limit"
        )
        format_hint.setStyleSheet("color: gray; font-style: italic;")
        format_hint.setWordWrap(True)
        text_input_layout.addWidget(format_hint)
        
        # Upload button
        upload_layout = QHBoxLayout()
        upload_button = QPushButton("Upload PDF")
        upload_button.clicked.connect(self.on_upload_pdf)
        upload_layout.addWidget(upload_button)
        
        # Status label for upload
        self.upload_status = QLabel("")
        self.upload_status.setStyleSheet("color: gray; font-style: italic;")
        upload_layout.addWidget(self.upload_status, 1)  # Give it stretch factor
        
        text_input_layout.addLayout(upload_layout)
        
        # Text input
        input_label = QLabel("Enter specifications:")
        text_input_layout.addWidget(input_label)
        
        self.specs_text_input = QTextEdit()
        self.specs_text_input.setPlaceholderText("Paste specifications here...")
        text_input_layout.addWidget(self.specs_text_input)
        
        # Parse button
        parse_button = QPushButton("Parse Specifications")
        parse_button.clicked.connect(self.on_parse_specifications)
        text_input_layout.addWidget(parse_button)
        
        # Auto-update checkbox
        self.auto_update_checkbox = QCheckBox("Update specifications as you type")
        self.auto_update_checkbox.setChecked(False)
        self.auto_update_checkbox.stateChanged.connect(self.on_auto_update_changed)
        text_input_layout.addWidget(self.auto_update_checkbox)
        
        text_input_tab.setLayout(text_input_layout)
        return text_input_tab 