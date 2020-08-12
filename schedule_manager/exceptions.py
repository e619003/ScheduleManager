"""
Exceptions.
"""

class OperationFailError(Exception):
    """Operation fail exception."""
    pass

class TaskNameDuplicateError(Exception):
    """Duplicate task name exception."""
    pass

class TaskNotFoundError(Exception):
    """Task is not registered in schedule manager."""
    pass

class TimeFormatError(Exception):
    """Time format error."""
    pass
