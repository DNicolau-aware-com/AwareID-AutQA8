"""
Timing and synchronization helpers for tests.

Provides smart delays and polling utilities for API tests.
"""

import time
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


def smart_delay(
    seconds: float,
    reason: str = "processing",
    silent: bool = False
) -> None:
    """
    Sleep with logging.
    
    Args:
        seconds: Seconds to sleep
        reason: Reason for delay (for logging)
        silent: If True, don't print to console
    """
    if not silent:
        print(f"  ⏱️  Waiting {seconds}s for {reason}...")
    
    logger.debug(f"Sleeping {seconds}s for {reason}")
    time.sleep(seconds)


def progressive_delay(
    base_delay: float = 1.0,
    max_delay: float = 5.0,
    attempt: int = 1
) -> float:
    """
    Calculate progressive delay (exponential backoff).
    
    Useful when you want delays to increase on retries.
    
    Args:
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        attempt: Attempt number (1-indexed)
    
    Returns:
        Calculated delay in seconds
    """
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    return delay


def poll_until(
    check_fn: Callable[[], bool],
    timeout: float = 30.0,
    poll_interval: float = 2.0,
    description: str = "condition"
) -> bool:
    """
    Poll until condition is met or timeout.
    
    Args:
        check_fn: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: Seconds between checks
        description: Description of what we're waiting for
    
    Returns:
        True if condition met, False if timeout
        
    Example:
        def check():
            resp = get_status()
            return resp.get("status") == "completed"
        
        success = poll_until(check, timeout=30, description="enrollment completion")
    """
    start_time = time.time()
    attempt = 1
    
    print(f"  ⏱️  Polling for {description} (timeout: {timeout}s)...")
    
    while time.time() - start_time < timeout:
        try:
            if check_fn():
                elapsed = time.time() - start_time
                print(f"  ✓ {description} confirmed after {elapsed:.1f}s")
                logger.info(f"{description} confirmed after {elapsed:.1f}s")
                return True
        except Exception as e:
            logger.debug(f"Poll attempt {attempt} failed: {e}")
        
        time.sleep(poll_interval)
        attempt += 1
    
    elapsed = time.time() - start_time
    print(f"  ⚠️  Timeout waiting for {description} after {elapsed:.1f}s")
    logger.warning(f"Timeout waiting for {description} after {elapsed:.1f}s")
    return False