import time
from datetime import datetime
from logging import getLogger
from threading import Event, Thread
from typing import Any, Callable, Dict

from schedule import Job, Scheduler

from doru.exceptions import DoruError
from doru.types import Cycle

logger = getLogger(__name__)


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

    def _run_job(self, job: Job) -> None:
        try:
            super()._run_job(job)
        except Exception as e:
            logger.error(f"Failed to run job: {str(e)}")
            if self.reschedule_on_failure:
                job.last_run = datetime.now()
                job._schedule_next_run()
            else:
                logger.warning("The job was canceled.")
                self.cancel_job(job)


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

            # Execute the registered job immediately after the start of the thread
            if not self.cease_continuous_run.is_set():
                self.scheduler.run_all()

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

    def _create_schedule_thread(self, func: Callable[..., Any], cycle: Cycle, *args, **kwargs) -> ScheduleThread:
        scheduler = SafeScheduler()
        if cycle == "Daily":
            scheduler.every(1).days.do(func, args=args, kwargs=kwargs)
        elif cycle == "Weekly":
            scheduler.every(1).weeks.do(func, args=args, kwargs=kwargs)
        else:
            scheduler.every(4).weeks.do(func, args=args, kwargs=kwargs)  # 1month
        return ScheduleThread(scheduler, daemon=True)

    @property
    def running_threads_count(self) -> int:
        return len([t for t in self.pool.values() if t.is_alive()])

    def _is_startable(self) -> bool:
        return self.running_threads_count < self.max_running_threads

    def submit(self, key: str, func: Callable[..., Any], cycle: Cycle, *args, **kwargs) -> None:
        if key in self.pool:
            # kill the zombie thread if it exists
            if self.pool[key].is_started() and not self.pool[key].is_alive():
                del self.pool[key]
            else:
                raise DoruError(f"The key `{key}` is a duplicate.")

        self.pool[key] = self._create_schedule_thread(func, cycle, *args, **kwargs)

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
