import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sleep(ms: int):
    await asyncio.sleep(ms / 1000.0)


def start_time_in_ms() -> float:
    return time.perf_counter() * 1000  # Convert seconds to milliseconds


def elapsed_time_in_ms(start_time_in_ms: float) -> float:
    end_time = time.perf_counter() * 1000
    return end_time - start_time_in_ms


def log_elapsed_time_in_ms(start_time_in_ms: float, message: str):
    elapsed = elapsed_time_in_ms(start_time_in_ms)
    logger.info(f"TIMING: {message}: {elapsed:.2f} ms")
