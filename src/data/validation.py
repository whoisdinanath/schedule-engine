"""
Data validation module for the timetabling system.
Validates data integrity and consistency across all entities.
"""

from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
import re
from datetime import datetime, time

from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """
    Validates data integrity and consistency across all timetabling entities.
    Performs both structural and semantic validation.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = get_logger(self.__class__.__name__)
        self.errors = []
        self.warnings = []
    
    def validate_all(self, 
                    courses: Dict[str, Course],
                    instructors: Dict[str, Instructor],
                    rooms: Dict[str, Room],
                    groups: Dict[str, Group]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate all data entities and their relationships.
        
        Args:
            courses: Dictionary of Course entities
            instructors: Dictionary of Instructor entities
            rooms: Dictionary of Room entities
            groups: Dictionary of Group entities
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        try:
            self.logger.info("Starting comprehensive data validation...")
            
            # Individual entity validation
            self._validate_courses(courses)
            self._validate_instructors(instructors)
            self._validate_rooms(rooms)
            self._validate_groups(groups)
            
            # Cross-entity relationship validation
            self._validate_course_instructor_relationships(courses, instructors)
            self._validate_course_group_relationships(courses, groups)
            self._validate_capacity_constraints(courses, rooms, groups)
            self._validate_availability_constraints(instructors, rooms)
            
            # System-wide constraints
            self._validate_system_feasibility(courses, instructors, rooms, groups)
            
            # Log results
            self._log_validation_results()
            
            is_valid = len(self.errors) == 0
            return is_valid, self.errors.copy(), self.warnings.copy()
            
        except Exception as e:
            self.logger.error(f"Validation process failed: {str(e)}")
            self.errors.append(f"Validation process failed: {str(e)}")
            return False, self.errors.copy(), self.warnings.copy()
    
    def _validate_courses(self, courses: Dict[str, Course]):
        """Validate course entities."""
        self.logger.debug(f"Validating {len(courses)} courses...")
        
        for course_id, course in courses.items():
            try:
                # Basic field validation
                if not course.course_id or not course.course_id.strip():
                    self.errors.append(f"Course has empty ID")
                    continue
                
                if course.course_id != course_id:
                    self.errors.append(f"Course ID mismatch: {course_id} vs {course.course_id}")
                
                if not course.name or not course.name.strip():
                    self.errors.append(f"Course {course_id} has empty name")
                
                if course.sessions_per_week <= 0:
                    self.errors.append(f"Course {course_id} has invalid sessions_per_week: {course.sessions_per_week}")
                
                if course.duration <= 0:
                    self.errors.append(f"Course {course_id} has invalid duration: {course.duration}")
                elif course.duration > 240:  # 4 hours
                    self.warnings.append(f"Course {course_id} has very long duration: {course.duration} minutes")
                
                if not course.required_room_type or not course.required_room_type.strip():
                    self.errors.append(f"Course {course_id} has empty required_room_type")
                
                # Validate groups and instructors lists
                if not course.group_ids:
                    self.errors.append(f"Course {course_id} has no enrolled groups")
                
                if not course.qualified_instructor_ids:
                    self.errors.append(f"Course {course_id} has no qualified instructors")
                
                # Check for duplicates
                if len(set(course.group_ids)) != len(course.group_ids):
                    self.warnings.append(f"Course {course_id} has duplicate group IDs")
                
                if len(set(course.qualified_instructor_ids)) != len(course.qualified_instructor_ids):
                    self.warnings.append(f"Course {course_id} has duplicate instructor IDs")
                
                # Validate total weekly hours
                total_hours = course.get_total_weekly_hours()
                if total_hours > 10:  # More than 10 hours per week
                    self.warnings.append(f"Course {course_id} has high weekly hours: {total_hours}")
                
            except Exception as e:
                self.errors.append(f"Error validating course {course_id}: {str(e)}")
    
    def _validate_instructors(self, instructors: Dict[str, Instructor]):
        """Validate instructor entities."""
        self.logger.debug(f"Validating {len(instructors)} instructors...")
        
        for instructor_id, instructor in instructors.items():
            try:
                # Basic field validation
                if not instructor.instructor_id or not instructor.instructor_id.strip():
                    self.errors.append(f"Instructor has empty ID")
                    continue
                
                if instructor.instructor_id != instructor_id:
                    self.errors.append(f"Instructor ID mismatch: {instructor_id} vs {instructor.instructor_id}")
                
                if not instructor.name or not instructor.name.strip():
                    self.errors.append(f"Instructor {instructor_id} has empty name")
                
                if not instructor.qualified_courses:
                    self.errors.append(f"Instructor {instructor_id} has no qualified courses")
                
                if not instructor.available_slots:
                    self.errors.append(f"Instructor {instructor_id} has no available time slots")
                
                # Validate time slots format
                for day, slots in instructor.available_slots.items():
                    if not self._validate_day_name(day):
                        self.errors.append(f"Instructor {instructor_id} has invalid day name: {day}")
                    
                    for slot in slots:
                        if not self._validate_time_slot_format(slot):
                            self.errors.append(f"Instructor {instructor_id} has invalid time slot format: {slot}")
                
                # Validate constraints
                if instructor.max_hours_per_day <= 0:
                    self.errors.append(f"Instructor {instructor_id} has invalid max_hours_per_day")
                elif instructor.max_hours_per_day > 12:
                    self.warnings.append(f"Instructor {instructor_id} has high max_hours_per_day: {instructor.max_hours_per_day}")
                
                if instructor.max_hours_per_week <= 0:
                    self.errors.append(f"Instructor {instructor_id} has invalid max_hours_per_week")
                elif instructor.max_hours_per_week > 60:
                    self.warnings.append(f"Instructor {instructor_id} has high max_hours_per_week: {instructor.max_hours_per_week}")
                
                # Check consistency between daily and weekly limits
                if instructor.max_hours_per_day * 5 < instructor.max_hours_per_week:
                    self.warnings.append(f"Instructor {instructor_id} has inconsistent daily/weekly hour limits")
                
            except Exception as e:
                self.errors.append(f"Error validating instructor {instructor_id}: {str(e)}")
    
    def _validate_rooms(self, rooms: Dict[str, Room]):
        """Validate room entities."""
        self.logger.debug(f"Validating {len(rooms)} rooms...")
        
        for room_id, room in rooms.items():
            try:
                # Basic field validation
                if not room.room_id or not room.room_id.strip():
                    self.errors.append(f"Room has empty ID")
                    continue
                
                if room.room_id != room_id:
                    self.errors.append(f"Room ID mismatch: {room_id} vs {room.room_id}")
                
                if not room.name or not room.name.strip():
                    self.errors.append(f"Room {room_id} has empty name")
                
                if room.capacity <= 0:
                    self.errors.append(f"Room {room_id} has invalid capacity: {room.capacity}")
                elif room.capacity > 500:
                    self.warnings.append(f"Room {room_id} has very high capacity: {room.capacity}")
                
                if not room.room_type or not room.room_type.strip():
                    self.errors.append(f"Room {room_id} has empty room_type")
                
                if not room.available_slots:
                    self.errors.append(f"Room {room_id} has no available time slots")
                
                # Validate time slots format
                for day, slots in room.available_slots.items():
                    if not self._validate_day_name(day):
                        self.errors.append(f"Room {room_id} has invalid day name: {day}")
                    
                    for slot in slots:
                        if not self._validate_time_slot_format(slot):
                            self.errors.append(f"Room {room_id} has invalid time slot format: {slot}")
                
                # Validate setup time
                if room.setup_time < 0:
                    self.errors.append(f"Room {room_id} has negative setup_time")
                elif room.setup_time > 60:
                    self.warnings.append(f"Room {room_id} has high setup_time: {room.setup_time} minutes")
                
            except Exception as e:
                self.errors.append(f"Error validating room {room_id}: {str(e)}")
    
    def _validate_groups(self, groups: Dict[str, Group]):
        """Validate group entities."""
        self.logger.debug(f"Validating {len(groups)} groups...")
        
        for group_id, group in groups.items():
            try:
                # Basic field validation
                if not group.group_id or not group.group_id.strip():
                    self.errors.append(f"Group has empty ID")
                    continue
                
                if group.group_id != group_id:
                    self.errors.append(f"Group ID mismatch: {group_id} vs {group.group_id}")
                
                if not group.name or not group.name.strip():
                    self.errors.append(f"Group {group_id} has empty name")
                
                if group.student_count <= 0:
                    self.errors.append(f"Group {group_id} has invalid student_count: {group.student_count}")
                elif group.student_count > 200:
                    self.warnings.append(f"Group {group_id} has high student_count: {group.student_count}")
                
                if not group.enrolled_courses:
                    self.errors.append(f"Group {group_id} has no enrolled courses")
                
                if group.year_level <= 0:
                    self.errors.append(f"Group {group_id} has invalid year_level: {group.year_level}")
                elif group.year_level > 6:
                    self.warnings.append(f"Group {group_id} has high year_level: {group.year_level}")
                
                # Validate time constraints
                if not self._validate_time_format(group.earliest_start_time):
                    self.errors.append(f"Group {group_id} has invalid earliest_start_time format")
                
                if not self._validate_time_format(group.latest_end_time):
                    self.errors.append(f"Group {group_id} has invalid latest_end_time format")
                
                if group.max_daily_hours <= 0:
                    self.errors.append(f"Group {group_id} has invalid max_daily_hours")
                elif group.max_daily_hours > 12:
                    self.warnings.append(f"Group {group_id} has high max_daily_hours: {group.max_daily_hours}")
                
            except Exception as e:
                self.errors.append(f"Error validating group {group_id}: {str(e)}")
    
    def _validate_course_instructor_relationships(self, 
                                                courses: Dict[str, Course],
                                                instructors: Dict[str, Instructor]):
        """Validate course-instructor qualification relationships."""
        self.logger.debug("Validating course-instructor relationships...")
        
        for course_id, course in courses.items():
            for instructor_id in course.qualified_instructor_ids:
                if instructor_id not in instructors:
                    self.errors.append(f"Course {course_id} references unknown instructor {instructor_id}")
                    continue
                
                instructor = instructors[instructor_id]
                if course_id not in instructor.qualified_courses:
                    self.errors.append(f"Course {course_id} lists instructor {instructor_id} as qualified, "
                                     f"but instructor doesn't list this course in qualifications")
        
        # Check from instructor side
        for instructor_id, instructor in instructors.items():
            for course_id in instructor.qualified_courses:
                if course_id not in courses:
                    self.errors.append(f"Instructor {instructor_id} qualified for unknown course {course_id}")
                    continue
                
                course = courses[course_id]
                if instructor_id not in course.qualified_instructor_ids:
                    self.warnings.append(f"Instructor {instructor_id} qualified for course {course_id}, "
                                       f"but course doesn't list instructor as qualified")
    
    def _validate_course_group_relationships(self,
                                           courses: Dict[str, Course],
                                           groups: Dict[str, Group]):
        """Validate course-group enrollment relationships."""
        self.logger.debug("Validating course-group relationships...")
        
        for course_id, course in courses.items():
            for group_id in course.group_ids:
                if group_id not in groups:
                    self.errors.append(f"Course {course_id} references unknown group {group_id}")
                    continue
                
                group = groups[group_id]
                if course_id not in group.enrolled_courses:
                    self.errors.append(f"Course {course_id} lists group {group_id} as enrolled, "
                                     f"but group doesn't list this course in enrollments")
        
        # Check from group side
        for group_id, group in groups.items():
            for course_id in group.enrolled_courses:
                if course_id not in courses:
                    self.errors.append(f"Group {group_id} enrolled in unknown course {course_id}")
                    continue
                
                course = courses[course_id]
                if group_id not in course.group_ids:
                    self.warnings.append(f"Group {group_id} enrolled in course {course_id}, "
                                       f"but course doesn't list group as enrolled")
    
    def _validate_capacity_constraints(self,
                                     courses: Dict[str, Course],
                                     rooms: Dict[str, Room],
                                     groups: Dict[str, Group]):
        """Validate room capacity constraints."""
        self.logger.debug("Validating capacity constraints...")
        
        for course_id, course in courses.items():
            # Check each group individually (groups are scheduled separately)
            course_has_suitable_rooms = True
            max_group_size = 0
            
            for group_id in course.group_ids:
                if group_id not in groups:
                    continue
                    
                group = groups[group_id]
                max_group_size = max(max_group_size, group.student_count)
                
                # Check if any room can accommodate this specific group
                group_suitable_rooms = []
                for room_id, room in rooms.items():
                    if (room.is_suitable_for_course_type(course.required_room_type) and
                        room.can_accommodate_group_size(group.student_count)):
                        group_suitable_rooms.append(room_id)
                
                if not group_suitable_rooms:
                    self.errors.append(f"Course {course_id} group {group_id} ({group.student_count} students, "
                                     f"type: {course.required_room_type}) has no suitable rooms")
                    course_has_suitable_rooms = False
            
            if max_group_size == 0:
                self.warnings.append(f"Course {course_id} has no students")
                continue
            
            # Check if there are enough suitable rooms for all sessions
            if course_has_suitable_rooms:
                suitable_rooms = []
                for room_id, room in rooms.items():
                    if (room.is_suitable_for_course_type(course.required_room_type) and
                        room.can_accommodate_group_size(max_group_size)):
                        suitable_rooms.append(room_id)
                
                total_sessions_needed = sum(course.sessions_per_week for _ in course.group_ids)
                if len(suitable_rooms) < total_sessions_needed:
                    self.warnings.append(f"Course {course_id} may have limited room options for "
                                       f"{total_sessions_needed} total sessions across all groups")
    
    def _validate_availability_constraints(self,
                                         instructors: Dict[str, Instructor],
                                         rooms: Dict[str, Room]):
        """Validate availability constraints."""
        self.logger.debug("Validating availability constraints...")
        
        # Check instructor availability coverage
        for instructor_id, instructor in instructors.items():
            total_slots = sum(len(slots) for slots in instructor.available_slots.values())
            if total_slots < 10:  # Less than 10 time slots available
                self.warnings.append(f"Instructor {instructor_id} has limited availability: {total_slots} slots")
        
        # Check room availability coverage
        for room_id, room in rooms.items():
            total_slots = sum(len(slots) for slots in room.available_slots.values())
            if total_slots < 15:  # Less than 15 time slots available
                self.warnings.append(f"Room {room_id} has limited availability: {total_slots} slots")
    
    def _validate_system_feasibility(self,
                                   courses: Dict[str, Course],
                                   instructors: Dict[str, Instructor],
                                   rooms: Dict[str, Room],
                                   groups: Dict[str, Group]):
        """Validate overall system feasibility."""
        self.logger.debug("Validating system feasibility...")
        
        # Calculate total sessions needed
        total_sessions = sum(course.sessions_per_week for course in courses.values())
        
        # Calculate available capacity
        instructor_capacity = sum(
            len(instructor.get_all_available_slots()) 
            for instructor in instructors.values()
        )
        
        room_capacity = sum(
            len(room.get_all_available_slots()) 
            for room in rooms.values()
        )
        
        # Check feasibility ratios
        if instructor_capacity < total_sessions:
            self.errors.append(f"Insufficient instructor capacity: need {total_sessions} sessions, "
                             f"have {instructor_capacity} available slots")
        elif instructor_capacity < total_sessions * 1.2:
            self.warnings.append(f"Low instructor capacity margin: {instructor_capacity}/{total_sessions}")
        
        if room_capacity < total_sessions:
            self.errors.append(f"Insufficient room capacity: need {total_sessions} sessions, "
                             f"have {room_capacity} available slots")
        elif room_capacity < total_sessions * 1.2:
            self.warnings.append(f"Low room capacity margin: {room_capacity}/{total_sessions}")
        
        # Check for resource conflicts
        self._check_resource_distribution(courses, instructors, rooms)
    
    def _check_resource_distribution(self,
                                   courses: Dict[str, Course],
                                   instructors: Dict[str, Instructor],  
                                   rooms: Dict[str, Room]):
        """Check for potential resource distribution issues."""
        # Group courses by required room type
        courses_by_room_type = defaultdict(list)
        for course in courses.values():
            courses_by_room_type[course.required_room_type].append(course)
        
        # Check room type availability
        rooms_by_type = defaultdict(list)
        for room in rooms.values():
            rooms_by_type[room.room_type].append(room)
        
        for room_type, course_list in courses_by_room_type.items():
            total_sessions = sum(course.sessions_per_week for course in course_list)
            available_rooms = rooms_by_type.get(room_type, [])
            
            if not available_rooms:
                # Check for compatible room types
                compatible_rooms = []
                for room in rooms.values():
                    if room.is_suitable_for_course_type(room_type):
                        compatible_rooms.append(room)
                
                if not compatible_rooms:
                    self.errors.append(f"No rooms available for type '{room_type}' "
                                     f"({len(course_list)} courses need this type)")
    
    def _validate_day_name(self, day: str) -> bool:
        """Validate day name format."""
        valid_days = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                     'saturday', 'sunday', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
        return day.lower() in valid_days
    
    def _validate_time_slot_format(self, time_slot: str) -> bool:
        """Validate time slot format (HH:MM-HH:MM)."""
        pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}$'
        if not re.match(pattern, time_slot):
            return False
        
        try:
            start_str, end_str = time_slot.split('-')
            start_time = datetime.strptime(start_str, '%H:%M').time()
            end_time = datetime.strptime(end_str, '%H:%M').time()
            return start_time < end_time
        except ValueError:
            return False
    
    def _validate_time_format(self, time_str: str) -> bool:
        """Validate time format (HH:MM)."""
        pattern = r'^\d{2}:\d{2}$'
        if not re.match(pattern, time_str):
            return False
        
        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False
    
    def _log_validation_results(self):
        """Log validation results."""
        if self.errors:
            self.logger.error(f"Validation completed with {len(self.errors)} errors:")
            for error in self.errors:
                self.logger.error(f"  - {error}")
        
        if self.warnings:
            self.logger.warning(f"Validation completed with {len(self.warnings)} warnings:")
            for warning in self.warnings:
                self.logger.warning(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            self.logger.info("Validation completed successfully - no issues found")
        elif not self.errors:
            self.logger.info(f"Validation completed with {len(self.warnings)} warnings (no errors)")
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report."""
        return {
            'is_valid': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'timestamp': datetime.now().isoformat()
        }
