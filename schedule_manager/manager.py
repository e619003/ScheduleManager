"""
Schedule management module.
"""
import threading
import uuid
import re
import time
from datetime import datetime, timedelta
import math

from .exceptions import TaskNameDuplicateError
from .exceptions import TaskNotFoundError
from .exceptions import TimeFormatError
from .exceptions import OperationFailError


class ScheduleManager:
    """Task schedule manager."""

    def __init__(self):
        """Constructor"""
        self._tasks = dict()

    def __del__(self):
        """Destructor"""
        # Make sure all tasks are not running.
        self.running_tasks.stop()

    def __contains__(self, name):
        """Returns True if task name is registered."""
        return name in self._tasks

    def __repr__(self):
        return ("ScheduleManager<("
                "Tasks: {c}, Running: {r}, Pending: {p}"
                ")>").format(c=self.count,
                             r=self.running_tasks.count,
                             p=self.pending_tasks.count)

    @property
    def count(self):
        """int: Number of tasks registered in the schedule manager."""
        return len(self._tasks)

    @property
    def all_tasks(self):
        """TaskGroup: All tasks."""
        return TaskGroup(list(self._tasks.values()))

    @property
    def running_tasks(self):
        """TaskGroup: All running tasks."""
        task_list = list()

        for name in self._tasks:
            if self._tasks[name].is_running:
                task_list.append(self._tasks[name])

        return TaskGroup(task_list)

    @property
    def pending_tasks(self):
        """TaskGroup: All pending tasks."""
        task_list = list()

        for name in self._tasks:
            if not self._tasks[name].is_running:
                task_list.append(self._tasks[name])

        return TaskGroup(task_list)

    def task(self, name):
        """Get task registerd in schedule manager by name.

        Args:
            name (str): Task name.

        Returns:
            Task: Task instance.

        Raises:
            TaskNotFoundError: Task is not registered in schedule manager.
        """
        if name not in self._tasks:
            raise TaskNotFoundError

        return self._tasks[name]

    def _task_list(self, tag):
        task_list = list()

        if isinstance(tag, list):
            for tag_ in tag:
                for name in self._tasks:
                    if tag_ in self._tasks[name].tag:
                        if self._tasks[name] not in task_list:
                            task_list.append(self._tasks[name])
        else:
            for name in self._tasks:
                if tag in self._tasks[name].tag:
                    task_list.append(self._tasks[name])

        return task_list

    def tasks(self, tag):
        """Get tasks registerd in schedule manager by name.

        Args:
            tag (Union[obj, list]): Tag or tag list.

        Returns:
            TaskGroup: TaskGroup instance.
        """
        task_list = self._task_list(tag)

        return TaskGroup(task_list)

    def register(self, task):
        """Register a task.

        Args:
            task (Task): Task.

        Returns:
            Task: Registered task instance.

        Raises:
            TaskNameDuplicateError: Duplicate task name.
        """
        if task.name in self._tasks:
            raise TaskNameDuplicateError

        self._tasks[task.name] = task

        task.manager = self

        return task

    def register_task(self, job, name=None, args=(), kwargs=None):
        """Create and register a task.

        Args:
            job (callable): Job to be scheduled.
            name (str): Task name.
                By default, a unique name is constructed.
            args (tuple): Argument tuple for the job invocation.
                Defaults to ().
            kwargs (dict): Dictionary of keyword arguments for the job
                invocation.
                Defaults to {}.

        Returns:
            Task: Registered task instance.

        Raises:
            TaskNameDuplicateError: Duplicate task name.
        """
        if name is None:
            name = "Task-{}".format(uuid.uuid4().hex)
            while name in self._tasks:
                name = "Task-{}".format(uuid.uuid4().hex)
        elif name in self._tasks:
            raise TaskNameDuplicateError

        task = Task(name=name, job=job, args=args, kwargs=kwargs)

        self._tasks[name] = task

        task.manager = self

        return task

    def unregister(self, name=None, tag=None):
        """Unregister the task.

        Args:
            name (str): Unregister task by name.
            tag (Union[obj, list]): Unregister tasks by tag or by
                a list of tags.
        """
        if name:
            if name in self._tasks:
                task = self._tasks[name]

                del self._tasks[name]
                task.manager = None

        if tag:
            task_list = self._task_list(tag)

            for task in task_list:
                del self._tasks[task.name]
                task.manager = None


