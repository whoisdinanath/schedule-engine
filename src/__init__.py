"""
Genetic Algorithm-based University Course Timetabling System
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "GA Timetabling Team"

from .entities import Course, Instructor, Room, Group
from .ga import GAEngine, Chromosome, Population
from .constraints import ConstraintChecker
from .fitness import FitnessEvaluator
from .data import DataIngestion
from .output import OutputGenerator

__all__ = [
    'Course', 'Instructor', 'Room', 'Group',
    'GAEngine', 'Chromosome', 'Population',
    'ConstraintChecker', 'FitnessEvaluator',
    'DataIngestion', 'OutputGenerator'
]
