"""
Custom exceptions and error handling utilities.

Defines application-specific exceptions for better error handling.
"""

from __future__ import annotations

from typing import Any, Optional


class AutoQAError(Exception):
    """Base exception for all AutoQA errors."""
    pass


class ConfigurationError(AutoQAError):
    """Raised when configuration is invalid or missing."""
    pass


class APIError(AutoQAError):
    """Raised when API request fails."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body text
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self):
        """String representation of error."""
        parts = [super().__str__()]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.response_body:
            parts.append(f"Response: {self.response_body[:200]}")
        return " | ".join(parts)


class EnrollmentError(AutoQAError):
    """Raised when enrollment operation fails."""
    pass


class AuthenticationError(AutoQAError):
    """Raised when authentication operation fails."""
    pass


class ValidationError(AutoQAError):
    """Raised when data validation fails."""
    pass


class TokenError(AutoQAError):
    """Raised when token is missing or invalid."""
    pass


class TestError(AutoQAError):
    """Raised when test execution fails."""
    pass


def require_env(value: Any, key: str) -> None:
    """
    Ensure environment variable has a value.
    
    Args:
        value: Value to check
        key: Environment variable name
        
    Raises:
        ConfigurationError: If value is empty or None
        
    Example:
        api_key = env.get("APIKEY")
        require_env(api_key, "APIKEY")
    """
    if not value:
        raise ConfigurationError(
            f"Required environment variable '{key}' is missing or empty. "
            f"Please set it in your .env file."
        )


def require_field(data: dict, field: str) -> Any:
    """
    Ensure response contains required field.
    
    Args:
        data: Response data dictionary
        field: Required field name
        
    Returns:
        Field value
        
    Raises:
        ValidationError: If field is missing
        
    Example:
        token = require_field(response, "enrollmentToken")
    """
    if field not in data:
        raise ValidationError(f"Response missing required field: '{field}'")
    
    value = data[field]
    
    if value is None:
        raise ValidationError(f"Required field '{field}' is null")
    
    return value


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to traverse
        *keys: Sequence of keys to traverse
        default: Default value if key not found
    
    Returns:
        Value at nested path or default
        
    Example:
        token = safe_get(response, "data", "user", "token", default="")
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current