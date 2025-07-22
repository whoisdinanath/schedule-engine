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


def decode_individual(
    individual: List[SessionGene],
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
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

    Returns:
        List[CourseSession]: A list of fully populated CourseSession objects derived
        from the input chromosome.
    """
    decoded_sessions = []

    for gene in individual:
        course = courses[gene.course_id]
        instructor = instructors[gene.instructor_id]
        group = groups[gene.group_id]

        session = CourseSession(
            course_id=gene.course_id,
            instructor_id=gene.instructor_id,
            group_ids=[gene.group_id],
            room_id=gene.room_id,
            session_quanta=gene.quanta,
            required_room_features=course.required_room_features,
            instructor=instructor,
            group=group,
        )

        decoded_sessions.append(session)

    return decoded_sessions
