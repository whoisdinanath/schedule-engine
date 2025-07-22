from dataclasses import dataclass
from typing import List
from src.entities.instructor import Instructor
from src.entities.group import Group


@dataclass
class CourseSession:
    """
    Represents a fully decoded session of a course within the university timetabling system.

    This object is used after decoding a GA individual (chromosome) for constraint checking,
    visualization, and scheduling logic. Unlike the gene, this class includes semantic
    information like resolved Instructor and Group objects.

    Attributes:
        course_id (str): Unique identifier for the course.
        instructor_id (str): ID of the instructor assigned to this session.
        group_ids (List[str]): List of group IDs attending this session.
        room_id (str): ID of the room assigned to this session.
        session_quanta (List[int]): List of time quanta (e.g., 15-min blocks) during which the session is scheduled.
        required_room_features (str): Room feature type required (e.g., "lab", "lecture").
        instructor (Instructor, optional): Reference to the assigned Instructor object.
        group (Group, optional): Reference to the primary Group object (if applicable).
    """

    course_id: str
    instructor_id: str
    group_ids: List[str]
    room_id: str
    session_quanta: List[int]
    required_room_features: str
    instructor: Instructor = None
    group: Group = None
