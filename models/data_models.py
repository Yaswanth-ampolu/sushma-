"""
Data models module for the Spring Test App.
Contains classes for chat messages and other data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class ChatMessage:
    """Represents a single chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the chat message to a dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a ChatMessage instance from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        )


@dataclass
class TestSequence:
    """Represents a generated test sequence with metadata."""
    rows: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the test sequence to a dictionary."""
        return {
            "rows": self.rows,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestSequence':
        """Create a TestSequence instance from a dictionary."""
        return cls(
            rows=data["rows"],
            parameters=data["parameters"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            name=data.get("name")
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the test sequence to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TestSequence':
        """Create a TestSequence instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class SetPoint:
    """Represents a set point for spring testing."""
    position_mm: float
    load_n: float
    tolerance_percent: float = 10.0
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the set point to a dictionary."""
        return {
            "position_mm": self.position_mm,
            "load_n": self.load_n,
            "tolerance_percent": self.tolerance_percent,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SetPoint':
        """Create a SetPoint instance from a dictionary."""
        return cls(
            position_mm=data.get("position_mm", 0.0),
            load_n=data.get("load_n", 0.0),
            tolerance_percent=data.get("tolerance_percent", 10.0),
            enabled=data.get("enabled", True)
        )


@dataclass
class SpringSpecification:
    """Specifications for a spring to be tested."""
    part_name: str = "Demo Spring"
    part_number: str = "Demo Spring-1"
    part_id: int = 28
    free_length_mm: float = 58.0
    coil_count: float = 7.5
    wire_dia_mm: float = 3.0
    outer_dia_mm: float = 32.0
    set_points: List[SetPoint] = field(default_factory=list)
    safety_limit_n: float = 300.0
    unit: str = "mm"  # mm or inch
    enabled: bool = True
    
    def __post_init__(self):
        """Initialize default set points if none are provided."""
        if not self.set_points:
            self.set_points = [
                SetPoint(40.0, 23.6),
                SetPoint(33.0, 34.14),
                SetPoint(28.0, 42.36)
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the spring specification to a dictionary."""
        return {
            "part_name": self.part_name,
            "part_number": self.part_number,
            "part_id": self.part_id,
            "free_length_mm": self.free_length_mm,
            "coil_count": self.coil_count,
            "wire_dia_mm": self.wire_dia_mm,
            "outer_dia_mm": self.outer_dia_mm,
            "set_points": [sp.to_dict() for sp in self.set_points],
            "safety_limit_n": self.safety_limit_n,
            "unit": self.unit,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpringSpecification':
        """Create a SpringSpecification instance from a dictionary."""
        spec = cls(
            part_name=data.get("part_name", "Demo Spring"),
            part_number=data.get("part_number", "Demo Spring-1"),
            part_id=data.get("part_id", 28),
            free_length_mm=data.get("free_length_mm", 58.0),
            coil_count=data.get("coil_count", 7.5),
            wire_dia_mm=data.get("wire_dia_mm", 3.0),
            outer_dia_mm=data.get("outer_dia_mm", 32.0),
            set_points=[],  # Will be set below
            safety_limit_n=data.get("safety_limit_n", 300.0),
            unit=data.get("unit", "mm"),
            enabled=data.get("enabled", True)
        )
        
        # Set the set points
        if "set_points" in data:
            spec.set_points = [SetPoint.from_dict(sp) for sp in data["set_points"]]
        
        return spec
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the spring specification to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SpringSpecification':
        """Create a SpringSpecification instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def to_prompt_text(self) -> str:
        """Convert the spring specification to text for use in AI prompts."""
        text = f"Spring Specifications:\n"
        text += f"Part Name: {self.part_name}\n"
        text += f"Part Number: {self.part_number}\n"
        text += f"ID: {self.part_id}\n"
        text += f"Free Length: {self.free_length_mm} mm\n"
        text += f"No of Coils: {self.coil_count}\n"
        text += f"Wire Dia: {self.wire_dia_mm} mm\n"
        text += f"OD: {self.outer_dia_mm} mm\n"
        
        for i, sp in enumerate(self.set_points, 1):
            if sp.enabled:
                text += f"Set Point-{i} in mm: {sp.position_mm} mm\n"
                text += f"Set Point-{i} Load In N: {sp.load_n}±{sp.tolerance_percent}% N\n"
        
        text += f"Safety limit: {self.safety_limit_n} N\n"
        text += f"Unit: {self.unit}\n"
        
        return text


@dataclass
class AppSettings:
    """Application settings that can be saved and loaded."""
    api_key: str = ""
    default_export_format: str = "CSV"
    recent_sequences: List[str] = field(default_factory=list)
    max_chat_history: int = 100
    spring_specification: Optional[SpringSpecification] = None
    
    def __post_init__(self):
        """Initialize default spring specification if none is provided."""
        if self.spring_specification is None:
            self.spring_specification = SpringSpecification()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the settings to a dictionary."""
        return {
            "api_key": self.api_key,
            "default_export_format": self.default_export_format,
            "recent_sequences": self.recent_sequences,
            "max_chat_history": self.max_chat_history,
            "spring_specification": self.spring_specification.to_dict() if self.spring_specification else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create an AppSettings instance from a dictionary."""
        spring_spec_data = data.get("spring_specification")
        spring_spec = SpringSpecification.from_dict(spring_spec_data) if spring_spec_data else None
        
        return cls(
            api_key=data.get("api_key", ""),
            default_export_format=data.get("default_export_format", "CSV"),
            recent_sequences=data.get("recent_sequences", []),
            max_chat_history=data.get("max_chat_history", 100),
            spring_specification=spring_spec
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the settings to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AppSettings':
        """Create an AppSettings instance from a JSON string."""
        return cls.from_dict(json.loads(json_str)) 