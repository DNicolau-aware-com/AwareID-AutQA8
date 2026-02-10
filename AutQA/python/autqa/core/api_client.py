"""
Unified API client with automatic OAuth token management.
"""

from __future__ import annotations

import logging
from typing import Optional

from autqa.api.authentication_api import AuthenticationApi
from autqa.api.enrollment_api import EnrollmentApi
from autqa.core.config import Settings, get_settings
from autqa.core.http_client import HttpClient
from autqa.services.token_service import get_token_service

logger = logging.getLogger(__name__)


class ApiClient:
    """
    Main API client with automatic OAuth token management.
    
    Automatically retrieves and injects OAuth tokens into all API requests.
    
    Example:
        api = ApiClient()
        # Token is automatically managed
        response = api.enrollment.initiate_enrollment({"username": "test"})
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        settings: Optional[Settings] = None,
        http_client: Optional[HttpClient] = None,
        auto_token: bool = True,
    ):
        """
        Initialize API client.
        
        Args:
            base_url: Optional override for base URL
            api_key: Optional override for API key
            settings: Optional Settings object
            http_client: Optional custom HTTP client
            auto_token: Whether to automatically manage OAuth tokens
        """
        if settings is None:
            settings = get_settings()
        
        self.settings = settings
        
        # Override settings if provided
        if base_url:
            self.settings = Settings(
                baseurl=base_url,
                apikey=api_key or settings.apikey,
                jwt=settings.jwt,
                client_id=settings.client_id,
                client_secret=settings.client_secret,
                realm_name=settings.realm_name,
                environment=settings.environment,
            )
        elif api_key:
            self.settings = Settings(
                baseurl=settings.baseurl,
                apikey=api_key,
                jwt=settings.jwt,
                client_id=settings.client_id,
                client_secret=settings.client_secret,
                realm_name=settings.realm_name,
                environment=settings.environment,
            )
        
        # Initialize token service if auto_token enabled
        self.auto_token = auto_token
        if auto_token and self.settings.has_oauth_auth():
            self.token_service = get_token_service()
            # Ensure we have a valid token
            token = self.token_service.ensure_token()
            logger.info("OAuth token management enabled")
        else:
            self.token_service = None
            token = self.settings.jwt
        
        # Create HTTP client with token
        if http_client is None:
            self.http_client = HttpClient(jwt_token=token)
        else:
            self.http_client = http_client
            if token:
                self.http_client.set_jwt_token(token)
        
        # Initialize API endpoint groups
        self.enrollment = EnrollmentApi(self.http_client)
        self.authentication = AuthenticationApi(self.http_client)
        
        logger.debug(
            f"Initialized ApiClient with base_url={self.settings.baseurl}, "
            f"auth_type={self.settings.get_auth_type()}, "
            f"auto_token={auto_token}"
        )
    
    def refresh_token(self) -> None:
        """
        Manually refresh OAuth token.
        
        Example:
            api.refresh_token()
        """
        if not self.token_service:
            logger.warning("Token service not initialized")
            return
        
        logger.info("Manually refreshing OAuth token")
        token = self.token_service.get_token(force_refresh=True)
        self.http_client.set_jwt_token(token)
    
    def health_check(self) -> bool:
        """Check if API is healthy."""
        return self.http_client.health_check()
    
    def get_auth_type(self) -> str:
        """Get the configured authentication type."""
        return self.settings.get_auth_type()
    
    def is_authenticated(self) -> bool:
        """Check if client has valid authentication configured."""
        auth_type = self.get_auth_type()
        return auth_type != "none"
    
    def __repr__(self) -> str:
        """String representation of API client."""
        return (
            f"ApiClient(base_url={self.settings.baseurl}, "
            f"auth_type={self.get_auth_type()}, "
            f"environment={self.settings.environment}, "
            f"auto_token={self.auto_token})"
        )
    
    # ==============================================================================
# CONVENIENCE FACTORY FUNCTIONS
# ==============================================================================

_default_client: Optional[ApiClient] = None


def get_api_client(force_reload: bool = False) -> ApiClient:
    """
    Get default API client instance (singleton pattern).
    
    Creates a single shared instance for the entire application.
    Useful for scripts and tests that don't need custom configuration.
    
    Args:
        force_reload: If True, recreate the client with fresh settings
    
    Returns:
        Shared ApiClient instance
        
    Example:
        from autqa.core.api_client import get_api_client
        
        api = get_api_client()
        response = api.enrollment.initiate_enrollment({...})
    """
    global _default_client
    
    if _default_client is None or force_reload:
        _default_client = ApiClient()
        logger.debug("Created default API client instance")
    
    return _default_client


def create_api_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    environment: Optional[str] = None,
) -> ApiClient:
    """
    Create a new API client with custom configuration.
    
    Convenience function for creating clients with specific overrides
    without needing to construct Settings objects manually.
    
    Args:
        base_url: Custom base URL
        api_key: Custom API key
        environment: Environment name (dev, staging, prod)
    
    Returns:
        New ApiClient instance
        
    Example:
        # Create client for staging environment
        staging_api = create_api_client(
            base_url="https://staging.api.com",
            api_key="staging_key_123",
            environment="staging"
        )
    """
    from autqa.core.config import get_settings, Settings
    
    settings = get_settings()
    
    # Create new settings with overrides
    custom_settings = Settings(
        baseurl=base_url or settings.baseurl,
        apikey=api_key or settings.apikey,
        jwt=settings.jwt,
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        realm_name=settings.realm_name,
        environment=environment or settings.environment,
    )
    
    return ApiClient(settings=custom_settings)