"""
Chat service for the Spring Test App.
Contains functions for managing chat history.
"""
import os
import json
import base64
import logging
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
        self.data_dir = self._ensure_data_dir()
        self.history_file = os.path.join(self.data_dir, "chat_history.dat")
        self.encryption_key = self._generate_key()
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
            fernet = Fernet(self.encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            history_data = json.loads(decrypted_data.decode('utf-8'))
            
            if not isinstance(history_data, list):
                logging.warning("Chat history is not a list, using empty history")
                return
            
            # Convert to ChatMessage objects
            self.history = [
                ChatMessage(role=msg.get("role", "assistant"), content=msg.get("content", ""))
                for msg in history_data if "content" in msg
            ]
            
            logging.info(f"Loaded {len(self.history)} chat messages")
        except Exception as e:
            logging.error(f"Error loading chat history: {str(e)}")
            self.history = []
    
    def save_history(self) -> None:
        """Save chat history to file."""
        try:
            # Ensure the data directory exists
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
                
            # Skip if history is empty
            if not self.history:
                logging.info("No chat history to save")
                # Create empty file if it doesn't exist
                if not os.path.exists(self.history_file):
                    with open(self.history_file, "wb") as f:
                        pass
                return
            
            # Convert to JSON-serializable format
            history_data = [
                {"role": msg.role, "content": msg.content}
                for msg in self.history
            ]
            
            # Convert to JSON
            history_json = json.dumps(history_data, indent=2)
            
            # Encrypt data
            fernet = Fernet(self.encryption_key)
            encrypted_data = fernet.encrypt(history_json.encode('utf-8'))
            
            # Write encrypted data
            with open(self.history_file, "wb") as f:
                f.write(encrypted_data)
            
            logging.info(f"Saved {len(self.history)} chat messages")
        except Exception as e:
            logging.error(f"Error saving chat history: {str(e)}")
            # Try to create an empty file if we can't save
            try:
                if not os.path.exists(self.data_dir):
                    os.makedirs(self.data_dir)
                with open(self.history_file, "wb") as f:
                    pass
            except Exception as inner_e:
                logging.error(f"Failed to create empty history file: {str(inner_e)}")
                pass
    
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