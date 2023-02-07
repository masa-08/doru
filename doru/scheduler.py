import datetime
import random
import re
import time
from logging import getLogger
from threading import Event, Thread
from typing import Any, Callable, Dict, Optional, Union

from schedule import IntervalError, Job, ScheduleError, Scheduler, ScheduleValueError

from doru.exceptions import DoruError
from doru.types import Cycle, Weekday

logger = getLogger(__name__)

DEFAULT_TIME = "00:00"


class MonthEnabledJob(Job):
    def __init__(self, interval: int, scheduler: Scheduler = None):
        super().__init__(interval, scheduler)
        # Specific date of the month to start on
        self.start_date: Optional[int] = None

    @property
    def month(self):
        if self.interval != 1:
            raise IntervalError("Use months instead of month")
        return self.months

    @property
    def months(self):
        self.unit = "months"
        return self

    def date(self, time_str: str):
        if self.unit != "months":
            raise ScheduleValueError("Invalid unit (valid unit is `months`")

        if not isinstance(time_str, str):
            raise TypeError("date() should be passed a string")

        if not re.match(r"^([1-9]|0[1-9]|[12]\d|3[01])$", time_str):
            raise ScheduleValueError("Invalid date format for a monthly job (valid format is dd)")

        self.start_date = int(time_str)
        return self

    def at(self, time_str):
        if self.unit not in ("days", "hours", "minutes") and not self.start_day and not self.start_date:
            raise ScheduleValueError("Invalid unit (valid units are `days`, `hours`, and `minutes`)")
        if not isinstance(time_str, str):
            raise TypeError("at() should be passed a string")
        if self.unit == "days" or self.start_day:
            if not re.match(r"^([0-2]\d:)?[0-5]\d:[0-5]\d$", time_str):
                raise ScheduleValueError("Invalid time format for a daily job (valid format is HH:MM(:SS)?)")
        if self.unit == "hours":
            if not re.match(r"^([0-5]\d)?:[0-5]\d$", time_str):
                raise ScheduleValueError("Invalid time format for an hourly job (valid format is (MM)?:SS)")

        if self.unit == "minutes":
            if not re.match(r"^:[0-5]\d$", time_str):
                raise ScheduleValueError("Invalid time format for a minutely job (valid format is :SS)")
        time_values = time_str.split(":")
        hour: Union[str, int]
        minute: Union[str, int]
        second: Union[str, int]
        if len(time_values) == 3:
            hour, minute, second = time_values
        elif len(time_values) == 2 and self.unit == "minutes":
            hour = 0
            minute = 0
            _, second = time_values
        elif len(time_values) == 2 and self.unit == "hours" and len(time_values[0]):
            hour = 0
            minute, second = time_values
        else:
            hour, minute = time_values
            second = 0
        if self.unit == "days" or self.start_day or self.start_date:
            hour = int(hour)
            if not (0 <= hour <= 23):
                raise ScheduleValueError("Invalid number of hours ({} is not between 0 and 23)")
        elif self.unit == "hours":
            hour = 0
        elif self.unit == "minutes":
            hour = 0
            minute = 0
        minute = int(minute)
        second = int(second)
        self.at_time = datetime.time(hour, minute, second)  # type: ignore
        return self

    def _schedule_next_run(self) -> None:
        if self.unit not in ("seconds", "minutes", "hours", "days", "weeks", "months"):
            raise ScheduleValueError(
                "Invalid unit (valid units are `seconds`, `minutes`, `hours`, `days`, `weeks`, and  `months`)"
            )

        if self.latest is not None:
            if not (self.latest >= self.interval):
                raise ScheduleError("`latest` is greater than `interval`")
            interval = random.randint(self.interval, self.latest)
        else:
            interval = self.interval

        if self.unit == "months":
            if self.start_date is None:
                raise ScheduleValueError("`start_date` is needed for `months`")

            now = datetime.datetime.now()
            start_month, start_year = now.month + self.interval, now.year
            while start_month > 12:
                start_month -= 12
                start_year += 1
            try:
                # The period property is not used when unit is `months` because timedelta doesn't support months.
                # However, if the period property is not set, a TypeError may occur in `if self.at_time is not None` part,
                # so the period property is set by estimating that 1month = 31days.
                self.period = datetime.timedelta(**{"days": 31 * interval})
                self.next_run = datetime.datetime(
                    start_year, start_month, self.start_date, now.hour, now.minute, now.second, now.microsecond
                )
            except ValueError:
                raise ScheduleValueError("Invalid datetime")
        else:
            self.period = datetime.timedelta(**{self.unit: interval})
            self.next_run = datetime.datetime.now() + self.period

        if self.start_day is not None:
            if self.unit != "weeks":
                raise ScheduleValueError("`unit` should be 'weeks'")
            weekdays = (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            )
            if self.start_day not in weekdays:
                raise ScheduleValueError("Invalid start day (valid start days are {})".format(weekdays))
            weekday = weekdays.index(self.start_day)
            days_ahead = weekday - self.next_run.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            self.next_run += datetime.timedelta(days_ahead) - self.period
        if self.at_time is not None:
            if self.unit not in ("days", "hours", "minutes") and self.start_day is None and self.start_date is None:
                raise ScheduleValueError("Invalid unit without specifying start day")
            kwargs = {"second": self.at_time.second, "microsecond": 0}
            if self.unit == "days" or self.start_day is not None or self.start_date is not None:
                kwargs["hour"] = self.at_time.hour
            if self.unit in ["days", "hours"] or self.start_day is not None or self.start_date is not None:
                kwargs["minute"] = self.at_time.minute
            self.next_run = self.next_run.replace(**kwargs)  # type:ignore

            # Make sure we run at the specified time *today* (or *this hour*)
            # as well. This accounts for when a job takes so long it finished
            # in the next period.
            if not self.last_run or (self.next_run - self.last_run) > self.period:
                now = datetime.datetime.now()
                if self.unit == "days" and self.at_time > now.time() and self.interval == 1:
                    self.next_run = self.next_run - datetime.timedelta(days=1)
                elif self.unit == "hours" and (
                    self.at_time.minute > now.minute
                    or (self.at_time.minute == now.minute and self.at_time.second > now.second)
                ):
                    self.next_run = self.next_run - datetime.timedelta(hours=1)
                elif self.unit == "minutes" and self.at_time.second > now.second:
                    self.next_run = self.next_run - datetime.timedelta(minutes=1)
        if self.start_day is not None and self.at_time is not None:
            # Let's see if we will still make that time we specified today
            if (self.next_run - datetime.datetime.now()).days >= 7:
                self.next_run -= self.period

        # For monthly job
        if self.start_date is not None and self.at_time is not None:
            next_run_interval_before = self.next_run.replace(month=self.next_run.month - self.interval)
            if next_run_interval_before >= datetime.datetime.now():
                self.next_run = next_run_interval_before
                while self.next_run.month <= 0:
                    self.next_run = self.next_run.replace(
                        month=self.next_run.month + 12,
                        year=self.next_run.year - 1,
                    )


