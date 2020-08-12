Quick Start
============

Schedule Manager provides an easy way to schedule your jobs.
It allows people to creates and schedule tasks to execute jobs in particular time.

This part of documentation will introduce how to use Schedule Manager.

Please make sure Schedule Manager is :ref:`installed <install>` first.


Task Management
---------------

:class:`Task <schedule_manager.Task>` object is used for scheduling a job to be run as the particular time.

Although :class:`Task <schedule_manager.Task>` object is able to be used directly, :class:`ScheduleManager <schedule_manager.ScheduleManager>` object provides a convenient way to manage multiple :class:`Task <schedule_manager.Task>` objects.


Task Registration
^^^^^^^^^^^^^^^^^

:class:`ScheduleManager <schedule_manager.ScheduleManager>` object is used to manage tasks.

It provides two ways to let Task can be managed by :class:`ScheduleManager <schedule_manager.ScheduleManager>`.

1. With :meth:`register_task <schedule_manager.ScheduleManager.register_task>` method:
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Using :meth:`register_task <schedule_manager.ScheduleManager.register_task>` method is able to create a new task and register it in manger directly.

.. code-block:: python

    from schedule_manager import ScheduleManager


    def jobs():
        current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("Working now {}".format(current))


    manager = ScheduleManager()

    # Register job as a new task 
    manager.register_task(name="task", job=jobs).period(60).start()

2. With :meth:`register <schedule_manager.ScheduleManager.register>` method:
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Use :meth:`register <schedule_manager.ScheduleManager.register>` method to register an exist task.

.. code-block:: python

    from schedule_manager import ScheduleManager
    from schedule_manager import Task


    manager = ScheduleManager()

    task = Task(name="task", job=print, args=("Hello task",)).period(60)
    task.start()

    # Register an existing task
    manager.register(task)


Tagging Tasks
^^^^^^^^^^^^^

:class:`Task <schedule_manager.Task>` object is able to be identified by tags.

We can label Task with different tags for `better management <#obtain-tasks-by-task-tags>`_.

1. Add tags
"""""""""""

A tag can be any :class:`Object <object>` like :obj:`str`, :obj:`int`, and so on.

We can use :meth:`add_tag <schedule_manager.Task.add_tag>` method to add single tag or use :meth:`add_tags <schedule_manager.Task.add_tags>` method to add multiple tags to the task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",)).period(60)


    # Add tag "tag1"
    task.add_tag("tag1")

    # Add tags "tagA" and "label-A"
    task.add_tags(["tagA", "label-A"])

2. Remove tags
""""""""""""""

Tags are able to be removed if we do not need them.

We can use :meth:`remove_tag <schedule_manager.Task.remove_tag>` method to remove single tag or use :meth:`remove_tags <schedule_manager.Task.remove_tags>` method to remove multiple tags to the task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",)).period(60)
    task.add_tags(["tagA", "label-A", "event-1", "job-I"])


    # Remove tag "tagA"
    task.remove_tag("tagA")

    # Remove tags "label-A" and "job-I"
    task.remove_tags(["label-A", "job-I"])

3. Set specific tags
""""""""""""""""""""

We can use :meth:`set_tags <schedule_manager.Task.set_tags>` method set specific tags to the task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",)).period(60)
    task.add_tags(["tagA", "label-A", "event-1", "job-I"])


    # Set tags to "tagB" and "tag2"
    # Now tags of the task will be changed to "tagB" and "tag2"
    task.set_tags(["tagB", "tag2"])

4. View tags of a task
""""""""""""""""""""""

| A task is able to have lots of tags in its tag list.
| We are able to use :attr:`tag <schedule_manager.Task.tag>` property to list all tags of a task.

.. code-block:: python

    >>> from schedule_manager import Task
    >>> task = Task(name="task", job=print, args=("Hello task",))
    >>> task.set_tags(["tag1", "tagA"]).add_tag("label-A")
    Task<(task, initial daemon, None)>
    >>> task.tag    # List tags
    ['tag1', 'tagA', 'label-A']



