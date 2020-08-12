.. Schedule Manager documentation master file, created by
   sphinx-quickstart on Fri Aug  7 23:25:01 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Schedule Manager
================

.. image:: https://travis-ci.org/e619003/ScheduleManager.svg?branch=master
    :target: https://travis-ci.org/e619003/ScheduleManager

.. image:: https://codecov.io/gh/e619003/ScheduleManager/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/e619003/ScheduleManager

.. image:: https://img.shields.io/pypi/v/schedule-manager
    :target: https://pypi.org/project/schedule-manager/

| A thread-based task scheduler. 
| Schedule manager provides an easy way to schedule your jobs.

Periodic, daily, weekly, monthly or even non-periodic jobs are available for scheduling as tasks.


Quick Installation
------------------

.. code-block:: bash

    $ pip install schedule-manager


Example
-------

.. code-block:: python

    from schedule_manager import ScheduleManager
    from datetime import datetime


    def jobs():
        current = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("Working now {}".format(current))


    manager = ScheduleManager()

    # Schedule a periodic task: do job every 60 seconds
    manager.register_task(name="task1", job=jobs).period(60).start()

    # Schedule a daily task: do job at 18:00 every day
    manager.register_task(name="task2",
                          job=jobs).period_day_at("18:00:00").start()

    # Schedule a periodic task: start task at 21:00
    manager.register_task(name="task3",
                          job=jobs).period(90).start_at("21:00:00").start()

    # Schedule a non-periodic task: do job 5 times
    manager.register_task(name="task4",
                          job=jobs).period(30).nonperiodic(5).start()


    # Pause task1
    manager.task("task1").pause()



    # Stop all tasks
    manager.all_tasks.stop()


User Guide
----------

.. toctree::
   :maxdepth: 3

   guide/install
   guide/quickstart
   guide/advanced


API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   api


License
-------

MIT license.

See `LICENSE <https://github.com/e619003/ScheduleManager/blob/master/LICENSE>`_ for for more information.