# ref: https://gist.github.com/mplewis/8483f1c24f2d6259aef6
class SafeScheduler(Scheduler):
    """
    An implementation of Scheduler that catches jobs that fail, logs their exception tracebacks as errors, optionally
    reschedules the jobs for their next run time, and keeps going. Use this to run jobs that may or may not crash
    without worrying about whether other jobs will run or if they'll crash the entire script.
    """

    def __init__(self, reschedule_on_failure=True) -> None:
        """
        If reschedule_on_failure is True, jobs will be rescheduled for their next run as if they had completed
        successfully. If False, they'll be canceled.
        """
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job: MonthEnabledJob) -> None:
        try:
            super()._run_job(job)
        except Exception as e:
            logger.error(f"Failed to run job: {str(e)}")
            if self.reschedule_on_failure:
                job.last_run = datetime.datetime.now()
                job._schedule_next_run()
            else:
                logger.warning("The job was canceled.")
                self.cancel_job(job)

    def every(self, interval: int = 1) -> "MonthEnabledJob":
        job = MonthEnabledJob(interval, self)
        return job


# ref: https://schedule.readthedocs.io/en/stable/background-execution.html
class ScheduleThread(Thread):
    """
    An implementation of Thread that executes jobs according to a specified schedule.
    The schedule management functionality depends on the schedule library.
    """

    def __init__(self, scheduler: SafeScheduler, cycle: float = 1, *args, **kwargs):
        """
        A thread will try to execute jobs at each `interval`.
        Whether or not the job is executed depends on the `scheduler`.
        """
        super().__init__(*args, **kwargs)
        self.scheduler = scheduler
        self.cycle = cycle
        self.cease_continuous_run = Event()
        self.started = Event()

    def _has_jobs(self) -> bool:
        return len(self.scheduler.get_jobs()) != 0

    def run(self) -> None:
        try:
            # TODO:
            # Implementation changes are needed when supporting execution of non-interval jobs in cli.
            # e.g. Execute every Monday at xx:xx
            self.started.set()

            while not self.cease_continuous_run.is_set() and self._has_jobs():
                self.scheduler.run_pending()
                time.sleep(self.cycle)
        finally:
            del self._target, self._args, self._kwargs  # type: ignore

    def stop(self) -> None:
        self.cease_continuous_run.set()

    def is_started(self) -> bool:
        return self.started.is_set()


