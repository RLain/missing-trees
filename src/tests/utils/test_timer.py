import asyncio
import time
import logging
import pytest
pytest_plugins = ("pytest_asyncio",)

from unittest.mock import patch

import utils.timer as timer  # <-- This replaces your_module_name

@pytest.mark.asyncio
async def test_sleep():
    start = time.perf_counter()
    await timer.sleep(100)  # 100 ms
    duration = (time.perf_counter() - start) * 1000
    assert duration >= 90


def test_start_and_elapsed_time_in_ms():
    start = timer.start_time_in_ms()
    time.sleep(0.05)  # 50 ms
    elapsed = timer.elapsed_time_in_ms(start)
    assert 40 <= elapsed <= 200


def test_log_elapsed_time_in_ms_logs_message(caplog):
    caplog.set_level(logging.INFO)
    start = timer.start_time_in_ms()
    time.sleep(0.01)  # 10 ms
    timer.log_elapsed_time_in_ms(start, "Test message")

    assert any("TIMING: Test message" in record.message for record in caplog.records)
