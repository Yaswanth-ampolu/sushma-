# Spring Test Sequence Generator

A desktop application for generating test sequences for spring testing machines. This application uses modern large language models to generate test sequences based on natural language descriptions of spring parameters.

## Features

- Natural language input for spring parameters
- AI-powered sequence generation
- Export to multiple formats (CSV, JSON, Excel)
- Dark/light theme support
- History of generated sequences
- Responsive UI

## Installation

### Requirements

- Python 3.8 or higher
- PyQt5
- Pandas
- Requests
- PyInstaller (for building executable)

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/spring-test-app.git
   cd spring-test-app
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

### Using Executable

1. Download the latest release from the releases page
2. Extract the ZIP file
3. Run `SpringTestApp.exe`

## Building from Source

To build the executable from source:

```
python build_exe.py --clean
```

Options:
- `--onefile`: Build a single executable file
- `--console`: Show console window 
- `--clean`: Clean build files before building

## Usage

1. Enter your API key in the sidebar settings
2. Enter your spring parameters in natural language in the chat box
   - Example: "Generate a test sequence for a compression spring with free length 50mm, wire diameter 2mm, and spring rate 5 N/mm"
3. Click "Generate Sequence"
4. View the generated sequence in the results panel
5. Export the sequence to your preferred format

## Project Structure

- `models/`: Data models for chat messages and sequences
- `services/`: Business logic and services
- `ui/`: User interface components
- `utils/`: Utility functions and constants
- `main.py`: Application entry point
- `build_exe.py`: Script for building executable

## API Key

This application requires an API key to access the language model API. You can obtain a key from:
- OpenAI API (https://openai.com/api/)
- Azure OpenAI Service
- Or another compatible LLM provider

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 