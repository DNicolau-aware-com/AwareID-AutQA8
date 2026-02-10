"""
Environment variable loading utilities.

Helper functions for loading and validating environment variables.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from autqa.core.config import default_env_path
from autqa.core.env_store import EnvStore
from autqa.utils.errors import ConfigurationError

logger = logging.getLogger(__name__)


def load_env(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file (uses default if None)
    
    Returns:
        Dictionary of environment variables
        
    Example:
        env = load_env()
        api_key = env.get("APIKEY")
    """
    path = env_path or default_env_path()
    store = EnvStore(path)
    return store.read()


def get_env(key: str, env: Dict[str, str], default: str = "") -> str:
    """
    Get environment variable with default.
    
    Args:
        key: Environment variable name
        env: Environment dictionary
        default: Default value if not found
    
    Returns:
        Environment variable value or default
        
    Example:
        workflow = get_env("WORKFLOW", env, "charlie4")
    """
    return env.get(key, default).strip()


def get_required_env(key: str, env: Dict[str, str]) -> str:
    """
    Get required environment variable.
    
    Args:
        key: Environment variable name
        env: Environment dictionary
    
    Returns:
        Environment variable value
        
    Raises:
        ConfigurationError: If variable is not set
        
    Example:
        api_key = get_required_env("APIKEY", env)
    """
    value = env.get(key, "").strip()
    if not value:
        raise ConfigurationError(
            f"Required environment variable '{key}' is not set. "
            f"Please add it to your .env file."
        )
    return value


def get_enrollment_token(env: Dict[str, str]) -> Optional[str]:
    """
    Get enrollment token from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Enrollment token or None if not found
        
    Example:
        token = get_enrollment_token(env)
        if token:
            print(f"Found token: {token}")
    """
    token = env.get("ENROLLMENT_TOKEN") or env.get("ETOKEN")
    return token.strip() if token else None


def get_auth_token(env: Dict[str, str]) -> Optional[str]:
    """
    Get authentication token from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Auth token or None if not found
    """
    token = env.get("AUTH_TOKEN") or env.get("AUTHTOKEN")
    return token.strip() if token else None


def get_registration_code(env: Dict[str, str]) -> Optional[str]:
    """
    Get registration code from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Registration code or None if not found
    """
    code = env.get("REGISTRATION_CODE")
    return code.strip() if code else None


def get_face_image(env: Dict[str, str]) -> Optional[str]:
    """
    Get face image base64 from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Base64 encoded face image or None if not found
    """
    face = env.get("FACE")
    return face.strip() if face else None


def get_voice_audio(env: Dict[str, str]) -> Optional[str]:
    """
    Get voice audio base64 from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Base64 encoded voice audio or None if not found
    """
    voice = env.get("VOICE")
    return voice.strip() if voice else None


def get_document_image(env: Dict[str, str]) -> Optional[str]:
    """
    Get document image base64 from environment.
    
    Args:
        env: Environment dictionary
    
    Returns:
        Base64 encoded document image or None if not found
    """
    doc = env.get("DOCUMENT")
    return doc.strip() if doc else None


def save_enrollment_token(token: str, env_path: Optional[Path] = None) -> None:
    """
    Save enrollment token to .env file.
    
    Args:
        token: Enrollment token to save
        env_path: Optional path to .env file
        
    Example:
        save_enrollment_token("abc123")
    """
    path = env_path or default_env_path()
    store = EnvStore(path)
    store.set("ENROLLMENT_TOKEN", token)
    logger.info(f"Saved ENROLLMENT_TOKEN to {path}")


def save_auth_token(token: str, env_path: Optional[Path] = None) -> None:
    """
    Save auth token to .env file.
    
    Args:
        token: Auth token to save
        env_path: Optional path to .env file
    """
    path = env_path or default_env_path()
    store = EnvStore(path)
    store.set("AUTH_TOKEN", token)
    logger.info(f"Saved AUTH_TOKEN to {path}")


def save_registration_code(code: str, env_path: Optional[Path] = None) -> None:
    """
    Save registration code to .env file.
    
    Args:
        code: Registration code to save
        env_path: Optional path to .env file
    """
    path = env_path or default_env_path()
    store = EnvStore(path)
    store.set("REGISTRATION_CODE", code)
    logger.info(f"Saved REGISTRATION_CODE to {path}")