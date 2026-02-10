"""
HTTP client for AwareID API communication.

Handles token caching, header construction, and request execution with
centralized configuration loading from .env file.
"""

import os
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests
from dotenv import dotenv_values


# --- Environment loading ---
_DOTENV: Dict[str, str] = dotenv_values()


def _get_env(key_upper: str, alt_keys: tuple = ()) -> Optional[str]:
    """
    Safely fetch environment variable from .env or system.
    
    Checks .env first (case-insensitive), then system environment.
    Supports alternate key names for flexibility.
    
    Args:
        key_upper: Primary environment variable name (uppercase).
        alt_keys: Alternative key names to check.
    
    Returns:
        Environment variable value or None if not found.
    """
    key_lower = key_upper.lower()

    # 1. Check lowercase in .env
    if key_lower in _DOTENV:
        return _DOTENV[key_lower]

    # 2. Check uppercase in .env
    if key_upper in _DOTENV:
        return _DOTENV[key_upper]

    # 3. Check alternate keys in .env
    for alt_key in alt_keys:
        if alt_key in _DOTENV:
            return _DOTENV[alt_key]
        if alt_key.lower() in _DOTENV:
            return _DOTENV[alt_key.lower()]

    # 4. Fallback to system environment
    if key_lower in os.environ:
        return os.environ[key_lower]
    if key_upper in os.environ:
        return os.environ[key_upper]

    # 5. Check system environment with alternate keys
    for alt_key in alt_keys:
        if alt_key in os.environ or alt_key.lower() in os.environ:
            return os.getenv(alt_key) or os.getenv(alt_key.lower())

    return None


# --- Configuration ---
BASEURL: Optional[str] = _get_env("BASEURL", ("baseUrl",)) or None
APIKEY: Optional[str] = _get_env("APIKEY", ("apikey",))
JWT: Optional[str] = _get_env("JWT", ("jwt",))
CLIENT_ID: Optional[str] = _get_env("CLIENT_ID", ("client_id",))
CLIENT_SECRET: Optional[str] = _get_env("CLIENT_SECRET", ("client_secret",))
REALM: Optional[str] = _get_env("REALM_NAME", ("realm_name",))


# --- Utilities ---
def build_url(path: str) -> str:
    """
    Construct full URL from BASEURL and relative path.
    
    Args:
        path: Relative path or full URL.
    
    Returns:
        Full URL string.
    
    Raises:
        ValueError: If BASEURL is not configured.
    """
    if not BASEURL:
        raise ValueError("BASEURL not configured in .env or environment")
    
    if path.startswith(("http://", "https://")):
        return path
    
    return urljoin(BASEURL.rstrip("/") + "/", path.lstrip("/"))


def retrieve_token() -> Optional[str]:
    """
    Retrieve OAuth2 access token using client credentials.
    
    Caches token in module-level JWT variable to avoid repeated requests.
    Requires CLIENT_ID, CLIENT_SECRET, REALM, and BASEURL in environment.
    
    Returns:
        Access token string or None if retrieval fails.
    """
    global JWT

    # Return cached token if available
    if JWT:
        return JWT

    # Validate required configuration
    if not all([CLIENT_ID, CLIENT_SECRET, REALM, BASEURL]):
        print("[ERROR] Missing required environment variables for token retrieval")
        print(f"  CLIENT_ID: {bool(CLIENT_ID)}")
        print(f"  CLIENT_SECRET: {bool(CLIENT_SECRET)}")
        print(f"  REALM: {bool(REALM)}")
        print(f"  BASEURL: {bool(BASEURL)}")
        return None

    # Construct token endpoint URL
    token_url = build_url(f"/auth/realms/{REALM}/protocol/openid-connect/token")

    # Prepare request
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid",
        "grant_type": "client_credentials",
    }
    req_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        print(f"[INFO] Requesting token from: {token_url}")
        resp = requests.post(token_url, data=data, headers=req_headers, timeout=15)
        resp.raise_for_status()

        data_resp = resp.json()
        JWT = data_resp.get("access_token")
        
        if JWT:
            print("[INFO] Token retrieved successfully")
            return JWT
        else:
            print(f"[ERROR] Token response missing 'access_token': {data_resp}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Token retrieval failed: {e}")
        return None


def build_headers(with_apikey: bool = True, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Build HTTP headers for API requests.
    
    Includes Content-Type, API key (if available), and Authorization token.
    Automatically retrieves and caches OAuth2 token if needed.
    
    Args:
        with_apikey: Include API key in headers. Default: True.
        extra: Additional headers to merge. Default: None.
    
    Returns:
        Dictionary of HTTP headers.
    """
    req_headers: Dict[str, str] = {"Content-Type": "application/json"}

    # Add API key if available
    if with_apikey and APIKEY:
        req_headers["apikey"] = APIKEY

    # Retrieve token if not cached
    global JWT
    if not JWT:
        _ = retrieve_token()

    # Add Authorization header if token available
    if JWT:
        req_headers["Authorization"] = f"Bearer {JWT}"

    # Merge additional headers
    if extra:
        req_headers.update(extra)

    return req_headers


def post(
    path: str,
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    with_apikey: bool = True,
    extra_headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    """
    Send POST request with default headers and configuration.
    
    Args:
        path: Relative API path or full URL.
        json: JSON payload for request body.
        params: Query parameters.
        with_apikey: Include API key in headers. Default: True.
        extra_headers: Additional headers to include.
    
    Returns:
        requests.Response object.
    
    Raises:
        ValueError: If URL construction fails.
        requests.RequestException: On network or HTTP errors.
    """
    try:
        url = build_url(path)
        h = build_headers(with_apikey=with_apikey, extra=extra_headers)
        print(f"[INFO] POST {url}")
        return requests.post(url, json=json, params=params, headers=h, timeout=15)
    except Exception as e:
        print(f"[ERROR] POST request failed: {e}")
        raise


def get(path: str, params: Optional[Dict[str, Any]] = None, with_apikey: bool = True, extra_headers: Optional[Dict[str, str]] = None) -> requests.Response:
    """
    Send GET request with default headers and configuration.
    
    Args:
        path: Relative API path or full URL.
        params: Query parameters.
        with_apikey: Include API key in headers. Default: True.
        extra_headers: Additional headers to include.
    
    Returns:
        requests.Response object.
    
    Raises:
        ValueError: If URL construction fails.
        requests.RequestException: On network or HTTP errors.
    """
    try:
        url = build_url(path)
        h = build_headers(with_apikey=with_apikey, extra=extra_headers)
        print(f"[INFO] GET {url}")
        return requests.get(url, params=params, headers=h, timeout=15)
    except Exception as e:
        print(f"[ERROR] GET request failed: {e}")
        raise
