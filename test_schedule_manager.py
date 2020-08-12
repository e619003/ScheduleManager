"""
Unit tests for schedule_manager
"""
# C0103: invalid-name
# C0302: too-many-lines
# C0116: missing-function-docstring
# R0201: no-self-use
# R0903: too-few-public-methods
# R0904: too-many-public-methods
# R0915: too-many-statements
# W0212: protected-access
# W0613: unused-argument
# W0621: redefined-outer-name
# pylint: disable=C0103, C0116, C0302
# pylint: disable=R0201, R0903, R0904, R0915
# pylint: disable=W0212, W0613, W0621

from datetime import datetime, timedelta
import time
import pytest

from schedule_manager import manager
from schedule_manager import ScheduleManager, Task, TaskGroup

from schedule_manager.exceptions import OperationFailError
from schedule_manager.exceptions import TaskNameDuplicateError
from schedule_manager.exceptions import TaskNotFoundError
from schedule_manager.exceptions import TimeFormatError

this_year = datetime.now().year


def mock_datetime(year, month, day, hour, minute, second):
    """Create mock Datetime class."""
    # R0913: too-many-arguments
    # pylint: disable=R0913

    class MockDatetime(datetime):
        """Datetime used for moker."""
        _mock_year = year
        _mock_month = month
        _mock_day = day
        _mock_hour = hour
        _mock_minute = minute
        _mock_second = second

        @classmethod
        def now(cls):
            return cls(cls._mock_year,
                       cls._mock_month,
                       cls._mock_day,
                       cls._mock_hour,
                       cls._mock_minute,
                       cls._mock_second)

    return MockDatetime


@pytest.fixture
def time_tester(request):
    tester = mock_datetime(year=request.param[0],
                           month=request.param[1],
                           day=request.param[2],
                           hour=request.param[3],
                           minute=request.param[4],
                           second=request.param[5])

    original = manager.datetime
    manager.datetime = tester
    yield tester
    manager.datetime = original


class FakeDatetime:
    """
    Fake datetime class.
    Used to simulate time passing.
    """

    def __init__(self, year, month, day, hour, minute, second):
        # R0913: too-many-arguments
        # pylint: disable=R0913
        self.original = None

        self._fake_year = year
        self._fake_month = month
        self._fake_day = day
        self._fake_hour = hour
        self._fake_minute = minute
        self._fake_second = second

    def __enter__(self):
        target = mock_datetime(year=self._fake_year,
                               month=self._fake_month,
                               day=self._fake_day,
                               hour=self._fake_hour,
                               minute=self._fake_minute,
                               second=self._fake_second)

        self.original = manager.datetime
        manager.datetime = target

    def __exit__(self, exc_type, exc_value, exc_traceback):
        manager.datetime = self.original


class Monitor:
    """Used for monitoring task process."""
    monitor = 0


@pytest.fixture
def monitor_handler():
    yield
    # Reset Monitor
    Monitor.monitor = 0


