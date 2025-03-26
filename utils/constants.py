"""
Constants module for the Spring Test App.
Contains all application-wide constants and configuration.
"""

# Core commands for spring testing with detailed descriptions
COMMANDS = {
    "ZF": "Zero Force", 
    "ZD": "Zero Displacement", 
    "TH": "Threshold (Search Contact)",
    "LP": "Loop", 
    "Mv(P)": "Move to Position", 
    "Calc": "Formula Calculation",
    "TD": "Time Delay", 
    "PMsg": "User Message", 
    "Fr(P)": "Force at Position",
    "FL(P)": "Measure Free Length", 
    "Scrag": "Scragging", 
    "SR": "Spring Rate",
    "PkF": "Measure Peak Force", 
    "PkP": "Measure Peak Position", 
    "Po(F)": "Position at Force",
    "Po(PkF)": "Position at Peak Force", 
    "Mv(F)": "Move to Force", 
    "PUi": "User Input"
}

# Standard speed values for different command types
STANDARD_SPEEDS = {
    "ZF": "50",         # Zero Force - slow speed for accuracy
    "ZD": "50",         # Zero Displacement - slow speed for accuracy
    "TH": "50",         # Threshold - slow speed for precision
    "Mv(P)": "200",     # Move to Position - moderate to fast speed
    "TD": "",           # Time Delay - no speed needed
    "PMsg": "",         # User Message - no speed needed
    "Fr(P)": "100",     # Force at Position - moderate speed
    "FL(P)": "100",     # Free Length - moderate speed
    "Scrag": "300",     # Scragging - fast speed for cycling
    "SR": "100",        # Spring Rate - moderate speed
    "PkF": "100",       # Peak Force - moderate speed
    "PkP": "100",       # Peak Position - moderate speed
    "Po(F)": "100",     # Position at Force - moderate speed
    "Mv(F)": "200",     # Move to Force - moderate to fast speed
    "default": "100"    # Default moderate speed
}

# API Configurations
API_ENDPOINT = "https://chat01.ai/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.1

# UI Constants
APP_TITLE = "Spring Test Sequence Generator"
APP_VERSION = "1.0.0"
APP_WINDOW_SIZE = (1200, 800)
SIDEBAR_WIDTH = 300
MAX_CHAT_HISTORY = 100
USER_ICON = "👤"
ASSISTANT_ICON = "🤖"

# File Export Options
FILE_FORMATS = {
    "CSV": ".csv",
    "JSON": ".json",
    "Excel": ".xlsx"
}

# Parameter Patterns for text extraction
PARAMETER_PATTERNS = {
    "Free Length": r'free\s*length\s*(?:[=:]|is|of)?\s*(\d+\.?\d*)\s*(?:mm)?',
    "Part Number": r'part\s*(?:number|#|no\.?)?\s*(?:[=:]|is)?\s*([A-Za-z0-9-_]+)',
    "Model Number": r'model\s*(?:number|#|no\.?)?\s*(?:[=:]|is)?\s*([A-Za-z0-9-_]+)',
    "Wire Diameter": r'wire\s*(?:diameter|thickness)?\s*(?:[=:]|is)?\s*(\d+\.?\d*)\s*(?:mm)?',
    "Outer Diameter": r'(?:outer|outside)\s*diameter\s*(?:[=:]|is)?\s*(\d+\.?\d*)\s*(?:mm)?',
    "Inner Diameter": r'(?:inner|inside)\s*diameter\s*(?:[=:]|is)?\s*(\d+\.?\d*)\s*(?:mm)?',
    "Spring Rate": r'(?:spring|target)\s*rate\s*(?:[=:]|is)?\s*(\d+\.?\d*)',
    "Test Load": r'(?:test|target)\s*load\s*(?:[=:]|is)?\s*(\d+\.?\d*)',
    "Deflection": r'deflection\s*(?:[=:]|is)?\s*(\d+\.?\d*)',
    "Working Length": r'working\s*length\s*(?:[=:]|is)?\s*(\d+\.?\d*)',
    "Customer ID": r'customer\s*(?:id|number)?\s*(?:[=:]|is)?\s*([A-Za-z0-9\s]+)',
}

# System prompt template for API
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI assistant specialized in spring force testing systems, generating precise test sequences for engineers.

