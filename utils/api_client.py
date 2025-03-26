"""
API client module for the Spring Test App.
Contains functions for making API requests and handling responses.
"""
import requests
import pandas as pd
import json
import time
import threading
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from utils.constants import API_ENDPOINT, DEFAULT_MODEL, DEFAULT_TEMPERATURE, SYSTEM_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE
from utils.text_parser import extract_command_sequence, format_parameter_text, extract_error_message


class APIClientWorker(QObject):
    """Worker class for making API requests in a separate thread."""
    
    # Define signals
    finished = pyqtSignal(object, str)  # (DataFrame, error_message)
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    status = pyqtSignal(str)    # Status message
    
    def __init__(self, api_client, parameters, model, temperature, max_retries):
        """Initialize the worker.
        
        Args:
            api_client: The API client to use for requests.
            parameters: Dictionary of spring parameters.
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__()
        self.api_client = api_client
        self.parameters = parameters
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.is_cancelled = False
    
    def cancel(self):
        """Cancel the current operation."""
        self.is_cancelled = True
    
    def run(self):
        """Run the API request in a separate thread."""
        # Format parameter text for prompt
        parameter_text = format_parameter_text(self.parameters)
        
        # Get the original user prompt
        original_prompt = self.parameters.get('prompt', '')
        
        # Check if test_type is provided in parameters
        test_type_text = ""
        if "Test Type" in self.parameters:
            test_type = self.parameters["Test Type"]
            test_type_text = f"This should be a {test_type} test sequence."
        
        # Create a simplified user prompt that instructs the AI about the format
        # Let the AI determine response format rather than trying to predict intent ourselves
        user_prompt = f"""
{parameter_text}

{test_type_text}

My message: {original_prompt}

IMPORTANT - RESPONSE FORMAT:
- Use your natural language understanding to decide how to respond to my request
- For NEW test sequence requests: Include a JSON array with the required test sequence format
- For analysis requests about EXISTING sequences: Provide conversational analysis in plain text 
- You can COMBINE both formats when appropriate:
  1. First provide your conversational response/analysis in plain text
  2. Then include "---SEQUENCE_DATA_START---" on a new line
  3. Include your JSON array sequence data
  4. End with "---SEQUENCE_DATA_END---" on a new line
  5. Continue with any additional conversational text if needed