class TestTask:
    """Test Task object."""

    def test_task_name(self):
        name = "Test"
        task = Task(name=name, job=lambda *args, **kwargs: None)

        assert task.name == name

    def test_add_tag(self):
        tag_list = list()
        task = Task(job=lambda *args, **kwargs: None)

        tag_list.append(1)
        task.add_tag(1)
        assert task.tag == tag_list

        tag_list.append("tag_str")
        task.add_tag("tag_str")
        assert task.tag == tag_list

        tag_list.append(1)
        task.add_tag(1)
        assert task.tag != tag_list

    def test_add_tags(self):
        tag_list = ["1", 2, "3"]
        task = Task(job=lambda *args, **kwargs: None)
        task2 = Task(job=lambda *args, **kwargs: None)

        task.add_tags(tag_list)
        assert task.tag == tag_list

        tag_list.append(4)
        assert task.tag != tag_list

        tag_iter = dict()
        for tag in tag_list:
            tag_iter[tag] = "value{}".format(tag)
        task2.add_tags(tag_iter)
        assert task2.tag == tag_list

    def test_set_tags(self):
        tag_list = ["1", 2, "3"]
        tag_list2 = [4, 5]
        task = Task(job=lambda *args, **kwargs: None)
        task.add_tags(tag_list)
        assert task.tag == tag_list

        task.set_tags(tag_list2)
        assert task.tag != tag_list
        assert task.tag == tag_list2

        task.set_tags([])
        assert task.tag == []
        tag_iter = dict()
        for tag in tag_list:
            tag_iter[tag] = "value{}".format(tag)
        task.add_tags(tag_iter)
        assert task.tag == tag_list

    def test_remove_tag(self):
        tag_list = [1, 2, 3, 4, 5]
        task = Task(job=lambda *args, **kwargs: None)
        task.set_tags(tag_list)
        assert task.tag == tag_list

        task.remove_tag("test")
        assert task.tag == tag_list

        tag_list.remove(3)
        task.remove_tag(3)
        assert task.tag == tag_list

    def test_remove_tags(self):
        tag_list = [1, 2, 3, 4, 5]
        task = Task(job=lambda *args, **kwargs: None)
        task.set_tags(tag_list)
        assert task.tag == tag_list
        task2 = Task(job=lambda *args, **kwargs: None)
        task2.set_tags(tag_list)
        assert task2.tag == tag_list

        tag_list.remove(2)
        tag_list.remove(5)
        task.remove_tags([2, 5])
        assert task.tag == tag_list

        tag_list.remove(1)
        assert task.tag != tag_list

        tag_list = [1, 2, 4]
        tag_iter = {3: "value3", 5: 2}
        task2.remove_tags(tag_iter)
        assert task2.tag == tag_list

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 1, 1)],
                             indirect=True)
    def test_delay(self, mocker, time_tester):
        test_datetime = datetime(year=this_year,
                                 month=1,
                                 day=1,
                                 hour=1,
                                 minute=1,
                                 second=1)

        task = Task(job=lambda *args, **kwargs: None)
        task._start_at = datetime.now()
        task._periodic_unit = "set"
        mocker.patch('threading.Thread.start', return_value=False)

        delta = timedelta(minutes=20, seconds=10)
        task.delay(delta)
        assert task._start_at is None
        assert task._delay == delta

        task.start()
        assert task._start_at == test_datetime + delta
        task._start = False

        task.delay(60)
        assert task._delay == timedelta(seconds=60)

        task.start()
        assert task._start_at == test_datetime + timedelta(seconds=60)
        task._start = False

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:00:00"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.delay(str_)

        tast_list = [("01", "05", "07"),
                     ("2", "3", "4"),
                     ("7", "03", "05"),
                     ("16", "3", "24"),
                     ("06", "33", "2"),
                     ("10", "10", "01")]
        for str_ in tast_list:
            task.delay(":".join(str_))
            assert task._delay == timedelta(hours=int(str_[0]),
                                            minutes=int(str_[1]),
                                            seconds=int(str_[2]))

            task.start()
            assert task._start_at == test_datetime + timedelta(hours=int(str_[0]),
                                                               minutes=int(str_[1]),
                                                               seconds=int(str_[2]))
            task._start = False

    def test_delay_cancel(self):
        task = Task(job=lambda *args, **kwargs: None)
        task.delay(5)

        assert task._delay

        task.delay()

        assert task._delay is None

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 1, 1)],
                             indirect=True)
    def test_start_at(self, time_tester):
        task = Task(job=lambda *args, **kwargs: None)
        task._delay = timedelta(seconds=60)

        input_value = time_tester(year=this_year, month=1, day=1)
        task.start_at(input_value)
        assert task._delay is None
        assert task._start_at == input_value

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:18:80",
                     "12-04 16:78:20",
                     "12-04 26:28:20",
                     "15-04 02:01:15",
                     "10-34 02:01:15",
                     "10/01 02:01:15"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.start_at(str_)

        tast_list = [("01", "05", "07"),
                     ("2", "3", "4"),
                     ("7", "03", "05"),
                     ("16", "3", "24"),
                     ("06", "33", "2"),
                     ("10", "10", "01")]
        for str_ in tast_list:
            task.start_at(":".join(str_))
            assert task._start_at == time_tester.now().replace(hour=int(str_[0]),
                                                               minute=int(str_[1]),
                                                               second=int(str_[2]))

        tast_list = [("1", "12", "01", "05", "07"),
                     ("10", "7", "2", "3", "4"),
                     ("08", "16", "7", "03", "05")]
        for str_ in tast_list:
            time_str = "{}-{} {}:{}:{}".format(str_[0],
                                               str_[1],
                                               str_[2],
                                               str_[3],
                                               str_[4])
            task.start_at(time_str)
            assert task._start_at == time_tester.now().replace(month=int(str_[0]),
                                                               day=int(str_[1]),
                                                               hour=int(str_[2]),
                                                               minute=int(str_[3]),
                                                               second=int(str_[4]))

    def test_start_at_cancel(self):
        task = Task(job=lambda *args, **kwargs: None)
        task.start_at("01:00:05")

        assert task._start_at

        task.start_at()

        assert task._start_at is None

    def test_nonperiodic(self):
        task = Task(job=lambda *args, **kwargs: None)

        with pytest.raises(OperationFailError) as e:
            task.nonperiodic(0)
        assert str(e.value) == "Number of times must be greater than 0."
        assert task._is_periodic

        with pytest.raises(OperationFailError) as e:
            task.nonperiodic(-3)
        assert str(e.value) == "Number of times must be greater than 0."
        assert task._is_periodic

        task.nonperiodic(3)
        assert not task._is_periodic
        assert task._nonperiod_count == 3

    def test_periodic(self):
        task = Task(job=lambda *args, **kwargs: None)
        task._is_periodic = False

        task.periodic()
        assert task._is_periodic

    def test_period(self):
        task = Task(job=lambda *args, **kwargs: None)

        delta = timedelta(minutes=32, seconds=5)
        task.period(delta)
        assert task._periodic_unit == "every"
        assert task._periodic == delta

        task._periodic_unit = None

        task.period(100)
        assert task._periodic_unit == "every"
        assert task._periodic == timedelta(seconds=100)

        task._periodic_unit = None

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:00:00"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period(str_)

        tast_list = [("01", "05", "07"),
                     ("2", "3", "4"),
                     ("7", "03", "05"),
                     ("16", "3", "24"),
                     ("06", "33", "2"),
                     ("10", "10", "01")]
        for str_ in tast_list:
            task.period(":".join(str_))
            assert task._periodic_unit == "every"
            assert task._periodic == timedelta(hours=int(str_[0]),
                                               minutes=int(str_[1]),
                                               seconds=int(str_[2]))

            task._periodic_unit = None

    def test_period_day_at(self):
        task = Task(job=lambda *args, **kwargs: None)

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:00:00"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period_day_at(str_)

        tast_list = [("01", "05", "07"),
                     ("2", "3", "4"),
                     ("7", "03", "05"),
                     ("16", "3", "24"),
                     ("06", "33", "2"),
                     ("10", "10", "01")]
        for str_ in tast_list:
            task.period_day_at(":".join(str_))
            assert task._periodic_unit == "day"
            assert task._at_time == [int(str_[0]),
                                     int(str_[1]),
                                     int(str_[2])]

            task._periodic_unit = None

    def test_period_week_at(self):
        task = Task(job=lambda *args, **kwargs: None)

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:00:00"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period_week_at(at_time=str_)

        tast_list = ["monday",
                     "tuesday",
                     "wednesday",
                     "thursday",
                     "friday",
                     "saturday",
                     "sunday",
                     "error_string",
                     "26:28:20",
                     123]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period_week_at(week_day=str_)

        week_day_list = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }
        tast_list = [("01", "05", "07", "Monday"),
                     ("2", "3", "4", "Tuesday"),
                     ("7", "03", "05", "Wednesday"),
                     ("16", "3", "24", "Thursday"),
                     ("06", "33", "2", "Friday"),
                     ("6", "33", "2", "Saturday"),
                     ("10", "10", "01", "Sunday")]
        for str_ in tast_list:
            task.period_week_at(at_time=":".join(str_[:3]), week_day=str_[3])
            assert task._periodic_unit == "week"
            assert task._at_time == [int(str_[0]),
                                     int(str_[1]),
                                     int(str_[2])]
            assert task._at_week_day == week_day_list[str_[3]]

            task._periodic_unit = None

    def test_period_month_at(self):
        task = Task(job=lambda *args, **kwargs: None)

        tast_list = ["16:18:80",
                     "16:78:20",
                     "26:28:20",
                     "12-04 16:00:00"]
        for str_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period_month_at(at_time=str_)

        tast_list = [0,
                     35,
                     -2]
        for int_ in tast_list:
            with pytest.raises(TimeFormatError):
                task.period_month_at(day=int_)

        tast_list = [("01", "05", "07", 1),
                     ("2", "3", "4", 31),
                     ("7", "03", "05", 10),
                     ("16", "3", "24", 8),
                     ("06", "33", "2", 22),
                     ("6", "33", "2", 20),
                     ("10", "10", "01", 15)]
        for str_ in tast_list:
            task.period_month_at(at_time=":".join(str_[:3]), day=str_[3])
            assert task._periodic_unit == "month"
            assert task._at_time == [int(str_[0]),
                                     int(str_[1]),
                                     int(str_[2])]
            assert task._at_day == str_[3]

            task._periodic_unit = None

    def test_period_at_error_unit(self):
        task = Task(job=lambda *args, **kwargs: None)

        with pytest.raises(TimeFormatError):
            task.period_at(unit="error")

    def test_flag_control_with_start_func(self, mocker):
        task = Task(job=lambda *args, **kwargs: None)
        mocker.patch('threading.Thread.start', return_value=False)

        with pytest.raises(OperationFailError):
            task.start()

        task.period(10)

        task.start()
        assert task._start
        assert task.is_running

    def test_flag_control_with_stop_func(self, mocker):
        task = Task(job=lambda *args, **kwargs: None)
        mocker.patch('threading.Thread.start', return_value=False)

        with pytest.raises(OperationFailError):
            task.stop()

        task.period(10)
        task.start()

        task.stop()
        assert not task._start
        assert not task.is_running
        assert task._stop_task

    def test_flag_control_with_pause_func(self, mocker):
        task = Task(job=lambda *args, **kwargs: None)
        mocker.patch('threading.Thread.start', return_value=False)

        with pytest.raises(OperationFailError) as e:
            task.pause()
        assert str(e.value) == "Task is not running."

        task.period(10)
        task.start()
        with pytest.raises(OperationFailError) as e:
            task.pause()
        assert str(e.value) == "Register task into ScheduleManager first."

        task = Task(job=lambda *args, **kwargs: None)
        task._manager = True
        task.period(10)
        task.start()

        task.pause()
        assert not task._start
        assert not task.is_running
        assert task._stop_task
        assert task._pause_task

    def test_start_task(self, mocker):
        task = Task(job=lambda *args, **kwargs: None)
        task.period(60)
        mock_run = mocker.patch.object(task, 'run')
        mock_run.return_value = False

        task.start()

        assert task._started.is_set()
        assert not task.is_alive()

    def test_stop_task(self):
        task = Task(job=lambda *args, **kwargs: None)
        task.period(60)
        task.start()

        time.sleep(2)
        task.stop()
        time.sleep(3)
        assert not task.is_alive()

    def test_avoid_to_use_run_method_directly(self):
        task = Task(job=lambda *args, **kwargs: None)
        task.period(60)

        with pytest.raises(OperationFailError):
            task.run()

    def test_run_task__period_Situation1(self, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(2)
        task.start()
        time.sleep(0.5)

        assert Monitor.monitor == 1
        time.sleep(2)
        assert Monitor.monitor == 2
        time.sleep(2)
        assert Monitor.monitor == 3
        time.sleep(2)
        assert Monitor.monitor == 4

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 1, 0)],
                             indirect=True)
    def test_run_task__period_Situation2(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(40)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 1, 1, 1, 37):
            time.sleep(1)
            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=1,
                                              day=1,
                                              hour=1,
                                              minute=1,
                                              second=40)
            with FakeDatetime(this_year, 1, 1, 1, 1, 40):
                time.sleep(1)
                assert Monitor.monitor == 2
                assert task._next_run == datetime(year=this_year,
                                                  month=1,
                                                  day=1,
                                                  hour=1,
                                                  minute=2,
                                                  second=20)
                with FakeDatetime(this_year, 1, 1, 1, 2, 5):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=1,
                                                      day=1,
                                                      hour=1,
                                                      minute=2,
                                                      second=20)
                    with FakeDatetime(this_year, 1, 1, 1, 2, 30):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=1,
                                                          day=1,
                                                          hour=1,
                                                          minute=3,
                                                          second=0)
                        with FakeDatetime(this_year, 1, 1, 2, 3, 10):
                            time.sleep(1)
                            assert Monitor.monitor == 4
                            assert task._next_run == datetime(year=this_year,
                                                              month=1,
                                                              day=1,
                                                              hour=2,
                                                              minute=3,
                                                              second=40)
                            with FakeDatetime(this_year, 1, 1, 2, 3, 40):
                                time.sleep(1)
                                assert Monitor.monitor == 5
                                assert task._next_run == datetime(year=this_year,
                                                                  month=1,
                                                                  day=1,
                                                                  hour=2,
                                                                  minute=4,
                                                                  second=20)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 5, 30)],
                             indirect=True)
    def test_run_task__period_Situation3(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(60)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 1, 1, 6, 0):
            time.sleep(1)
            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=1,
                                              day=1,
                                              hour=1,
                                              minute=6,
                                              second=30)
            with FakeDatetime(this_year, 1, 1, 1, 6, 26):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=1,
                                                  day=1,
                                                  hour=1,
                                                  minute=6,
                                                  second=30)
                with FakeDatetime(this_year, 1, 1, 1, 23, 30):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=1,
                                                      day=1,
                                                      hour=1,
                                                      minute=24,
                                                      second=30)
                    with FakeDatetime(this_year, 1, 1, 1, 24, 24):
                        time.sleep(1)
                        assert Monitor.monitor == 2
                        assert task._next_run == datetime(year=this_year,
                                                          month=1,
                                                          day=1,
                                                          hour=1,
                                                          minute=24,
                                                          second=30)
                        with FakeDatetime(this_year, 1, 1, 1, 24, 30):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=1,
                                                              day=1,
                                                              hour=1,
                                                              minute=25,
                                                              second=30)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 0, 0)],
                             indirect=True)
    def test_run_task__period_skipped_False(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func, ignore_skipped=False)
        task.period(90)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 1, 1, 1, 0):
            time.sleep(1)
            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=1,
                                              day=1,
                                              hour=1,
                                              minute=1,
                                              second=30)
            with FakeDatetime(this_year, 1, 1, 1, 1, 30):
                time.sleep(1)
                assert Monitor.monitor == 2
                assert task._next_run == datetime(year=this_year,
                                                  month=1,
                                                  day=1,
                                                  hour=1,
                                                  minute=3,
                                                  second=0)
                with FakeDatetime(this_year, 1, 1, 1, 6, 20):
                    time.sleep(1)
                    assert Monitor.monitor == 3
                    assert task._next_run == datetime(year=this_year,
                                                      month=1,
                                                      day=1,
                                                      hour=1,
                                                      minute=4,
                                                      second=30)
                    with FakeDatetime(this_year, 1, 1, 1, 6, 21):
                        time.sleep(1)
                        assert Monitor.monitor == 4
                        assert task._next_run == datetime(year=this_year,
                                                          month=1,
                                                          day=1,
                                                          hour=1,
                                                          minute=6,
                                                          second=0)
                        with FakeDatetime(this_year, 1, 1, 1, 6, 22):
                            time.sleep(1)
                            assert Monitor.monitor == 5
                            assert task._next_run == datetime(year=this_year,
                                                              month=1,
                                                              day=1,
                                                              hour=1,
                                                              minute=7,
                                                              second=30)
                            with FakeDatetime(this_year, 1, 1, 1, 7, 20):
                                time.sleep(1)
                                assert Monitor.monitor == 5
                                assert task._next_run == datetime(year=this_year,
                                                                  month=1,
                                                                  day=1,
                                                                  hour=1,
                                                                  minute=7,
                                                                  second=30)
                                with FakeDatetime(this_year, 1, 1, 1, 7, 30):
                                    time.sleep(1)
                                    assert Monitor.monitor == 6
                                    assert task._next_run == datetime(year=this_year,
                                                                      month=1,
                                                                      day=1,
                                                                      hour=1,
                                                                      minute=9,
                                                                      second=0)

        task.stop()

    def test_run_task__period_day_at_Init_run_at(self, monitor_handler):
        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        with FakeDatetime(this_year, 3, 5, 12, 0, 0):
            task = Task(job=test_func)
            task.period_day_at("18:00:00")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=5,
                                              hour=18,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_day_at("6:00:00")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=6,
                                              hour=6,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_day_at("12:00:00")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=6,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 6, 5, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_day_at_Situation1(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_day_at("12:00:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 6, 5, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=6,
                                              day=6,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 6, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=6,
                                                  day=7,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 6, 7, 11, 59, 59):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=6,
                                                      day=7,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 6, 7, 14, 30, 10):
                        time.sleep(1)
                        assert Monitor.monitor == 2
                        assert task._next_run == datetime(year=this_year,
                                                          month=6,
                                                          day=8,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 6, 18, 13, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=6,
                                                              day=19,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 6, 19, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 4
                                assert task._next_run == datetime(year=this_year,
                                                                  month=6,
                                                                  day=20,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 6, 5, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_day_at_Situation2(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_day_at("12:00:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 6, 5, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=6,
                                              day=6,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 6, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=6,
                                                  day=7,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 6, 7, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=6,
                                                      day=7,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 6, 15, 12, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 2
                        assert task._next_run == datetime(year=this_year,
                                                          month=6,
                                                          day=16,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 6, 16, 12, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=6,
                                                              day=17,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 6, 5, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_day_at_Situation3(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_day_at("12:00:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 6, 5, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=6,
                                              day=6,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 6, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=6,
                                                  day=7,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 6, 7, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=6,
                                                      day=7,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 6, 15, 11, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 2
                        assert task._next_run == datetime(year=this_year,
                                                          month=6,
                                                          day=15,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 6, 15, 12, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=6,
                                                              day=16,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 6, 5, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_day_at_skipped_False(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func, ignore_skipped=False)
        task.period_day_at("12:00:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 6, 5, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=6,
                                              day=6,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 6, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=6,
                                                  day=7,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 6, 9, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=6,
                                                      day=8,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 6, 9, 11, 0, 1):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=6,
                                                          day=9,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 6, 9, 11, 0, 2):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=6,
                                                              day=9,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 6, 9, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 4
                                assert task._next_run == datetime(year=this_year,
                                                                  month=6,
                                                                  day=10,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    def test_run_task__period_week_at_Init_run_at(self, monitor_handler):
        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        with FakeDatetime(this_year, 7, 8, 12, 0, 0):
            task = Task(job=test_func)
            task.period_week_at(at_time="18:00:00", week_day="Friday")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=10,
                                              hour=18,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_week_at(at_time="06:00:00", week_day="Tuesday")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=14,
                                              hour=6,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_week_at(at_time="10:00:00", week_day="Wednesday")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=10,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_week_at(at_time="12:00:00", week_day="Wednesday")
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation1(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 14, 13, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 0
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=22,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 7, 22, 11, 59, 59):
                        time.sleep(1)
                        assert Monitor.monitor == 1
                        assert task._next_run == datetime(year=this_year,
                                                          month=7,
                                                          day=22,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 7, 22, 14, 30, 10):
                            time.sleep(1)
                            assert Monitor.monitor == 2
                            assert task._next_run == datetime(year=this_year,
                                                              month=7,
                                                              day=29,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 8, 20, 10, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 3
                                assert task._next_run == datetime(year=this_year,
                                                                  month=8,
                                                                  day=26,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)
                                with FakeDatetime(this_year, 8, 26, 12, 0, 0):
                                    time.sleep(1)
                                    assert Monitor.monitor == 4
                                    assert task._next_run == datetime(year=this_year,
                                                                      month=9,
                                                                      day=2,
                                                                      hour=12,
                                                                      minute=0,
                                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation2(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 26, 10, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=8,
                                                      day=26,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 26, 12, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=9,
                                                          day=2,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation3(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 24, 10, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=8,
                                                      day=26,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 26, 12, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=9,
                                                          day=2,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation4(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 7, 22, 14, 30, 10):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=29,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 19, 12, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=8,
                                                          day=26,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 8, 26, 12, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 4
                            assert task._next_run == datetime(year=this_year,
                                                              month=9,
                                                              day=2,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation5(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 7, 22, 14, 30, 10):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=29,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 19, 10, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=8,
                                                          day=19,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 8, 19, 12, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 4
                            assert task._next_run == datetime(year=this_year,
                                                              month=8,
                                                              day=26,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_Situation6(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 8, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 7, 22, 14, 30, 10):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=29,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 12, 16, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=8,
                                                          day=19,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 8, 19, 12, 0, 0):
                            time.sleep(1)
                            assert Monitor.monitor == 4
                            assert task._next_run == datetime(year=this_year,
                                                              month=8,
                                                              day=26,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 7, 8, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_week_at_skipped_False(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func, ignore_skipped=False)
        task.period_week_at(at_time="12:00:00", week_day="Wednesday")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 7, 12, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=22,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 4, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=29,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 8, 4, 11, 0, 1):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=8,
                                                          day=5,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 8, 4, 11, 0, 2):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=8,
                                                              day=5,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 8, 5, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 4
                                assert task._next_run == datetime(year=this_year,
                                                                  month=8,
                                                                  day=12,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    def test_run_task__period_month_at_Init_run_at_part1(self, monitor_handler):
        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        with FakeDatetime(this_year, 7, 8, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="18:00:00", day=12)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=7,
                                              day=12,
                                              hour=18,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_month_at(at_time="06:00:00", day=2)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=8,
                                              day=2,
                                              hour=6,
                                              minute=0,
                                              second=0)
            task.stop()

            task = Task(job=test_func)
            task.period_month_at(at_time="12:00:00", day=8)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year,
                                              month=8,
                                              day=8,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()

    def test_run_task__period_month_at_Init_run_at_part2(self, monitor_handler):
        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        with FakeDatetime(this_year, 2, 2, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="18:00:00", day=30)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=30,
                                              hour=18,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 12, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="11:00:00", day=31)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year+1,
                                              month=1,
                                              day=31,
                                              hour=11,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 12, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="11:00:00", day=10)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year+1,
                                              month=1,
                                              day=10,
                                              hour=11,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 3, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="11:00:00", day=31)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=5,
                                              day=31,
                                              hour=11,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 12, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="12:00:00", day=31)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 1
            assert task._next_run == datetime(year=this_year+1,
                                              month=1,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 3, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="12:00:00", day=31)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 2
            assert task._next_run == datetime(year=this_year,
                                              month=5,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

        with FakeDatetime(this_year, 1, 31, 12, 0, 0):
            task = Task(job=test_func)
            task.period_month_at(at_time="12:00:00", day=30)
            task.start()
            time.sleep(0.5)

            assert Monitor.monitor == 2
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=30,
                                              hour=12,
                                              minute=0,
                                              second=0)
            task.stop()
            time.sleep(1)

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation1(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 2, 22, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 3, 14, 10, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 0
                assert task._next_run == datetime(year=this_year,
                                                  month=3,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 3, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=4,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 4, 15, 11, 59, 59):
                        time.sleep(1)
                        assert Monitor.monitor == 1
                        assert task._next_run == datetime(year=this_year,
                                                          month=4,
                                                          day=15,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 4, 15, 14, 30, 10):
                            time.sleep(1)
                            assert Monitor.monitor == 2
                            assert task._next_run == datetime(year=this_year,
                                                              month=5,
                                                              day=15,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 12, 7, 10, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 3
                                assert task._next_run == datetime(year=this_year,
                                                                  month=12,
                                                                  day=15,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)
                                with FakeDatetime(this_year, 12, 15, 12, 0, 0):
                                    time.sleep(1)
                                    assert Monitor.monitor == 4
                                    assert task._next_run == datetime(year=this_year+1,
                                                                      month=1,
                                                                      day=15,
                                                                      hour=12,
                                                                      minute=0,
                                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 12, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation2(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 12, 22, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=12,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 12, 31, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=1,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 1, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=1,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year+1, 1, 31, 12, 0, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 2
                        assert task._next_run == datetime(year=this_year+1,
                                                          month=3,
                                                          day=31,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year+1, 2, 28, 14, 30, 10):
                            time.sleep(1)
                            assert Monitor.monitor == 2
                            assert task._next_run == datetime(year=this_year+1,
                                                              month=3,
                                                              day=31,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year+1, 3, 31, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 3
                                assert task._next_run == datetime(year=this_year+1,
                                                                  month=5,
                                                                  day=31,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 3, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation3(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 30, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=7,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 7, 31, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=8,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation4(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 6, 11, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=6,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 6, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=7,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation5(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 12, 25, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=1,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 1, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=2,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation6(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 25, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=8,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=9,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 11, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation7(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=30)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 11, 28, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=11,
                                              day=30,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year+1, 1, 31, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=3,
                                                  day=30,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 3, 30, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=4,
                                                      day=30,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation8(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 20, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=8,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=9,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation9(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 8, 31, 20, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=10,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 10, 31, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=12,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation10(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 12, 31, 20, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=1,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 1, 31, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=3,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation11(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=15)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=15,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 7, 15, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=8,
                                                  day=15,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 8, 15, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=9,
                                                      day=15,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation12(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 8, 31, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=10,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 10, 31, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=12,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_Situation13(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 3, 3, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=3,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 12, 31, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=1,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 1, 31, 12, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=3,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_skipped_False(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func, ignore_skipped=False)
        task.period_month_at(at_time="12:00:00", day=5)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 2, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=1,
                                              day=5,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 1, 5, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year,
                                                  month=2,
                                                  day=5,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year, 4, 4, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year,
                                                      month=3,
                                                      day=5,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year, 4, 4, 11, 0, 1):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year,
                                                          month=4,
                                                          day=5,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year, 4, 4, 11, 0, 2):
                            time.sleep(1)
                            assert Monitor.monitor == 3
                            assert task._next_run == datetime(year=this_year,
                                                              month=4,
                                                              day=5,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year, 4, 5, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 4
                                assert task._next_run == datetime(year=this_year,
                                                                  month=5,
                                                                  day=5,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 11, 1, 18, 0, 0)],
                             indirect=True)
    def test_run_task__period_month_at_skipped_False_Part2(self, time_tester,
                                                           monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func, ignore_skipped=False)
        task.period_month_at(at_time="12:00:00", day=31)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 11, 2, 22, 0, 0):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run == datetime(year=this_year,
                                              month=12,
                                              day=31,
                                              hour=12,
                                              minute=0,
                                              second=0)
            with FakeDatetime(this_year, 12, 31, 12, 0, 0):
                time.sleep(1)
                assert Monitor.monitor == 1
                assert task._next_run == datetime(year=this_year+1,
                                                  month=1,
                                                  day=31,
                                                  hour=12,
                                                  minute=0,
                                                  second=0)
                with FakeDatetime(this_year+1, 6, 4, 11, 0, 0):
                    time.sleep(1)
                    assert Monitor.monitor == 2
                    assert task._next_run == datetime(year=this_year+1,
                                                      month=3,
                                                      day=31,
                                                      hour=12,
                                                      minute=0,
                                                      second=0)
                    with FakeDatetime(this_year+1, 6, 4, 11, 0, 1):
                        time.sleep(1)
                        assert Monitor.monitor == 3
                        assert task._next_run == datetime(year=this_year+1,
                                                          month=5,
                                                          day=31,
                                                          hour=12,
                                                          minute=0,
                                                          second=0)
                        with FakeDatetime(this_year+1, 6, 4, 11, 0, 2):
                            time.sleep(1)
                            assert Monitor.monitor == 4
                            assert task._next_run == datetime(year=this_year+1,
                                                              month=7,
                                                              day=31,
                                                              hour=12,
                                                              minute=0,
                                                              second=0)
                            with FakeDatetime(this_year+1, 6, 30, 12, 0, 0):
                                time.sleep(1)
                                assert Monitor.monitor == 4
                                assert task._next_run == datetime(year=this_year+1,
                                                                  month=7,
                                                                  day=31,
                                                                  hour=12,
                                                                  minute=0,
                                                                  second=0)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__delay(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(60)
        task.delay(30)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 2, 15, 18, 0, 20):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run is None
            with FakeDatetime(this_year, 2, 15, 18, 0, 25):
                time.sleep(1)
                assert Monitor.monitor == 0
                assert task._next_run is None
                with FakeDatetime(this_year, 2, 15, 18, 0, 30):
                    time.sleep(1)
                    assert Monitor.monitor == 1
                    assert task._next_run == datetime(year=this_year,
                                                      month=2,
                                                      day=15,
                                                      hour=18,
                                                      minute=1,
                                                      second=30)

        task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 2, 15, 18, 0, 0)],
                             indirect=True)
    def test_run_task__start_at(self, time_tester, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(60)
        task.start_at("23:05:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 2, 15, 18, 0, 20):
            time.sleep(1)
            assert Monitor.monitor == 0
            assert task._next_run is None
            with FakeDatetime(this_year, 2, 15, 22, 0, 25):
                time.sleep(1)
                assert Monitor.monitor == 0
                assert task._next_run is None
                with FakeDatetime(this_year, 2, 15, 23, 4, 59):
                    time.sleep(1)
                    assert Monitor.monitor == 0
                    assert task._next_run is None
                    with FakeDatetime(this_year, 2, 15, 23, 5, 0):
                        time.sleep(1)
                        assert Monitor.monitor == 1
                        assert task._next_run == datetime(year=this_year,
                                                          month=2,
                                                          day=15,
                                                          hour=23,
                                                          minute=6,
                                                          second=0)

        task.stop()

    def test_run_task__nonperiodic(self, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(2)
        task.nonperiodic(3)
        task.start()
        time.sleep(0.5)

        assert Monitor.monitor == 1
        time.sleep(2)
        assert Monitor.monitor == 2
        time.sleep(2)
        assert Monitor.monitor == 3
        time.sleep(2)
        assert Monitor.monitor == 3
        time.sleep(2)
        assert Monitor.monitor == 3

        assert not task.is_alive()

        task.stop()

    def test_run_task__periodic(self, monitor_handler):

        def test_func():
            """Job used for testing."""
            Monitor.monitor += 1

        task = Task(job=test_func)
        task.period(2)
        task.nonperiodic(3)
        task.periodic()
        task.start()
        time.sleep(0.5)

        assert Monitor.monitor == 1
        time.sleep(2)
        assert Monitor.monitor == 2
        time.sleep(2)
        assert Monitor.monitor == 3
        time.sleep(2)
        assert Monitor.monitor == 4
        time.sleep(2)
        assert Monitor.monitor == 5

        assert task.is_alive()

        task.stop()

    def test_modify_schedule_after_start(self):
        task = Task(job=lambda *args, **kwargs: None)
        task.period(300)
        task.start()

        try:
            with pytest.raises(OperationFailError):
                task.delay(5)

            with pytest.raises(OperationFailError):
                task.start_at("00:00:00")

            with pytest.raises(OperationFailError):
                task.nonperiodic(1)

            with pytest.raises(OperationFailError):
                task.periodic()

            with pytest.raises(OperationFailError):
                task.period(60)

            with pytest.raises(OperationFailError):
                task.period_at()
        finally:
            task.stop()

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 0, 0)],
                             indirect=True)
    def test_property_next_run(self, time_tester):
        task = Task(job=lambda *args, **kwargs: None)
        task.period(40)
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 1, 1, 0, 5):
            time.sleep(1)
            assert task.next_run == datetime(year=this_year,
                                             month=1,
                                             day=1,
                                             hour=1,
                                             minute=0,
                                             second=40)
            with FakeDatetime(this_year, 1, 1, 1, 0, 35):
                time.sleep(1)
                assert task.next_run == datetime(year=this_year,
                                                 month=1,
                                                 day=1,
                                                 hour=1,
                                                 minute=0,
                                                 second=40)
                with FakeDatetime(this_year, 1, 1, 1, 0, 40):
                    time.sleep(1)
                    assert task.next_run == datetime(year=this_year,
                                                     month=1,
                                                     day=1,
                                                     hour=1,
                                                     minute=1,
                                                     second=20)
                    with FakeDatetime(this_year, 1, 1, 1, 1, 30):
                        time.sleep(1)
                        assert task._next_run == datetime(year=this_year,
                                                          month=1,
                                                          day=1,
                                                          hour=1,
                                                          minute=2,
                                                          second=0)

        task.stop()

        task = Task(job=lambda *args, **kwargs: None)
        task.period(40)
        task.start_at("02:30:00")
        task.start()
        time.sleep(0.5)

        with FakeDatetime(this_year, 1, 1, 1, 0, 5):
            time.sleep(1)
            assert task.next_run == datetime(year=this_year,
                                             month=1,
                                             day=1,
                                             hour=2,
                                             minute=30,
                                             second=0)
            with FakeDatetime(this_year, 1, 1, 2, 0, 35):
                time.sleep(1)
                assert task.next_run == datetime(year=this_year,
                                                 month=1,
                                                 day=1,
                                                 hour=2,
                                                 minute=30,
                                                 second=0)
                with FakeDatetime(this_year, 1, 1, 2, 30, 0):
                    time.sleep(1)
                    assert task.next_run == datetime(year=this_year,
                                                     month=1,
                                                     day=1,
                                                     hour=2,
                                                     minute=30,
                                                     second=40)
                    with FakeDatetime(this_year, 1, 1, 2, 30, 30):
                        time.sleep(1)
                        assert task._next_run == datetime(year=this_year,
                                                          month=1,
                                                          day=1,
                                                          hour=2,
                                                          minute=30,
                                                          second=40)
                        with FakeDatetime(this_year, 1, 1, 2, 30, 40):
                            time.sleep(1)
                            assert task._next_run == datetime(year=this_year,
                                                              month=1,
                                                              day=1,
                                                              hour=2,
                                                              minute=31,
                                                              second=20)

        task.stop()

    def test_property_manager_setter_with_exception(self):
        task = Task(name="test", job=lambda *args, **kwargs: None)
        task2 = Task(name="test2", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()

        with pytest.raises(OperationFailError):
            task.manager = None

        manager._tasks = {"test": task}
        task._manager = manager
        with pytest.raises(OperationFailError):
            task.manager = None

        manager._tasks = dict()
        task._manager = None
        with pytest.raises(OperationFailError):
            task.manager = manager

        manager._tasks = {"test": task2}
        with pytest.raises(OperationFailError):
            task.manager = manager

    def test_property_manager_setter(self):
        task = Task(name="test", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()

        task._manager = manager
        task.manager = None
        assert task._manager is None

        manager._tasks = {"test": task}
        task.manager = manager
        assert task._manager == manager


class TestScheduleManager:
    """Test ScheduleManager object."""

    def test_register_task(self):
        task = Task(name="test_task", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task)

        assert "test_task" in manager._tasks
        assert task is manager._tasks["test_task"]
        assert task.manager is manager

    def test_register_task_duplicate_name(self):
        task = Task(name="test_task", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task)

        with pytest.raises(TaskNameDuplicateError):
            manager.register(task2)

    def test_register_task_by_name(self):
        manager = ScheduleManager()
        manager.register_task(name="test", job=lambda *args, **kwargs: None)

        assert "test" in manager._tasks
        assert isinstance(manager._tasks["test"], Task)
        assert manager._tasks["test"].manager is manager

    def test_register_task_without_giving_name(self):
        manager = ScheduleManager()
        manager.register_task(job=lambda *args, **kwargs: None)
        task_name = list(manager._tasks.keys())[0]

        assert task_name.startswith("Task-")

    def test_register_task_by_name_duplicate_name(self):
        manager = ScheduleManager()
        manager.register_task(name="test", job=lambda *args, **kwargs: None)

        with pytest.raises(TaskNameDuplicateError):
            manager.register_task(name="test",
                                  job=lambda *args, **kwargs: None)

    def test_property_count(self):
        manager = ScheduleManager()
        manager.register_task(name="test", job=lambda *args, **kwargs: None)
        manager.register_task(name="test2", job=lambda *args, **kwargs: None)
        manager.register_task(name="test3", job=lambda *args, **kwargs: None)

        assert manager.count == len(manager._tasks)

    def test_unregister_task_by_name(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)

        assert manager.count == 3
        manager.unregister(name="test_task2")
        assert manager.count == 2
        assert "test_task1" in manager._tasks
        assert task1.manager is manager
        assert "test_task2" not in manager._tasks
        assert task2.manager is None
        assert "test_task3" in manager._tasks
        assert task3.manager is manager

    def test_unregister_task_by_tag(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)
        task4.add_tag(2)

        assert manager.count == 4
        manager.unregister(tag=2)
        assert manager.count == 2
        assert "test_task1" in manager._tasks
        assert task1.manager is manager
        assert "test_task2" not in manager._tasks
        assert task2.manager is None
        assert "test_task3" in manager._tasks
        assert task3.manager is manager
        assert "test_task4" not in manager._tasks
        assert task4.manager is None

    def test_unregister_task_by_tags(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        task5 = Task(name="test_task5", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        manager.register(task5)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)
        task4.add_tag(2)
        task5.add_tag("tag")

        assert manager.count == 5
        manager.unregister(tag=[2, "tag"])
        assert manager.count == 2
        assert "test_task1" in manager._tasks
        assert task1.manager is manager
        assert "test_task2" not in manager._tasks
        assert task2.manager is None
        assert "test_task3" in manager._tasks
        assert task3.manager is manager
        assert "test_task4" not in manager._tasks
        assert task4.manager is None
        assert "test_task5" not in manager._tasks
        assert task5.manager is None

    def test_unregister_task_by_both_name_tags(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        task5 = Task(name="test_task5", job=lambda *args, **kwargs: None)
        task6 = Task(name="test_task6", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        manager.register(task5)
        manager.register(task6)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)
        task4.add_tag(2)
        task5.add_tag("tag")

        assert manager.count == 6
        manager.unregister(name="test_task6", tag=[2, "tag"])
        assert manager.count == 2
        assert "test_task1" in manager._tasks
        assert task1.manager is manager
        assert "test_task2" not in manager._tasks
        assert task2.manager is None
        assert "test_task3" in manager._tasks
        assert task3.manager is manager
        assert "test_task4" not in manager._tasks
        assert task4.manager is None
        assert "test_task5" not in manager._tasks
        assert task5.manager is None
        assert "test_task6" not in manager._tasks
        assert task6.manager is None

    def test_get_task(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)

        assert manager.task("test_task3") is task3

    def test_get_unregistered_task(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)

        with pytest.raises(TaskNotFoundError):
            manager.task("test")

    def test_get_tasks(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)
        task4.add_tag(2)
        task_list = manager.tasks(2)

        assert len(task_list._tasks) == 2
        assert task1 not in task_list
        assert task2 in task_list
        assert task3 not in task_list
        assert task4 in task_list

    def test_get_tasks_by_tags(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(3)
        task4.add_tag(2)
        task_list = manager.tasks([1, 2])

        assert len(task_list._tasks) == 3
        assert task1 in task_list
        assert task2 in task_list
        assert task3 not in task_list
        assert task4 in task_list

    def test_property_all_tasks(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task_list = manager.all_tasks

        assert len(task_list._tasks) == 4
        assert task1 in task_list
        assert task2 in task_list
        assert task3 in task_list
        assert task4 in task_list

    def test_property_running_tasks(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task1.period(5)
        task1.start()
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        task4.period(5)
        task4.start()
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task_list = manager.running_tasks

        assert len(task_list._tasks) == 2
        assert task1 in task_list
        assert task2 not in task_list
        assert task3 not in task_list
        assert task4 in task_list

        task1.stop()
        task4.stop()

    def test_property_pending_tasks(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task1.period(5)
        task1.start()
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        task4.period(5)
        task4.start()
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task_list = manager.pending_tasks

        assert len(task_list._tasks) == 2
        assert task1 not in task_list
        assert task2 in task_list
        assert task3 in task_list
        assert task4 not in task_list

        task1.stop()
        task4.stop()

    def test_task_finish_action_stop(self):
        manager = ScheduleManager()
        task1 = Task(name="test", job=lambda *args, **kwargs: None)
        manager.register(task1)
        task1.period(5)
        task1.start()
        time.sleep(1)

        assert "test" in manager

        task1.stop()
        time.sleep(2)
        assert "test" not in manager

    def test_task_finish_action_pause_Situation1(self):
        manager = ScheduleManager()
        task1 = Task(name="test", job=lambda *args, **kwargs: None)
        manager.register(task1)
        task1.period(5)
        task1.start()
        time.sleep(1)

        assert "test" in manager
        assert manager.task("test").is_running
        assert manager.task("test")._started.is_set()
        assert manager.task("test").is_alive()
        assert manager.task("test").next_run

        manager.task("test").pause()
        time.sleep(2)
        assert "test" in manager
        assert not manager.task("test").is_running
        assert not manager.task("test")._started.is_set()
        assert not manager.task("test").is_alive()
        assert not manager.task("test")._is_stopped
        assert not manager.task("test").next_run
        assert not manager.task("test")._pause_task
        assert not manager.task("test")._stop_task
        assert manager.task("test")._periodic == task1._periodic

    def test_task_finish_action_pause_Situation2(self):
        manager = ScheduleManager()
        task2 = Task(name="test2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        task2.period_day_at("16:00:00")
        task2.set_tags(["a", 1])
        task3 = Task(name="test3", job=lambda *args, **kwargs: None)
        manager.register(task3)
        task3.period_week_at(at_time="17:00:00", week_day="Sunday")
        task3.set_tags(["b", 2])
        task4 = Task(name="test4", job=lambda *args, **kwargs: None)
        manager.register(task4)
        task4.period_month_at(at_time="18:00:00", day=7)
        task4.set_tags(["c", 3])

        task2.start()
        task3.start()
        task4.start()
        time.sleep(1)

        assert "test2" in manager
        assert manager.task("test2").is_running
        assert manager.task("test2")._started.is_set()
        assert manager.task("test2").is_alive()
        assert manager.task("test2").next_run
        assert "test3" in manager
        assert manager.task("test3").is_running
        assert manager.task("test3")._started.is_set()
        assert manager.task("test3").is_alive()
        assert manager.task("test3").next_run
        assert "test4" in manager
        assert manager.task("test4").is_running
        assert manager.task("test4")._started.is_set()
        assert manager.task("test4").is_alive()
        assert manager.task("test4").next_run

        manager.task("test2").pause()
        manager.task("test3").pause()
        manager.task("test4").pause()
        time.sleep(2)

        assert "test2" in manager
        assert not manager.task("test2").is_running
        assert not manager.task("test2")._started.is_set()
        assert not manager.task("test2").is_alive()
        assert not manager.task("test2")._is_stopped
        assert not manager.task("test2").next_run
        assert not manager.task("test2")._pause_task
        assert not manager.task("test2")._stop_task
        assert manager.task("test2").tag == ["a", 1]
        assert manager.task("test2")._periodic_unit == task2._periodic_unit
        assert manager.task("test2")._at_time == task2._at_time
        assert "test3" in manager
        assert not manager.task("test3").is_running
        assert not manager.task("test3")._started.is_set()
        assert not manager.task("test3").is_alive()
        assert not manager.task("test3")._is_stopped
        assert not manager.task("test3").next_run
        assert not manager.task("test3")._pause_task
        assert not manager.task("test3")._stop_task
        assert manager.task("test3").tag == ["b", 2]
        assert manager.task("test3")._periodic_unit == task3._periodic_unit
        assert manager.task("test3")._at_time == task3._at_time
        assert manager.task("test3")._at_week_day == task3._at_week_day
        assert "test4" in manager
        assert not manager.task("test4").is_running
        assert not manager.task("test4")._started.is_set()
        assert not manager.task("test4").is_alive()
        assert not manager.task("test4")._is_stopped
        assert not manager.task("test4").next_run
        assert not manager.task("test4")._pause_task
        assert not manager.task("test4")._stop_task
        assert manager.task("test4").tag == ["c", 3]
        assert manager.task("test4")._periodic_unit == task4._periodic_unit
        assert manager.task("test4")._at_time == task4._at_time
        assert manager.task("test4")._at_day == task4._at_day

    def test_task_finish_action_pause_Situation3(self):
        manager = ScheduleManager()
        task = Task(name="test", job=lambda *args, **kwargs: None)
        manager.register(task)
        task.period(2)
        task.nonperiodic(10)
        task.start()
        time.sleep(5)
        manager.task("test").pause()
        time.sleep(2)

        assert "test" in manager
        assert not manager.task("test").is_running
        assert not manager.task("test")._started.is_set()
        assert not manager.task("test").is_alive()
        assert not manager.task("test")._is_stopped
        assert not manager.task("test").next_run
        assert not manager.task("test")._pause_task
        assert not manager.task("test")._stop_task
        assert manager.task("test")._periodic == task._periodic
        assert manager.task("test")._nonperiod_count == task._nonperiod_count

    def test_task_finish_action_pause_Situation4(self):
        time_start = datetime.now() + timedelta(hours=6)
        manager = ScheduleManager()
        task = Task(name="test", job=lambda *args, **kwargs: None)
        manager.register(task)
        task.period(5)
        task.start_at(time_start)
        task.start()
        time.sleep(2)
        manager.task("test").pause()
        time.sleep(2)

        assert "test" in manager
        assert not manager.task("test").is_running
        assert not manager.task("test")._started.is_set()
        assert not manager.task("test").is_alive()
        assert not manager.task("test")._is_stopped
        assert not manager.task("test").next_run
        assert not manager.task("test")._pause_task
        assert not manager.task("test")._stop_task
        assert manager.task("test")._periodic == task._periodic
        assert manager.task("test")._start_at == task._start_at

    @pytest.mark.parametrize('time_tester',
                             [(this_year, 1, 1, 1, 0, 0)],
                             indirect=True)
    def test_task_finish_action_pause_Situation5(self, time_tester):
        manager = ScheduleManager()
        task = Task(name="test", job=lambda *args, **kwargs: None)
        manager.register(task)
        task.period(5)
        task.delay(60)
        task.start()
        time.sleep(2)

        with FakeDatetime(this_year, 1, 1, 1, 0, 20):
            manager.task("test").pause()
            time.sleep(2)

            assert "test" in manager
            assert not manager.task("test").is_running
            assert not manager.task("test")._started.is_set()
            assert not manager.task("test").is_alive()
            assert not manager.task("test")._is_stopped
            assert not manager.task("test").next_run
            assert not manager.task("test")._pause_task
            assert not manager.task("test")._stop_task
            assert manager.task("test")._periodic == task._periodic
            assert manager.task("test")._delay == timedelta(seconds=40)


class TestTaskGroup:
    """Test TaskGroup object."""

    def test_property_count(self):
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task3", job=lambda *args, **kwargs: None)
        task4 = Task(name="test_task4", job=lambda *args, **kwargs: None)
        manager = ScheduleManager()
        manager.register(task1)
        manager.register(task2)
        manager.register(task3)
        manager.register(task4)
        task1.add_tag(1)
        task2.add_tag(2)
        task3.add_tag(2)
        task4.add_tag(2)
        task_list = manager.tasks(2)

        assert task_list.count == 3

    def test_add_tag(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'add_tag')

        task_list.add_tag(1)

        assert mock_mathod.called

    def test_add_tags(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'add_tags')

        task_list.add_tags([1, "2"])

        assert mock_mathod.called

    def test_remove_tag(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'remove_tag')

        task_list.remove_tag(1)

        assert mock_mathod.called

    def test_remove_tags(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'remove_tags')

        task_list.remove_tags([1, "2"])

        assert mock_mathod.called

    def test_set_tags(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'set_tags')

        task_list.set_tags([1, "2"])

        assert mock_mathod.called

    def test_delay(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'delay')

        task_list.delay(60)

        assert mock_mathod.called

    def test_start_at(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'start_at')

        task_list.start_at("01:00:00")

        assert mock_mathod.called

    def test_nonperiodic(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'nonperiodic')

        task_list.nonperiodic(10)

        assert mock_mathod.called

    def test_periodic(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'periodic')

        task_list.periodic()

        assert mock_mathod.called

    def test_period(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'period')

        task_list.period(50)

        assert mock_mathod.called

    def test_period_at(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'period_at')

        task_list.period_at()

        assert mock_mathod.called

    def test_period_day_at(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'period_day_at')

        task_list.period_day_at()

        assert mock_mathod.called

    def test_period_week_at(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'period_week_at')

        task_list.period_week_at()

        assert mock_mathod.called

    def test_period_month_at(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'period_month_at')

        task_list.period_month_at()

        assert mock_mathod.called

    def test_start(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks
        mock_mathod = mocker.patch.object(task1, 'start')

        task_list.start()

        assert mock_mathod.called

    def test_stop(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks
        task1.start()
        task2.start()
        mock_mathod = mocker.patch.object(task1, 'stop')

        task_list.stop()

        assert mock_mathod.called

    def test_pause(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks
        task_list.start()

        task_list.pause()
        time.sleep(2)

        for task in task_list:
            assert task.manager
            assert not task.manager.task(task.name).is_running
            assert not task.manager.task(task.name)._started.is_set()
            assert not task.manager.task(task.name).is_alive()
            assert not task.manager.task(task.name)._is_stopped
            assert not task.manager.task(task.name).next_run
            assert not task.manager.task(task.name)._pause_task
            assert not task.manager.task(task.name)._stop_task

    def test_set_manager(self, mocker):
        manager = ScheduleManager()
        manager2 = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks
        task_list.set_manager(manager2)

        assert manager.count == 0
        assert manager2.count == 2

    def test_set_manager_duplicate_task_name(self, mocker):
        manager = ScheduleManager()
        manager2 = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        task3 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        manager.register(task1)
        manager.register(task2)
        manager2.register(task3)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks

        with pytest.raises(TaskNameDuplicateError):
            task_list.set_manager(manager2)

    def test_set_manager_create_new(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task2)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task_list = manager.all_tasks
        manager2 = task_list.set_manager()

        assert manager.count == 0
        assert manager2.count == 2

    def test___add__(self, mocker):
        manager = ScheduleManager()
        task1 = Task(name="test_task1", job=lambda *args, **kwargs: None)
        task2 = Task(name="test_task2", job=lambda *args, **kwargs: None)
        manager.register(task1)
        task1.period(10)
        task2.period(10)
        task1.add_tag(1)
        task2.add_tag(2)
        task_list1 = manager.tasks(1)
        task_list2 = TaskGroup((task2,))
        task_list3 = task_list1 + task_list2

        assert task2 not in task_list1
        assert task1 in task_list3
        assert task2 in task_list3

        task_list1 += task_list2
        assert task1 in task_list1
        assert task2 in task_list1
