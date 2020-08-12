.. _advanced:

Advanced Usage
==============

This part of documentation will introduce extra usage of Schedule Manager.


Task Information
----------------

We are able to get task information from :class:`Task <schedule_manager.Task>` object.


Check Activation
^^^^^^^^^^^^^^^^

:class:`Task <schedule_manager.Task>` provides :attr:`is_running <schedule_manager.Task.is_running>` property to check the activation of the task.

.. code-block:: python

    >>> from schedule_manager import Task
    >>> task = Task(name="task", job=print, args=("Hello task",))
    >>> task.is_running
    False
    >>> task.period_day_at("15:00:00").start()
    >>> task.is_running
    True


Job Next Run Time
^^^^^^^^^^^^^^^^^

:class:`Task <schedule_manager.Task>` provides :attr:`next_run <schedule_manager.Task.next_run>` property to check when the job will be done next time  .

.. code-block:: python

    >>> from schedule_manager import Task
    >>> from datetime import datetime
    >>> task = Task(name="task", job=print, args=("Hello task",))
    >>> datetime.now()
    datetime.datetime(2020, 8, 9, 12, 14, 10, 361827)
    >>> task.period_day_at("15:00:00").start()
    >>> task.next_run
    datetime.datetime(2020, 8, 9, 15, 0, 0, 802553)


Task Behavior with `ignore_skipped` flag
----------------------------------------

The :attr:`ignore_skipped` flag is used to control the behavior
if the job take `more` time than time interval configured to the task.

If :attr:`ignore_skipped` flag is set to `True`, :class:`Task <schedule_manager.Task>` will ignore the overdue work.

Let's use examples for explanation.


Set `ignore_skipped` flag to `True`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will use following python code for testing.

.. code-block:: python

    """test_ignore_skipped_True.py"""

    from schedule_manager import Task
    import time

    # A task will take 5 seconds to do the job
    task = Task(job=time.sleep, args=(5,), ignore_skipped=True)

    # Set time interval to 2 second
    task.period(2)

    task.start()

    while True:
        # Show job next run time
        print(task.next_run.strftime("%H:%M:%S"))

        time.sleep(1)

We can see that the works at following time are skipped when `ignore_skipped` flag is set to `True`.

    - `19:34:00`
    - `19:34:02`

    - `19:34:06`
    - `19:34:08`

    - `19:34:12`
    - `19:34:14`

Because the task is busy at those time.

.. code-block:: console

    $ python test_ignore_skipped_True.py
    19:33:58
    19:33:58
    19:33:58
    19:33:58
    19:33:58
    19:33:58
    19:34:04
    19:34:04
    19:34:04
    19:34:04
    19:34:04
    19:34:04
    19:34:10
    19:34:10
    19:34:10
    19:34:10
    19:34:10
    19:34:10
    19:34:16
    19:34:16
    19:34:16


Set `ignore_skipped` flag to `False`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we use following python code for another test.

.. code-block:: python

    """test_ignore_skipped_False.py"""

    from schedule_manager import Task
    import time

    # A task will take 5 seconds to do the job
    task = Task(job=time.sleep, args=(5,), ignore_skipped=False)

    # Set time interval to 2 second
    task.period(2)

    task.start()

    while True:
        # Show job next run time
        print(task.next_run.strftime("%H:%M:%S"))

        time.sleep(1)

If `ignore_skipped` flag is set to `False`, We can see that all works are not skipped even those works are overdue works.

.. code-block:: console

    $ python test_ignore_skipped_False.py
    19:37:39
    19:37:39
    19:37:39
    19:37:39
    19:37:39
    19:37:39
    19:37:41
    19:37:41
    19:37:41
    19:37:41
    19:37:41
    19:37:41
    19:37:43
    19:37:43
    19:37:43
    19:37:43
    19:37:43
    19:37:43
    19:37:45
    19:37:45


Task Count
----------

:class:`ScheduleManager <schedule_manager.ScheduleManager>` provides :attr:`count <schedule_manager.ScheduleManager.count>` property to show how many tasks are registered in this manager.

.. code-block:: python

    >>> from schedule_manager import ScheduleManager
    >>> manager = ScheduleManager()
    >>> manager.register_task(job=print, args=("Task 1",))
    Task<(Task-47844607c2ef4354903824cf1abc70be, initial daemon, None)>
    >>> manager.register_task(job=print, args=("Task 2",))
    Task<(Task-d512b84c33384a6b9bcb09c5f5f00207, initial daemon, None)>
    >>> manager.register_task(job=print, args=("Task 3",))
    Task<(Task-0cdeb2892d244e1fb489ab943a5a70af, initial daemon, None)>
    >>> manager.count    # how many tasks are registered in this manager
    3

:class:`TaskGroup <schedule_manager.TaskGroup>` also provides :attr:`count <schedule_manager.TaskGroup.count>` property to show how many tasks we keep in the task group.

.. code-block:: python

    >>> from schedule_manager import ScheduleManager
    >>> manager = ScheduleManager()
    >>> task1 = manager.register_task(job=print, args=("Task 1",))
    >>> task2 = manager.register_task(job=print, args=("Task 2",))
    >>> task3 = manager.register_task(job=print, args=("Task 3",))
    >>> task1.period_day_at("22:00:00").start()
    >>> manager.pending_tasks.count
    2












