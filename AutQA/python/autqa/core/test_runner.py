"""
Base test runner and utilities for API automation.

Provides reusable test methods, result containers, and validation functions
for all API endpoint tests. Designed to work with pytest or standalone execution.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

from autqa.core.http_client import HttpClient, get_client

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class APITestResult:
    """
    Container for API test results.
    
    Provides structured storage of test outcomes with support for
    multiple validation errors and custom metadata.
    
    Example:
        result = APITestResult(test_name="Add Face")
        result.status_code = 200
        result.response = {"registrationCode": "abc123"}
        if result.success:
            print("Test passed!")
    """
    
    test_name: str = "API Test"
    success: bool = True
    status: TestStatus = TestStatus.PASSED
    status_code: Optional[int] = None
    response: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    request_payload: Optional[Dict[str, Any]] = None
    endpoint: Optional[str] = None
    
    def add_error(self, error: str) -> None:
        """
        Add an error and mark test as failed.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.success = False
        self.status = TestStatus.FAILED
    
    def add_warning(self, warning: str) -> None:
        """
        Add a warning (doesn't fail the test).
        
        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add custom metadata to the test result.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert test result to dictionary.
        
        Returns:
            Dictionary representation of test result
        """
        return {
            "test_name": self.test_name,
            "success": self.success,
            "status": self.status.value,
            "status_code": self.status_code,
            "response": self.response,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "endpoint": self.endpoint,
        }
    
    def __repr__(self) -> str:
        """String representation of test result."""
        status_emoji = "✓" if self.success else "✗"
        return f"{status_emoji} {self.test_name} ({self.status.value})"


