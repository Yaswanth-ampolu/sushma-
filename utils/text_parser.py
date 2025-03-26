"""
Text parser module for the Spring Test App.
Contains functions for extracting spring parameters from natural language text.
"""
import re
from typing import Dict, Any
from datetime import datetime
from utils.constants import PARAMETER_PATTERNS, COMMANDS


def is_sequence_request(text: str) -> bool:
    """
    Determine if the text is likely a request for generating a test sequence.
    
    Args:
        text: The text to analyze.
        
    Returns:
        True if the text is likely a test sequence request, False otherwise.
    """
    # Check for explicit test sequence request indicators
    sequence_keywords = [
        r'\b(?:generat|creat|mak)(?:e|ing)?\s+(?:a|the)?\s+(?:test)?\s*sequence',
        r'\b(?:test|testing)\s+sequence',
        r'\bsequence\s+for',
        r'\bspring\s+test',
        r'\bcompression\s+test',
        r'\btension\s+test',
        r'\b(?:displacement|deflection|height)\s+test',
        r'\bmeasur(?:e|ing)\s+(?:a|the)?\s+spring'
    ]
    
    # Check if any of the sequence keywords are in the text
    for pattern in sequence_keywords:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check for test type specific keywords
    test_type_keywords = {
        'compression': [r'\bcompress(?:ion)?', r'\bpush(?:ing)?', r'\bdeflect(?:ion)?', r'\bdeformation'],
        'tension': [r'\btens(?:ion)?', r'\bextend(?:ing)?', r'\bpull(?:ing)?', r'\bstretch(?:ing)?', r'\bextension']
    }
    
    # Check if there's a combination of "test" word with test type keywords
    if re.search(r'\btest', text, re.IGNORECASE):
        for test_type, patterns in test_type_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
    
    # Check for casual conversation patterns that should NOT trigger sequence generation
    conversation_patterns = [
        r'^(?:hi|hello|hey|greetings)',
        r'^(?:how are you|what can you do|who are you)',
        r'\b(?:explain|tell me about|what is|how does)',
        r'\b(?:thanks|thank you|good job)',
        r'^(?:[?])'  # Text starting with a question mark
    ]
    
    # If text matches a conversational pattern, it's likely not a sequence request
    for pattern in conversation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # If no specific indicators found, check for spring parameter patterns
    # which might indicate an implicit request for a test sequence
    parameter_count = 0
    for _, pattern in PARAMETER_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            parameter_count += 1
    
    # If multiple spring parameters are mentioned, it's likely a sequence request
    if parameter_count >= 2:
        return True
    
    # By default, assume it's not a sequence request if no clear indicators
    return False