class Task(threading.Thread):
    """Thread-based Task.

    Task will be considered as periodic task by default.

    :class:`Task` is able to registered in :class:`ScheduleManager` or run
    directly.

    Attributes:
        job (callable): Job to be scheduled as a task.
        name (str): Task name.
        args (tuple): Argument tuple for the job invocation.
        kwargs (dict): Dictionary of keyword arguments for the job invocation.
        ignore_skipped (bool): Set True to ignore skipped job if time spent on
                 job is longer than the task cycle time.
    """

    def __init__(self, job, name=None, args=(), kwargs=None,
                 ignore_skipped=True):
        """Constructor

        Args:
            job (callable): Job to be scheduled as a task.
            name (str): Task name.
                By default, a unique name is constructed.
            args (tuple): Argument tuple for the job invocation.
                Defaults to ().
            kwargs (dict): Dictionary of keyword arguments for the job
                invocation.
                Defaults to {}.
            ignore_skipped (bool): Set True to ignore skipped job if time
                spent on job is longer than the task cycle time.
                Defaults to True.
        """
        self.CHECK_INTERVAL = 1

        # Flag (start task): Set to True is start() is called.
        self._start = False

        # Flag (stop task): Used to stop current task
        self._stop_task = False

        # Flag (pause task):
        #     Used re-registercurrent task because threads can only
        #     be started once
        self._pause_task = False

        self._manager = None
        self._tag = list()    # Tag list

        self._ignore_skipped = ignore_skipped    # Ignore skipped job activity.

        self._next_run = None    # datetime when the job run at next time

        self._delay = None    # Task delay time
        self._start_at = None    # Task start time

        self._is_periodic = True    # A periodic task or a non-periodic task.
        self._nonperiod_count = 0    # Count used for non-periodic task.
        self._periodic_unit = None
        self._periodic = None
        self._at_time = None
        self._at_week_day = None
        self._at_day = None

        if name is None:
            name = "Task-{}".format(uuid.uuid4().hex)

        super().__init__(target=job, name=name, args=args, kwargs=kwargs)

    def __repr__(self):
        status = "initial"
        if self._start:
            status = "started"
        if self._stop_task:
            status = "stopping"
        if self._is_stopped:
            status = "stopped"
        if self._daemonic:
            status += " daemon"
        if self._ident is not None:
            status += " %s" % self._ident

        d_format = "%y-%m-%d %H:%M:%S"
        if self._next_run:
            time_next_run = self._next_run.strftime(d_format)
        else:
            if self._start and self._start_at:
                time_next_run = "Start At {}".format((self
                                                      ._start_at
                                                      .strftime(d_format)))
            else:
                time_next_run = None

        return "Task<({}, {}, {})>".format(self._name, status, time_next_run)

    @property
    def next_run(self):
        """datetime: Datetime when the job run at next time."""
        returns = self._next_run

        if self._start:
            if not returns and self._start_at:
                returns = self._start_at

        return returns

    @property
    def is_running(self):
        """bool: Return True if the task is running."""
        return self._start

    @property
    def manager(self):
        """ScheduleManager: Schedule manager which manages current task."""
        return self._manager

    @manager.setter
    def manager(self, manager):
        """Register task into schedule manager.

        Use ScheduleManager.register(Task) instead of using
        Task.set_manager(manager).

        Args:
            manager (ScheduleManager): ScheduleManager instance.
        """
        if not manager:
            if self._manager is None:
                raise OperationFailError("Use ScheduleManager.register(Task)"
                                         " instead.")
            if self.name in self._manager:
                raise OperationFailError("Use ScheduleManager.register(Task)"
                                         " instead.")

            self._manager = None

            return

        if self.name not in manager:
            raise OperationFailError("Use ScheduleManager.register(Task)"
                                     " instead.")
        if self is not manager.task(self.name):
            raise OperationFailError("Use ScheduleManager.register(Task)"
                                     " instead.")

        self._manager = manager

    @property
    def tag(self):
        """list: Tag list of the task."""
        return self._tag

    def add_tag(self, tag):
        """Add tag to task.

        Args:
            tag (obj): Tag.

        Returns:
            Task: Invoked task instance.
        """
        if tag not in self._tag:
            self._tag.append(tag)

        return self

    def add_tags(self, tags):
        """Add a list of tags to task.

        Args:
            tags (iterable): Tag list.

        Returns:
            Task: Invoked task instance.
        """
        for tag in tags:
            self.add_tag(tag)

        return self

    def remove_tag(self, tag):
        """Remove tag from task.

        Args:
            tag (obj): Tag.

        Returns:
            Task: Invoked task instance.
        """
        if tag in self._tag:
            self._tag.remove(tag)

        return self

    def remove_tags(self, tags):
        """Remove a list of tags from task.

        Args:
            tags (iterable): Tag list.

        Returns:
            Task: Invoked task instance.
        """
        for tag in tags:
            self.remove_tag(tag)

        return self

    def set_tags(self, tags):
        """Set tag list to task.

        Replace old tag list.

        Args:
            tags (iterable): Tag list.

        Returns:
            Task: Invoked task instance.
        """
        self._tag.clear()

        for tag in tags:
            if tag not in self._tag:
                self._tag.append(tag)

        return self

    def delay(self, interval=None):
        """Task delay time.

        Args:
            interval (Union[str, timedelta, int]): Time interval.
                A string with format `HH:MM:SS` or :obj:`timedelta` or int in
                seconds.
                Or set None to cancel task delay time.
                Defaults to None.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        if interval is None:
            self._delay = None
        else:
            if isinstance(interval, timedelta):
                self._start_at = None    # Use delay instead of start time.
                self._delay = interval
            elif isinstance(interval, int):
                self._start_at = None    # Use delay instead of start time.
                self._delay = timedelta(seconds=interval)
            else:
                time_pattern = r'^([0-1]?\d|[2][0-3]):[0-5]?\d:[0-5]?\d$'
                if re.match(time_pattern, interval):
                    self._start_at = None    # Use delay instead of start time.
                    tsp = interval.split(":")
                    self._delay = timedelta(hours=int(tsp[0]),
                                            minutes=int(tsp[1]),
                                            seconds=int(tsp[2]))
                else:
                    raise TimeFormatError

        return self

    def start_at(self, at_time=None):
        """Set task start time.

        Specify a particular time that the job should be start.

        Args:
            at_time (Union[str, datetime]): Start time.
                A string or :obj:`datetime`.
                A string can be in one of the following formats:
                    `HH:MM:SS`, `mm-dd HH:MM:SS`
                Or set None to cancel task start time.
                Defaults to None.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        if at_time is None:
            self._start_at = None
        else:
            if isinstance(at_time, datetime):
                self._delay = None    # Use start time instead of delay.
                self._start_at = at_time
            else:
                match1 = r'^([0-1]?\d|[2][0-3]):[0-5]?\d:[0-5]?\d$'
                match2 = (r'^([0]?\d|[1][0-2])-([0-2]?\d|[3][0-1])'
                          r' ([0-1]?\d|[2][0-3]):[0-5]?\d:[0-5]?\d$')
                if re.match(match1, at_time):
                    self._delay = None    # Use start time instead of delay.
                    tsp = at_time.split(":")

                    self._start_at = datetime.now().replace(hour=int(tsp[0]),
                                                            minute=int(tsp[1]),
                                                            second=int(tsp[2]))
                elif re.match(match2, at_time):
                    self._delay = None    # Use start time instead of delay.
                    dtsp = at_time.split(" ")
                    dsp = dtsp[0].split("-")
                    tsp = dtsp[1].split(":")

                    self._start_at = datetime.now().replace(month=int(dsp[0]),
                                                            day=int(dsp[1]),
                                                            hour=int(tsp[0]),
                                                            minute=int(tsp[1]),
                                                            second=int(tsp[2]))
                else:
                    raise TimeFormatError

        return self

    def nonperiodic(self, count):
        """See as an non-periodic task.

        Args:
            count (int): Do the job for a certain number of times.

        Returns:
            Task: Invoked task instance.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        if count <= 0:
            raise OperationFailError("Number of times must be greater than 0.")

        self._is_periodic = False
        self._nonperiod_count = count

        return self

    def periodic(self):
        """See as an periodic task.

        Returns:
            Task: Invoked task instance.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        self._is_periodic = True

        return self

    def period(self, interval):
        """Scheduling periodic task.

        Args:
            interval (Union[str, timedelta, int]): Time interval.
                A string with format `HH:MM:SS` or :obj:`timedelta` or int in
                seconds.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        self._periodic_unit = "every"

        if isinstance(interval, timedelta):
            self._periodic = interval
        elif isinstance(interval, int):
            self._periodic = timedelta(seconds=interval)
        else:
            if re.match(r'^([0-1]?\d|[2][0-3]):[0-5]?\d:[0-5]?\d$', interval):
                tsp = interval.split(":")
                self._periodic = timedelta(hours=int(tsp[0]),
                                           minutes=int(tsp[1]),
                                           seconds=int(tsp[2]))
            else:
                raise TimeFormatError

        return self

    def period_at(self, unit="day", at_time="00:00:00",
                  week_day="Monday", day=1):
        """Scheduling periodic task.

        Specify a particular time that the job should be run at.

        Args:
            unit (str): Time unit of the periodic task.
                Defaults to `day`.
                The following unit is available:
                    1. `day`: Run job everyday.
                    2. `week`: Run job every week.
                    3. `month`: Run job every month.
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.
                Defaults to `Monday`.
                This argument will only be used is unit is `week`.
                A string should br one of following value:
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"]
            day (int): Day to do the job.
                Defaults to 1.
                This argument will only be used is unit is `month`.
                Value should be in 1 ~ 31.
                Job will be skipped if specific date is not available.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        if self._start:
            raise OperationFailError("Task is already running.")

        time_pattern = r'^([0-1]?\d|[2][0-3]):[0-5]?\d:[0-5]?\d$'

        week_day_list = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

        if unit == "day":
            self._periodic_unit = unit

            if not re.match(time_pattern, at_time):
                raise TimeFormatError

            tsp = at_time.split(":")
            self._at_time = [int(i) for i in tsp]

        elif unit == "week":
            self._periodic_unit = unit

            if not re.match(time_pattern, at_time):
                raise TimeFormatError
            tsp = at_time.split(":")
            self._at_time = [int(i) for i in tsp]

            if week_day not in week_day_list:
                raise TimeFormatError
            self._at_week_day = week_day_list[week_day]

        elif unit == "month":
            self._periodic_unit = unit

            if not re.match(time_pattern, at_time):
                raise TimeFormatError
            tsp = at_time.split(":")
            self._at_time = [int(i) for i in tsp]

            if day not in range(1, 32):
                raise TimeFormatError
            self._at_day = day

        else:
            raise TimeFormatError

        return self

    def period_day_at(self, at_time="00:00:00"):
        """Scheduling periodic task.

        Specify a particular time that the job should be run at.
        Job runs everyday.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        self.period_at(unit="day", at_time=at_time)

        return self

    def period_week_at(self, at_time="00:00:00", week_day="Monday"):
        """Scheduling periodic task.

        Specify a particular time that the job should be run at.
        Job runs every week.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.
                Defaults to `Monday`.
                A string should br one of following value:
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"]

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        self.period_at(unit="week", at_time=at_time, week_day=week_day)

        return self

    def period_month_at(self, at_time="00:00:00", day=1):
        """Scheduling periodic task.

        Specify a particular time that the job should be run at.
        Job runs every month.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            day (int): Day to do the job.
                Defaults to 1.
                Value should be in 1 ~ 31.
                Job will be skipped if specific date is not available.

        Returns:
            Task: Invoked task instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        self.period_at(unit="month", at_time=at_time, day=day)

        return self

    def _set_next_run_init(self):
        # First time the job run at.
        if self._periodic_unit == "every":
            self._next_run = datetime.now()
        elif self._periodic_unit == "day":
            self._set_next_run_init_day()
        elif self._periodic_unit == "week":
            self._set_next_run_init_week()
        elif self._periodic_unit == "month":
            self._set_next_run_init_month()

    def _set_next_run_init_day(self):
        run_time = datetime.now().replace(hour=self._at_time[0],
                                          minute=self._at_time[1],
                                          second=self._at_time[2])

        if run_time < datetime.now():
            self._next_run = run_time + timedelta(days=1)
        else:
            self._next_run = run_time

    def _set_next_run_init_week(self):
        tmp_runtime = datetime.now().replace(hour=self._at_time[0],
                                             minute=self._at_time[1],
                                             second=self._at_time[2])

        now_weekday = tmp_runtime.date().weekday()
        if now_weekday < self._at_week_day:
            tmp_runtime += timedelta(days=self._at_week_day-now_weekday)
        elif now_weekday > self._at_week_day:
            tmp_runtime += timedelta(days=7+self._at_week_day-now_weekday)
        else:
            if tmp_runtime < datetime.now():
                tmp_runtime += timedelta(days=7)

        self._next_run = tmp_runtime

    def _set_next_run_init_month(self):
        try:
            tmp_runtime = datetime.now().replace(day=self._at_day,
                                                 hour=self._at_time[0],
                                                 minute=self._at_time[1],
                                                 second=self._at_time[2])

            if datetime.now().day > self._at_day:
                if tmp_runtime.month == 12:
                    tmp_runtime = tmp_runtime.replace(year=tmp_runtime.year+1,
                                                      month=1)
                else:
                    try:
                        tmp_runtime = tmp_runtime.replace(month=(tmp_runtime
                                                                 .month)+1)
                    except ValueError:
                        # Because day is out of range in next month.
                        tmp_runtime = tmp_runtime.replace(month=(tmp_runtime
                                                                 .month)+2)
            elif datetime.now().day == self._at_day:
                if tmp_runtime < datetime.now():
                    if tmp_runtime.month == 12:
                        tmp_runtime = tmp_runtime.replace(year=(tmp_runtime
                                                                .year)+1,
                                                          month=1)
                    else:
                        try:
                            tmp_runtime = (tmp_runtime
                                           .replace(month=tmp_runtime.month+1))
                        except ValueError:
                            # Because day is out of range in next month.
                            tmp_runtime = (tmp_runtime
                                           .replace(month=tmp_runtime.month+2))

            self._next_run = tmp_runtime
        except ValueError:
            # Because day is out of range in this month.
            self._next_run = datetime.now().replace(month=(datetime
                                                           .now()
                                                           .month)+1,
                                                    day=self._at_day,
                                                    hour=self._at_time[0],
                                                    minute=self._at_time[1],
                                                    second=self._at_time[2])

    def _set_next_run(self):
        if self._periodic_unit == "every":
            self._set_next_run_every()
        elif self._periodic_unit == "day":
            self._set_next_run_day()
        elif self._periodic_unit == "week":
            self._set_next_run_week()
        elif self._periodic_unit == "month":
            self._set_next_run_month()

    def _set_next_run_every(self):
        if self._ignore_skipped:
            next_ = self._next_run + self._periodic

            if next_ < datetime.now():
                rate = (datetime.now() - self._next_run) / self._periodic
                next_ = self._next_run + math.ceil(rate) * self._periodic

            if next_ == datetime.now():
                next_ += self._periodic

            self._next_run = next_
        else:
            self._next_run += self._periodic

    def _set_next_run_day(self):
        if self._ignore_skipped:
            next_ = self._next_run + timedelta(days=1)

            if next_ < datetime.now():
                # Record current datetime to avoid 23:59:XX situation.
                time_now = datetime.now()

                next_ = next_.replace(month=time_now.month,
                                      day=time_now.day)

            if next_ <= datetime.now():
                next_ += timedelta(days=1)

            self._next_run = next_
        else:
            self._next_run += timedelta(days=1)

    def _set_next_run_week(self):
        if self._ignore_skipped:
            next_ = self._next_run + timedelta(days=7)

            if next_ < datetime.now():
                next_ = datetime.now().replace(hour=self._at_time[0],
                                               minute=self._at_time[1],
                                               second=self._at_time[2])

                weekday_ = next_.date().weekday()
                if weekday_ < self._at_week_day:
                    next_ += timedelta(days=self._at_week_day-weekday_)
                elif weekday_ > self._at_week_day:
                    next_ += timedelta(days=7+self._at_week_day-weekday_)
                else:
                    if next_ < datetime.now():
                        next_ += timedelta(days=7)

            if next_ <= datetime.now():
                next_ += timedelta(days=7)

            self._next_run = next_
        else:
            self._next_run += timedelta(days=7)

    def _set_next_run_month(self):
        if self._ignore_skipped:
            if self._next_run.month == 12:
                next_ = self._next_run.replace(year=self._next_run.year+1,
                                               month=1)
            else:
                try:
                    next_ = self._next_run.replace(month=(self
                                                          ._next_run
                                                          .month)+1)
                except ValueError:
                    # Because day is out of range in next month.
                    next_ = self._next_run.replace(month=(self
                                                          ._next_run
                                                          .month)+2)

            if next_ < datetime.now():
                try:
                    next_ = datetime.now().replace(day=self._at_day,
                                                   hour=self._at_time[0],
                                                   minute=self._at_time[1],
                                                   second=self._at_time[2])

                    if datetime.now().day > self._at_day:
                        if next_.month == 12:
                            next_ = next_.replace(year=next_.year+1,
                                                  month=1)
                        else:
                            try:
                                next_ = next_.replace(month=next_.month+1)
                            except ValueError:
                                # Because day is out of range in next month.
                                next_ = next_.replace(month=next_.month+2)
                    elif datetime.now().day == self._at_day:
                        if next_ < datetime.now():
                            if next_.month == 12:
                                next_ = next_.replace(year=next_.year+1,
                                                      month=1)
                            else:
                                try:
                                    next_ = next_.replace(month=next_.month+1)
                                except ValueError:
                                    # Because day is out of range in next
                                    # month.
                                    next_ = next_.replace(month=next_.month+2)
                except ValueError:
                    next_ = datetime.now().replace(month=(datetime
                                                          .now()
                                                          .month)+1,
                                                   day=self._at_day,
                                                   hour=self._at_time[0],
                                                   minute=self._at_time[1],
                                                   second=self._at_time[2])

            if next_ <= datetime.now():
                if next_.month == 12:
                    next_ = next_.replace(year=next_.year+1,
                                          month=1)
                else:
                    try:
                        next_ = next_.replace(month=next_.month+1)
                    except ValueError:
                        # Because day is out of range in next month.
                        next_ = next_.replace(month=next_.month+2)

            self._next_run = next_
        else:
            if self._next_run.month == 12:
                self._next_run = self._next_run.replace(year=(self
                                                              ._next_run
                                                              .year)+1,
                                                        month=1)
            else:
                try:
                    month_next = self._next_run.month+1
                    self._next_run = self._next_run.replace(month=month_next)
                except ValueError:
                    # Because day is out of range in next month.
                    month_next = self._next_run.month+2
                    self._next_run = self._next_run.replace(month=month_next)

    def _next_run_at(self):
        if self._next_run is None:
            self._set_next_run_init()
        else:
            self._set_next_run()

    def start(self):
        """Start the Task's activity."""
        if not self._periodic_unit:
            raise OperationFailError("Please set period first.")

        self._start = True

        # Set start at by delay time
        if self._delay:
            self._start_at = datetime.now() + self._delay

        super().start()

    def stop(self):
        """Stop the Task's activity."""
        if not self._start:
            raise OperationFailError("Task is not running.")

        self._start = False
        self._stop_task = True

    def pause(self):
        """Pause the Task's activity.

        Works only the task is registered into ScheduleManager.
        """
        if not self._start:
            raise OperationFailError("Task is not running.")
        if not self._manager:
            raise OperationFailError("Register task into "
                                     "ScheduleManager first.")

        self._start = False
        self._stop_task = True
        self._pause_task = True

    def _action_after_finish(self):
        # Remove task from manager
        if self._manager:
            # Keep ScheduleManager instance
            manager = self._manager
            manager.unregister(self.name)

            if self._pause_task:
                # Thread-based object can only be started once.
                # So create new task with same action and register task after
                # delete.
                # current task to realize pause action.

                kwargs = None if self._kwargs == {} else self._kwargs

                # New task
                new_task = manager.register_task(name=self.name,
                                                 job=self._target,
                                                 args=self._args,
                                                 kwargs=kwargs)
                new_task.set_tags(self.tag)

                # schedule task
                if self._periodic_unit == "every":
                    new_task.period(self._periodic)
                else:
                    ref_week = {
                        0: "Monday",
                        1: "Tuesday",
                        2: "Wednesday",
                        3: "Thursday",
                        4: "Friday",
                        5: "Saturday",
                        6: "Sunday",
                        None: None
                    }

                    time_str = "{}:{}:{}".format(str(self._at_time[0]),
                                                 str(self._at_time[1]),
                                                 str(self._at_time[2]))
                    new_task.period_at(unit=self._periodic_unit,
                                       at_time=time_str,
                                       week_day=ref_week[self._at_week_day],
                                       day=self._at_day)

                if not self._is_periodic:
                    new_task.nonperiodic(self._nonperiod_count)

                if self._delay:
                    new_task.delay(self._start_at - datetime.now())
                elif self._start_at:
                    if datetime.now() < self._start_at:
                        new_task.start_at(self._start_at)

    def run(self):
        """Representing the Task's activity.

        DO NOT CALL DIRECTLY.
        """
        if not self._start:
            raise OperationFailError("Use Task.start() instead.")

        # Modified from :meth:`Thread.run`.
        try:
            # Delay or start at.
            if self._start_at:
                while not self._stop_task:
                    if datetime.now() >= self._start_at:
                        break

                    time.sleep(self.CHECK_INTERVAL)

            self._next_run_at()

            while not self._stop_task:

                if datetime.now() >= self._next_run:
                    self._target(*self._args, **self._kwargs)
                    self._next_run_at()

                    if not self._is_periodic:
                        self._nonperiod_count -= 1
                        if self._nonperiod_count <= 0:
                            self._stop_task = True
                            break

                time.sleep(self.CHECK_INTERVAL)
        finally:
            self._action_after_finish()

            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs


