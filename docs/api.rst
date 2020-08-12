Schedule Manager API Guide
==========================

.. module:: schedule_manager

This part of documentation provides all the interfaces of Schedule Manager.
Detailed information about a specific function, class or method can be found here.


ScheduleManager Object
----------------------

.. autoclass:: ScheduleManager
    :members:


Task Object
-----------

.. autoclass:: Task
    :members:
    :exclude-members: run


TaskGroup Object
----------------

.. autoclass:: TaskGroup
    :members:


Exceptions
----------

.. autoclass:: schedule_manager.exceptions.OperationFailError

.. autoclass:: schedule_manager.exceptions.TaskNameDuplicateError

.. autoclass:: schedule_manager.exceptions.TaskNotFoundError

.. autoclass:: schedule_manager.exceptions.TimeFormatError
