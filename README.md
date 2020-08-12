Schedule Manager
------

[![Build Status](https://travis-ci.org/e619003/ScheduleManager.svg?branch=master)](https://travis-ci.org/e619003/ScheduleManager) 
[![codecov](https://codecov.io/gh/e619003/ScheduleManager/branch/master/graph/badge.svg)](https://codecov.io/gh/e619003/ScheduleManager) 
[![PyPI](https://img.shields.io/pypi/v/schedule-manager)](https://pypi.org/project/schedule-manager/)  

Thread-based task scheduling management.  

Schedule manager provide an easy way to schedule periodic jobs.  
Periodic, daily, weekly, monthly or even non-periodic jobs are available for scheduling as tasks.  

## Example

```python
from schedule_manager import ScheduleManager
from datetime import datetime


def example_job():
    print("Working now {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


manager = ScheduleManager()

# Schedule a periodic task: do job every 60 seconds
manager.register_task(name="task1",
                      job=example_job).period(60).start()
# Schedule a daily task: do job at 18:00 every day
manager.register_task(name="task2",
                      job=example_job).period_day_at("18:00:00").start()
# Schedule a periodic task: start task at 21:00
manager.register_task(name="task3",
                      job=example_job).period(120).start_at("21:00:00").start()
# Schedule a non-periodic task: do job 5 times
manager.register_task(name="task4",
                      job=example_job).period(30).nonperiodic(5).start()


# Pause task1
manager.task("task1").pause()



# Stop all tasks
manager.all_tasks.stop()
```

## Installation

Install schedule manager with pip:  

```sh
pip install schedule-manager
```

## How To Use

### 1. Task Management

Schedule manager provides a convenient way to manage tasks.  

##### I. Task registration

Here provides two ways to register task with  manager.  

###### 1. With ***register_task*** method：

```python
from schedule_manager import ScheduleManager

manager = ScheduleManager()

# Register job as a new task 
manager.register_task(name="task", job=print, args=("Hello task",)).period(60).start()
```

###### 2. With ***register*** method：

```python
from schedule_manager import ScheduleManager
from schedule_manager import Task

manager = ScheduleManager()

task = Task(name="task", job=print, args=("Hello task",)).period(60)
task.start()

# Register an existing task 
manager.register(task)
```

##### II. Obtain registered task

It is able to get task by task name or by task tags.  

###### 1. Get task by **name**:

```python
from schedule_manager import ScheduleManager

manager = ScheduleManager()
manager.register_task(name="task1", job=print, args=("Hello task1",))
manager.register_task(name="task2", job=print, args=("Hello task2",))

# Get task1
task = manager.task("task1")
```

###### 2. Get tasks by **tag**:

```python
from schedule_manager import ScheduleManager

manager = ScheduleManager()
manager.register_task(name="task1", job=print, args=("Hello task1",)).add_tag("label-1")
manager.register_task(name="task2", job=print, args=("Hello task2",)).add_tag("label-2")
manager.register_task(name="task3", job=print, args=("Hello task3",)).add_tag("label-1")

# Get task1 and task3 whuch tags have "label-1"
task = manager.tasks("label-1")
```

##### III. Daemon thread based task

A task can be flagged as a daemon thread based task.  

```python
from schedule_manager import ScheduleManager

manager = ScheduleManager()
manager.register_task(name="task", job=print, args=("Hello task",))

# Flagged as a daemon thread based task
manager.task("task").daemon = True
```

### 2. Task Scheduling

Job is able to be scheduled as periodic, daily, weekly, monthly or even non-periodic task.  

##### I. Periodic task

Scheduling a periodic task by using **period** method.  

```python
# Set time interval to 300 seconds
manager.task("task").period(300)
```

```python
# Set time interval to 1 hour and 30 minutes
manager.task("task").period("01:30:00")
```

```python
from datetime import timedelta

# Set time interval to 20 minutes
manager.task("task").period(timedelta(minutes=20))
``` 

##### II. Daily task

Scheduling a daily task by using **period_day_at** method.  

```python
# Do job at 15:00 everyday
manager.task("task").period_day_at("15:00:00")
```

##### III. Weekly task

Scheduling a weekly task by using **period_week_at** method.  

```python
# Do job at 15:00 on Tuesday every week
manager.task("task").period_week_at("15:00:00", "Tuesday")
```

##### VI. Monthly task

Scheduling a monthly task by using **period_month_at** method.  

```python
# Do job at 12:00 on day 10 every month
manager.task("task").period_month_at("12:00:00", day=10)
```

##### V. Non-periodic task

Scheduling a non-periodic task by using **nonperiodic** method.  
Time interval between job activity is required in the task.  

```python
# A task which will do job 10 times
manager.task("task").period(60).nonperiodic(10)
```

```python
# A 5 days daily task
manager.task("task").period_day_at("15:00:00").nonperiodic(5)
```

### 3. Postpone the Start of a Task

 It is able to postpone a task by setting delay time or assigning a particular start time.  

##### I. Delay task start time

Set delay time to the task.  

```python
# Start of task delay 600 seconds
manager.task("task").period(60).delay(600)
```

```python
# Start of task delay 1 hour
manager.task("task").period(60).delay("01:00:00")
```

```python
from datetime import timedelta

# Start of task delay 50 minutes
manager.task("task").period(60).delay(timedelta(minutes=50))
```

##### II. Start task at particular time

Set particular start time to the task.  

```python
# Start task at 21:00
manager.task("task").period(60).start_at("21:00:00")
```

```python
from datetime import datetime

target = datetime(year=2020, month=8, day=15,
                  hour=12, minute=30, second=0)

# Start task at 2020-08-15 12:30:00
manager.task("task").period(60).start_at(target)
```

### 4. Task Operation

Task object is able to be **started** or **stopped** no matter the task is registered in the manager.  
But it is necessary to register task in a manager for working with **pause** operation.  

##### I. Start the task

Use ***start()*** method to start the task.  

```python
# Start task
manager.task("task").start()
```

##### II. Stop the task

Use ***stop()*** method to stop the task.  

```python
# Stop task
manager.task("task").stop()
```

##### II. Pause the task

Use ***pause()*** method to Pause the task.  

```python
# Pause task
manager.task("task").pause()
```

*OperationFailError* exception will be raised if the task is not be registered in a manager.  

```python
>>> from schedule_manager import Task
>>> task = Task(name="task", job=print, args=("Hello task!",)).period(30)
>>> task.start()
Hello task!
>>> task.pause()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "C:\Workspace\VENV\test-venv\lib\site-packages\schedule_manager\manager.py", line 1013, in pause
    raise OperationFailError("Register task into "
schedule_manager.exceptions.OperationFailError: Register task into ScheduleManager first.
>>> 
```

### 5. Task Tag Management

Tags in the task can be added or deleted.  

##### I. Add tag

Use ***add_tag*** method to add single tag or use ***add_tags*** method to add multiple tags.  

```python
# Add tag "tag1"
manager.task("task").add_tag("tag1")


# Add tags "tagA" and "label-A"
manager.task("task").add_tags(["tagA", "label-A"])
```

##### II. Remove tag

Use ***remove_tag*** method to remove single tag or use ***remove_tags*** method to remove multiple tags.  

```python
# Remove tag "tag1"
manager.task("task").remove_tag("tag1")


# Remove tags "tagA" and "label-A"
manager.task("task").remove_tags(["tagA", "label-A"])
```

##### III. Set tag

Use ***set_tags*** method to set particulars tags.  
Old tags will be removed first.  

```python
# Set tags to "tagA" and "label-A"
manager.task("task").set_tags(["tagA", "label-A"])
```

### 6. Operating Multiple Tasks

TaskGroup allows operating multiple tasks in a time and it is able to be operated like single task.  

##### I. TaskGroup from schedule manager

```python
# TaskGroup with all tasks in the manager
task_group1 = manager.all_tasks

# TaskGroup with all running tasks in the manager
task_group2 = manager.running_tasks

# TaskGroup with all pending tasks in the manager
task_group3 = manager.pending_tasks
```

```python
from schedule_manager import ScheduleManager
manager = ScheduleManager()


manager.register_task(name="task1", job=example_job).add_tags(["tag1", "label-1"])
manager.register_task(name="task2", job=example_job).add_tags(["tag2"])
manager.register_task(name="task3", job=example_job).add_tags(["tag3"])
manager.register_task(name="task4", job=example_job).add_tags(["tag4", "label-1"])

# TaskGroup: task has tag "label-1"
# task1 and task4
task_group1 = manager.tasks("label-1")

# TaskGroup: task has tag "label-1" or "tag2"
# task1, task2 and task4
task_group2 = manager.tasks(["label-1", "tag2"])
```

##### II. TaskGroup Operation

TaskGroup is able to be operated like single task.  
The operation will affect with all tasks in TaskGroup.  

```python
task_group = manager.pending_tasks

task_group.add_tag("tag1")
task_group.add_tags(["tagA", "label-A"])
task_group.remove_tag("tag1")
task_group.remove_tags(["tagA", "label-A"])
task_group.set_tags(["tagA", "label-A"])

task_group.period(300)
task_group.period_day_at("15:00:00")
task_group.period_week_at("15:00:00", "Tuesday")
task_group.period_month_at("12:00:00", day=10)
task_group.period(60).nonperiodic(10)

task_group.period(60).delay(600)
task_group.period(60).start_at("21:00:00")

task_group.start()
task_group.stop()
task_group.pause()
```
