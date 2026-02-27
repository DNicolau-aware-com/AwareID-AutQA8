"""
Retrieve OAuth token using client credentials.

Standalone script with minimal dependencies. Can be used independently
or integrated with the automation framework.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Try to import framework utilities (optional)
try:
    from autqa.core.env_store import EnvStore
    from autqa.core.test_runner import APITestResult, run_single_test
    from autqa.utils.logger import get_logger
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None


def retrieve_token(
    base_url: str,
    realm_name: str,
    client_id: str,
    client_secret: str,
    scope: str = "openid",
    timeout: int = 15,
) -> Dict[str, str]:
    """
    Retrieve OAuth token using client credentials.
    
    Args:
        base_url: Base URL of auth server
        realm_name: Realm name
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scope: OAuth scope (default: openid)
        timeout: Request timeout in seconds
    
    Returns:
        Token response dictionary containing access_token, token_type, expires_in, etc.
        
    Raises:
        Exception: If token retrieval fails
        
    Example:
        token_data = retrieve_token(
            base_url="https://auth.example.com",
            realm_name="myrealm",
            client_id="myclient",
            client_secret="secret123"
        )
        access_token = token_data["access_token"]
    """
    # Build token URL
    url = f"{base_url.rstrip('/')}/auth/realms/{realm_name}/protocol/openid-connect/token"
    
    print(f"[INFO] Requesting token from: {url}")
    if logger:
        logger.info(f"Requesting token from: {url}")
        logger.debug(f"Client ID: {client_id}, Realm: {realm_name}, Scope: {scope}")
    
    # Prepare request data
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope,
        'grant_type': 'client_credentials'
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        resp = requests.post(url, data=data, headers=headers, timeout=timeout)
        print(f'[INFO] Status: {resp.status_code}')
        
        if resp.status_code != 200:
            error_msg = f"Token retrieval failed: {resp.status_code}"
            print(f"[ERROR] {error_msg}")
            print(resp.text)
            
            if logger:
                logger.error(f"{error_msg} - {resp.text}")
            
            raise Exception(f"{error_msg} - {resp.text[:200]}")
        
        # Parse response
        try:
            token_data = resp.json()
        except Exception as e:
            raise Exception(f"Failed to parse token response: {e}")
        
        # Validate response
        if "access_token" not in token_data:
            raise Exception("Response missing 'access_token' field")
        
        print("[INFO] [OK] Token retrieved successfully")
        if logger:
            logger.info("[OK] Token retrieved successfully")
            if "expires_in" in token_data:
                logger.info(f"Token expires in: {token_data['expires_in']}s")
        
        return token_data
        
    except requests.exceptions.Timeout:
        error_msg = f"Request timed out after {timeout}s"
        print(f"[ERROR] {error_msg}")
        if logger:
            logger.error(error_msg)
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection failed: {e}"
        print(f"[ERROR] {error_msg}")
        if logger:
            logger.error(error_msg)
        raise Exception(error_msg)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        print(f"[ERROR] {error_msg}")
        if logger:
            logger.error(error_msg)
        raise Exception(error_msg)


def save_token_to_env(token: str, env_path: Path) -> None:
    """
    Save token to .env file as JWT.
    
    Args:
        token: Access token to save
        env_path: Path to .env file
    """
    if not env_path.exists():
        print(f"[ERROR] .env file not found: {env_path}")
        return
    
    # Use framework EnvStore if available, otherwise use simple implementation
    if FRAMEWORK_AVAILABLE:
        try:
            store = EnvStore(env_path)
            store.set("JWT", token)
            print(f"[INFO] Saved token to .env as JWT")
            if logger:
                logger.info(f"Saved token to {env_path} as JWT")
            return
        except Exception as e:
            print(f"[WARNING] Failed to use EnvStore: {e}, falling back to simple save")
    
    # Fallback: simple file manipulation
    lines = env_path.read_text(encoding='utf-8').splitlines()
    
    # Update or append JWT
    found = False
    out_lines = []
    for line in lines:
        if line.startswith("JWT="):
            out_lines.append(f"JWT={token}")
            found = True
        else:
            out_lines.append(line)
    
    if not found:
        out_lines.append(f"JWT={token}")
    
    env_path.write_text("\n".join(out_lines) + "\n", encoding='utf-8')
    print(f"[INFO] Saved token to .env as JWT")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Retrieve OAuth token using client credentials"
    )
    
    parser.add_argument(
        "--save",
        "--save-token",
        action="store_true",
        dest="save_token",
        help="Save retrieved token to .env as JWT",
    )
    
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Path to .env file (default: python/.env)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Save full token response to JSON file",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode",
    )
    
    return parser.parse_args()


def display_token_info(token_data: Dict[str, str], truncate: bool = True) -> None:
    """
    Display token information in a user-friendly format.
    
    Args:
        token_data: Token response dictionary
        truncate: Whether to truncate the access token for security
    """
    print("\n" + "=" * 60)
    print("TOKEN RETRIEVED SUCCESSFULLY")
    print("=" * 60)
    
    # Display token metadata
    if "token_type" in token_data:
        print(f"Token Type:    {token_data['token_type']}")
    
    if "expires_in" in token_data:
        expires_in = token_data['expires_in']
        print(f"Expires In:    {expires_in}s ({expires_in // 60} minutes)")
    
    if "scope" in token_data:
        print(f"Scope:         {token_data['scope']}")
    
    # Display access token (truncated for security)
    if "access_token" in token_data:
        access_token = token_data["access_token"]
        if truncate and len(access_token) > 50:
            display_token = f"{access_token[:25]}...{access_token[-25:]}"
        else:
            display_token = access_token
        print(f"Access Token:  {display_token}")
    
    print("=" * 60 + "\n")


def save_token_response(token_data: Dict[str, str], output_file: Path) -> None:
    """
    Save full token response to JSON file.
    
    Args:
        token_data: Token response dictionary
        output_file: Path to output JSON file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(token_data, indent=2), encoding='utf-8')
    print(f"[INFO] Saved full token response to {output_file}")