This format allows you to provide both explanatory text AND sequence data when appropriate.
"""
        
        # Include previous context if available
        if self.api_client.chat_memory:
            user_prompt += "\n\nPrevious context:\n" + "\n".join(self.api_client.chat_memory[-3:])
        
        # Create payload
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature
        }
        
        # Save the request for debugging
        self.api_client.request_history.append({
            "timestamp": time.time(),
            "payload": payload
        })
        
        # Make the request with retries
        response_text = ""
        error_message = ""
        
        self.status.emit("Preparing request...")
        self.progress.emit(10)
        
        for attempt in range(self.max_retries):
            if self.is_cancelled:
                self.finished.emit(pd.DataFrame(), "Operation cancelled")
                return
                
            try:
                self.status.emit(f"Sending request (attempt {attempt+1}/{self.max_retries})...")
                self.progress.emit(20 + (attempt * 15))
                
                response = self.api_client.session.post(
                    API_ENDPOINT,
                    headers=self.api_client.get_headers(),
                    json=payload,
                    timeout=60  # 60 second timeout
                )
                response.raise_for_status()
                response_json = response.json()
                
                self.status.emit("Processing response...")
                self.progress.emit(80)
                
                message = response_json['choices'][0].get('message', {})
                response_text = message.get('content', '')
                
                # Save context for continuity
                self.api_client.chat_memory.append(parameter_text)
                if len(self.api_client.chat_memory) > 10:  # Keep memory limited
                    self.api_client.chat_memory = self.api_client.chat_memory[-10:]
                
                # Save raw response for debugging
                self.api_client.last_raw_response = response_text
                
                # Process the response
                self.status.emit("Processing response...")
                self.progress.emit(80)
                
                # Clean up response text - remove markdown backticks if present
                response_text = response_text.replace("```json", "").replace("```", "").strip()
                
                # Check for hybrid response format with both text and sequence data
                sequence_data_start = "---SEQUENCE_DATA_START---"
                sequence_data_end = "---SEQUENCE_DATA_END---"
                
                if sequence_data_start in response_text and sequence_data_end in response_text:
                    # This is a hybrid response with both text and sequence data
                    # Extract the parts
                    parts = response_text.split(sequence_data_start)
                    conversation_text = parts[0].strip()
                    
                    # Extract the sequence data
                    seq_parts = parts[1].split(sequence_data_end)
                    sequence_json_text = seq_parts[0].strip()
                    
                    # If there's additional text after the sequence data, add it to conversation
                    if len(seq_parts) > 1 and seq_parts[1].strip():
                        conversation_text += "\n\n" + seq_parts[1].strip()
                    
                    try:
                        # Parse the sequence data
                        data = json.loads(sequence_json_text)
                        
                        # Create a DataFrame with the sequence data
                        df = pd.DataFrame(data)
                        
                        # Ensure all required columns are present
                        required_columns = ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]
                        
                        # Fix column names - handle both "Cmd" and "CMD" variations
                        if "Cmd" in df.columns and "CMD" not in df.columns:
                            df = df.rename(columns={"Cmd": "CMD"})
                        
                        # Rename any mismatched columns
                        if "Speed" in df.columns and "Speed rpm" not in df.columns:
                            df = df.rename(columns={"Speed": "Speed rpm"})
                            
                        # Add any missing columns
                        for col in required_columns:
                            if col not in df.columns:
                                df[col] = ""
                        
                        # Reorder columns to match required format
                        df = df[required_columns]
                        
                        # Add the conversation text to a special "CHAT" row
                        chat_row = pd.DataFrame({
                            "Row": ["CHAT"], 
                            "CMD": ["CHAT"], 
                            "Description": [conversation_text]
                        })
                        
                        # Add empty values for other columns
                        for col in required_columns:
                            if col not in chat_row.columns:
                                chat_row[col] = ""
                        
                        # Combine the chat row with the sequence data
                        df = pd.concat([chat_row, df], ignore_index=True)
                        
                    except (json.JSONDecodeError, ValueError) as e:
                        # If parsing fails, create a conversation-only response
                        self.status.emit(f"Failed to parse sequence data: {str(e)}")
                        message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                        df = message_df
                
                # Handle JSON-only responses (sequence data without conversation)
                elif response_text.strip().startswith("[") and response_text.strip().endswith("]"):
                    try:
                        # Parse the JSON data
                        data = json.loads(response_text)
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(data)
                        
                        # Ensure all required columns are present
                        required_columns = ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]
                        
                        # Fix column names - handle both "Cmd" and "CMD" variations
                        if "Cmd" in df.columns and "CMD" not in df.columns:
                            df = df.rename(columns={"Cmd": "CMD"})
                        
                        # Rename any mismatched columns
                        if "Speed" in df.columns and "Speed rpm" not in df.columns:
                            df = df.rename(columns={"Speed": "Speed rpm"})
                            
                        # Add any missing columns
                        for col in required_columns:
                            if col not in df.columns:
                                df[col] = ""
                        
                        # Reorder columns to match required format
                        df = df[required_columns]
                    except (json.JSONDecodeError, ValueError):
                        # If parsing fails, create a conversation-only response
                        message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                        df = message_df
                else:
                    # No sequence data found - this was a conversational response
                    # Create a custom message-only DataFrame
                    message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
                    df = message_df

                break  # Success, exit retry loop
                
            except requests.exceptions.RequestException as e:
                error_message = f"Request error: {str(e)}"
                self.status.emit(f"Request error: {str(e)}")
                # Exponential backoff
                if attempt < self.max_retries - 1 and not self.is_cancelled:  # Don't sleep after the last attempt
                    backoff_time = 2 ** attempt  # 1, 2, 4 seconds
                    self.status.emit(f"Retrying in {backoff_time} seconds...")
                    time.sleep(backoff_time)
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                error_message = f"Response parsing error: {str(e)}"
                self.status.emit(f"Response parsing error: {str(e)}")
                break  # Don't retry on parsing errors
        
        self.progress.emit(100)
        
        # Always return df - if it's empty or contains a CHAT row, will be handled correctly by the receiver
        self.finished.emit(df, error_message)


class APIClient:
    """Client for making API requests to generate test sequences."""
    
    def __init__(self, api_key: str = ""):
        """Initialize the API client.
        
        Args:
            api_key: The API key to use for requests.
        """
        self.api_key = api_key
        self.last_raw_response = ""
        self.chat_memory = []
        self.request_history = []
        self.session = requests.Session()
        self.current_worker = None
        self.current_thread = None
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key.
        
        Args:
            api_key: The API key to use for requests.
        """
        self.api_key = api_key
    
    def get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests.
        
        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_sequence_async(self, parameters: Dict[str, Any], 
                             callback: Callable[[pd.DataFrame, str], None],
                             progress_callback: Optional[Callable[[int], None]] = None,
                             status_callback: Optional[Callable[[str], None]] = None,
                             model: str = DEFAULT_MODEL, 
                             temperature: float = DEFAULT_TEMPERATURE,
                             max_retries: int = 3) -> None:
        """Generate a test sequence based on parameters asynchronously.
        
        Args:
            parameters: Dictionary of spring parameters.
            callback: Function to call with the result (DataFrame, error_message).
            progress_callback: Optional function to call with progress updates.
            status_callback: Optional function to call with status messages.
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
        """
        # Cancel any existing operation
        self.cancel_current_operation()
        
        # Create a worker
        self.current_worker = APIClientWorker(
            self, parameters, model, temperature, max_retries
        )
        
        # Connect signals
        self.current_worker.finished.connect(callback)
        if progress_callback:
            self.current_worker.progress.connect(progress_callback)
        if status_callback:
            self.current_worker.status.connect(status_callback)
        
        # Create a thread for the worker
        self.current_thread = threading.Thread(target=self.current_worker.run)
        self.current_thread.daemon = True
        
        # Start the thread
        self.current_thread.start()
    
    def cancel_current_operation(self) -> None:
        """Cancel the current operation."""
        if self.current_worker:
            self.current_worker.cancel()
        
        if self.current_thread and self.current_thread.is_alive():
            # Just let it finish on its own, since we've cancelled the worker
            pass
        
        self.current_worker = None
        self.current_thread = None
    
    def generate_sequence(self, parameters: Dict[str, Any], 
                         model: str = DEFAULT_MODEL, 
                         temperature: float = DEFAULT_TEMPERATURE,
                         max_retries: int = 3) -> Tuple[pd.DataFrame, str]:
        """Generate a test sequence based on parameters (synchronous version).
        
        Note: This method is kept for backward compatibility but should be avoided
        in the UI to prevent freezing.
        
        Args:
            parameters: Dictionary of spring parameters.
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
            
        Returns:
            Tuple of (DataFrame of the sequence, raw response text)
        """
        result = [None, None]  # To store result from callback
        event = threading.Event()
        
        def callback(df, error_msg):
            result[0] = df
            result[1] = error_msg
            event.set()
        
        # Start async operation
        self.generate_sequence_async(
            parameters, callback, None, None, model, temperature, max_retries
        )
        
        # Wait for completion
        event.wait()
        
        return result[0], result[1]
    
    def validate_api_key(self) -> Tuple[bool, str]:
        """Validate the API key with a simple request.
        
        Returns:
            Tuple of (success flag, error message)
        """
        if not self.api_key:
            return False, "API key is empty"
        
        try:
            # Simple test payload that should return quickly
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, are you working?"}
                ],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = self.session.post(
                API_ENDPOINT,
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            
            # Check status code
            if response.status_code == 200:
                return True, "API key is valid"
            elif response.status_code == 401:
                return False, "Invalid API key"
            else:
                return False, f"API error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}" 