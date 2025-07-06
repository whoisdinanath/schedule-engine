"""
Data handling modules for the timetabling system
"""

from .ingestion import DataIngestion
from .validation import DataValidator

__all__ = ['DataIngestion', 'DataValidator']
