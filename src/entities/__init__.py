"""
Entity models for the timetabling system
These all entities works on quanta based time representation in our system
This module defines the main entities used in the system, including Course, Instructor, Room, and Group.
"""

from .course import Course
from .instructor import Instructor
from .room import Room
from .group import Group

__all__ = ["Course", "Instructor", "Room", "Group"]
