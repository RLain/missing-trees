import time
import logging
import pytest
pytest_plugins = ("pytest_asyncio",)
import src.utils.time_utils as time_utils

@pytest.mark.asyncio
async def test_sleep():
    start = time.perf_counter()
    await time_utils.sleep(100)  # 100 ms
    duration = (time.perf_counter() - start) * 1000
    assert duration >= 90


def test_start_and_elapsed_time_in_ms():
    start = time_utils.start_time_in_ms()
    # Use standard blocking sleep since test is sync
    time.sleep(0.05)  # 50 ms
    elapsed = time_utils.elapsed_time_in_ms(start)
    assert 40 <= elapsed <= 200


def test_log_elapsed_time_in_ms_logs_message(caplog):
    caplog.set_level(logging.INFO)
    start = time_utils.start_time_in_ms()
    time.sleep(0.01)  # 10 ms
    time_utils.log_elapsed_time_in_ms(start, "Test message")

    assert any("TIMING: Test message" in record.message for record in caplog.records)