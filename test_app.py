"""
Test script for the Spring Test App.
"""
import sys
import os
from PyQt5.QtWidgets import QApplication

# Add current directory to path to make imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.settings_service import SettingsService
from services.sequence_generator import SequenceGenerator
from services.chat_service import ChatService
from services.export_service import ExportService


def test_services():
    """Test that all services initialize correctly."""
    print("Testing services initialization...")
    
    # Create services
    settings_service = SettingsService()
    export_service = ExportService()
    chat_service = ChatService()
    sequence_generator = SequenceGenerator()
    
    # Check settings
    print(f"Default export format: {settings_service.get_default_export_format()}")
    print(f"Dark mode: {settings_service.get_dark_mode()}")
    
    # Check export formats
    formats = export_service.get_supported_formats()
    print(f"Supported export formats: {formats}")
    
    # Create a chat message
    message = chat_service.add_message("assistant", "Hello, I'm the test assistant.")
    print(f"Added chat message: {message.content}")
    
    # Clear chat history
    chat_service.clear_history()
    print("Chat history cleared.")
    
    print("Services initialization test passed.")
    return True


def main():
    """Main entry point for testing."""
    # Create application
    app = QApplication(sys.argv)
    
    # Test services
    test_services()
    
    # Not actually running the app
    print("Tests completed successfully.")


if __name__ == "__main__":
    main() 