class ScheduleThreadPool:
    """
    An Implementation of a class that manages scheduling threads.
    This implementation allocates one scheduled job per thread.
    """

    pool: Dict[str, ScheduleThread]

    def __init__(self, max_running_threads: int) -> None:
        self.max_running_threads = max_running_threads
        self.pool = {}

    def _create_schedule_thread(
        self,
        func: Callable[..., Any],
        cycle: Cycle,
        weekday: Optional[Weekday] = None,
        day: Optional[int] = None,
        time: str = DEFAULT_TIME,
        *args,
        **kwargs,
    ) -> ScheduleThread:
        scheduler = SafeScheduler()
        if cycle == "Daily":
            scheduler.every().day.at(time).do(func, args=args, kwargs=kwargs)
        elif cycle == "Weekly":
            if weekday is None:
                raise DoruError("The weekday parameter should not be None in the weekly schedule thread.")

            if weekday == "Sun":
                scheduler.every().sunday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Mon":
                scheduler.every().monday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Tue":
                scheduler.every().tuesday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Wed":
                scheduler.every().wednesday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Thu":
                scheduler.every().thursday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Fri":
                scheduler.every().friday.at(time).do(func, args=args, kwargs=kwargs)
            elif weekday == "Sat":
                scheduler.every().saturday.at(time).do(func, args=args, kwargs=kwargs)
        elif cycle == "Monthly":
            if day is None:
                raise DoruError("The day parameter should not be None in the monthly schedule thread.")

            scheduler.every().month.date(str(day)).at(time).do(func, args=args, kwargs=kwargs)
        return ScheduleThread(scheduler, daemon=True)

    @property
    def running_threads_count(self) -> int:
        return len([t for t in self.pool.values() if t.is_alive()])

    def _is_startable(self) -> bool:
        return self.running_threads_count < self.max_running_threads

    def submit(
        self,
        key: str,
        func: Callable[..., Any],
        cycle: Cycle,
        weekday: Optional[Weekday] = None,
        day: Optional[int] = None,
        time: str = DEFAULT_TIME,
        *args,
        **kwargs,
    ) -> None:
        if key in self.pool:
            # kill the zombie thread if it exists
            if self.pool[key].is_started() and not self.pool[key].is_alive():
                del self.pool[key]
            else:
                raise DoruError(f"The key `{key}` is a duplicate.")

        self.pool[key] = self._create_schedule_thread(func, cycle, weekday, day, time, *args, **kwargs)

    def start(self, key: str) -> None:
        if not self._is_startable():
            raise DoruError("Cannot start a new thread because the number of running threads has reached the limit.")

        try:
            self.pool[key].start()
        except KeyError:
            logger.debug(f"The key `{key}` is missing.")

    def kill(self, key: str) -> None:
        try:
            self.pool[key].stop()
            del self.pool[key]
        except KeyError:
            logger.debug(f"The key `{key}` is missing.")

    def next_run(self, key: str) -> Optional[datetime.datetime]:
        try:
            return self.pool[key].scheduler.next_run
        except KeyError:
            logger.debug(f"The key `{key}` is missing.")
        return None
