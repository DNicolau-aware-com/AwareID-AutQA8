"""
Token management service.

Handles OAuth token retrieval, caching, and refresh.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from autqa.core.env_store import EnvStore
from autqa.core.config import get_settings, default_env_path
from autqa.utils.errors import ConfigurationError, APIError

logger = logging.getLogger(__name__)


class TokenService:
    """
    Service for OAuth token management.
    
    Handles token retrieval, caching, and automatic refresh.
    
    Example:
        service = TokenService()
        token = service.get_token()
        # Token is automatically cached and reused
    """
    
    def __init__(self, env_store: Optional[EnvStore] = None):
        """
        Initialize token service.
        
        Args:
            env_store: Optional env store (uses default if None)
        """
        self.env_store = env_store or EnvStore(default_env_path())
        self._token_cache: Optional[str] = None
        self._token_expiry: Optional[float] = None
        logger.debug("Initialized TokenService")
    
    def retrieve_new_token(self) -> str:
        """
        Retrieve a new OAuth token from the auth server.
        
        Returns:
            Access token
            
        Raises:
            ConfigurationError: If OAuth settings are missing
            APIError: If token retrieval fails
        """
        from generated.retrieve_token import retrieve_token
        
        settings = get_settings()
        
        # Validate OAuth configuration
        if not settings.has_oauth_auth():
            raise ConfigurationError(
                "OAuth authentication not configured. "
                "Please set CLIENT_ID, CLIENT_SECRET, and REALM_NAME in .env"
            )
        
        logger.info("Retrieving new OAuth token")
        
        # Retrieve token
        token_data = retrieve_token(
            base_url=settings.baseurl,
            realm_name=settings.realm_name,
            client_id=settings.client_id,
            client_secret=settings.client_secret,
        )
        
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 300)  # Default 5 minutes
        
        # Cache token and expiry time
        self._token_cache = access_token
        self._token_expiry = time.time() + expires_in
        
        # Save to .env
        self.env_store.set("JWT", access_token)
        logger.info(f"Token cached (expires in {expires_in}s)")
        
        return access_token
    
    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get valid OAuth token (cached or new).
        
        Automatically retrieves new token if cache is expired.
        
        Args:
            force_refresh: If True, always retrieve new token
        
        Returns:
            Valid access token
            
        Example:
            token = service.get_token()
            # Use token in API calls
        """
        # Check if we need a new token
        needs_refresh = (
            force_refresh
            or self._token_cache is None
            or self._token_expiry is None
            or time.time() >= self._token_expiry - 60  # Refresh 1 minute early
        )
        
        if needs_refresh:
            logger.debug("Token cache expired or force refresh requested")
            return self.retrieve_new_token()
        
        logger.debug("Using cached token")
        return self._token_cache
    
    def get_token_from_env(self) -> Optional[str]:
        """
        Get token from .env file.
        
        Returns:
            JWT token or None if not found
        """
        return self.env_store.get("JWT") or None
    
    def ensure_token(self) -> str:
        """
        Ensure valid token exists (from cache, .env, or retrieve new).
        
        Returns:
            Valid access token
        """
        # Try cache first
        if self._token_cache and self._token_expiry:
            if time.time() < self._token_expiry - 60:
                logger.debug("Using cached token")
                return self._token_cache
        
        # Try .env
        token = self.get_token_from_env()
        if token:
            logger.debug("Using token from .env")
            # Cache it (assume valid for 5 minutes)
            self._token_cache = token
            self._token_expiry = time.time() + 300
            return token
        
        # Retrieve new token
        logger.info("No valid token found, retrieving new one")
        return self.retrieve_new_token()
    
    def clear_token_cache(self) -> None:
        """Clear cached token."""
        logger.info("Clearing token cache")
        self._token_cache = None
        self._token_expiry = None
    
    def is_token_expired(self) -> bool:
        """
        Check if cached token is expired.
        
        Returns:
            True if token is expired or not cached
        """
        if self._token_expiry is None:
            return True
        return time.time() >= self._token_expiry


# Singleton instance
_token_service: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """
    Get default token service instance (singleton).
    
    Returns:
        Shared TokenService instance
    """
    global _token_service
    
    if _token_service is None:
        _token_service = TokenService()
    
    return _token_service