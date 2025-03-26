# Spring Test App Modular Structure

## Core Modules

1. **models/**
   - `data_models.py` - DataFrame models and data structures
   - `command_models.py` - Command definitions and properties
   - `table_models.py` - Table visualization models

2. **utils/**
   - `api_client.py` - API communication
   - `text_parser.py` - Parameter extraction from text
   - `constants.py` - Application constants
   - `validators.py` - Input validation utilities

3. **ui/**
   - `main_window.py` - Main application window
   - `sidebar.py` - Command reference and settings panel
   - `chat_panel.py` - Chat interface components
   - `results_panel.py` - Results display and export
   - `dialogs.py` - Custom dialog components
   - `styles.py` - UI styling and themes

4. **services/**
   - `sequence_generator.py` - Business logic for sequence generation
   - `chat_service.py` - Chat history management
   - `export_service.py` - Export functionality (CSV, JSON)
   - `settings_service.py` - App settings management

5. **main.py** - Application entry point

## Additional Features to Implement

1. **Authentication**
   - API key management/storage
   - User profiles

2. **Enhanced UI**
   - Dark/light theme toggle
   - Responsive layouts
   - Custom styling
   - Progress indicators

3. **Extended Functionality**
   - Predefined templates
   - Recent history
   - Batch processing
   - Results visualization/charts
   - Parameter validation
   - Offline mode

4. **Production Features**
   - Logging
   - Error handling
   - Auto-updates
   - Installer configuration
   - Documentation

## Deployment Considerations

1. **Exe Packaging**
   - PyInstaller configuration
   - Resource bundling
   - Single-file vs directory mode
   - Splash screen

2. **Distribution**
   - Version management
   - Update mechanism
   - Installation process 