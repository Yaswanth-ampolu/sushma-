"""
Settings service for the Spring Test App.
Contains functions for saving and loading application settings.
"""
import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from models.data_models import SpringSpecification, SetPoint
import pickle

# Default settings
DEFAULT_SETTINGS = {
    "api_key": "",
    "default_export_format": "CSV",
    "recent_sequences": [],
    "max_chat_history": 100,
    "spring_specification": None
}

# App salt for encryption (do not change)
APP_SALT = b'SpringTestApp_2025_Salt_Value'
# App encryption key derivation password
APP_PASSWORD = b'SpringTestApp_Secure_Password_2025'

class SettingsService:
    """Service for managing application settings."""
    
    def __init__(self):
        """Initialize the settings service."""
        # Set up default settings
        self.settings = {
            "api_key": "",
            "theme": "light",
            "spring_specification": None
        }
        
        # Path to settings file
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appdata")
        self.settings_file = os.path.join(data_dir, "settings.dat")
        
        # Create the appdata directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load settings from file
        self.load_settings()
        
        # Initialize spring specification if it doesn't exist
        if "spring_specification" not in self.settings or self.settings["spring_specification"] is None:
            self.settings["spring_specification"] = SpringSpecification().to_dict()
    
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
    
    def load_settings(self):
        """Load settings from file."""
        if not os.path.exists(self.settings_file):
            logging.info("Settings file not found, using defaults")
            return
        
        try:
            # Read encrypted data
            with open(self.settings_file, "rb") as f:
                encrypted_data = f.read()
            
            # Decrypt data
            fernet = Fernet(self._generate_key())
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse JSON
            loaded_settings = json.loads(decrypted_data.decode('utf-8'))
            
            # Update settings with loaded values
            self.settings.update(loaded_settings)
            logging.info("Settings loaded successfully")
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
    
    def save_settings(self):
        """Save settings to disk."""
        try:
            # Ensure the settings directory exists
            data_dir = os.path.dirname(self.settings_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
                
            # Convert settings to JSON
            settings_json = json.dumps(self.settings, indent=2)
            
            # Encrypt data
            fernet = Fernet(self._generate_key())
            encrypted_data = fernet.encrypt(settings_json.encode('utf-8'))
            
            # Write encrypted data
            with open(self.settings_file, "wb") as f:
                f.write(encrypted_data)
                
            logging.info("Settings saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False
    
    def get_api_key(self):
        """Get the API key.
        
        Returns:
            The API key.
        """
        return self.settings.get("api_key", "")
    
    def set_api_key(self, api_key):
        """Set the API key.
        
        Args:
            api_key: The API key to set.
        """
        self.settings["api_key"] = api_key
        self.save_settings()
    
    def get_default_export_format(self):
        """Get the default export format.
        
        Returns:
            The default export format.
        """
        return self.settings.get("default_export_format", "CSV")
    
    def set_default_export_format(self, format):
        """Set the default export format.
        
        Args:
            format: The format to use.
        """
        self.settings["default_export_format"] = format
        self.save_settings()
    
    def add_recent_sequence(self, sequence_id):
        """Add a sequence to the recent sequences list.
        
        Args:
            sequence_id: The ID of the sequence to add.
        """
        recent = self.settings.get("recent_sequences", [])
        
        # Remove the sequence if it already exists
        if sequence_id in recent:
            recent.remove(sequence_id)
        
        # Add to the beginning of the list
        recent.insert(0, sequence_id)
        
        # Limit the list to 10 items
        self.settings["recent_sequences"] = recent[:10]
        self.save_settings()
    
    def get_recent_sequences(self):
        """Get the list of recent sequences.
        
        Returns:
            List of recent sequence IDs.
        """
        return self.settings.get("recent_sequences", [])
    
    def get_spring_specification(self):
        """Get the spring specification.
        
        Returns:
            The SpringSpecification object.
        """
        spec_dict = self.settings.get("spring_specification")
        if spec_dict:
            return SpringSpecification.from_dict(spec_dict)
        else:
            # Return default specification
            return SpringSpecification()
    
    def set_spring_specification(self, specification):
        """Set the spring specification.
        
        Args:
            specification: The SpringSpecification object.
        """
        self.settings["spring_specification"] = specification.to_dict()
        self.save_settings()
    
    def update_spring_basic_info(self, part_name, part_number, part_id, 
                                free_length, coil_count, wire_dia, outer_dia,
                                safety_limit, unit, enabled):
        """Update basic spring specification information.
        
        Args:
            part_name: Part name
            part_number: Part number
            part_id: Part ID
            free_length: Free length in mm
            coil_count: Number of coils
            wire_dia: Wire diameter in mm
            outer_dia: Outer diameter in mm
            safety_limit: Safety limit in N
            unit: Unit (mm or inch)
            enabled: Whether the specification is enabled
        """
        spec = self.get_spring_specification()
        
        spec.part_name = part_name
        spec.part_number = part_number
        spec.part_id = part_id
        spec.free_length_mm = float(free_length)
        spec.coil_count = float(coil_count)
        spec.wire_dia_mm = float(wire_dia)
        spec.outer_dia_mm = float(outer_dia)
        spec.safety_limit_n = float(safety_limit)
        spec.unit = unit
        spec.enabled = enabled
        
        self.set_spring_specification(spec)
    
    def update_set_point(self, index, position, load, tolerance, enabled):
        """Update a set point in the spring specification.
        
        Args:
            index: Set point index (0-based)
            position: Position in mm
            load: Load in N
            tolerance: Tolerance in percent
            enabled: Whether the set point is enabled
        """
        spec = self.get_spring_specification()
        
        # Ensure we have enough set points
        while len(spec.set_points) <= index:
            spec.set_points.append(SetPoint(0.0, 0.0))
        
        # Update the set point
        spec.set_points[index].position_mm = float(position)
        spec.set_points[index].load_n = float(load)
        spec.set_points[index].tolerance_percent = float(tolerance)
        spec.set_points[index].enabled = enabled
        
        self.set_spring_specification(spec)
    
    def delete_set_point(self, index):
        """Delete a set point from the spring specification.
        
        Args:
            index: Set point index (0-based)
        """
        spec = self.get_spring_specification()
        
        if 0 <= index < len(spec.set_points):
            spec.set_points.pop(index)
            self.set_spring_specification(spec)
    
    def add_set_point(self):
        """Add a new set point to the spring specification."""
        spec = self.get_spring_specification()
        spec.set_points.append(SetPoint(0.0, 0.0))
        self.set_spring_specification(spec) 