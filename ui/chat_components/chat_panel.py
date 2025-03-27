"""
Chat panel module for the Spring Test App.
Main chat interface with message display and controls.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                           QPushButton, QMessageBox, QProgressBar, QSplitter, QFrame,
                           QSizePolicy)
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QTimer, QSize, pyqtProperty, 
                         QPropertyAnimation)
from PyQt5.QtGui import QIcon, QMovie, QTransform, QPixmap
from PyQt5.QtSvg import QSvgWidget
import pandas as pd
from datetime import datetime
import re

from ui.chat_components.chat_display import ChatBubbleDisplay
from utils.text_parser import extract_parameters
from models.data_models import TestSequence


class ChatPanel(QWidget):
    """Chat panel widget for the Spring Test App."""
    
    # Define signals
    sequence_generated = pyqtSignal(object)  # TestSequence object
    
    def __init__(self, chat_service, sequence_generator):
        """Initialize the chat panel.
        
        Args:
            chat_service: Chat service.
            sequence_generator: Sequence generator service.
        """
        super().__init__()
        
        # Enable transparency for the widget
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Store services
        self.chat_service = chat_service
        self.sequence_generator = sequence_generator
        
        # Get the settings service from chat service
        self.settings_service = self.chat_service.settings_service
        
        # State variables
        self.is_generating = False
        
        # Set up the UI
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
        
        # Load chat history
        self.refresh_chat_display()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for full-width content
        layout.setSpacing(0)  # Remove spacing between components
        
        # Create a main content widget with padding
        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Apply transparency to the content widget
        content_widget.setStyleSheet("""
            #ContentWidget {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                      stop:0 rgba(255, 255, 255, 0.7),
                                      stop:1 rgba(240, 240, 255, 0.8));
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.8);
            }
        """)
        
        # Chat panel title
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 8)
        
        # Replace the text title with the Sushma logo
        logo_widget = QSvgWidget("resources/Sushma_logo-722x368.svg")
        logo_widget.setObjectName("LogoWidget")
        logo_widget.setFixedSize(200, 100)
        logo_widget.setStyleSheet("""
            #LogoWidget {
                background-color: transparent;
                margin-bottom: 10px;
            }
        """)
        title_layout.addWidget(logo_widget)
        title_layout.setAlignment(Qt.AlignLeft)
        
        # Add the title layout to the content layout
        content_layout.addLayout(title_layout)
        
        # Create a frame for the chat display
        chat_frame = QFrame()
        chat_frame.setObjectName("ChatDisplayFrame")
        chat_frame.setFrameShape(QFrame.NoFrame)
        chat_frame.setStyleSheet("""
            #ChatDisplayFrame {
                background-color: transparent;
                border-radius: 12px;
                border: none;
            }
        """)
        
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat display with bubble styling
        self.chat_display = ChatBubbleDisplay(self)
        chat_layout.addWidget(self.chat_display)
        
        # Add the chat frame to the content layout with stretch
        content_layout.addWidget(chat_frame, 1)  # Give it stretch factor 1
        
        # Create a container for the input area (to manage positioning)
        input_container = QWidget()
        input_container.setObjectName("InputContainer")
        input_container.setContentsMargins(0, 0, 0, 0)
        input_container.setFixedHeight(60)  # Fixed height for the input container
        
        # Style the input container
        input_container.setStyleSheet("""
            #InputContainer {
                background-color: transparent;
            }
        """)
        
        # Input container layout
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(12)
        
        # Create a frame for the floating input area
        input_frame = QFrame()
        input_frame.setObjectName("InputFrame")
        
        # Style the input frame to look like a floating element
        input_frame.setStyleSheet("""
            #InputFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                    stop:0 rgba(255, 255, 255, 0.7),
                                    stop:1 rgba(255, 255, 255, 0.85));
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 24px;
            }
            #InputFrame:hover {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(66, 133, 244, 0.3);
            }
        """)
        
        # Input frame layout
        input_frame_layout = QHBoxLayout(input_frame)
        input_frame_layout.setContentsMargins(16, 8, 8, 8)
        input_frame_layout.setSpacing(8)
        
        # Modern text input area
        self.user_input = QTextEdit()
        self.user_input.setObjectName("ChatInput")
        self.user_input.setPlaceholderText("Message Sushma Assistant...")
        self.user_input.setFixedHeight(40)
        self.user_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Style the input text area
        self.user_input.setStyleSheet("""
            QTextEdit#ChatInput {
                border: none;
                background-color: transparent;
                padding: 8px 0px;
                font-size: 14px;
                color: #202124;
            }
            QTextEdit#ChatInput:focus {
                outline: none;
            }
        """)
        
        # Add the input text area to the input frame layout
        input_frame_layout.addWidget(self.user_input, 1)  # Give it stretch factor
        
        # Send button with modern icon
        self.generate_btn = QPushButton()
        self.generate_btn.setObjectName("SendButton")
        self.generate_btn.setIcon(QIcon("resources/sendbutton.svg"))
        self.generate_btn.setIconSize(QSize(20, 20))
        self.generate_btn.setFixedSize(40, 40)
        self.generate_btn.setCursor(Qt.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_send_clicked)
        
        # Style the send button
        self.generate_btn.setStyleSheet("""
            QPushButton#SendButton {
                background-color: #4285F4;
                border-radius: 20px;
                border: none;
                margin: 0;
                padding: 0;
            }
            QPushButton#SendButton:hover {
                background-color: #5294FF;
            }
            QPushButton#SendButton:pressed {
                background-color: #3060C0;
            }
            QPushButton#SendButton:disabled {
                background-color: #C0C0C0;
            }
        """)
        
        # Add the send button to the input frame layout
        input_frame_layout.addWidget(self.generate_btn)
        
        # Add the input frame to the input container layout
        input_layout.addWidget(input_frame)
        
        # Add the input container to the content layout
        content_layout.addWidget(input_container, 0)  # No stretch
        
        # Create a container for the progress indicators
        progress_container = QWidget()
        progress_container.setObjectName("ProgressContainer")
        progress_container.setContentsMargins(0, 0, 0, 0)
        progress_container.setFixedHeight(40)
        progress_container.hide()  # Initially hidden
        
        # Progress container layout
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(16, 0, 16, 0)
        progress_layout.setSpacing(12)
        
        # Modern loading indicator
        self.loading_indicator = QFrame()
        self.loading_indicator.setObjectName("LoadingIndicator")
        self.loading_indicator.setFixedSize(20, 20)
        
        # Style the loading indicator
        self.loading_indicator.setStyleSheet("""
            #LoadingIndicator {
                background-color: transparent;
                border: 2px solid rgba(66, 133, 244, 0.2);
                border-top: 2px solid #4285F4;
                border-radius: 10px;
            }
        """)
        
        # Create a simpler animation effect without using rotation property
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.toggle_loading_indicator)
        self.loading_state = 0
        
        # Status label
        self.status_label = QLabel("Processing your request...")
        self.status_label.setObjectName("StatusLabel")
        font = self.status_label.font()
        font.setPointSize(11)
        self.status_label.setFont(font)
        
        # Style the status label
        self.status_label.setStyleSheet("""
            #StatusLabel {
                color: #5F6368;
            }
        """)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        
        # Style the cancel button
        self.cancel_btn.setStyleSheet("""
            #CancelButton {
                background-color: transparent;
                color: #4285F4;
                border: none;
                font-size: 12px;
                padding: 4px 8px;
            }
            #CancelButton:hover {
                text-decoration: underline;
            }
        """)
        
        # Modern progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        
        # Style the progress bar
        self.progress_bar.setStyleSheet("""
            #ProgressBar {
                background-color: rgba(66, 133, 244, 0.1);
                border: none;
                border-radius: 2px;
            }
            #ProgressBar::chunk {
                background-color: #4285F4;
                border-radius: 2px;
            }
        """)
        
        # Add the loading indicator and status label to the progress layout
        progress_layout.addWidget(self.loading_indicator)
        progress_layout.addWidget(self.status_label, 1)  # Give it stretch
        progress_layout.addWidget(self.cancel_btn)
        
        # Create a progress bar container
        progress_bar_container = QWidget()
        progress_bar_layout = QVBoxLayout(progress_bar_container)
        progress_bar_layout.setContentsMargins(0, 4, 0, 0)
        progress_bar_layout.addWidget(self.progress_bar)
        
        # Add the progress bar container to the content layout
        content_layout.addWidget(progress_bar_container)
        
        # Add the progress container to the content layout
        content_layout.addWidget(progress_container)
        
        # Store references to containers for showing/hiding
        self.progress_container = progress_container
        self.progress_bar_container = progress_bar_container
        
        # Add the content widget to the main layout
        layout.addWidget(content_widget, 1)  # Give it stretch
        
        # Set the main layout
        self.setLayout(layout)
        
        # Style the chat display scrollbar
        self.chat_display.setStyleSheet("""
            QWebEngineView {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 12px 2px 12px 2px;
            }
            QScrollBar::handle:vertical {
                background: rgba(66, 133, 244, 0.5);
                min-height: 40px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(66, 133, 244, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
    
    def connect_signals(self):
        """Connect signals from the sequence generator."""
        self.sequence_generator.sequence_generated.connect(self.on_sequence_generated_async)
        self.sequence_generator.progress_updated.connect(self.on_progress_updated)
        self.sequence_generator.status_updated.connect(self.on_status_updated)
    
    def refresh_chat_display(self):
        """Refresh the chat display with current history."""
        # Get chat history
        history = self.chat_service.get_history()
        
        # Use the chat display component to refresh
        self.chat_display.refresh_display(history)
    
    def on_send_clicked(self):
        """Handle send button clicks (for both chat and generation)."""
        # Get user input
        user_input = self.user_input.toPlainText()
        
        # Check if input is empty
        if not user_input:
            QMessageBox.warning(self, "Missing Input", "Please enter your request.")
            return
        
        # Check if generation is already in progress
        if self.is_generating:
            QMessageBox.warning(self, "Processing", "Please wait for the current request to complete.")
            return
        
        # Add user message to chat history
        self.chat_service.add_message("user", user_input)
        
        # Clear the input field immediately after sending
        self.user_input.clear()
        
        # Refresh chat display
        self.refresh_chat_display()
        
        # Extract parameters from user input
        parameters = extract_parameters(user_input)
        
        # Add a processing message 
        self.chat_service.add_message(
            "assistant",
            "Processing your message..."
        )
        self.refresh_chat_display()
        
        # Add the original prompt to parameters if not already there
        if "prompt" not in parameters:
            parameters["prompt"] = user_input
        
        # Check if the input contains spring specifications and parse them
        contains_specs = self.parse_spring_specs(user_input)
        
        # If specs were parsed, update the sequence generator
        if contains_specs:
            # Get the updated specification and set it in the sequence generator
            updated_spec = self.settings_service.get_spring_specification()
            self.sequence_generator.set_spring_specification(updated_spec)
            
            # Add a note to the chat about using the parsed specifications
            self.chat_service.add_message(
                "assistant",
                "I'll use the current spring specifications for this request."
            )
            self.refresh_chat_display()
        
        # Include spring specification in the prompt if available and enabled
        spring_spec = self.sequence_generator.get_spring_specification()
        if spring_spec and spring_spec.enabled:
            # Add specification text to the prompt if not already included
            if 'prompt' in parameters:
                spec_text = spring_spec.to_prompt_text()
                if spec_text not in parameters['prompt']:
                    parameters['prompt'] = f"{spec_text}\n\n{parameters['prompt']}"
        
        # Start generation
        self.start_generation(parameters)
    
    def on_cancel_clicked(self):
        """Handle cancel button clicks."""
        if self.is_generating:
            # Cancel the operation
            self.sequence_generator.cancel_current_operation()
            
            # Update UI
            self.on_status_updated("Operation cancelled")
            self.on_progress_updated(0)
            
            # Add cancellation message to chat
            self.chat_service.add_message(
                "assistant", 
                "I've cancelled the sequence generation as requested."
            )
            self.refresh_chat_display()
            
            # Reset generating state
            self.set_generating_state(False)
    
    def start_generation(self, parameters):
        """Start sequence generation.
        
        Args:
            parameters: Dictionary of spring parameters.
        """
        # Set generating state
        self.set_generating_state(True)
        
        # Reset progress and status
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting generation...")
        
        # Start async generation
        self.sequence_generator.generate_sequence_async(parameters)
    
    def set_generating_state(self, is_generating):
        """Set the generating state and update UI accordingly.
        
        Args:
            is_generating: Whether generation is in progress.
        """
        self.is_generating = is_generating
        
        # Update UI based on state
        self.generate_btn.setEnabled(not is_generating)
        self.user_input.setReadOnly(is_generating)
        
        if is_generating:
            # Show progress indicators
            self.progress_container.show()
            self.progress_bar_container.show()
            self.progress_bar.setValue(0)
            # Start timer-based animation
            self.loading_timer.start(150)  # Update every 150ms for smooth animation
            self.status_label.setText("Processing your request...")
        else:
            # Hide progress indicators
            self.progress_container.hide()
            self.progress_bar_container.hide()
            # Stop timer-based animation
            self.loading_timer.stop()
            self.status_label.setText("Ready")
    
    def on_sequence_generated_async(self, sequence, error):
        """Handle asynchronous sequence generation completion.
        
        Args:
            sequence: The generated sequence or None if error.
            error: Error message if any.
        """
        # Reset generating state
        self.set_generating_state(False)
        
        # Check if sequence is None or empty
        if sequence is None or (isinstance(sequence, pd.DataFrame) and sequence.empty):
            # Handle error case
            if error:
                # Show error message
                error_msg = f"Error generating sequence: {error}"
                self.chat_service.add_message(
                    "assistant", 
                    error_msg + "\nPlease try providing more specific spring details."
                )
            else:
                # Generic error
                self.chat_service.add_message(
                    "assistant", 
                    "I'm having trouble processing your request. Please try again with more details."
                )
            self.refresh_chat_display()
            return
        
        # Handle different types of sequence objects properly
        if isinstance(sequence, pd.DataFrame):
            # Check if it has a CHAT row (for conversation or hybrid responses)
            chat_rows = sequence[sequence["Row"] == "CHAT"]
            
            # If we have chat content, display it in the chat panel
            if not chat_rows.empty:
                chat_message = chat_rows["Description"].values[0]
                self.chat_service.add_message("assistant", chat_message)
                self.refresh_chat_display()
            
            # Check if we also have actual sequence rows (for hybrid or sequence-only responses)
            sequence_rows = sequence[sequence["Row"] != "CHAT"]
            if not sequence_rows.empty:
                # We have actual sequence data to display in the results panel
                # Only send the sequence part (without the CHAT row)
                sequence_rows = sequence_rows.reset_index(drop=True)
                
                # Convert DataFrame to TestSequence object before emitting
                
                # Create a simple parameter dictionary for the TestSequence
                parameters = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "prompt": "Generated sequence"
                }
                
                # Create TestSequence with the sequence rows and parameters
                test_sequence = TestSequence(
                    rows=sequence_rows.to_dict('records'),
                    parameters=parameters
                )
                
                # Emit the TestSequence object to display in the sidebar
                self.sequence_generated.emit(test_sequence)
                
                # If we didn't have chat content already, add a generic message to the chat panel
                if chat_rows.empty:
                    self.chat_service.add_message(
                        "assistant", 
                        "I've generated a test sequence based on your request. "
                        "You can see the results in the right panel."
                    )
                    self.refresh_chat_display()
            else:
                # No sequence data was found, this was purely a conversation message
                # Make sure the chat display is refreshed 
                self.refresh_chat_display()
        
        elif hasattr(sequence, 'rows') and hasattr(sequence, 'parameters'):
            # It's already a TestSequence object - send it directly to the sidebar
            
            # Add a notification in the chat panel
            self.chat_service.add_message(
                "assistant", 
                "I've generated a test sequence based on your request. "
                "You can see the results in the right panel."
            )
            self.refresh_chat_display()
            
            # Emit the TestSequence object to display in the sidebar
            self.sequence_generated.emit(sequence)
        else:
            # Unknown object type - show error
            self.chat_service.add_message(
                "assistant", 
                "I received an unexpected response format. Please try again with a different request."
            )
            self.refresh_chat_display()
    
    def on_progress_updated(self, progress):
        """Handle progress updates.
        
        Args:
            progress: Progress percentage (0-100).
        """
        if progress > 0 and progress < 100:
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setValue(0)
    
    def on_status_updated(self, status):
        """Handle status updates.
        
        Args:
            status: Status message.
        """
        if status and status.strip():
            self.status_label.setText(status)
    
    def validate_api_key(self):
        """Check if API key is provided, but don't validate it to save credits."""
        # Get the API key from the sequence generator
        api_key = self.sequence_generator.api_client.api_key
        
        # Check if API key is empty
        if not api_key:
            # Add message to chat history
            self.chat_service.add_message(
                "assistant", 
                "Please enter an API key in the Settings tab of the Specifications panel to use the chat."
            )
            self.refresh_chat_display()
            return False
        
        # Simply acknowledge the key is present, don't validate to save credits
        self.chat_service.add_message(
            "assistant", 
            "API key is set. You can start chatting or generating sequences."
        )
        self.refresh_chat_display()
        return True
    
    def parse_spring_specs(self, text):
        """Parse spring specifications from the user input if present.
        
        Args:
            text: User input text
        
        Returns:
            True if specifications were found and parsed, False otherwise
        """
        # Check if the text contains spring specification format
        if not any(pattern in text.lower() for pattern in [
            "part name:", "free length:", "wire dia:", "od:", "set point", "safety limit:"
        ]):
            return False
        
        # Create parsed data dictionary
        parsed_data = {
            "basic_info": {},
            "set_points": []
        }
        
        # Define patterns for basic info
        patterns = {
            "part_name": r"Part Name:\s*(.+?)(?:\n|$)",
            "part_number": r"Part Number:\s*(.+?)(?:\n|$)",
            "part_id": r"ID:\s*(\d+)(?:\n|$)",
            "free_length": r"Free Length:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "coil_count": r"No of Coils:\s*([\d.]+)(?:\n|$)",
            "wire_dia": r"(?:Wire|Wired) Dia(?:meter)?:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "outer_dia": r"OD:\s*([\d.]+)(?:\s*mm)?(?:\n|$)",
            "safety_limit": r"[Ss]afety limit:\s*([\d.]+)(?:\s*N)?(?:\n|$)"
        }
        
        # Extract basic info
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
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
        
        # Extract set points
        set_point_indices = []
        
        # Find all set point indices mentioned in the text
        for match in re.finditer(r"Set Po(?:i|n)(?:i|t)-(\d+)", text, re.IGNORECASE):
            try:
                index = int(match.group(1))
                if index not in set_point_indices:
                    set_point_indices.append(index)
            except ValueError:
                continue
        
        # Process each set point
        for index in set_point_indices:
            set_point = {"index": index - 1}  # Convert to 0-based index
            
            # Position pattern
            position_pattern = r"Set Po(?:i|n)(?:i|t)-" + str(index) + r"(?:\s+in mm)?:\s*([\d.]+)(?:\s*mm)?(?:\n|$)"
            position_match = re.search(position_pattern, text, re.IGNORECASE)
            
            # Load pattern (with tolerance)
            load_pattern = r"Set Po(?:i|n)(?:i|t)-" + str(index) + r" Load In N:\s*([\d.]+)(?:±([\d.]+)%)?(?:\s*N)?(?:\n|$)"
            load_match = re.search(load_pattern, text, re.IGNORECASE)
            
            # Extract values
            if position_match:
                try:
                    set_point["position"] = float(position_match.group(1).strip())
                except (ValueError, TypeError):
                    continue
            
            if load_match:
                try:
                    set_point["load"] = float(load_match.group(1).strip())
                    
                    # Extract tolerance if present
                    if load_match.group(2):
                        set_point["tolerance"] = float(load_match.group(2).strip())
                except (ValueError, TypeError):
                    continue
            
            # Add set point if it has both position and load
            if "position" in set_point and "load" in set_point:
                set_point["enabled"] = True
                if "tolerance" not in set_point:
                    set_point["tolerance"] = 10.0  # Default tolerance
                parsed_data["set_points"].append(set_point)
        
        # Update specifications if we found any
        if not parsed_data["basic_info"] and not parsed_data["set_points"]:
            return False
        
        # Use the settings service
        settings_service = self.settings_service
        
        # Update basic info if any was found
        if parsed_data["basic_info"]:
            # Get values from basic info or use current values
            spec = settings_service.get_spring_specification()
            
            part_name = parsed_data["basic_info"].get("part_name", spec.part_name)
            part_number = parsed_data["basic_info"].get("part_number", spec.part_number)
            part_id = parsed_data["basic_info"].get("part_id", spec.part_id)
            free_length = parsed_data["basic_info"].get("free_length", spec.free_length_mm)
            coil_count = parsed_data["basic_info"].get("coil_count", spec.coil_count)
            wire_dia = parsed_data["basic_info"].get("wire_dia", spec.wire_dia_mm)
            outer_dia = parsed_data["basic_info"].get("outer_dia", spec.outer_dia_mm)
            safety_limit = parsed_data["basic_info"].get("safety_limit", spec.safety_limit_n)
            
            # Update basic info
            settings_service.update_spring_basic_info(
                part_name, part_number, part_id, free_length, coil_count,
                wire_dia, outer_dia, safety_limit, "mm", True
            )
        
        # Update set points if any were found
        for sp in parsed_data["set_points"]:
            if sp["index"] < len(settings_service.get_spring_specification().set_points):
                # Update existing set point
                settings_service.update_set_point(
                    sp["index"], sp["position"], sp["load"], sp["tolerance"], sp["enabled"]
                )
            else:
                # Add new set point first
                settings_service.add_set_point()
                settings_service.update_set_point(
                    sp["index"], sp["position"], sp["load"], sp["tolerance"], sp["enabled"]
                )
        
        return len(parsed_data["basic_info"]) > 0 or len(parsed_data["set_points"]) > 0
    
    def toggle_loading_indicator(self):
        """Toggle the loading indicator appearance for animation effect."""
        self.loading_state = (self.loading_state + 1) % 4
        
        # Use different border styles to create a rotation illusion
        if self.loading_state == 0:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-top: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        elif self.loading_state == 1:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-right: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        elif self.loading_state == 2:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-bottom: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """)
        else:
            self.loading_indicator.setStyleSheet("""
                #LoadingIndicator {
                    background-color: transparent;
                    border: 2px solid rgba(66, 133, 244, 0.2);
                    border-left: 2px solid #4285F4;
                    border-radius: 10px;
                }
            """) 