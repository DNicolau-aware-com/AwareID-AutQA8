"""
Central configuration management.

Keeps all "where is the .env?" logic in one place so scripts/tests don't
need sys.path hacks. Provides project path utilities and settings management.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def python_root() -> Path:
    """
    Return the absolute path to the `python/` directory.
    
    Path resolution: <repo>/AutQA/python/autqa/core/config.py -> python/
    
    Returns:
        Path to python/ directory
    """
    return Path(__file__).resolve().parents[2]


def autqa_project_root() -> Path:
    """
    Return the absolute path to the `AutQA/` directory.
    
    Returns:
        Path to AutQA/ project root
    """
    return python_root().parent


def default_env_path() -> Path:
    """
    Default .env location used by this project.
    
    This repo stores .env inside AutQA/python/.env
    
    Returns:
        Path to .env file
    """
    return python_root() / ".env"


def get_env_path() -> Path:
    """
    Get the .env file path, checking environment variable override first.
    
    Allows using ENV_FILE environment variable to specify custom .env location.
    Useful for different environments (dev, staging, prod).
    
    Returns:
        Path to .env file (custom or default)
    
    Example:
        ENV_FILE=/path/to/custom/.env python script.py
    """
    custom_path = os.getenv("ENV_FILE")
    if custom_path:
        path = Path(custom_path)
        if path.exists():
            return path
        else:
            raise FileNotFoundError(f"Custom ENV_FILE not found: {custom_path}")
    return default_env_path()


@dataclass(frozen=True)
class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        baseurl: API base URL
        apikey: API key for authentication
        jwt: JWT token for authentication
        client_id: OAuth client ID
        client_secret: OAuth client secret
        realm_name: Authentication realm name
        environment: Environment name (dev, staging, prod)
    """
    baseurl: Optional[str] = None
    apikey: Optional[str] = None
    jwt: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    realm_name: Optional[str] = None
    environment: Optional[str] = "dev"
    
    def __post_init__(self):
        """Validate settings after initialization."""
        if not self.baseurl:
            raise ValueError("BASEURL is required in environment configuration")
    
    def is_valid(self) -> bool:
        """
        Check if settings have minimum required values.
        
        Returns:
            True if baseurl is set, False otherwise
        """
        return bool(self.baseurl)
    
    def has_api_key_auth(self) -> bool:
        """Check if API key authentication is configured."""
        return bool(self.apikey)
    
    def has_jwt_auth(self) -> bool:
        """Check if JWT authentication is configured."""
        return bool(self.jwt)
    
    def has_oauth_auth(self) -> bool:
        """Check if OAuth authentication is configured."""
        return bool(self.client_id and self.client_secret and self.realm_name)
    
    def get_auth_type(self) -> str:
        """
        Determine which authentication type is configured.
        
        Returns:
            "apikey", "jwt", "oauth", or "none"
        """
        if self.has_api_key_auth():
            return "apikey"
        elif self.has_jwt_auth():
            return "jwt"
        elif self.has_oauth_auth():
            return "oauth"
        else:
            return "none"


def load_settings(env: dict) -> Settings:
    """
    Build a Settings object from an environment dict.
    
    Args:
        env: Dictionary of environment variables (e.g., from EnvStore.read())
    
    Returns:
        Settings object with configuration values
    
    Example:
        from autqa.core.env_store import EnvStore
        env = EnvStore.read()
        settings = load_settings(env)
    """
    def pick(*keys: str) -> Optional[str]:
        """
        Pick the first non-empty value from env dict for given keys.
        
        Checks both uppercase and lowercase variants.
        
        Args:
            *keys: Key names to check in priority order
        
        Returns:
            First non-empty value found, or None
        """
        for k in keys:
            # Check exact key
            v = env.get(k)
            if v:
                return v.strip()
            # Check lowercase variant
            v = env.get(k.lower())
            if v:
                return v.strip()
        return None

    return Settings(
        baseurl=pick("BASEURL", "baseUrl", "BASE_URL"),
        apikey=pick("APIKEY", "apikey", "API_KEY"),
        jwt=pick("JWT", "jwt"),
        client_id=pick("CLIENT_ID", "client_id"),
        client_secret=pick("CLIENT_SECRET", "client_secret"),
        realm_name=pick("REALM_NAME", "realm_name"),
        environment=pick("ENVIRONMENT", "ENV") or "dev",
    )


def load_settings_from_file(env_path: Optional[Path] = None) -> Settings:
    """
    Load settings directly from .env file.
    
    Convenience function that combines env_store reading and settings loading.
    
    Args:
        env_path: Optional custom path to .env file
    
    Returns:
        Settings object
    
    Example:
        settings = load_settings_from_file()
        print(settings.baseurl)
    """
    from autqa.core.env_store import EnvStore
    
    path = env_path or get_env_path()
    env_store = EnvStore(path)  
    env = env_store.read()
    return load_settings(env)


# Convenience instance for quick access
_settings_cache: Optional[Settings] = None


def get_settings(force_reload: bool = False) -> Settings:
    """
    Get cached settings instance (singleton pattern).
    
    Args:
        force_reload: If True, reload settings from file
    
    Returns:
        Cached Settings instance
    
    Example:
        from autqa.core.config import get_settings
        settings = get_settings()
        print(settings.baseurl)
    """
    global _settings_cache
    
    if _settings_cache is None or force_reload:
        _settings_cache = load_settings_from_file()
    
    return _settings_cache