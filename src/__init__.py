"""
Genetic Algorithm-based University Course Timetabling System
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "GA Timetabling Team"

from .entities import Course, Instructor, Room, Group

__all__ = ["Course", "Instructor", "Room", "Group"]
