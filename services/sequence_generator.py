"""
Sequence generator service for the Spring Test App.
Contains classes and functions for generating test sequences.
"""
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple, Callable
from utils.api_client import APIClient
from models.data_models import TestSequence, SpringSpecification
from PyQt5.QtCore import QObject, pyqtSignal


class SequenceGenerator(QObject):
    """Service for generating test sequences."""
    
    # Define signals
    sequence_generated = pyqtSignal(object, str)  # TestSequence, error_message
    progress_updated = pyqtSignal(int)            # Progress percentage (0-100)
    status_updated = pyqtSignal(str)              # Status message
    
    def __init__(self, api_client: Optional[APIClient] = None):
        """Initialize the sequence generator.
        
        Args:
            api_client: API client to use.
        """
        super().__init__()
        
        # Create API client if not provided
        self.api_client = api_client or APIClient()
        
        # Initialize spring specification
        self.spring_specification = None
        
        # Store history
        self.history = []
        self.last_sequence = None
        self.last_parameters = None  # Add this line to store the last parameters
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key for the API client.
        
        Args:
            api_key: API key to use.
        """
        self.api_client.set_api_key(api_key)
    
    def set_spring_specification(self, specification: SpringSpecification) -> None:
        """Set the spring specification to use for sequence generation.
        
        Args:
            specification: Spring specification.
        """
        self.spring_specification = specification
    
    def get_spring_specification(self) -> Optional[SpringSpecification]:
        """Get the current spring specification.
        
        Returns:
            The current spring specification, or None if not set.
        """
        return self.spring_specification
    
    def _prepare_parameters_with_specification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters with spring specification data.
        
        Args:
            parameters: Original parameters dictionary.
            
        Returns:
            Updated parameters with spring specification.
        """
        if not self.spring_specification or not self.spring_specification.enabled:
            return parameters
        
        # Create a new parameters dictionary to avoid modifying the original
        updated_params = parameters.copy()
        
        # Calculate optimal speeds based on spring characteristics
        speeds = self.calculate_optimal_speeds(self.spring_specification)
        
        # Add spring specification as context
        if 'prompt' in updated_params:
            spec_text = self.spring_specification.to_prompt_text()
            updated_params['prompt'] = f"{spec_text}\n\n{updated_params['prompt']}"
        
        # Add additional parameters
        updated_params['spring_specification'] = {
            'part_name': self.spring_specification.part_name,
            'part_number': self.spring_specification.part_number,
            'part_id': self.spring_specification.part_id,
            'free_length_mm': self.spring_specification.free_length_mm,
            'coil_count': self.spring_specification.coil_count,
            'wire_dia_mm': self.spring_specification.wire_dia_mm,
            'outer_dia_mm': self.spring_specification.outer_dia_mm,
            'safety_limit_n': self.spring_specification.safety_limit_n,
            'unit': self.spring_specification.unit,
            'set_points': [
                {
                    'position_mm': sp.position_mm,
                    'load_n': sp.load_n,
                    'tolerance_percent': sp.tolerance_percent,
                    'enabled': sp.enabled
                }
                for sp in self.spring_specification.set_points if sp.enabled
            ],
            'optimal_speeds': speeds
        }
        
        return updated_params
    
    def calculate_optimal_speeds(self, specification: SpringSpecification) -> Dict[str, float]:
        """Calculate optimal speeds for different operations based on spring characteristics.
        
        This method uses a physics-informed approach to determine appropriate 
        testing speeds and forces based on the spring's physical properties.
        
        The calculation takes into account:
        
        1. Spring Stiffness Factor:
           - Calculated from wire diameter, coil count, and outer diameter
           - Stiffer springs (thicker wire, fewer coils) can handle faster speeds
           
        2. Size Factor:
           - Based on outer diameter and free length
           - Larger springs generally can handle faster testing speeds
           
        3. Brittleness Factor:
           - Primarily based on wire diameter
           - Thinner wires are more brittle and require gentler handling (slower speeds)
           
        4. Force Factor:
           - Based on the safety limit of the spring
           - Springs that handle higher forces may need slower testing speeds
           
        The final speeds are calculated using weighted combinations of these factors
        and constrained within practical limits for the testing equipment.
        
        Args:
            specification: Spring specification object
            
        Returns:
            Dictionary containing:
                - threshold_speed: Optimal speed for threshold operations (rpm)
                - movement_speed: Optimal speed for movement operations (rpm)
                - contact_force: Optimal force for contact detection (N)
        """
        # Get spring parameters
        wire_dia = specification.wire_dia_mm
        outer_dia = specification.outer_dia_mm
        free_length = specification.free_length_mm
        safety_limit = specification.safety_limit_n
        
        # Calculate spring stiffness factor (higher = stiffer spring)
        # Use wire diameter and coil count if available
        stiffness_factor = 1.0
        if wire_dia and specification.coil_count:
            # Thicker wire and fewer coils = stiffer spring
            stiffness_factor = (wire_dia ** 2) / (specification.coil_count * (outer_dia or 10))
        
        # Calculate size factor (higher = larger spring)
        # Base primarily on outer diameter and free length
        size_factor = 1.0
        if outer_dia and free_length:
            # Larger diameter and longer length = bigger spring
            size_factor = (outer_dia * free_length) / 1000  # Normalize to ~1.0 for medium springs
        
        # Calculate brittleness factor (higher = more brittle, needs gentler handling)
        # Base on wire diameter (thinner wire = more brittle)
        brittleness_factor = 1.0
        if wire_dia:
            brittleness_factor = 2.0 / (wire_dia + 0.5)  # Will be higher for thinner wire
        
        # Calculate force factor (higher = more force required)
        # Base on safety limit
        force_factor = 1.0
        if safety_limit:
            force_factor = safety_limit / 100  # Normalize to ~1.0 for medium springs
            
        # Base speeds - these will be adjusted based on factors
        base_threshold_speed = 30  # rpm for threshold operations
        base_movement_speed = 60   # rpm for movement operations
        
        # Calculate adjustment multiplier
        # - Smaller springs need slower speeds (lower size_factor)
        # - More brittle springs need slower speeds (higher brittleness_factor)
        # - Stiffer springs can handle faster speeds (higher stiffness_factor)
        # - Higher force springs need slower speeds (higher force_factor)
        
        # Adjust threshold speed
        # More affected by brittleness and force factors
        threshold_multiplier = (size_factor * 0.7 + stiffness_factor * 0.5) / (brittleness_factor * 0.8 + force_factor * 0.5)
        threshold_speed = round(base_threshold_speed * threshold_multiplier)
        
        # Keep within reasonable limits
        threshold_speed = max(5, min(threshold_speed, 50))
        
        # Adjust movement speed
        # More affected by size and stiffness factors
        movement_multiplier = (size_factor * 0.6 + stiffness_factor * 0.7) / (brittleness_factor * 0.5 + force_factor * 0.4)
        movement_speed = round(base_movement_speed * movement_multiplier)
        
        # Keep within reasonable limits
        movement_speed = max(10, min(movement_speed, 100))
        
        # Calculate contact force - primarily based on force factor but also spring size
        contact_force = max(5, min(round(10 * force_factor), 20))
        
        # Log the calculation for debugging
        self._log_speed_calculation(
            wire_dia, outer_dia, free_length, safety_limit,
            stiffness_factor, size_factor, brittleness_factor, force_factor,
            threshold_speed, movement_speed, contact_force
        )
        
        # Return speeds for different operations
        return {
            "threshold_speed": threshold_speed,  # For TH operations
            "movement_speed": movement_speed,    # For Mv(P) operations
            "contact_force": contact_force       # For threshold contact detection (N)
        }
        
    def _log_speed_calculation(self, wire_dia, outer_dia, free_length, safety_limit,
                              stiffness_factor, size_factor, brittleness_factor, force_factor,
                              threshold_speed, movement_speed, contact_force):
        """Log the speed calculation factors and results for debugging.
        
        Args:
            wire_dia: Wire diameter in mm
            outer_dia: Outer diameter in mm
            free_length: Free length in mm
            safety_limit: Safety limit in N
            stiffness_factor: Calculated stiffness factor
            size_factor: Calculated size factor
            brittleness_factor: Calculated brittleness factor
            force_factor: Calculated force factor
            threshold_speed: Calculated threshold speed in rpm
            movement_speed: Calculated movement speed in rpm
            contact_force: Calculated contact force in N
        """
        import logging
        logger = logging.getLogger("SpringTestApp")
        
        # Format input parameters
        logger.debug("Speed calculation input parameters:")
        logger.debug(f"  Wire diameter: {wire_dia} mm")
        logger.debug(f"  Outer diameter: {outer_dia} mm")
        logger.debug(f"  Free length: {free_length} mm")
        logger.debug(f"  Safety limit: {safety_limit} N")
        
        # Format calculated factors
        logger.debug("Calculated factors:")
        logger.debug(f"  Stiffness factor: {stiffness_factor:.2f}")
        logger.debug(f"  Size factor: {size_factor:.2f}")
        logger.debug(f"  Brittleness factor: {brittleness_factor:.2f}")
        logger.debug(f"  Force factor: {force_factor:.2f}")
        
        # Format results
        logger.debug("Calculated speeds:")
        logger.debug(f"  Threshold speed: {threshold_speed} rpm")
        logger.debug(f"  Movement speed: {movement_speed} rpm")
        logger.debug(f"  Contact force: {contact_force} N")
    
    def generate_sequence(self, parameters: Dict[str, Any]) -> Tuple[Optional[TestSequence], str]:
        """Generate a test sequence based on parameters (synchronous version).
        
        Note: This method is kept for backward compatibility but should be avoided
        in the UI to prevent freezing.
        
        Args:
            parameters: Dictionary of spring parameters.
            
        Returns:
            Tuple of (TestSequence object, error message if any)
        """
        # Save parameters for reference
        self.last_parameters = parameters
        
        # Add spring specification to parameters
        parameters_with_spec = self._prepare_parameters_with_specification(parameters)
        
        # Generate sequence
        df, response_text = self.api_client.generate_sequence(parameters_with_spec)
        
        # If generation failed, return error
        if df.empty:
            return None, response_text
        
        # Create TestSequence object
        sequence = TestSequence(
            rows=df.to_dict('records'),
            parameters=parameters_with_spec
        )
        
        # Save sequence for reference
        self.last_sequence = sequence
        
        # Add to history
        self.history.append(sequence)
        if len(self.history) > 10:  # Keep history limited
            self.history = self.history[-10:]
        
        return sequence, ""
    
    def generate_sequence_async(self, parameters: Dict[str, Any]) -> None:
        """Generate a test sequence based on parameters asynchronously.
        
        Args:
            parameters: Dictionary of spring parameters.
        """
        # Save parameters for reference
        self.last_parameters = parameters.copy()
        
        # Add spring specification to parameters
        parameters_with_spec = self._prepare_parameters_with_specification(parameters)
        
        # Start async generation
        self.api_client.generate_sequence_async(
            parameters_with_spec,
            self._on_sequence_generated,
            self.progress_updated.emit,  # Forward progress signal
            self.status_updated.emit     # Forward status signal
        )
    
    def _on_sequence_generated(self, df: pd.DataFrame, error_msg: str) -> None:
        """Handle sequence generation completion.
        
        Args:
            df: Generated DataFrame.
            error_msg: Error message if any.
        """
        # Check if this is a chat message (has a CHAT row)
        if not df.empty and "CHAT" in df["Row"].values:
            # For chat messages, just pass the DataFrame directly
            self.sequence_generated.emit(df, error_msg)
            return
            
        sequence = None
        
        if not df.empty:
            # Create TestSequence object
            sequence = TestSequence(
                rows=df.to_dict('records'),
                parameters=self.last_parameters
            )
            
            # Save sequence for reference
            self.last_sequence = sequence
            
            # Add to history
            self.history.append(sequence)
            if len(self.history) > 10:  # Keep history limited
                self.history = self.history[-10:]
        
        # Emit signal
        self.sequence_generated.emit(sequence, error_msg)
    
    def cancel_current_operation(self) -> None:
        """Cancel the current operation."""
        self.api_client.cancel_current_operation()
    
    def get_last_sequence(self) -> Optional[TestSequence]:
        """Get the last generated sequence.
        
        Returns:
            The last generated sequence, or None if none available.
        """
        return self.last_sequence
    
    def get_sequence_history(self) -> List[TestSequence]:
        """Get the sequence generation history.
        
        Returns:
            List of generated sequences.
        """
        return self.history
    
    def add_to_history(self, sequence: TestSequence) -> None:
        """Add a sequence to the history.
        
        Args:
            sequence: Sequence to add.
        """
        self.history.append(sequence)
        if len(self.history) > 10:  # Keep history limited
            self.history = self.history[-10:]
    
    def clear_history(self) -> None:
        """Clear the sequence generation history."""
        self.history = []
    
    def validate_sequence(self, sequence: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate a sequence.
        
        Args:
            sequence: Sequence to validate.
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation checks
        if not sequence:
            return False, "Sequence is empty"
        
        required_columns = ["Row", "CMD", "Description", "Condition", "Unit", "Tolerance", "Speed rpm"]
        
        # Check if all required columns are present
        for col in required_columns:
            if col not in sequence[0]:
                return False, f"Missing required column: {col}"
        
        # More validation could be added here
        
        return True, ""
    
    def create_sequence_from_template(self, template_name: str, parameters: Dict[str, Any]) -> Optional[TestSequence]:
        """Create a sequence from a predefined template.
        
        Args:
            template_name: Name of the template to use.
            parameters: Dictionary of parameters to fill in.
            
        Returns:
            Generated sequence, or None if template not found.
        """
        # This would load predefined templates and fill in the parameters
        # For now, just return None
        return None 