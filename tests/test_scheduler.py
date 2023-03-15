import time
from datetime import date, datetime, timedelta
from logging import ERROR, WARNING

import pytest
import schedule

from doru.exceptions import DoruError
from doru.scheduler import SafeScheduler, ScheduleThread, ScheduleThreadPool

MAX_RUNNING_THREADS = 3


class Count:
    value = 0

    def increment(self) -> None:
        self.value += 1


def good_job(count: Count):
    count.increment()


def bad_job(count: Count):
    count.increment()
    raise Exception("bad job")


@pytest.fixture
def scheduler():
    return SafeScheduler()


@pytest.fixture
def thread_pool():
    pool = ScheduleThreadPool(MAX_RUNNING_THREADS)
    pool.submit("1", lambda x: x, "Daily")
    pool.submit("2", lambda x: x, "Daily")
    return pool


@pytest.fixture
def counter():
    return Count()


@pytest.mark.freeze_time("2023-10-10 10:10:00")
def test_month_enabled_job(scheduler: SafeScheduler):
    def job():
        pass

    next_run = scheduler.every().date("09").at("12:34:56").do(job).next_run
    assert (
        next_run.year == 2023
        and next_run.month == 11
        and next_run.day == 9
        and next_run.hour == 12
        and next_run.minute == 34
        and next_run.second == 56
    )

    next_run = scheduler.every().date("11").at("12:34:56").do(job).next_run
    assert (
        next_run.year == 2023
        and next_run.month == 10
        and next_run.day == 11
        and next_run.hour == 12
        and next_run.minute == 34
        and next_run.second == 56
    )

    next_run = scheduler.every(3).date("09").at("12:34:56").do(job).next_run
    assert (
        next_run.year == 2024
        and next_run.month == 1
        and next_run.day == 9
        and next_run.hour == 12
        and next_run.minute == 34
        and next_run.second == 56
    )

    next_run = scheduler.every(3).date("11").at("12:34:56").do(job).next_run
    assert (
        next_run.year == 2023
        and next_run.month == 10
        and next_run.day == 11
        and next_run.hour == 12
        and next_run.minute == 34
        and next_run.second == 56
    )

    with pytest.raises(schedule.ScheduleValueError):
        scheduler.every().date("09").seconds.do(job)
        scheduler.every().date("09").minutes.do(job)
        scheduler.every().date("09").hours.do(job)
        scheduler.every().date("09").days.do(job)
        scheduler.every().date("09").weeks.do(job)

        scheduler.every().seconds.date("09").do(job)
        scheduler.every().minutes.date("09").do(job)
        scheduler.every().hours.date("09").do(job)
        scheduler.every().days.date("09").do(job)
        scheduler.every().weeks.date("09").do(job)

        scheduler.every().date("9")
        scheduler.every().date("00")
        scheduler.every().date("32")

    with pytest.raises(TypeError):
        scheduler.every().date(9)  # type:ignore[arg-type]


def test_safe_scheduler_schedule_job_succeed(scheduler, counter):
    scheduler.every(0.1).seconds.until(timedelta(seconds=0.25)).do(good_job, counter)
    while scheduler.next_run is not None:
        scheduler.run_pending()
    assert counter.value == 2


def test_flagged_safe_scheduler_with_job_exception_reschedule_job(scheduler, counter, caplog):
    scheduler.every(0.1).seconds.until(timedelta(seconds=0.25)).do(bad_job, counter)
    while scheduler.next_run is not None:
        scheduler.run_pending()
    assert counter.value == 2
    assert ("doru.scheduler", ERROR, "Failed to run job: bad job") in caplog.record_tuples


def test_unflagged_safe_scheduler_with_job_exception_cancel_job(counter, caplog):
    s = SafeScheduler(reschedule_on_failure=False)
    s.every(1).until(timedelta(seconds=2.5)).seconds.do(bad_job, counter)
    while s.next_run is not None:
        s.run_pending()
    assert counter.value == 1
    assert ("doru.scheduler", ERROR, "Failed to run job: bad job") in caplog.record_tuples
    assert ("doru.scheduler", WARNING, "The job was canceled.") in caplog.record_tuples


def test_schedule_thread_run_continuously_until_stop_called(scheduler: SafeScheduler, counter):
    scheduler.every(1).seconds.do(good_job, counter)
    t = ScheduleThread(scheduler=scheduler, cycle=0.1)

    t.start()
    time.sleep(2.5)
    assert t.is_alive()

    t.stop()
    time.sleep(2.5)
    # There are two execution timings
    # - Approximately 0.1 second after thread start
    # - Approximately 0.2 seconds after thread start
    # After that, the thread is stopped, job execution stops, and the thread becomes inactive.
    assert counter.value == 2
    assert not t.is_alive()


def test_schedule_thread_run_will_be_finished_when_there_is_no_job_to_execute(scheduler: SafeScheduler, counter):
    scheduler.every(1).seconds.do(good_job, counter)
    t = ScheduleThread(scheduler=scheduler, cycle=0.1)

    t.start()
    time.sleep(2.5)
    assert t.is_alive()

    t.scheduler.clear()
    time.sleep(2.5)
    assert not t.is_alive()


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_submit_with_new_key_succeed(thread_pool: ScheduleThreadPool, key):
    running_threads_before = thread_pool.running_threads_count
    thread_pool.submit(key, lambda x: x, "Daily")
    assert key in thread_pool.pool
    assert thread_pool.running_threads_count == running_threads_before


