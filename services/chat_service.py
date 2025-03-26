"""
Chat service for the Spring Test App.
Contains functions for managing chat history.
"""
import os
import json
import base64
import logging
import pickle
from typing import List, Optional
from models.data_models import ChatMessage
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# App salt for encryption (do not change) - same as settings_service
APP_SALT = b'SpringTestApp_2025_Salt_Value'
# App encryption key derivation password - same as settings_service
APP_PASSWORD = b'SpringTestApp_Secure_Password_2025'

class ChatService:
    """Service for managing chat history."""
    
    def __init__(self, settings_service=None, max_history: int = 100):
        """Initialize the chat service.
        
        Args:
            settings_service: Settings service instance.
            max_history: Maximum number of messages to keep in history.
        """
        self.history = []
        self.max_history = max_history
        self.settings_service = settings_service
        
        # Path to chat history file
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")
        self.history_file = os.path.join(data_dir, "chat_history.dat")
        
        # Create the data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load chat history
        self.load_history()
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists.
        
        Returns:
            Path to the data directory.
        """
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            # Create .gitignore to prevent accidental commit of sensitive data
            with open(os.path.join(data_dir, ".gitignore"), "w") as f:
                f.write("# Ignore all files in this directory\n*\n!.gitignore\n")
        return data_dir
    
    def _generate_key(self):
        """Generate encryption key from app password.
        
        Returns:
            Encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=APP_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(APP_PASSWORD))
        return key
    
    def add_message(self, role: str, content: str) -> ChatMessage:
        """Add a message to the chat history.
        
        Args:
            role: Role of the message sender (user, assistant).
            content: Content of the message.
            
        Returns:
            The added message.
        """
        message = ChatMessage(role=role, content=content)
        self.history.append(message)
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return message
    
    def get_history(self) -> List[ChatMessage]:
        """Get the chat history.
        
        Returns:
            List of chat messages.
        """
        return self.history
    
    def clear_history(self) -> None:
        """Clear the chat history."""
        self.history = []
    
    def load_history(self) -> None:
        """Load chat history from file."""
        if not os.path.exists(self.history_file):
            logging.info("Chat history file not found, using empty history")
            return
        
        try:
            # Read encrypted data
            with open(self.history_file, "rb") as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                logging.warning("Chat history file is empty")
                return
            
            # Decrypt data
            fernet = Fernet(self._generate_key())
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Try to parse as pickle first (new format)
            try:
                history_data = pickle.loads(decrypted_data)
                if isinstance(history_data, list):
                    self.history = history_data
                    logging.info(f"Loaded {len(self.history)} chat messages from pickle format")
                    return
            except Exception as pickle_error:
                logging.warning(f"Could not parse chat history as pickle: {str(pickle_error)}")
                
            # Fall back to JSON format (old format)
            try:
                history_data = json.loads(decrypted_data.decode('utf-8'))
                
                if not isinstance(history_data, list):
                    logging.warning("Chat history is not a list, using empty history")
                    return
                
                # Convert to ChatMessage objects
                self.history = [
                    ChatMessage(role=msg.get("role", "assistant"), content=msg.get("content", ""))
                    for msg in history_data if "content" in msg
                ]
                
                logging.info(f"Loaded {len(self.history)} chat messages from JSON format")
            except Exception as json_error:
                logging.warning(f"Could not parse chat history as JSON: {str(json_error)}")
                raise Exception(f"Failed to parse chat history in any supported format")
                
        except Exception as e:
            logging.error(f"Error loading chat history: {str(e)}")
            self.history = []
    
    def save_history(self):
        """Save chat history to disk."""
        try:
            # Ensure the data directory exists
            data_dir = os.path.dirname(self.history_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Serialize the history (limited to max_history)
            history_data = self.history[-self.max_history:]
            serialized = pickle.dumps(history_data)
            
            # Encrypt the data
            fernet = Fernet(self._generate_key())
            encrypted_data = fernet.encrypt(serialized)
            
            # Write to file
            with open(self.history_file, "wb") as f:
                f.write(encrypted_data)
                
            logging.info("Chat history saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving chat history: {e}")
            return False
    
    def get_message(self, index: int) -> Optional[ChatMessage]:
        """Get a message from the chat history.
        
        Args:
            index: Index of the message to get.
            
        Returns:
            The message, or None if index is out of range.
        """
        if 0 <= index < len(self.history):
            return self.history[index]
        return None
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message from the chat history.
        
        Returns:
            The last message, or None if history is empty.
        """
        if self.history:
            return self.history[-1]
        return None
    
    def get_last_user_message(self) -> Optional[ChatMessage]:
        """Get the last user message from the chat history.
        
        Returns:
            The last user message, or None if none found.
        """
        for message in reversed(self.history):
            if message.role == "user":
                return message
        return None
    
    def get_last_assistant_message(self) -> Optional[ChatMessage]:
        """Get the last assistant message from the chat history.
        
        Returns:
            The last assistant message, or None if none found.
        """
        for message in reversed(self.history):
            if message.role == "assistant":
                return message
        return None 