def extract_parameters(text: str) -> Dict[str, Any]:
    """
    Extract spring parameters from natural language text.
    
    Args:
        text: The natural language text to extract parameters from.
        
    Returns:
        A dictionary of extracted parameters.
    """
    parameters = {}
    
    # Extract test type with more flexible pattern matching
    compression_pattern = r'\b(?:compress|compression|comp|compressive|pushing|push|pressing|press)\b'
    tension_pattern = r'\b(?:tens|tension|extension|extend|tensile|extending|pulling|pull|stretching|stretch)\b'
    
    if re.search(compression_pattern, text, re.IGNORECASE):
        parameters["Test Type"] = "Compression"
    elif re.search(tension_pattern, text, re.IGNORECASE):
        parameters["Test Type"] = "Tension"
    
    # Extract parameters based on patterns
    for param, pattern in PARAMETER_PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Convert to float if it's a numeric value
            if param not in ["Part Number", "Model Number", "Customer ID"]:
                try:
                    parameters[param] = float(value)
                except ValueError:
                    parameters[param] = value
            else:
                parameters[param] = value
    
    # Add timestamp and original prompt to parameters
    parameters["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parameters["prompt"] = text
    
    return parameters


def extract_command_sequence(text: str) -> Dict[str, Any]:
    """
    Extract a command sequence from text (usually API response).
    
    Args:
        text: The text containing a command sequence, often from API response.
        
    Returns:
        A dictionary representation of the command sequence.
    """
    import json
    
    # Try to extract JSON from the response
    json_match = re.search(r'```json\n(.*?)\n```|(\[.*\])', text, re.DOTALL)
    if json_match:
        json_content = json_match.group(1) or json_match.group(2)
    else:
        json_content = text
    
    # Clean up any remaining markdown or text
    json_content = re.sub(r'^```.*|```$', '', json_content, flags=re.MULTILINE).strip()
    
    # Try to parse the JSON
    try:
        data = json.loads(json_content)
        
        # Post-process and standardize the data format
        standardized_data = standardize_sequence_data(data)
        return standardized_data
        
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract just the array part
        array_match = re.search(r'\[(.*)\]', json_content, re.DOTALL)
        if array_match:
            cleaned_json = '[' + array_match.group(1) + ']'
            try:
                data = json.loads(cleaned_json)
                # Apply standardization
                standardized_data = standardize_sequence_data(data)
                return standardized_data
            except json.JSONDecodeError:
                pass
    
    # If all parsing attempts fail, return an empty list
    return []


def standardize_sequence_data(data):
    """
    Standardize the sequence data to match expected format without changing values.
    
    Args:
        data: The parsed JSON data.
        
    Returns:
        Standardized data that matches our expected format.
    """
    standardized_data = []
    
    # Required columns and their correct names
    required_columns = ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]
    
    # Map possible variations of column names to the standard name
    column_map = {
        "Cmd": "CMD",
        "Command": "CMD",
        "cmd": "CMD",
        "Units": "Unit",
        "unit": "Unit",
        "Speed": "Speed rpm"
    }
    
    # Command descriptions map to ensure consistent descriptions
    description_map = {
        "ZF": "Zero Force",
        "TH": "Search Contact",
        "FL(P)": "Measure Free Length-Position",
        "Mv(P)": "Move to Position",  # Default, but preserve L1/L2 if specified
        "Fr(P)": "Force @ Position",
        "Scrag": "Scragging",
        "TD": "Time Delay",
        "PMsg": "User Message"
    }
    
    for row in data:
        # Create a standardized row
        std_row = {}
        
        # First, normalize column names
        for key, value in row.items():
            std_key = column_map.get(key, key)
            std_row[std_key] = value
        
        # Ensure CMD is uppercase
        if "cmd" in std_row:
            std_row["CMD"] = std_row["cmd"]
            del std_row["cmd"]
        
        # Ensure consistent command descriptions, but preserve special cases
        if "CMD" in std_row:
            cmd = std_row["CMD"]
            current_desc = std_row.get("Description", "")
            
            # Special case for Mv(P) with "L1" or "L2" in description
            if cmd == "Mv(P)" and current_desc:
                if "L1" in current_desc:
                    std_row["Description"] = "L1"
                elif "L2" in current_desc:
                    std_row["Description"] = "L2"
                else:
                    std_row["Description"] = description_map.get(cmd, current_desc)
            else:
                std_row["Description"] = description_map.get(cmd, current_desc)
        
        # Format tolerance value correctly - ensure it's in "50(40,60)" format if not already
        if "Tolerance" in std_row and std_row["Tolerance"]:
            tolerance_str = str(std_row["Tolerance"])
            if "nominal" in tolerance_str.lower():
                # Convert "nominal(min,max)" to "nominal(min,max)"
                tolerance_parts = re.match(r'.*?(\d+(?:\.\d+)?).*?\((\d+(?:\.\d+)?),(\d+(?:\.\d+)?)\)', tolerance_str)
                if tolerance_parts:
                    nominal, min_val, max_val = tolerance_parts.groups()
                    std_row["Tolerance"] = f"{nominal}({min_val},{max_val})"
        
        # Ensure condition has no units (e.g. "50" not "50 mm")
        if "Condition" in std_row and std_row["Condition"]:
            condition_str = str(std_row["Condition"])
            if isinstance(condition_str, str) and not re.match(r'^R\d+,\d+$', condition_str):  # Skip Scrag references
                # Extract just the numeric part if it contains units
                match = re.match(r'(\d+(?:\.\d+)?)', condition_str)
                if match and match.group(1) != condition_str:
                    std_row["Condition"] = match.group(1)
        
        # Add any missing required columns without changing existing values
        for col in required_columns:
            if col not in std_row:
                std_row[col] = ""
        
        # Add to standardized data
        standardized_data.append(std_row)
    
    return standardized_data


def format_parameter_text(parameters: Dict[str, Any]) -> str:
    """
    Format parameters for display or for use in API prompts.
    
    Args:
        parameters: Dictionary of parameters.
        
    Returns:
        Formatted parameter text.
    """
    lines = []
    
    # Format each parameter as a line
    for key, value in parameters.items():
        # Skip timestamp and other metadata
        if key in ["Timestamp"]:
            continue
            
        # Format numeric values with appropriate precision
        if isinstance(value, float):
            # Use 1 decimal place for most values, 2 for small values
            if value < 0.1:
                formatted_value = f"{value:.3f}"
            elif value < 1:
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = f"{value:.1f}"
                
            # Add units based on parameter type
            if "Length" in key or "Diameter" in key:
                formatted_value += " mm"
            elif "Force" in key or "Load" in key:
                formatted_value += " N"
            elif "Rate" in key:
                formatted_value += " N/mm"
        else:
            formatted_value = str(value)
            
        lines.append(f"{key}: {formatted_value}")
    
    return "\n".join(lines)


def extract_error_message(response_text: str) -> str:
    """
    Extract error message from API response.
    
    Args:
        response_text: The API response text.
        
    Returns:
        Extracted error message or empty string if none found.
    """
    # Common error patterns
    error_patterns = [
        r'error["\']?\s*:\s*["\']([^"\']+)["\']',  # "error": "message"
        r'message["\']?\s*:\s*["\']([^"\']+)["\']',  # "message": "error message"
        r'ERROR:\s*(.+?)(?:\n|$)',  # ERROR: message
        r'Exception:\s*(.+?)(?:\n|$)',  # Exception: message
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "" 