"""
Module: individual_decoder

This module provides functionality to decode a genetic algorithm (GA) individual—
represented as a list of `SessionGene` objects—into a list of rich, semantically
meaningful `CourseSession` objects.

The decoded structure is used for constraint evaluation, visualization,
and schedule analysis in the University Course Timetabling Problem (UCTP).
"""

from typing import List, Dict
from src.ga.sessiongene import SessionGene
from src.entities.decoded_session import CourseSession
from src.entities.course import Course
from src.entities.instructor import Instructor
from src.entities.group import Group
from src.entities.room import Room


def decode_individual(
    individual: List[SessionGene],
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> List[CourseSession]:
    """Decodes a GA individual (chromosome) into a list of CourseSession objects.

    This function translates each `SessionGene` into a `CourseSession`, enriching
    the basic encoded representation with full instructor and group references,
    along with room and course metadata. The output is suitable for use in
    constraint checking and visualization.

    Args:
        individual (List[SessionGene]): The chromosome to decode; each gene represents
            a single course session assignment with encoded time, room, and entities.
        courses (Dict[str, Course]): Mapping from course ID to Course objects, providing
            metadata like required room features.
        instructors (Dict[str, Instructor]): Mapping from instructor ID to Instructor objects.
        groups (Dict[str, Group]): Mapping from group ID to Group objects, including
            availability and enrollment data.
        rooms (Dict[str, Room]): Mapping from room ID to Room objects, including
            capacity and features data.

    Returns:
        List[CourseSession]: A list of fully populated CourseSession objects derived
        from the input chromosome.
    """
    decoded_sessions = []

    for gene in individual:
        # Look up course using tuple key (course_id, course_type)
        course_key = (gene.course_id, gene.course_type)
        course = courses[course_key]

        instructor = instructors[gene.instructor_id]
        # Get primary group (first group in the list)
        group = groups[gene.group_ids[0]] if gene.group_ids else None
        room = rooms[gene.room_id]

        session = CourseSession(
            course_id=gene.course_id,
            instructor_id=gene.instructor_id,
            group_ids=gene.group_ids,
            room_id=gene.room_id,
            session_quanta=gene.quanta,
            required_room_features=course.required_room_features,
            course_type=gene.course_type,  # Use gene's course_type
            instructor=instructor,
            group=group,  # Primary group (first in list)
            room=room,
        )

        decoded_sessions.append(session)

    return decoded_sessions