class APITestRunner:
    """
    Test runner for API endpoints.
    
    Provides standardized test execution with automatic timing,
    logging, and result collection.
    
    Example:
        runner = APITestRunner()
        result = runner.test_endpoint(
            endpoint="/onboarding/enrollment/enroll",
            payload={"username": "test"},
            expected_status=200,
        )
    """
    
    def __init__(self, client: Optional[HttpClient] = None):
        """
        Initialize test runner.
        
        Args:
            client: Optional HTTP client. If None, uses default client.
        """
        self.client = client or get_client()
        self.results: List[APITestResult] = []
    
    def test_endpoint(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        method: str = "POST",
        expected_status: int = 200,
        validate_fn: Optional[Callable[[Dict[str, Any]], List[str]]] = None,
        test_name: Optional[str] = None,
        with_apikey: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> APITestResult:
        """
        Test an API endpoint with comprehensive validation.
        
        Args:
            endpoint: API endpoint path (e.g., "/onboarding/enrollment/addFace")
            payload: Request payload dictionary
            method: HTTP method (POST, GET, etc.)
            expected_status: Expected HTTP status code
            validate_fn: Optional custom validation function returning list of errors
            test_name: Descriptive name for the test
            with_apikey: Whether to include API key in request
            extra_headers: Additional headers to include
        
        Returns:
            APITestResult object with test outcome
            
        Example:
            result = runner.test_endpoint(
                endpoint="/onboarding/enrollment/addFace",
                payload={"enrollmentToken": "abc", "faceLivenessData": {...}},
                expected_status=200,
                validate_fn=validate_registration_code,
                test_name="Add Face - Happy Path"
            )
        """
        if test_name is None:
            test_name = f"{method} {endpoint}"
        
        result = APITestResult(
            test_name=test_name,
            endpoint=endpoint,
            request_payload=payload,
        )
        
        try:
            logger.info(f"Running test: {test_name}")
            logger.debug(f"{method} {endpoint}")
            
            # Start timing
            start_time = time.time()
            
            # Send request
            if method.upper() == "POST":
                resp = self.client.post(
                    endpoint,
                    json=payload,
                    with_apikey=with_apikey,
                    extra_headers=extra_headers,
                )
            elif method.upper() == "GET":
                resp = self.client.get(
                    endpoint,
                    params=payload,
                    with_apikey=with_apikey,
                    extra_headers=extra_headers,
                )
            else:
                result.add_error(f"Unsupported HTTP method: {method}")
                return result
            
            # Calculate execution time
            result.execution_time = time.time() - start_time
            result.status_code = resp.status_code
            
            # Log response time
            logger.debug(f"Response time: {result.execution_time:.3f}s")
            
            # Validate status code
            if resp.status_code != expected_status:
                result.add_error(
                    f"Expected status {expected_status}, got {resp.status_code}"
                )
            
            # Parse response
            try:
                result.response = resp.json()
            except Exception as e:
                result.add_error(f"Failed to parse JSON response: {e}")
                result.response = {"raw_text": resp.text}
                return result
            
            # Run custom validation if provided
            if validate_fn and resp.status_code == expected_status:
                validation_errors = validate_fn(result.response)
                if validation_errors:
                    for error in validation_errors:
                        result.add_error(error)
            
            # Check for slow responses
            if result.execution_time and result.execution_time > 5.0:
                result.add_warning(
                    f"Slow response: {result.execution_time:.2f}s (>5s threshold)"
                )
            
            # Log result
            if result.success:
                logger.info(f"✓ {test_name} passed ({result.execution_time:.3f}s)")
            else:
                logger.error(f"✗ {test_name} failed: {result.errors}")
            
        except Exception as e:
            result.add_error(f"Test execution failed: {str(e)}")
            result.status = TestStatus.ERROR
            logger.exception(f"Test error in {test_name}")
        
        # Store result
        self.results.append(result)
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all test results.
        
        Returns:
            Dictionary with test statistics
            
        Example:
            summary = runner.get_summary()
            print(f"Passed: {summary['passed']}/{summary['total']}")
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        avg_time = None
        if self.results:
            times = [r.execution_time for r in self.results if r.execution_time]
            avg_time = sum(times) / len(times) if times else None
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "average_execution_time": avg_time,
        }
    
    def print_summary(self) -> None:
        """Print formatted test summary to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for result in self.results:
            status_emoji = "✓" if result.success else "✗"
            time_str = f"{result.execution_time:.3f}s" if result.execution_time else "N/A"
            print(f"{status_emoji} {result.test_name} ({time_str})")
            
            if result.errors:
                for error in result.errors:
                    print(f"    ❌ {error}")
            
            if result.warnings:
                for warning in result.warnings:
                    print(f"    ⚠️  {warning}")
        
        print("=" * 60)
        print(f"Total Tests:    {summary['total']}")
        print(f"Passed:         {summary['passed']}")
        print(f"Failed:         {summary['failed']}")
        print(f"Errors:         {summary['errors']}")
        print(f"Success Rate:   {summary['success_rate']:.1f}%")
        
        if summary['average_execution_time']:
            print(f"Avg Time:       {summary['average_execution_time']:.3f}s")
        
        print("=" * 60)
    
    def save_results(self, output_path: Path) -> None:
        """
        Save test results to JSON file.
        
        Args:
            output_path: Path to save results JSON
            
        Example:
            runner.save_results(Path("test_results.json"))
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
        }
        
        output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Test results saved to {output_path}")
    
    def clear_results(self) -> None:
        """Clear all stored test results."""
        self.results.clear()
        logger.debug("Test results cleared")


# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

def validate_registration_code(response: Dict[str, Any]) -> List[str]:
    """
    Validate response contains a valid registrationCode.
    
    Args:
        response: API response dictionary
    
    Returns:
        List of validation errors (empty if valid)
        
    Example:
        errors = validate_registration_code(response)
        if errors:
            print(f"Validation failed: {errors}")
    """
    errors = []
    
    if "registrationCode" not in response:
        errors.append("Response missing 'registrationCode' field")
    elif not response["registrationCode"]:
        errors.append("registrationCode is empty")
    elif not isinstance(response["registrationCode"], str):
        errors.append(f"registrationCode has wrong type: {type(response['registrationCode'])}")
    
    return errors


