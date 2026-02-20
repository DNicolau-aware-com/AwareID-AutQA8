import pytest
import time

@pytest.fixture(autouse=True, scope="function")
def delay_between_tests():
    """Add 2 second delay after each test to protect admin portal"""
    yield
    time.sleep(2)

@pytest.fixture(autouse=True, scope="class")
def delay_between_classes():
    """Add 5 second delay between test classes"""
    yield
    time.sleep(5)
