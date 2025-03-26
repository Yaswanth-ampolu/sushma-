"""
Export service for the Spring Test App.
Contains classes and functions for exporting sequences to different formats.
"""
import os
import pandas as pd
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from models.data_models import TestSequence


class ExportService:
    """Service for exporting test sequences to different formats."""
    
    def __init__(self):
        """Initialize the export service."""
        self.supported_formats = {
            "CSV": self._export_csv,
            "JSON": self._export_json,
            "Excel": self._export_excel,
        }
    
    def export_sequence(self, sequence: TestSequence, file_path: str, format_name: str = None) -> Tuple[bool, str]:
        """Export a sequence to a file.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            format_name: Format to export to. If None, infer from file extension.
            
        Returns:
            Tuple of (success flag, error message)
        """
        # If format is not specified, infer from file extension
        if format_name is None:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == ".csv":
                format_name = "CSV"
            elif ext == ".json":
                format_name = "JSON"
            elif ext in [".xlsx", ".xls"]:
                format_name = "Excel"
            else:
                return False, f"Unsupported file extension: {ext}"
        
        # Check if format is supported
        if format_name not in self.supported_formats:
            return False, f"Unsupported format: {format_name}"
        
        # Export the sequence
        try:
            export_func = self.supported_formats[format_name]
            return export_func(sequence, file_path)
        except Exception as e:
            return False, f"Export error: {str(e)}"
    
    def _export_csv(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to CSV.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Create DataFrame from sequence
            df = pd.DataFrame(sequence.rows)
            
            # Add a header row with metadata
            metadata = [
                f"# Spring Test Sequence",
                f"# Created: {sequence.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            
            # Add parameter information
            for key, value in sequence.parameters.items():
                # Skip timestamp and other metadata
                if key in ["Timestamp"]:
                    continue
                metadata.append(f"# {key}: {value}")
            
            # Write to file
            with open(file_path, "w") as f:
                # Write metadata
                for line in metadata:
                    f.write(line + "\n")
                
                # Write CSV
                df.to_csv(f, index=False)
            
            return True, ""
        except Exception as e:
            return False, f"CSV export error: {str(e)}"
    
    def _export_json(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to JSON.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Convert sequence to dict
            data = sequence.to_dict()
            
            # Write to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            
            return True, ""
        except Exception as e:
            return False, f"JSON export error: {str(e)}"
    
    def _export_excel(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to Excel.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Create DataFrame from sequence
            df = pd.DataFrame(sequence.rows)
            
            # Create parameters DataFrame
            param_data = [[key, str(value)] for key, value in sequence.parameters.items() if key != "Timestamp"]
            param_df = pd.DataFrame(param_data, columns=["Parameter", "Value"])
            
            # Create Excel writer
            with pd.ExcelWriter(file_path) as writer:
                # Write sequence to 'Sequence' sheet
                df.to_excel(writer, sheet_name="Sequence", index=False)
                
                # Write parameters to 'Parameters' sheet
                param_df.to_excel(writer, sheet_name="Parameters", index=False)
            
            return True, ""
        except Exception as e:
            return False, f"Excel export error: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Get the list of supported export formats.
        
        Returns:
            List of supported format names.
        """
        return list(self.supported_formats.keys())


from typing import Tuple, Dict, List, Optional, Any

class TemplateManager:
    """Manager for sequence templates."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize the template manager.
        
        Args:
            templates_dir: Directory to store templates in.
        """
        self.templates_dir = templates_dir
        self._ensure_templates_dir()
        self.templates = self._load_templates()
    
    def _ensure_templates_dir(self) -> None:
        """Ensure the templates directory exists."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def _load_templates(self) -> Dict[str, TestSequence]:
        """Load templates from the templates directory.
        
        Returns:
            Dictionary of template name -> TestSequence.
        """
        templates = {}
        
        # List template files
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(".json")]
        
        # Load each template
        for file_name in template_files:
            try:
                file_path = os.path.join(self.templates_dir, file_name)
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                # Create TestSequence from data
                sequence = TestSequence.from_dict(data)
                
                # Use file name without extension as template name
                template_name = os.path.splitext(file_name)[0]
                
                templates[template_name] = sequence
            except (json.JSONDecodeError, IOError, KeyError):
                # Skip invalid templates
                pass
        
        return templates
    
    def save_template(self, name: str, sequence: TestSequence) -> bool:
        """Save a sequence as a template.
        
        Args:
            name: Template name.
            sequence: Sequence to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create file path
            file_path = os.path.join(self.templates_dir, f"{name}.json")
            
            # Save sequence to file
            with open(file_path, "w") as f:
                json.dump(sequence.to_dict(), f, indent=2)
            
            # Add to templates
            self.templates[name] = sequence
            
            return True
        except Exception:
            return False
    
    def delete_template(self, name: str) -> bool:
        """Delete a template.
        
        Args:
            name: Template name.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if template exists
            if name not in self.templates:
                return False
            
            # Delete template file
            file_path = os.path.join(self.templates_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from templates
            del self.templates[name]
            
            return True
        except Exception:
            return False
    
    def get_template(self, name: str) -> Optional[TestSequence]:
        """Get a template.
        
        Args:
            name: Template name.
            
        Returns:
            Template sequence, or None if not found.
        """
        return self.templates.get(name)
    
    def get_template_names(self) -> List[str]:
        """Get the list of template names.
        
        Returns:
            List of template names.
        """
        return list(self.templates.keys())
    
    def get_templates(self) -> Dict[str, TestSequence]:
        """Get all templates.
        
        Returns:
            Dictionary of template name -> TestSequence.
        """
        return self.templates 