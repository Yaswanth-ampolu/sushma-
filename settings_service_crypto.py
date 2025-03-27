#!/usr/bin/env python
"""
Settings Service with Encryption

This module extends the application's settings functionality with encryption capabilities.
It can be integrated with the existing settings service to provide transparent encryption.
"""

import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logger
logger = logging.getLogger(__name__)

class SettingsServiceCrypto:
    """Settings service with encryption support.
    
    This class can be used to replace or extend the existing settings service,
    providing encrypted storage of sensitive application settings.
    """
    
    def __init__(self, settings_file="appdata/settings.dat", password=None):
        """Initialize the settings service with encryption.
        
        Args:
            settings_file: Path to the settings file
            password: Password for encryption/decryption (optional)
        """
        self.settings_file = settings_file
        self.settings = {}
        self.password = password or "sushma_default_key"
        self.salt = b'sushma_salt_value_123'
        self.key = self._derive_key()
        
        # Create the appdata directory if it doesn't exist
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        
        # Load settings if file exists
        if os.path.exists(settings_file):
            self.load_settings()
    
    def _derive_key(self):
        """Derive encryption key from password."""
        password_bytes = self.password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def load_settings(self):
        """Load and decrypt settings from the settings file."""
        try:
            # Determine if file is encrypted by checking for Fernet format marker
            with open(self.settings_file, 'rb') as f:
                data = f.read()
            
            # Check if data looks encrypted (Fernet encrypted data starts with gAAAAA)
            is_encrypted = data.startswith(b'gAAAAA')
            
            if is_encrypted:
                # Decrypt the data
                fernet = Fernet(self.key)
                try:
                    decrypted_data = fernet.decrypt(data)
                    self.settings = json.loads(decrypted_data.decode('utf-8'))
                    logger.info("Settings loaded and decrypted successfully")
                except Exception as e:
                    logger.error(f"Failed to decrypt settings: {str(e)}")
                    # Initialize with empty settings if decryption fails
                    self.settings = {}
            else:
                # Load unencrypted data - for backward compatibility
                try:
                    self.settings = json.loads(data.decode('utf-8'))
                    logger.info("Settings loaded successfully (unencrypted)")
                except json.JSONDecodeError:
                    logger.error("Failed to parse settings file")
                    self.settings = {}
        except FileNotFoundError:
            logger.warning(f"Settings file not found: {self.settings_file}")
            self.settings = {}
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            self.settings = {}
    
    def save_settings(self, encrypt=True):
        """Save settings to file with optional encryption.
        
        Args:
            encrypt: Whether to encrypt the settings (default: True)
        """
        try:
            # Serialize settings to JSON
            json_data = json.dumps(self.settings, indent=2)
            
            if encrypt:
                # Encrypt the data
                fernet = Fernet(self.key)
                encrypted_data = fernet.encrypt(json_data.encode('utf-8'))
                
                # Write encrypted data
                with open(self.settings_file, 'wb') as f:
                    f.write(encrypted_data)
                logger.info("Settings saved with encryption")
            else:
                # Write unencrypted data
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                logger.info("Settings saved without encryption")
            
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get_setting(self, key, default=None):
        """Get a setting value by key.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default if not found
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key, value, save=True):
        """Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
            save: Whether to save settings after setting the value
            
        Returns:
            True if successful, False otherwise
        """
        self.settings[key] = value
        
        if save:
            return self.save_settings()
        return True
    
    def delete_setting(self, key, save=True):
        """Delete a setting.
        
        Args:
            key: Setting key to delete
            save: Whether to save settings after deletion
            
        Returns:
            True if successful, False otherwise
        """
        if key in self.settings:
            del self.settings[key]
            
            if save:
                return self.save_settings()
        return True
    
    def change_password(self, new_password):
        """Change the encryption password.
        
        Args:
            new_password: New password for encryption
            
        Returns:
            True if successful, False otherwise
        """
        # Store the current settings
        current_settings = self.settings
        
        # Update the password and derive a new key
        self.password = new_password
        self.key = self._derive_key()
        
        # Re-save settings with the new key
        self.settings = current_settings
        return self.save_settings()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s [%(levelname)s] %(message)s')
    
    # Create an instance with a custom password
    service = SettingsServiceCrypto(password="test_password")
    
    # Set some test settings
    service.set_setting("api_key", "sk-12345abcdef")
    service.set_setting("user_preferences", {
        "theme": "dark",
        "language": "en",
        "notifications": True
    })
    
    print("Settings saved with encryption.")
    
    # Create a new instance to load the settings
    new_service = SettingsServiceCrypto(password="test_password")
    
    # Display the loaded settings
    print("\nLoaded settings:")
    print(f"API Key: {new_service.get_setting('api_key')}")
    print(f"User Preferences: {new_service.get_setting('user_preferences')}")
    
    # Try with wrong password to show decryption failure
    wrong_service = SettingsServiceCrypto(password="wrong_password")
    print(f"\nWith wrong password: {wrong_service.get_setting('api_key', 'Decryption failed')}")
    
    # Change password
    service.change_password("new_password")
    print("\nPassword changed. Testing with new password:")
    
    # Test with new password
    newer_service = SettingsServiceCrypto(password="new_password")
    print(f"API Key with new password: {newer_service.get_setting('api_key')}")
    
    # Save an unencrypted version for demonstration
    service.save_settings(encrypt=False)
    print("\nSettings also saved without encryption for comparison.") 