class TaskGroup:
    """Task group.

    A set of tasks.

    Attributes:
        tasks (iterable): Job to be scheduled as a task.
    """

    def __init__(self, tasks=None):
        """Constructor

        Args:
            tasks (iterable): Task list.
        """
        if not tasks:
            self._tasks = list()
        else:
            self._tasks = list()

            if isinstance(tasks, list):
                self._tasks = tasks[:]
            else:
                for task in tasks:
                    self._tasks.append(task)

    def __repr__(self):
        return ("TaskGroup<("
                "Tasks: {task_count}"
                ")>").format(task_count=len(self._tasks))

    def __contains__(self, task):
        """Returns True if task is in the group."""
        return task in self._tasks

    def __iter__(self):
        """Iterate over tasks."""
        return iter(self._tasks)

    def __add__(self, other):
        if isinstance(other, TaskGroup):
            task_list = self._tasks + other._tasks
            return TaskGroup(task_list)
        return NotImplemented

    @property
    def count(self):
        """int: Number of tasks registered in the group."""
        return len(self._tasks)

    def set_manager(self, manager=None):
        """Change schedule manager of all tasks.

        Task will be unregistered from old manager if it has been registered
        in a manager.

        Args:
            manager (ScheduleManager): A exist schedule manager object.
                Set None to create new schedule manager.

        Returns:
            ScheduleManager: Invoked ScheduleManager instance.

        Raises:
            TaskNameDuplicateError: There is a duplicate task name.
        """
        if not manager:
            manager = ScheduleManager()
        else:
            for task in self._tasks:
                if task.name in manager:
                    error = "Duplicate task name <{}>.".format(task.name)
                    raise TaskNameDuplicateError(error)

        for task in self._tasks:
            if task.manager:
                task.manager.unregister(name=task.name)
                manager.register(task)

        return manager

    def add_tag(self, tag):
        """Add tag to tasks.

        Args:
            tag (obj): Tag.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.add_tag(tag)

        return self

    def add_tags(self, tags):
        """Add a list of tags to tasks.

        Args:
            tags (iterable): Tag list.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.add_tags(tags)

        return self

    def remove_tag(self, tag):
        """Remove tag from tasks.

        Args:
            tag (obj): Tag.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.remove_tag(tag)

        return self

    def remove_tags(self, tags):
        """Remove a list of tags from tasks.

        Args:
            tags (iterable): Tag list.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.remove_tags(tags)

        return self

    def set_tags(self, tags):
        """Set tag list to tasks.

        Replace old tag list.

        Args:
            tags (iterable): Tag list.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.set_tags(tags)

        return self

    def delay(self, interval=None):
        """Task delay time.

        Args:
            interval (Union[str, timedelta, int]): Time interval.
                A string with format `HH:MM:SS` or :obj:`timedelta` or int
                in seconds.
                Or set None to cancel task delay time.
                Defaults to None.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.delay(interval)

        return self

    def start_at(self, at_time):
        """Set task start time.

        Specify a particular time that the job should be start.

        Args:
            at_time (Union[str, datetime]): Start time.
                A string or :obj:`datetime`.
                A string can be in one of the following formats:
                    `HH:MM:SS`, `mm-dd HH:MM:SS`
                Or set None to cancel task start time.
                Defaults to None.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.start_at(at_time)

        return self

    def nonperiodic(self, count):
        """See as non-periodic tasks.

        Args:
            count (int): Do the job for a certain number of times.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.nonperiodic(count)

        return self

    def periodic(self):
        """See as periodic tasks.

        Returns:
            TaskGroup: Invoked TaskGroup instance.
        """
        for task in self._tasks:
            task.periodic()

        return self

    def period(self, interval):
        """Scheduling periodic tasks.

        Args:
            interval (Union[str, timedelta, int]): Time interval.
                A string with format `HH:MM:SS` or :obj:`timedelta` or int
                in seconds.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.period(interval)

        return self

    def period_at(self,
                  unit="day", at_time="00:00:00",
                  week_day="Monday", day=1):
        """Scheduling periodic tasks.

        Specify a particular time that the job should be run at.

        Args:
            unit (str): Time unit of the periodic task.
                Defaults to `day`.
                The following unit is available:
                    1. `day`: Run job everyday.
                    2. `week`: Run job every week.
                    3. `month`: Run job every month.
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.
                Defaults to `Monday`.
                This argument will only be used is unit is `week`.
                A string should br one of following value:
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"]
            day (int): Day to do the job.
                Defaults to 1.
                This argument will only be used is unit is `month`.
                Value should be in 1 ~ 31.
                Job will be skipped if specific date is not available.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.period_at(unit=unit,
                           at_time=at_time,
                           week_day=week_day,
                           day=day)

        return self

    def period_day_at(self, at_time="00:00:00"):
        """Scheduling periodic tasks.

        Specify a particular time that the job should be run at.
        Job runs everyday.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.period_day_at(at_time=at_time)

        return self

    def period_week_at(self, at_time="00:00:00", week_day="Monday"):
        """Scheduling periodic tasks.

        Specify a particular time that the job should be run at.
        Job runs every week.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            week_day (str): Week to do the job.
                Defaults to `Monday`.
                A string should br one of following value:
                    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                    "Saturday", "Sunday"]

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.period_week_at(at_time=at_time, week_day=week_day)

        return self

    def period_month_at(self, at_time="00:00:00", day=1):
        """Scheduling periodic tasks.

        Specify a particular time that the job should be run at.
        Job runs every month.

        Args:
            at_time (str): Time to do the job.
                A string with format `HH:MM:SS`.
                Defaults to `00:00:00`.
            day (int): Day to do the job.
                Defaults to 1.
                Value should be in 1 ~ 31.
                Job will be skipped if specific date is not available.

        Returns:
            TaskGroup: Invoked TaskGroup instance.

        Raises:
            TimeFormatError: Invalid time format.
        """
        for task in self._tasks:
            task.period_month_at(at_time=at_time, day=day)

        return self

    def start(self):
        """Start the Tasks' activity."""
        for task in self._tasks:
            task.start()

    def stop(self):
        """Stop the Tasks' activity."""
        for task in self._tasks:
            task.stop()

    def pause(self):
        """Pause the Tasks' activity.

        Works only the task is registered into ScheduleManager.
        """
        new_task_list = list()

        for task in self._tasks:
            manager = task.manager
            task_name = task.name
            task.pause()

            while task.manager is not None:
                time.sleep(1)

            if manager:
                new_task_list.append(manager.task(task_name))

        self._tasks = new_task_list[:]
