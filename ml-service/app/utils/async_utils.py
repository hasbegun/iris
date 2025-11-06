"""
Async utilities for common patterns
Provides context managers and helpers for async operations
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
import time
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def timed_operation(operation_name: str) -> AsyncGenerator[Dict[str, float], None]:
    """
    Context manager for timing async operations

    Automatically logs timing information and provides elapsed time

    Args:
        operation_name: Name of the operation for logging

    Yields:
        dict: Timer dict with 'start' and 'elapsed_ms' keys

    Usage:
        async with timed_operation("detection") as timer:
            result = await yolo_service.detect(...)
        print(f"Detection took {timer['elapsed_ms']}ms")
    """
    start_time = time.time()
    timer = {"start": start_time, "elapsed_ms": 0.0}

    try:
        yield timer
    finally:
        elapsed = time.time() - start_time
        timer['elapsed_ms'] = round(elapsed * 1000, 2)
        logger.debug(f"{operation_name} completed in {timer['elapsed_ms']}ms")


@asynccontextmanager
async def error_context(
    operation_name: str,
    log_errors: bool = True
) -> AsyncGenerator[None, None]:
    """
    Context manager for consistent error handling

    Logs errors and re-raises them for handling at higher level

    Args:
        operation_name: Name of the operation for error messages
        log_errors: Whether to log errors (default: True)

    Usage:
        async with error_context("object detection"):
            result = await yolo_service.detect(...)
    """
    try:
        yield
    except Exception as e:
        if log_errors:
            logger.error(f"{operation_name} failed: {e}", exc_info=True)
        raise


async def run_with_timeout(
    coro,
    timeout_seconds: float,
    operation_name: str = "operation"
):
    """
    Run async operation with timeout

    Args:
        coro: Coroutine to run
        timeout_seconds: Timeout in seconds
        operation_name: Name for error messages

    Returns:
        Result of the coroutine

    Raises:
        TimeoutError: If operation times out
    """
    import asyncio

    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout_seconds}s")
        raise TimeoutError(
            f"{operation_name} timed out after {timeout_seconds} seconds"
        )