def validate_enrollment_token(response: Dict[str, Any]) -> List[str]:
    """
    Validate response contains a valid enrollmentToken.
    
    Args:
        response: API response dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "enrollmentToken" not in response:
        errors.append("Response missing 'enrollmentToken' field")
    elif not response["enrollmentToken"]:
        errors.append("enrollmentToken is empty")
    elif not isinstance(response["enrollmentToken"], str):
        errors.append(f"enrollmentToken has wrong type: {type(response['enrollmentToken'])}")
    
    return errors


def validate_auth_token(response: Dict[str, Any]) -> List[str]:
    """
    Validate response contains a valid authToken.
    
    Args:
        response: API response dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "authToken" not in response:
        errors.append("Response missing 'authToken' field")
    elif not response["authToken"]:
        errors.append("authToken is empty")
    elif not isinstance(response["authToken"], str):
        errors.append(f"authToken has wrong type: {type(response['authToken'])}")
    
    return errors


def validate_verification_result(response: Dict[str, Any]) -> List[str]:
    """
    Validate response contains verification result.
    
    Args:
        response: API response dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if "verified" not in response:
        errors.append("Response missing 'verified' field")
    elif not isinstance(response["verified"], bool):
        errors.append(f"verified has wrong type: {type(response['verified'])}")
    
    return errors


def validate_required_fields(
    response: Dict[str, Any],
    required_fields: List[str],
) -> List[str]:
    """
    Generic validator for required fields.
    
    Args:
        response: API response dictionary
        required_fields: List of required field names
    
    Returns:
        List of validation errors (empty if valid)
        
    Example:
        errors = validate_required_fields(
            response,
            ["userId", "username", "email"]
        )
    """
    errors = []
    
    for field in required_fields:
        if field not in response:
            errors.append(f"Response missing required field: '{field}'")
        elif response[field] is None:
            errors.append(f"Required field '{field}' is null")
    
    return errors


def combine_validators(*validators: Callable[[Dict[str, Any]], List[str]]) -> Callable[[Dict[str, Any]], List[str]]:
    """
    Combine multiple validation functions into one.
    
    Args:
        *validators: Validation functions to combine
    
    Returns:
        Combined validation function
        
    Example:
        validator = combine_validators(
            validate_enrollment_token,
            lambda r: validate_required_fields(r, ["username", "email"])
        )
        errors = validator(response)
    """
    def combined_validator(response: Dict[str, Any]) -> List[str]:
        all_errors = []
        for validator in validators:
            errors = validator(response)
            all_errors.extend(errors)
        return all_errors
    
    return combined_validator


# ==============================================================================
# STANDALONE TEST EXECUTION HELPER
# ==============================================================================

def run_single_test(
    test_func: Callable[..., APITestResult],
    *args,
    **kwargs,
) -> int:
    """
    Run a single test function and return exit code.
    
    Useful for standalone script execution.
    
    Args:
        test_func: Test function to execute
        *args: Positional arguments for test function
        **kwargs: Keyword arguments for test function
    
    Returns:
        Exit code (0 for success, 1 for failure)
        
    Example:
        if __name__ == "__main__":
            sys.exit(run_single_test(test_add_face))
    """
    result = test_func(*args, **kwargs)
    
    print("\n" + "=" * 60)
    print(f"TEST: {result.test_name}")
    print("=" * 60)
    print(f"Status:        {result.status.value}")
    print(f"Status Code:   {result.status_code}")
    print(f"Execution Time: {result.execution_time:.3f}s" if result.execution_time else "N/A")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ❌ {error}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
    
    if result.response:
        print("\nResponse:")
        print(json.dumps(result.response, indent=2))
    
    print("=" * 60)
    
    return 0 if result.success else 1