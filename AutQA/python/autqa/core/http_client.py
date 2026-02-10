"""
HTTP client wrapper with OAuth token support.

Provides a test-friendly, dependency-injectable interface with automatic
OAuth token injection for API calls.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

# Re-use your existing request helpers
from client import get as _get
from client import post as _post

from autqa.core.config import get_settings

logger = logging.getLogger(__name__)


class HttpClient:
    """
    HTTP client for API requests with retry logic and OAuth token support.
    
    Automatically includes OAuth token in requests when available.
    
    Example:
        client = HttpClient()
        response = client.post("/onboarding/enrollment/enroll", json={...})
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
        jwt_token: Optional[str] = None,
    ):
        """
        Initialize HTTP client.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            retry_delay: Delay in seconds between retry attempts
            timeout: Request timeout in seconds
            jwt_token: Optional JWT token (loads from settings if None)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # Load JWT token from settings if not provided
        if jwt_token is None:
            settings = get_settings()
            self.jwt_token = settings.jwt
        else:
            self.jwt_token = jwt_token
    
    def set_jwt_token(self, token: str) -> None:
        """
        Set JWT token for authentication.
        
        Args:
            token: JWT token to use for requests
            
        Example:
            client.set_jwt_token("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
        """
        self.jwt_token = token
        logger.info("JWT token updated")
    
    def _get_auth_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Build authentication headers.
        
        Args:
            extra_headers: Additional headers to merge
            
        Returns:
            Headers dictionary with authentication
        """
        headers = extra_headers.copy() if extra_headers else {}
        
        # Add JWT token if available
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
            logger.debug("Added JWT token to request headers")
        
        return headers

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        with_apikey: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> requests.Response:
        """
        Execute GET request with OAuth token.
        
        Args:
            path: API endpoint path
            params: Query parameters
            with_apikey: Whether to include API key in headers
            extra_headers: Additional headers to include
            retry: Whether to retry on failure
        
        Returns:
            Response object
        """
        # Merge auth headers
        headers = self._get_auth_headers(extra_headers)
        
        logger.debug(f"GET {path} | params={params} | with_apikey={with_apikey}")
        
        if retry:
            return self._execute_with_retry(
                lambda: _get(
                    path,
                    params=params,
                    with_apikey=with_apikey,
                    extra_headers=headers,
                ),
                method="GET",
                path=path,
            )
        else:
            return _get(
                path,
                params=params,
                with_apikey=with_apikey,
                extra_headers=headers,
            )

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        with_apikey: bool = True,
        extra_headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> requests.Response:
        """
        Execute POST request with OAuth token.
        
        Args:
            path: API endpoint path
            json: JSON payload
            params: Query parameters
            with_apikey: Whether to include API key in headers
            extra_headers: Additional headers to include
            retry: Whether to retry on failure
        
        Returns:
            Response object
        """
        # Merge auth headers
        headers = self._get_auth_headers(extra_headers)
        
        logger.debug(
            f"POST {path} | payload_size={len(str(json)) if json else 0} | "
            f"with_apikey={with_apikey}"
        )
        
        if retry:
            return self._execute_with_retry(
                lambda: _post(
                    path,
                    json=json,
                    params=params,
                    with_apikey=with_apikey,
                    extra_headers=headers,
                ),
                method="POST",
                path=path,
            )
        else:
            return _post(
                path,
                json=json,
                params=params,
                with_apikey=with_apikey,
                extra_headers=headers,
            )

    def _execute_with_retry(
        self,
        request_func,
        method: str,
        path: str,
    ) -> requests.Response:
        """Execute request with automatic retry logic."""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = request_func()
                
                logger.debug(
                    f"{method} {path} | status={response.status_code} | "
                    f"attempt={attempt}/{self.max_retries}"
                )
                
                # Return successful responses (2xx, 4xx)
                if response.status_code < 500:
                    return response
                
                # 5xx errors - retry if we have attempts left
                if attempt < self.max_retries:
                    logger.warning(
                        f"{method} {path} returned {response.status_code}, "
                        f"retrying in {self.retry_delay}s... "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"{method} {path} failed after {self.max_retries} attempts: "
                        f"{response.status_code} {response.text[:200]}"
                    )
                    return response
                    
            except requests.RequestException as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(
                        f"{method} {path} request failed: {e}, "
                        f"retrying in {self.retry_delay}s... "
                        f"(attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(self.retry_delay)
                else:
                    logger.error(
                        f"{method} {path} failed after {self.max_retries} attempts: {e}"
                    )
                    raise
        
        if last_exception:
            raise last_exception
        
        raise RuntimeError(f"Request failed unexpectedly: {method} {path}")

    def get_json(self, path: str, **kwargs) -> Dict[str, Any]:
        """Execute GET request and return JSON response."""
        response = self.get(path, **kwargs)
        response.raise_for_status()
        return response.json()

    def post_json(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute POST request and return JSON response."""
        response = self.post(path, json=json, **kwargs)
        response.raise_for_status()
        return response.json()

    def health_check(self, path: str = "/health") -> bool:
        """Check if API is healthy."""
        try:
            response = self.get(path, retry=False, with_apikey=False)
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def __repr__(self) -> str:
        """String representation of HttpClient."""
        return (
            f"HttpClient(max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}s, timeout={self.timeout}s, "
            f"jwt_token={'set' if self.jwt_token else 'not set'})"
        )


# Singleton instance for convenience
_default_client: Optional[HttpClient] = None


def get_client(force_reload: bool = False) -> HttpClient:
    """
    Get default HTTP client instance (singleton pattern).
    
    Returns:
        Shared HttpClient instance
    """
    global _default_client
    
    if _default_client is None or force_reload:
        _default_client = HttpClient()
    
    return _default_client