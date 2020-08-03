"""
Thread-based task scheduling management.

An easy way to manage periodic jobs.
"""
__version_info__ = ('0', '1', '0')
__version__ = '.'.join(__version_info__)

from .manager import ScheduleManager
from .manager import TaskGroup
from .manager import Task