Remove Task from ScheduleManager
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If we do not want to manaage specific task with :class:`ScheduleManager <schedule_manager.ScheduleManager>`, we are able to remove the task from the manager.

:class:`ScheduleManager <schedule_manager.ScheduleManager>` object provides :meth:`unregister <schedule_manager.ScheduleManager.unregister>` method to remove the task from itself.
We can use :meth:`unregister <schedule_manager.ScheduleManager.unregister>` method to unregister tasks `by name` or `by tags`.

1. Unregister task by name
""""""""""""""""""""""""""

Here shows how to unregister a task by name.

.. code-block:: python

    from schedule_manager import ScheduleManager
    from schedule_manager import Task

    manager = ScheduleManager()

    task1 = Task(name="task1", job=print, args=("Hello task1",)).period(60)
    manager.register(task1)

    task2 = Task(name="task2", job=print, args=("Hello task2",)).period(60)
    manager.register(task2)


    # Unregister task by name.
    # task1 will be removed
    manager.unregister(name="task1")

2. Unregister tasks by tag
""""""""""""""""""""""""""

Here shows how to unregister tasks by a tag.

.. code-block:: python

    from schedule_manager import ScheduleManager
    from schedule_manager import Task

    manager = ScheduleManager()

    task1 = Task(name="task1", job=print, args=("Hello task1",)).period(60)
    task1.add_tag("tag-1")
    manager.register(task1)

    task2 = Task(name="task2", job=print, args=("Hello task2",)).period(60)
    task2.add_tag("tag-2")
    manager.register(task2)


    # Unregister task by tag.
    # task1 will be removed
    manager.unregister(tag="tag-1")

3. Unregister tasks by tags
"""""""""""""""""""""""""""

Here shows how to unregister tasks by several tags.

.. code-block:: python

    from schedule_manager import ScheduleManager
    from schedule_manager import Task

    manager = ScheduleManager()

    task1 = Task(name="task1", job=print, args=("Hello task1",)).period(60)
    task1.add_tag("tag-1")
    manager.register(task1)

    task2 = Task(name="task2", job=print, args=("Hello task2",)).period(60)
    task2.add_tag("tag-2")
    manager.register(task2)

    task3 = Task(name="task3", job=print, args=("Hello task3",)).period(60)
    task3.add_tag("tag-I")
    manager.register(task3)

    task4 = Task(name="task4", job=print, args=("Hello task4",)).period(60)
    task4.add_tag("tag-I")
    manager.register(task4)


    # Unregister task by tags.
    # task1, task3 and task4 will be removed
    manager.unregister(tag=["tag-1", "tag-I"])


Managing Registered Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^

| Tasks can be configured before and after being registerd in a :class:`ScheduleManager <schedule_manager.ScheduleManager>`.
| Once we want to configure registered tasks, we need to obtain them from schedule manager first.

1. Obtain task by task name
"""""""""""""""""""""""""""

Tasks with same name are not able to register in a :class:`ScheduleManager <schedule_manager.ScheduleManager>` at the same time.

Every task have an unique name.
We can obtain specific task by searching with the name with :meth:`task <schedule_manager.ScheduleManager.task>` method.

.. code-block:: python

    from schedule_manager import ScheduleManager

    manager = ScheduleManager()

    manager.register_task(name="task1", job=print, args=("Hello task1",))
    manager.register_task(name="task2", job=print, args=("Hello task2",))

    # Obtain task by task name.
    # We will get task named 'task1'
    task = manager.task("task1")

    # Task is able to be configured directly after obtaining it.
    # Get task named 'task1' and add a tag 'tag-I' to it
    manager.task("task1").add_tag("tag-I")