# 2023-01-01 is Sunday.
@pytest.mark.freeze_time("2023-01-01 00:00:00")
@pytest.mark.parametrize("key", ["3"])
@pytest.mark.parametrize(
    "weekday, expected",
    [
        ("Sun", datetime(2023, 1, 1, 0, 0)),
        ("Mon", datetime(2023, 1, 2, 0, 0)),
        ("Tue", datetime(2023, 1, 3, 0, 0)),
        ("Wed", datetime(2023, 1, 4, 0, 0)),
        ("Thu", datetime(2023, 1, 5, 0, 0)),
        ("Fri", datetime(2023, 1, 6, 0, 0)),
        ("Sat", datetime(2023, 1, 7, 0, 0)),
    ],
)
def test_schedule_thread_pool_submit_weekly_thread_with_new_key_succeed(
    thread_pool: ScheduleThreadPool, key, weekday, expected
):
    running_threads_before = thread_pool.running_threads_count
    thread_pool.submit(key, lambda x: x, "Weekly", weekday=weekday)
    assert key in thread_pool.pool
    assert thread_pool.running_threads_count == running_threads_before

    next_run = thread_pool.next_run(key)
    assert next_run is not None and next_run == expected


@pytest.mark.freeze_time("2023-01-01 00:01:00")
@pytest.mark.parametrize("key", ["3"])
@pytest.mark.parametrize(
    "day, time, expected",
    [
        (1, "00:00", datetime(2023, 2, 1, 0, 0)),
        (1, "00:01", datetime(2023, 1, 1, 0, 1)),
        (1, "00:02", datetime(2023, 1, 1, 0, 2)),
        (2, "00:00", datetime(2023, 1, 2, 0, 0)),
    ],
)
def test_schedule_thread_pool_submit_monthly_thread_with_new_key_succeed(
    thread_pool: ScheduleThreadPool, key, day, time, expected
):
    running_threads_before = thread_pool.running_threads_count
    thread_pool.submit(key, lambda x: x, "Monthly", day=day, time=time)
    assert key in thread_pool.pool
    assert thread_pool.running_threads_count == running_threads_before

    next_run = thread_pool.next_run(key)
    assert next_run is not None and next_run == expected


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_submit_with_duplicate_key_raise_exception(thread_pool: ScheduleThreadPool, key):
    with pytest.raises(DoruError):
        thread_pool.submit(key, lambda x: x, "Daily")


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_submit_without_weekday_param_for_weekly_thread_raise_exception(
    thread_pool: ScheduleThreadPool, key
):
    with pytest.raises(DoruError):
        thread_pool.submit(key, lambda x: x, "Weekly")


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_submit_without_day_param_for_monthly_thread_raise_exception(
    thread_pool: ScheduleThreadPool, key
):
    with pytest.raises(DoruError):
        thread_pool.submit(key, lambda x: x, "Monthly")


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_submit_delete_zombie_thread_and_succeed(thread_pool: ScheduleThreadPool, key):
    thread_pool.start(key)
    thread_pool.pool[key].stop()
    time.sleep(2)
    assert key in thread_pool.pool
    assert thread_pool.pool[key].is_started()

    thread_pool.submit(key, lambda x: x, "Daily")
    assert key in thread_pool.pool
    assert not thread_pool.pool[key].is_started()


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_start_when_running_threads_are_less_than_limit_succeed(
    thread_pool: ScheduleThreadPool, key
):
    assert not thread_pool.pool[key].is_alive()

    running_threads_before = thread_pool.running_threads_count
    thread_pool.start(key)
    assert thread_pool.running_threads_count == running_threads_before + 1
    assert thread_pool.pool[key].is_alive()


def test_schedule_thread_pool_start_when_running_threads_reach_limit_raise_exception(thread_pool: ScheduleThreadPool):
    thread_pool.submit("3", lambda x: x, "Daily")
    thread_pool.submit("4", lambda x: x, "Daily")
    thread_pool.start("1")
    thread_pool.start("2")
    thread_pool.start("3")
    with pytest.raises(DoruError):
        thread_pool.start("4")


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_start_with_invalid_key_only_output_debug_log(
    thread_pool: ScheduleThreadPool, key, caplog
):
    from logging import DEBUG

    from doru.scheduler import logger

    logger.setLevel(DEBUG)

    thread_pool.start(key)
    assert f"The key `{key}` is missing." in caplog.text


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_kill_with_valid_key_succeed(thread_pool: ScheduleThreadPool, key):
    thread_pool.kill(key)
    assert key not in thread_pool.pool


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_kill_with_invalid_key_only_output_debug_log(
    thread_pool: ScheduleThreadPool, key, caplog
):
    from logging import DEBUG

    from doru.scheduler import logger

    logger.setLevel(DEBUG)

    thread_pool.kill(key)
    assert f"The key `{key}` is missing." in caplog.text


@pytest.mark.parametrize("key", ["1", "2"])
def test_schedule_thread_pool_next_run_with_valid_key_succeed(thread_pool: ScheduleThreadPool, key):
    from doru.api.schema import TIMESTAMP_STRING_FORMAT

    tomorrow = date.today() + timedelta(days=1)
    next_run = thread_pool.next_run(key)
    assert next_run is not None and next_run.strftime(TIMESTAMP_STRING_FORMAT) == tomorrow.strftime(
        TIMESTAMP_STRING_FORMAT
    )


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_next_run_with_not_submitted_thread_retrun_none(thread_pool: ScheduleThreadPool, key):
    thread_pool.pool[key] = ScheduleThread(SafeScheduler())
    assert thread_pool.next_run(key) is None
