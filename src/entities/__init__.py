"""
Entity models for the timetabling system
"""

from .course import Course
from .instructor import Instructor
from .room import Room
from .group import Group

__all__ = ['Course', 'Instructor', 'Room', 'Group']