2. Obtain tasks by task tags
""""""""""""""""""""""""""""

Tasks are able to be `identified by tags <#tagging-tasks>`_.
We can obtain tasks by searching with the tags with :meth:`tasks <schedule_manager.ScheduleManager.tasks>` method.

.. code-block:: python

    from schedule_manager import ScheduleManager

    manager = ScheduleManager()

    manager.register_task(name="task1", job=print, args=("Hello task1",))
    manager.task("task1").add_tag("type-I")
    manager.register_task(name="task2", job=print, args=("Hello task2",))
    manager.task("task2").add_tag("type-II")
    manager.register_task(name="task3", job=print, args=("Hello task3",))
    manager.task("task3").add_tag("type-I")
    manager.register_task(name="task4", job=print, args=("Hello task4",))
    manager.task("task4").add_tag("type-III")

    # Obtain tasks by tags.
    # We will get tasks named 'task1' and 'task3'
    # Note: return will be a TaskGroup instance which can be operated
    #       like a Task instance
    task_group = manager.tasks("type-I")

    # This will get tasks named 'task1', 'task3' and 'task4'
    task_group2 = manager.tasks(["type-I", "type-III"])

    # Tasks are able to be configured directly after obtaining them.
    # Get tasks and add a tag 'tag-I' to them
    manager.tasks("type-I").add_tag("tag-I")

3. Obtain all tasks registered in the schedule manager
""""""""""""""""""""""""""""""""""""""""""""""""""""""

It is able to obtain all tasks registered in the schedule manager with :attr:`all_tasks <schedule_manager.ScheduleManager.all_tasks>` property.

.. code-block:: python

    from schedule_manager import ScheduleManager

    manager = ScheduleManager()

    manager.register_task(name="task1", job=print, args=("Hello task1",))
    manager.register_task(name="task2", job=print, args=("Hello task2",))
    manager.register_task(name="task3", job=print, args=("Hello task3",))
    manager.register_task(name="task4", job=print, args=("Hello task4",))

    # Obtain all tasks registered in the schedule manager.
    # Note: return will be a TaskGroup instance which can be operated
    #       like a Task instance
    task_group = manager.all_tasks

    # Tasks are able to be configured directly after obtaining them.
    # Get tasks and add a tag 'tag-I' to them
    manager.all_tasks.add_tag("tag-I")

4. Obtain all running tasks registered in the schedule manager
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

It is able to obtain all running tasks registered in the schedule manager with :attr:`running_tasks <schedule_manager.ScheduleManager.running_tasks>` property.

.. code-block:: python

    from schedule_manager import ScheduleManager

    manager = ScheduleManager()

    manager.register_task(name="task1", job=print, args=("Hello task1",))
    manager.task("task1").period(10).start()
    manager.register_task(name="task2", job=print, args=("Hello task2",))
    manager.register_task(name="task3", job=print, args=("Hello task3",))
    manager.register_task(name="task4", job=print, args=("Hello task4",))
    manager.task("task4").period(30).start()

    # Obtain tasks named 'task1' and 'task4'
    # Note: return will be a TaskGroup instance which can be operated
    #       like a Task instance
    task_group = manager.running_tasks

    # Tasks are able to be configured directly after obtaining them.
    # Get tasks and add a tag 'tag-I' to them
    manager.running_tasks.add_tag("tag-I")

5. Obtain all pending tasks registered in the schedule manager
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

It is able to obtain all pending tasks registered in the schedule manager with :attr:`pending_tasks <schedule_manager.ScheduleManager.pending_tasks>` property.

.. code-block:: python

    from schedule_manager import ScheduleManager

    manager = ScheduleManager()

    manager.register_task(name="task1", job=print, args=("Hello task1",))
    manager.task("task1").period(10).start()
    manager.register_task(name="task2", job=print, args=("Hello task2",))
    manager.register_task(name="task3", job=print, args=("Hello task3",))
    manager.register_task(name="task4", job=print, args=("Hello task4",))
    manager.task("task4").period(30).start()

    # Obtain tasks named 'task2' and 'task3'
    # Note: return will be a TaskGroup instance which can be operated
    #       like a Task instance
    task_group = manager.pending_tasks

    # Tasks are able to be configured directly after obtaining them.
    # Get tasks and add a tag 'tag-I' to them
    manager.pending_tasks.add_tag("tag-I")


Task Scheduling
---------------

Job is able to be scheduled as periodic, daily, weekly, monthly or even non-periodic :class:`Task <schedule_manager.Task>`.
It depends on what you need.

| Every :class:`Task <schedule_manager.Task>` should be scheduled before activating them.
| It will not be able to activate the task activity if the task has not been scheduled.


Periodic Task
^^^^^^^^^^^^^

Periodic task will do the job every time interval you set.

Please note that the periodic task will `do the job once immediately` when `starting` the task.

Use :meth:`period <schedule_manager.Task.period>` method to schedule a periodic task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Periodic Task
    # Set time interval to 300 seconds
    task.period(300)

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Periodic Task
    # Set time interval to 1 hour and 30 minutes
    # String format should match `HH:MM:SS`
    task.period("01:30:00")

.. code-block:: python

    from schedule_manager import Task
    from datetime import timedelta

    task = Task(name="task", job=print, args=("Hello task",))

    # Periodic Task
    # Set time interval to 20 minutes
    task.period(timedelta(minutes=20))


Daily Task
^^^^^^^^^^

Daily task will do the job at particular time everyday.

Use :meth:`period_day_at <schedule_manager.Task.period_day_at>` method to schedule a daily task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Daily Task
    # Job will be done at 15:00 everyday
    # String format should match `HH:MM:SS`
    task.period_day_at("15:00:00")


Weekly Task
^^^^^^^^^^^

Weekly task will do the job at particular time every week.

Use :meth:`period_week_at <schedule_manager.Task.period_week_at>` method to schedule a weekly task.

Argument **week_day** can be one of following value:
    - `Monday`
    - `Tuesday`
    - `Wednesday`
    - `Thursday`
    - `Friday`
    - `Saturday`
    - `Sunday`


.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Weekly Task
    # Job will be done at 15:00 on Tuesday every week
    task.period_week_at("15:00:00", week_day="Tuesday")


Monthly Task
^^^^^^^^^^^^

Monthly task will do the job at particular time every month.
Task will skip job activity that month if specific date is not available.

Use :meth:`period_month_at <schedule_manager.Task.period_month_at>` method to schedule a monthly task.

Argument **day** should be in 1 ~ 31.



.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Monthly Task
    # Job will be done at 12:00 on day 10 every month
    task.period_month_at("12:00:00", day=10)


    # Job will be done only in 1/31, 3/31, 5/31, 7/31, 8/31, 10/31
    # and 12/31 every year
    task.period_month_at("12:00:00", day=31)


Non-periodic Task
^^^^^^^^^^^^^^^^^

If you want to schedule a task to do job in a specific times, non-periodic task is appropriate for you.

Use :meth:`nonperiodic <schedule_manager.Task.nonperiodic>` method to schedule task as a non-periodic task after assigning time interval between job activity to the task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Non-periodic Task
    # Job will be done 10 times.
    task.period(60).nonperiodic(10)

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Schedule a 5 days daily task
    task.period_day_at("15:00:00").nonperiodic(5)


Postpone the Start of a Task
----------------------------

Sometimes we do not want to start the task immediately, we need to start it later.
So :class:`Task <schedule_manager.Task>` object provides two ways for us to postpone the start time of the task.

It is convenient especially for scheduling a periodic task.


Delay Task Start Time
^^^^^^^^^^^^^^^^^^^^^

We can set a delay time to postpone the start time of the task.

Use :meth:`delay <schedule_manager.Task.delay>` method to configure a delay time to a task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Task will be started after 600 seconds
    task.period(60).delay(600)

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Task will be started after 1 hour
    # String format should match `HH:MM:SS`
    task.period(60).delay("01:00:00")

.. code-block:: python

    from schedule_manager import Task
    from datetime import timedelta

    task = Task(name="task", job=print, args=("Hello task",))

    # Task will be started after 50 minutes
    task.period(60).delay(timedelta(minutes=50))


Start Task at Particular Time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can set a start time to tell the task when the task should be started.

Use :meth:`start_at <schedule_manager.Task.start_at>` method to configure a start time to a task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Task will be started at 21:00
    # String format should match `HH:MM:SS`
    task.period(60).start_at("21:00:00")

.. code-block:: python

    from schedule_manager import Task
    from datetime import datetime

    target = datetime(year=2020, month=8, day=15,
                      hour=12, minute=30, second=0)


    task = Task(name="task", job=print, args=("Hello task",))

    # Task will be started at 2020-08-15 12:30:00
    task.period(60).start_at(target)


Activate Task
-------------

After we have configured a :class:`Task <schedule_manager.Task>`,
we need to activate the task to let it do the job on schedule.

After activating the task, we are able to `stop` or `pause` the task in any time.


Start the Task
^^^^^^^^^^^^^^

We can use :meth:`start <schedule_manager.Task.start>` method to activate the task when we have configured already it.

Activation is `not allowed` if the task has not been scheduled.
We need to `schedule the task <#task-scheduling>`_ first.

Please note that the task `is not able to be configured` any more after we activate the task.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))

    # Schedule the task first.
    task.period(300)

    # Activate the task
    task.start()


Stop the Task
^^^^^^^^^^^^^

We can use :meth:`stop <schedule_manager.Task.stop>` method to stop the task's activity if we do not need it anymore.

The :meth:`stop <schedule_manager.Task.stop>` method is `not allowed` if the task is not activated.

Because :class:`Task <schedule_manager.Task>` class is inherited from :class:`Thread <threading.Thread>` class, the task is not able to be activated again.
(See `here <https://docs.python.org/3/library/threading.html#threading.Thread.start>`_ for more information.)

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))
    task.period(300).start()

    # Stop the task
    task.stop()

If the task is registered in a :class:`ScheduleManager <schedule_manager.ScheduleManager>`,
the :meth:`stop <schedule_manager.Task.stop>` method will unregister the task from the schedule manager automatically.

.. code-block:: python

    >>> from schedule_manager import ScheduleManager
    >>> from schedule_manager import Task
    >>> manager = ScheduleManager()
    >>> task = Task(name="task", job=print, args=("Hello task",))
    >>> manager.register(task).period_day_at("15:00:00").start()
    >>> "task" in manager
    True
    >>> task.stop()
    >>> "task" in manager
    False
    >>> task.start()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "D:\Application\Python3\Lib\site-packages\schedule_manager\manager.py", line 995, in start
        super().start()
      File "D:\Application\Python3\Lib\threading.py", line 848, in start
        raise RuntimeError("threads can only be started once")
    RuntimeError: threads can only be started once


Pause the Task
^^^^^^^^^^^^^^

We can use :meth:`pause <schedule_manager.Task.pause>` method to pause the task's activity if we want to reconfigure the task or want to stop the task for a while.

The :meth:`pause <schedule_manager.Task.pause>` method is `not allowed` if the task is not activated.

Please note that :meth:`pause <schedule_manager.Task.pause>` method is `only allowed` when the task is registerd in a :class:`ScheduleManager <schedule_manager.ScheduleManager>` object.

.. code-block:: python

    from schedule_manager import Task

    task = Task(name="task", job=print, args=("Hello task",))
    task.period(300).start()

    # Pause the task
    task.pause()

.. code-block:: python

    >>> from schedule_manager import ScheduleManager
    >>> from schedule_manager import Task
    >>> manager = ScheduleManager()
    >>> task = Task(name="task", job=print, args=("Hello task",))
    >>> manager.register(task).period_day_at("15:00:00").start()
    >>> "task" in manager
    True
    >>> task.pause()
    >>> "task" in manager
    True
    >>> manager.task("task").start()
    >>> manager.task("task").stop()

-------------------------------------------------------------------------

Check out :ref:`Advance Usage <advanced>` section for more information.
