"""
Main entry point for the Spring Test App.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Add current directory to path to make imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.settings_service import SettingsService
from services.sequence_generator import SequenceGenerator
from services.chat_service import ChatService
from services.export_service import ExportService, TemplateManager

# Import UI components
from ui.main_window import create_main_window
from ui.styles import apply_theme


def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point."""
    # Set up logging
    setup_logging()
    
    logging.info("Starting Spring Test App")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Spring Test Sequence Generator")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        logging.info(f"Application icon set from {icon_path}")
    else:
        logging.warning(f"Icon file not found at {icon_path}")
    
    # Create services
    logging.info("Initializing services")
    settings_service = SettingsService()
    export_service = ExportService()
    chat_service = ChatService(settings_service)
    
    # Get API key from settings
    api_key = settings_service.get_api_key()
    
    # Create sequence generator with API key
    sequence_generator = SequenceGenerator()
    sequence_generator.set_api_key(api_key)
    
    # Set spring specifications from settings
    spring_specification = settings_service.get_spring_specification()
    sequence_generator.set_spring_specification(spring_specification)
    
    # Create and show main window
    logging.info("Creating main window")
    window = create_main_window(
        settings_service=settings_service,
        sequence_generator=sequence_generator,
        chat_service=chat_service,
        export_service=export_service
    )
    
    # Apply theme
    apply_theme(window)
    
    window.show()
    
    # Start event loop
    logging.info("Application started")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 