Schedule Manager
----------------

[![Build Status](https://travis-ci.org/e619003/ScheduleManager.svg?branch=master)](https://travis-ci.org/e619003/ScheduleManager) 
[![codecov](https://codecov.io/gh/e619003/ScheduleManager/branch/master/graph/badge.svg)](https://codecov.io/gh/e619003/ScheduleManager) 
[![PyPI](https://img.shields.io/pypi/v/schedule-manager)](https://pypi.org/project/schedule-manager/) 
[![Documentation Status](https://readthedocs.org/projects/schedulemanager/badge/?version=latest)](https://schedulemanager.readthedocs.io/en/latest/?badge=latest)  

Thread-based task scheduling management.  

Schedule manager provide an easy way to schedule periodic jobs.  
Periodic, daily, weekly, monthly or even non-periodic jobs are available for scheduling as tasks.  

## Example Code

```python
from schedule_manager import ScheduleManager
from datetime import datetime


def example_job():
    print("Working now {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


manager = ScheduleManager()

# Schedule a periodic task: do job every 60 seconds
manager.register_task(name="task1", job=example_job).period(60).start()
# Schedule a daily task: do job at 18:00 every day
manager.register_task(name="task2", job=example_job).period_day_at("18:00:00").start()
# Schedule a periodic task: start task at 21:00
manager.register_task(name="task3", job=example_job).period(120).start_at("21:00:00").start()
# Schedule a non-periodic task: do job 5 times
manager.register_task(name="task4", job=example_job).period(30).nonperiodic(5).start()


# Pause task1
manager.task("task1").pause()



# Stop all tasks
manager.all_tasks.stop()
```

## Installation

Install schedule manager with pip:  

```
pip install schedule-manager
```

## Documentation

Documentation is available at [**schedulemanager.readthedocs.io**](https://schedulemanager.readthedocs.io).
