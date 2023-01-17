import time
from datetime import timedelta
from logging import ERROR, WARNING

import pytest

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
    pool.submit("1", lambda x: x, "1day")
    pool.submit("2", lambda x: x, "1day")
    return pool


@pytest.fixture
def counter():
    return Count()


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
    assert ("doru", ERROR, "bad job") in caplog.record_tuples


def test_unflagged_safe_scheduler_with_job_exception_cancel_job(counter, caplog):
    s = SafeScheduler(reschedule_on_failure=False)
    s.every(0.1).until(timedelta(seconds=0.25)).seconds.do(bad_job, counter)
    while s.next_run is not None:
        s.run_pending()
    assert counter.value == 1
    assert ("doru", ERROR, "bad job") in caplog.record_tuples
    assert ("doru", WARNING, "The job was canceled.") in caplog.record_tuples


def test_schedule_thread_run_continuously_until_stop_called(scheduler: SafeScheduler, counter):
    scheduler.every(0.1).seconds.do(good_job, counter)
    t = ScheduleThread(scheduler=scheduler, interval=0.01)

    t.start()
    time.sleep(0.25)
    assert t.is_alive()

    t.stop()
    time.sleep(0.25)
    # There are three execution timings
    # - Immediately after the start of the thread
    # - Approximately 0.1 second after thread start
    # - Approximately 0.2 seconds after thread start
    # After that, the thread is stopped, job execution stops, and the thread becomes inactive.
    assert counter.value == 3
    assert not t.is_alive()


def test_schedule_thread_run_will_be_finished_when_there_is_no_job_to_execute(scheduler: SafeScheduler, counter):
    scheduler.every(0.1).seconds.do(good_job, counter)
    t = ScheduleThread(scheduler=scheduler, interval=0.01)

    t.start()
    time.sleep(0.25)
    assert t.is_alive()

    t.scheduler.clear()
    time.sleep(0.25)
    assert not t.is_alive()


@pytest.mark.parametrize("key", ["3"])
def test_schedule_thread_pool_submit_with_new_key_succeed(thread_pool: ScheduleThreadPool, key):
    running_threads_before = thread_pool.running_threads_count
    thread_pool.submit(key, lambda x: x, "1day", "hoge", "foo")
    assert key in thread_pool.pool
    assert thread_pool.running_threads_count == running_threads_before


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_submit_with_duplicate_key_raise_exception(thread_pool: ScheduleThreadPool, key):
    with pytest.raises(DoruError):
        thread_pool.submit(key, lambda x: x, "1day", "hoge", "foo")


@pytest.mark.parametrize("key", ["1"])
def test_schedule_thread_pool_submit_delete_zombie_thread_and_succeed(thread_pool: ScheduleThreadPool, key):
    thread_pool.start(key)
    thread_pool.pool[key].stop()
    time.sleep(1)
    assert key in thread_pool.pool
    assert thread_pool.pool[key].is_started()

    thread_pool.submit(key, lambda x: x, "1day", "hoge", "foo")
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
    thread_pool.submit("3", lambda x: x, "1day")
    thread_pool.submit("4", lambda x: x, "1day")
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