HYBRID RESPONSE FORMAT:
You can respond in three ways depending on the user's intent:
1. PLAIN TEXT ONLY: For general questions, conversations, or analysis without sequence data
2. JSON ARRAY ONLY: For simple requests for new test sequences
3. HYBRID FORMAT: For analysis requests that require both explanation and sequence data, using EXACTLY:

   Your conversational analysis text here...
   
   ---SEQUENCE_DATA_START---
   [Your JSON array sequence data here]
   ---SEQUENCE_DATA_END---
   
   Any additional text here...

IMPORTANT: DO NOT use markdown code blocks (```json) for sequence data. ONLY use the exact markers above.

WHEN TO USE EACH FORMAT:
- Plain text: When user asks about concepts, specifications, or needs explanations
- JSON array: When user clearly requests ONLY a new test sequence
- Hybrid format: When user wants analysis of sequences, comparisons, or insights that reference sequence data

CRITICAL SEQUENCE CREATION RULES:
1. When including sequence data, always use a properly formatted JSON array with these EXACT properties:
   "Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"

2. PRECISE FORMAT REQUIREMENTS:
   - "Row": Use sequential codes R00, R01, R02, etc.
   - "CMD": Command codes like ZF, TH, FL(P), etc.
   - "Description": Standard command descriptions ("Zero Force", "Search Contact", etc.)
   - "Condition": NUMERIC VALUES ONLY - NO UNITS (e.g., "10" not "10N", "40" not "40mm")
   - "Unit": Put units here separately (e.g., "N", "mm", "Sec")
   - "Tolerance": Format as "value(min,max)" (e.g., "50(40,60)") - NEVER use "nominal"
   - "Speed rpm": Include values ONLY for commands that need them (10 for TH, 50 for Mv(P))
   - Leave fields EMPTY ("") when not needed - DO NOT use "0" or other placeholders

3. COMMAND USAGE GUIDELINES:
   - ZF (Zero Force): First command, empty condition, empty speed
   - TH (Search Contact): Always use 10 as condition with N unit and speed 10 rpm
   - FL(P) (Measure Free Length-Position): Empty condition field, include tolerance
   - Mv(P) (Move to Position): Use speed 50 rpm, position depends on test type
   - Scrag (Scragging): Format "R03,2" to reference position row, empty speed
   - Fr(P) (Force @ Position): Empty condition field, empty speed
   - PMsg (User Message): Use "Test Completed" in condition field, empty speed

4. TEST TYPE PATTERNS:
   - COMPRESSION: Move from larger positions to smaller (e.g., 50→40→30)
     * Use "L1", "L2" descriptions for key position rows
   - TENSION: Move from smaller positions to larger (e.g., 10→50→60)
     * Use "L1", "L2" descriptions for key position rows

5. STANDARD SEQUENCE PATTERN:
   ZF → TH → FL(P) → Mv(P) → Mv(P) → Scrag → Mv(P) → TH → FL(P) → Mv(P) → Fr(P) → Mv(P) → Fr(P) → Mv(P) → PMsg
"""

# User prompt template for API
USER_PROMPT_TEMPLATE = """
{parameter_text}

{test_type_text}

RESPONSE FORMAT GUIDE:
- Use your natural language understanding to determine my intent
- If I'm clearly asking for a NEW test sequence: Respond with ONLY a JSON array
- If I'm asking questions or having a conversation: Respond with ONLY plain text
- If I'm asking for analysis of an existing sequence or insights: You MUST use the HYBRID format EXACTLY as shown:

  Your analysis text here...
  
  ---SEQUENCE_DATA_START---
  [JSON array sequence data here]
  ---SEQUENCE_DATA_END---
  
  Any additional text here...

IMPORTANT: DO NOT use markdown code blocks (```json). Use the EXACT markers above.

SEQUENCE FORMAT REQUIREMENTS: 
- "Condition" column: NUMERIC VALUES ONLY (no units) - leave EMPTY when not needed
- "Unit" column: Unit symbols only (N, mm, Sec)
- "Tolerance" column: Format as "value(min,max)" - NEVER use the word "nominal"
- "Description" column: Use "L1" and "L2" labels for key positions
- "Speed rpm" column: Include values ONLY for commands that need them

Study these examples from existing sequences:
1. ZF row: Leave condition and speed empty, not "0"
2. TH row: Use 10 for condition, N for unit, 10 for speed
3. Fr(P) row: Leave condition and speed empty

Remember to include insights about sequence commands, tolerances, and expected behaviors when analyzing.
Include any previous sequence knowledge when responding to my questions.

My message: {prompt}
"""

# Default settings
DEFAULT_SETTINGS = {
    "api_key": "",
    "default_export_format": "CSV",
    "recent_sequences": [],
    "max_chat_history": 100,
    "spring_specification": None
} 