"""
Room entity model for the timetabling system.
Represents a room with its capacity, type, and availability.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass


@dataclass
class Room:
    """
    Represents a room in the university timetabling system.
    
    Attributes:
        room_id: Unique identifier for the room
        name: Display name of the room
        capacity: Maximum number of students the room can accommodate
        room_type: Type of room (e.g., 'lecture', 'lab', 'seminar', 'auditorium')
        available_slots: Dictionary mapping days to available time ranges
        equipment: List of available equipment in the room
        building: Building where the room is located
        floor: Floor number
        is_accessible: Whether the room is wheelchair accessible
        setup_time: Time needed to setup room between classes (minutes)
        special_features: Additional features (e.g., 'projector', 'computers')
    """
    
    room_id: str
    name: str
    capacity: int
    room_type: str
    available_slots: Dict[str, List[str]]  # day -> list of time ranges
    equipment: List[str] = None
    building: str = "Main Building"
    floor: int = 1
    is_accessible: bool = True
    setup_time: int = 10  # minutes
    special_features: List[str] = None
    
    def __post_init__(self):
        """Validate room data after initialization."""
        if self.capacity <= 0:
            raise ValueError(f"Room {self.room_id}: capacity must be positive")
        
        if not self.available_slots:
            raise ValueError(f"Room {self.room_id}: must have available time slots")
        
        # Initialize empty lists if None
        if self.equipment is None:
            self.equipment = []
        if self.special_features is None:
            self.special_features = []
    
    def is_available_at_slot(self, day: str, time_slot: str) -> bool:
        """
        Check if room is available at a specific day and time slot.
        
        Args:
            day: Day of the week (e.g., 'monday', 'tuesday')
            time_slot: Time slot in format 'HH:MM-HH:MM'
        
        Returns:
            True (rooms are always available - no availability constraints)
        """
        # Rooms are always available in this simplified scheduler
        return True
    
    def can_accommodate_group_size(self, group_size: int) -> bool:
        """
        Check if room can accommodate a given group size.
        
        Args:
            group_size: Number of students
        
        Returns:
            True if room capacity is sufficient
        """
        return self.capacity >= group_size
    
    def is_suitable_for_course_type(self, required_room_type: str) -> bool:
        """
        Check if room type matches the required room type for a course.
        
        Args:
            required_room_type: Required room type
        
        Returns:
            True if room type is suitable
        """
        # Exact match
        if self.room_type == required_room_type:
            return True
        
        # Allow flexibility for certain room types
        flexibility_map = {
            'lecture': ['auditorium', 'seminar'],
            'seminar': ['lecture'],
            'lab': ['computer_lab', 'science_lab'],
            'computer_lab': ['lab'],
            'science_lab': ['lab']
        }
        
        if required_room_type in flexibility_map:
            return self.room_type in flexibility_map[required_room_type]
        
        return False
    
    def has_equipment(self, required_equipment: str) -> bool:
        """
        Check if room has specific equipment.
        
        Args:
            required_equipment: Required equipment name
        
        Returns:
            True if equipment is available
        """
        return required_equipment.lower() in [eq.lower() for eq in self.equipment]
    
    def get_all_available_slots(self) -> List[tuple]:
        """
        Get all available time slots as a list of (day, time_slot) tuples.
        
        Returns:
            List of (day, time_slot) tuples
        """
        slots = []
        for day, time_slots in self.available_slots.items():
            for time_slot in time_slots:
                slots.append((day, time_slot))
        return slots
    
    def calculate_utilization_score(self, group_size: int) -> float:
        """
        Calculate room utilization score based on group size vs capacity.
        Higher score means better utilization.
        
        Args:
            group_size: Number of students
        
        Returns:
            Utilization score between 0 and 1
        """
        if group_size > self.capacity:
            return 0.0  # Cannot accommodate
        
        utilization = group_size / self.capacity
        
        # Optimal utilization is around 80-90%
        if 0.8 <= utilization <= 0.9:
            return 1.0
        elif 0.6 <= utilization < 0.8:
            return 0.8
        elif 0.4 <= utilization < 0.6:
            return 0.6
        elif utilization < 0.4:
            return 0.4 * utilization  # Penalize underutilization
        else:  # utilization > 0.9
            return 0.9  # Slight penalty for over-packing
    
    def get_location_string(self) -> str:
        """Get formatted location string."""
        return f"{self.building}, Floor {self.floor}"
    
    def __str__(self) -> str:
        return f"Room({self.room_id}: {self.name}, {self.room_type}, capacity={self.capacity})"
    
    def __repr__(self) -> str:
        return self.__str__()
