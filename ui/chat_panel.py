"""
Chat panel module for the Spring Test App.
Contains the chat interface components.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                           QPushButton, QMessageBox, QProgressBar, QSplitter, QFrame,
                           QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QSize
from PyQt5.QtGui import QFont, QTextCursor, QIcon, QMovie
import pandas as pd
from datetime import datetime

from utils.text_parser import extract_parameters
from models.data_models import TestSequence, ChatMessage
from utils.constants import USER_ICON, ASSISTANT_ICON


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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Chat panel title
        title_label = QLabel("Spring Test Chat Assistant")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        layout.addWidget(self.chat_display, 1)  # Give it stretch factor 1
        
        # Progress section frame - wrap in a fixed-height frame
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_frame.setFixedHeight(50)  # Set a fixed height
        progress_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        progress_layout = QHBoxLayout(progress_frame)
        progress_layout.setContentsMargins(5, 5, 5, 5)
        progress_layout.setSpacing(5)
        
        # Progress bar 
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        progress_layout.addWidget(self.progress_bar, 1)
        
        # Loading animation
        self.loading_label = QLabel()
        self.loading_movie = QMovie("resources/loading.gif")
        self.loading_movie.setScaledSize(QSize(24, 24))
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setFixedSize(24, 24)
        progress_layout.addWidget(self.loading_label)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        self.status_label.setMinimumWidth(100)
        progress_layout.addWidget(self.status_label, 2)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)
        self.cancel_btn.setFixedWidth(80)
        progress_layout.addWidget(self.cancel_btn)
        
        # Initially hide progress components but keep the frame
        self.progress_bar.hide()
        self.loading_label.hide()
        self.cancel_btn.hide()
        
        # Add progress frame to main layout
        layout.addWidget(progress_frame, 0)  # No stretch factor
        
        # Input area
        input_label = QLabel("Enter your request:")
        layout.addWidget(input_label, 0)  # No stretch factor
        
        self.user_input = QTextEdit()
        self.user_input.setPlaceholderText("Ask a question, chat, or request a test sequence (e.g., 'Generate a test sequence for a compression spring with free length 50mm')")
        self.user_input.setMinimumHeight(100)
        self.user_input.setMaximumHeight(150)
        layout.addWidget(self.user_input, 0)  # No stretch factor
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Send button with icon
        self.generate_btn = QPushButton(" Send Message")
        self.generate_btn.setIcon(QIcon("resources/send_icon.png"))
        self.generate_btn.setIconSize(QSize(20, 20))
        self.generate_btn.clicked.connect(self.on_send_clicked)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border-radius: 20px;
                padding: 8px 15px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #5294FF;
            }
            QPushButton:pressed {
                background-color: #3060C0;
            }
        """)
        button_layout.addStretch(1)  # Add stretch before button for right alignment
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout, 0)  # No stretch factor
        
        # Set the layout
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect signals from the sequence generator."""
        self.sequence_generator.sequence_generated.connect(self.on_sequence_generated_async)
        self.sequence_generator.progress_updated.connect(self.on_progress_updated)
        self.sequence_generator.status_updated.connect(self.on_status_updated)
    
    def refresh_chat_display(self):
        """Refresh the chat display with current history."""
        self.chat_display.clear()
        
        # Get chat history
        history = self.chat_service.get_history()
        
        # Display each message
        for message in history:
            if message.role == "user":
                self.chat_display.append(f"<b>{USER_ICON} You:</b>")
                self.chat_display.append(message.content)
                self.chat_display.append("")
            else:
                self.chat_display.append(f"<b>{ASSISTANT_ICON} Assistant:</b>")
                self.chat_display.append(message.content)
                self.chat_display.append("")
        
        # Scroll to bottom
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
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
            self.progress_bar.show()
            self.loading_label.show()
            self.loading_movie.start()
            self.cancel_btn.show()
        else:
            # Hide progress indicators
            self.progress_bar.hide()
            self.loading_label.hide()
            self.loading_movie.stop()
            self.cancel_btn.hide()
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
            
            # If we have chat content, display it
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
                from models.data_models import TestSequence
                
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
                
                # Emit the TestSequence object
                self.sequence_generated.emit(test_sequence)
                
                # If we didn't have chat content already, add a generic message
                if chat_rows.empty:
                    self.chat_service.add_message(
                        "assistant", 
                        "I've generated a test sequence based on your request. "
                        "You can see the results in the right panel."
                    )
                    self.refresh_chat_display()
        
        elif hasattr(sequence, 'rows') and hasattr(sequence, 'parameters'):
            # It's a TestSequence object - handle accordingly
            self.chat_service.add_message(
                "assistant", 
                "I've generated a test sequence based on your request. "
                "You can see the results in the right panel."
            )
            self.refresh_chat_display()
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
        self.progress_bar.setValue(progress)
    
    def on_status_updated(self, status):
        """Handle status updates.
        
        Args:
            status: Status message.
        """
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
        
        # Import regex for pattern matching
        import re
        
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