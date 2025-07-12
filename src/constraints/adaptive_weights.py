"""
Adaptive constraint weights system -  for dynamic constraint prioritization.
Adjusts constraint weights based on - violation patterns during evolution.
"""

from typing import Dict, List, Any
import logging
from collections import defaultdict, deque
from ..utils.logger import get_logger


class AdaptiveConstraintWeights:
    """
    Dynamically adjusts constraint weights based on evolution progress.
    Increases weights for persistently violated constraints and decreases 
    weights for well-satisfied constraints.
    """
    
    def __init__(self, initial_weights: Dict[str, float], learning_rate: float = 0.1):
        """
        Initialize adaptive constraint weights.
        
        Args:
            initial_weights: Initial constraint weights
            learning_rate: Rate of weight adaptation (0.0 to 1.0)
        """
        self.logger = get_logger(self.__class__.__name__)
        self.initial_weights = initial_weights.copy()
        self.current_weights = initial_weights.copy()
        self.learning_rate = learning_rate
        
        # Update frequency (can be set from outside)
        self.update_frequency = 10
        
        # History tracking
        self.violation_history = deque(maxlen=20)  # Keep last 20 generations
        self.weight_history: List[Dict[str, float]] = []
        self.adaptation_count = 0
        
        # Weight adjustment parameters
        self.increase_factor = 1.2
        self.decrease_factor = 0.9
        self.max_weight_multiplier = 5.0
        self.min_weight_multiplier = 0.1
        
        # Statistics
        self.total_adaptations = 0
        self.successful_adaptations = 0
        
        self.logger.info("Initialized enhanced adaptive constraint weights")
        
    def update_weights(self, violations: Dict[str, int], generation: int) -> None:
        """
        Update constraint weights based on current violation patterns.
        
        Args:
            violations: Current constraint violations
            generation: Current generation number
        """
        # Debug: Check the structure of violations
        self.logger.debug(f"Received violations: {violations}")
        self.logger.debug(f"Violations type: {type(violations)}")
        
        # Ensure all values are numeric and flatten any nested structures
        flat_violations = {}
        for key, value in violations.items():
            if isinstance(value, dict):
                self.logger.error(f"Dict found in violations for {key}: {value}")
                # If it's a dict, skip it or try to extract numeric values
                continue
            elif isinstance(value, (int, float)):
                flat_violations[key] = value
            else:
                self.logger.error(f"Non-numeric value in violations for {key}: {value} (type: {type(value)})")
                flat_violations[key] = 0
        
        self.logger.debug(f"Flattened violations: {flat_violations}")
        
        self.violation_history.append(flat_violations.copy())
        
        # Only adapt after collecting enough history
        if len(self.violation_history) >= 5:
            self._adapt_weights(flat_violations, generation)
            
        # Record current weights
        self.weight_history.append(self.current_weights.copy())
        
        # Log status periodically
        if generation % 20 == 0:
            self.log_current_status(generation)
        
    def _adapt_weights(self, current_violations: Dict[str, int], generation: int) -> None:
        """
        Adapt weights based on violation patterns.
        
        Args:
            current_violations: Current constraint violations
            generation: Current generation number
        """
        try:
            # Get recent violation history
            recent_history = list(self.violation_history)[-10:]
            
            for constraint_name in self.current_weights.keys():
                # Calculate average violations for this constraint
                recent_violations = []
                for h in recent_history:
                    val = h.get(constraint_name, 0)
                    # Ensure we always get a numeric value
                    if isinstance(val, dict):
                        self.logger.error(f"Dict found in violation history for {constraint_name}: {val}")
                        val = 0
                    recent_violations.append(val)
                
                avg_violations = sum(recent_violations) / len(recent_violations)
                current_count = current_violations.get(constraint_name, 0)
                
                # Ensure current_count is numeric
                if isinstance(current_count, dict):
                    self.logger.error(f"Dict found in current violations for {constraint_name}: {current_count}")
                    current_count = 0
                
                # Calculate violation trend
                if len(recent_violations) >= 3:
                    early_avg = sum(recent_violations[:3]) / 3
                    late_avg = sum(recent_violations[-3:]) / 3
                    trend = late_avg - early_avg
                else:
                    trend = 0
                
                old_weight = self.current_weights[constraint_name]
                new_weight = self._calculate_new_weight(
                    old_weight, current_count, avg_violations, trend, constraint_name
                )
                
                # Apply weight change with smoothing
                weight_change = (new_weight - old_weight) * self.learning_rate
                self.current_weights[constraint_name] = old_weight + weight_change
                
                # Log significant weight changes
                if abs(weight_change) > old_weight * 0.15:  # 15% change threshold
                    self.logger.debug(
                        f"Gen {generation}: Adapted {constraint_name} weight: "
                        f"{old_weight:.2f} -> {self.current_weights[constraint_name]:.2f} "
                        f"(violations: {current_count}, avg: {avg_violations:.1f}, trend: {trend:.1f})"
                    )
            
            self.adaptation_count += 1
            
        except Exception as e:
            self.logger.error(f"Error adapting weights: {str(e)}")
    
    def _calculate_new_weight(self, current_weight: float, current_violations: int, 
                            avg_violations: float, trend: float, constraint_name: str) -> float:
        """
        Calculate new weight for a constraint based on violation patterns.
        
        Args:
            current_weight: Current weight value
            current_violations: Current number of violations
            avg_violations: Average violations over recent history
            trend: Violation trend (positive = increasing, negative = decreasing)
            constraint_name: Name of the constraint
            
        Returns:
            New weight value
        """
        initial_weight = self.initial_weights[constraint_name]
        
        # Ensure all values are numeric
        if not isinstance(current_violations, (int, float)):
            self.logger.error(f"Non-numeric current_violations for {constraint_name}: {current_violations}")
            current_violations = 0
        if not isinstance(avg_violations, (int, float)):
            self.logger.error(f"Non-numeric avg_violations for {constraint_name}: {avg_violations}")
            avg_violations = 0
        if not isinstance(trend, (int, float)):
            self.logger.error(f"Non-numeric trend for {constraint_name}: {trend}")
            trend = 0
        
        # Base weight adjustment factors
        violation_factor = 1.0
        trend_factor = 1.0
        
        # Increase weight for persistent violations
        if avg_violations > 0:
            if avg_violations > 50:
                violation_factor = 1.4  # Very high violations
            elif avg_violations > 20:
                violation_factor = 1.3  # High violations
            elif avg_violations > 10:
                violation_factor = 1.2  # Moderate violations
            elif avg_violations > 1:
                violation_factor = 1.1  # Low violations
        else:
            # Decrease weight for consistently zero violations
            violation_factor = 0.9
        
        # Adjust based on trend
        if trend > 5:  # Violations increasing significantly
            trend_factor = 1.3
        elif trend > 1:  # Violations increasing
            trend_factor = 1.15
        elif trend < -5:  # Violations decreasing significantly
            trend_factor = 0.8
        elif trend < -1:  # Violations decreasing
            trend_factor = 0.9
        
        # Calculate new weight
        new_weight = current_weight * violation_factor * trend_factor
        
        # Apply bounds (min_multiplier to max_multiplier of initial weight)
        min_weight = initial_weight * self.min_weight_multiplier
        max_weight = initial_weight * self.max_weight_multiplier
        new_weight = max(min_weight, min(max_weight, new_weight))
        
        return new_weight
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get current constraint weights.
        
        Returns:
            Current constraint weights
        """
        return self.current_weights.copy()
    
    def reset_weights(self) -> None:
        """Reset weights to initial values."""
        self.current_weights = self.initial_weights.copy()
        self.violation_history.clear()
        self.weight_history.clear()
        self.adaptation_count = 0
        self.logger.info("Constraint weights reset to initial values")
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about weight adaptations.
        
        Returns:
            Dictionary with adaptation statistics
        """
        if not self.weight_history:
            return {}
        
        stats = {
            'total_adaptations': self.adaptation_count,
            'generations_tracked': len(self.violation_history),
            'weight_changes': {},
            'current_vs_initial': {}
        }
        
        # Calculate weight changes over time
        for constraint in self.current_weights:
            initial = self.initial_weights[constraint]
            current = self.current_weights[constraint]
            change_ratio = current / initial if initial > 0 else 1.0
            
            stats['weight_changes'][constraint] = {
                'initial': initial,
                'current': current,
                'change_ratio': change_ratio,
                'change_percent': (change_ratio - 1.0) * 100
            }
        
        return stats
    
    def log_current_status(self, generation: int) -> None:
        """
        Log current weight status.
        
        Args:
            generation: Current generation number
        """
        self.logger.info(f"Generation {generation} - Adaptive Weights Status:")
        
        significant_changes = []
        for constraint, weight in self.current_weights.items():
            initial = self.initial_weights[constraint]
            change = ((weight / initial) - 1.0) * 100 if initial > 0 else 0
            
            if abs(change) > 20:  # Only log significant changes
                significant_changes.append(f"  {constraint}: {weight:.1f} ({change:+.1f}%)")
        
        if significant_changes:
            for change in significant_changes:
                self.logger.info(change)
        else:
            self.logger.info("  No significant weight changes")
    
    def get_weights(self) -> Dict[str, float]:
        """Get current constraint weights."""
        return self.current_weights.copy()
    
    def reset_weights(self):
        """Reset weights to initial values."""
        self.current_weights = self.initial_weights.copy()
        self.violation_history.clear()
        self.logger.info("Reset constraint weights to initial values")
    
    def _log_weight_status(self, generation: int):
        """Log current weight status."""
        self.logger.info(f"Generation {generation} - Weight adjustments:")
        for constraint, weight in self.current_weights.items():
            initial = self.initial_weights[constraint]
            if abs(weight - initial) > 0.01:  # Only log if significantly changed
                change_pct = ((weight - initial) / initial) * 100
                self.logger.info(f"  {constraint}: {weight:.2f} ({change_pct:+.1f}%)")