def main() -> None:
    """Main entry point for CLI execution."""
    args = parse_args()
    
    # Setup logging if framework is available
    if FRAMEWORK_AVAILABLE and args.verbose:
        from autqa.utils.logger import setup_logging
        setup_logging(level="DEBUG")
    
    # Determine .env path
    if args.env_file:
        env_path = args.env_file
    else:
        env_path = ROOT / '.env'
    
    # Load .env
    if not env_path.exists():
        print(f"[ERROR] .env file not found: {env_path}")
        print("Please create a .env file with the required OAuth settings")
        sys.exit(1)
    
    env = dotenv_values(env_path)
    
    # Get required settings
    BASEURL = env.get('BASEURL', '').strip()
    REALM = env.get('REALM_NAME', '').strip()
    CLIENT_ID = env.get('CLIENT_ID', '').strip()
    CLIENT_SECRET = env.get('CLIENT_SECRET', '').strip()
    
    # Validate required settings
    if not all([BASEURL, REALM, CLIENT_ID, CLIENT_SECRET]):
        print("[ERROR] Missing required environment variables:")
        print(f"  BASEURL:        {'[OK]' if BASEURL else '[MISSING]'}")
        print(f"  REALM_NAME:     {'[OK]' if REALM else '[MISSING]'}")
        print(f"  CLIENT_ID:      {'[OK]' if CLIENT_ID else '[MISSING]'}")
        print(f"  CLIENT_SECRET:  {'[OK]' if CLIENT_SECRET else '[MISSING]'}")
        print(f"\nPlease add these to your .env file: {env_path}")
        sys.exit(1)
    
    print("[INFO] OAuth Configuration:")
    print(f"  Base URL:     {BASEURL}")
    print(f"  Realm:        {REALM}")
    print(f"  Client ID:    {CLIENT_ID}")
    print(f"  Client Secret: {'*' * 8}")
    print()
    
    try:
        # Retrieve token
        token_data = retrieve_token(
            base_url=BASEURL,
            realm_name=REALM,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        
        # Display token info
        display_token_info(token_data, truncate=not args.verbose)
        
        # Save to .env if requested
        if args.save_token:
            access_token = token_data["access_token"]
            save_token_to_env(access_token, env_path)
        else:
            print("[INFO] To save token to .env, run with --save flag")
        
        # Save full response if requested
        if args.output:
            save_token_response(token_data, args.output)
        
        # Print full JSON in verbose mode
        if args.verbose:
            print("\nFull Token Response:")
            print(json.dumps(token_data, indent=2))
        
    except Exception as e:
        print(f"\n[ERROR] Failed to retrieve token: {e}")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_retrieve_token(
    base_url: Optional[str] = None,
    realm_name: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> APITestResult:
    """
    Test the token retrieval endpoint.
    
    Args:
        base_url: Override base URL (uses env if None)
        realm_name: Override realm name (uses env if None)
        client_id: Override client ID (uses env if None)
        client_secret: Override client secret (uses env if None)
    
    Returns:
        APITestResult object
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules to be available")
        sys.exit(1)
    
    import time
    
    result = APITestResult(test_name="Retrieve OAuth Token")
    result.endpoint = "/auth/realms/{realm}/protocol/openid-connect/token"
    
    try:
        # Load settings from .env
        env_path = ROOT / '.env'
        env = dotenv_values(env_path)
        
        base_url = base_url or env.get("BASEURL", "").strip()
        realm_name = realm_name or env.get("REALM_NAME", "").strip()
        client_id = client_id or env.get("CLIENT_ID", "").strip()
        client_secret = client_secret or env.get("CLIENT_SECRET", "").strip()
        
        # Validate required fields
        if not all([base_url, realm_name, client_id, client_secret]):
            result.add_error("Missing required OAuth configuration")
            return result
        
        # Execute token retrieval
        start_time = time.time()
        
        token_data = retrieve_token(
            base_url=base_url,
            realm_name=realm_name,
            client_id=client_id,
            client_secret=client_secret,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = token_data
        
        # Validate response structure
        if "access_token" not in token_data:
            result.add_error("Response missing 'access_token'")
        else:
            result.add_metadata("access_token", token_data["access_token"])
        
        if "token_type" not in token_data:
            result.add_warning("Response missing 'token_type'")
        
        if "expires_in" not in token_data:
            result.add_warning("Response missing 'expires_in'")
        
        logger.info(f"[OK] Token retrieval test passed ({result.execution_time:.3f}s)")

    except Exception as e:
        result.add_error(str(e))
        logger.error(f"[FAIL] Token retrieval test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            print("Please ensure autqa package is available")
            sys.exit(1)
        sys.exit(run_single_test(test_retrieve_token))
    else:
        main()