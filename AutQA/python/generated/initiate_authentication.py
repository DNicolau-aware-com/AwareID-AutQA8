"""
Initiate authentication process.

Starts an authentication session using a username from previous enrollment.
Returns an authentication token (AUTHTOKEN) used for subsequent verification steps.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from dotenv import dotenv_values

# Ensure parent directory is on path for imports
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Try to import framework utilities (optional)
try:
    from autqa.core.env_store import EnvStore
    from autqa.core.test_runner import APITestResult, run_single_test
    from autqa.services.authentication_service import AuthenticationService
    from autqa.utils.cli import add_common_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, get_env
    from autqa.utils.errors import require_env
    from autqa.utils.logger import setup_logging, get_logger
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None

from client import post


def initiate_authentication(
    username: str,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, any]:
    """
    Initiate authentication session.
    
    Args:
        username: Username to authenticate
        env: Environment variables dict (loads from .env if None)
    
    Returns:
        Response dictionary containing authToken
        
    Raises:
        Exception: If authentication initiation fails
        
    Example:
        result = initiate_authentication(username="john_doe")
        auth_token = result["authToken"]
    """
    if not username:
        raise ValueError("username is required")
    
    # Build payload
    payload = {
        "username": username
    }
    
    print(f"[INFO] POST /onboarding/authentication/authenticate")
    print(f"[INFO] Username: {username}")
    
    if logger:
        logger.info(f"Initiating authentication for {username}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Send request
    resp = post("/onboarding/authentication/authenticate", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Authentication initiation failed: {resp.status_code}"
        print(f"[ERROR] {error_msg}")
        print(resp.text)
        if logger:
            logger.error(f"{error_msg} - {resp.text}")
        raise Exception(f"{error_msg} - {resp.text[:200]}")
    
    # Parse response
    try:
        data = resp.json()
    except Exception as e:
        raise Exception(f"Failed to parse response: {e}")
    
    # Extract auth token
    auth_token = data.get("authToken")
    
    if not auth_token:
        print("[ERROR] No authToken in response")
        print(json.dumps(data, indent=2))
        raise Exception("Response missing authToken")
    
    print(f"\n✅ Authentication initiated successfully!")
    print(f"   AuthToken: {auth_token[:20]}...{auth_token[-20:]}")
    
    if logger:
        logger.info(f"✓ Authentication initiated - AuthToken: {auth_token[:20]}...")
    
    return data


def save_auth_token(auth_token: str, env_path: Optional[Path] = None) -> None:
    """
    Save authentication token to .env file.
    
    Args:
        auth_token: Authentication token to save
        env_path: Optional path to .env file
    """
    if env_path is None:
        env_path = _ROOT / ".env"
    
    # Use framework EnvStore if available
    if FRAMEWORK_AVAILABLE:
        try:
            store = EnvStore(env_path)
            store.set_multiple({
                "AUTHTOKEN": auth_token,
                "AUTH_TOKEN": auth_token,
            })
            print(f"[INFO] Saved AUTHTOKEN to .env")
            if logger:
                logger.info(f"Saved AUTHTOKEN to {env_path}")
            return
        except Exception as e:
            print(f"[WARNING] Failed to use EnvStore: {e}, falling back")
    
    # Fallback: simple file manipulation
    try:
        if not env_path.exists():
            env_path.write_text("", encoding='utf-8')
        
        lines = env_path.read_text(encoding='utf-8').splitlines()
        
        def update_or_add(lines, key, value):
            """Update existing key or append new one."""
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    return lines
            lines.append(f"{key}={value}")
            return lines
        
        lines = update_or_add(lines, "AUTHTOKEN", auth_token)
        lines = update_or_add(lines, "AUTH_TOKEN", auth_token)
        
        env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
        print(f"[INFO] Saved AUTHTOKEN to .env")
        
    except Exception as e:
        print(f"[WARNING] Could not update .env: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Initiate authentication and get authentication token"
    )
    
    if FRAMEWORK_AVAILABLE:
        add_common_arguments(parser)
    else:
        parser.add_argument("--env-file", type=Path, help="Path to .env file")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--test", action="store_true", help="Run in test mode")
    
    parser.add_argument(
        "--username",
        type=str,
        help="Username to authenticate (uses USERNAME from .env if not provided)",
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save auth token to .env",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Save response to JSON file",
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for CLI execution."""
    args = parse_args()
    
    # Setup logging if framework available
    if FRAMEWORK_AVAILABLE and hasattr(args, 'verbose'):
        setup_logging(
            level=parse_log_level(args),
            log_file=getattr(args, 'log_file', None),
        )
    
    try:
        # Load environment
        env_path = getattr(args, 'env_file', None) or _ROOT / ".env"
        
        if FRAMEWORK_AVAILABLE:
            env = load_env(env_path)
        else:
            env = dotenv_values(env_path)
        
        # Get username
        if args.username:
            username = args.username
        else:
            username = env.get("USERNAME")
        
        if not username:
            print("[ERROR] No username provided")
            print("Please provide --username or set USERNAME in .env")
            print("(USERNAME is set during enrollment)")
            sys.exit(1)
        
        if FRAMEWORK_AVAILABLE:
            print_section("Authentication Initiation")
        else:
            print("\n" + "=" * 60)
            print("AUTHENTICATION INITIATION")
            print("=" * 60 + "\n")
        
        print(f"Authenticating user: {username}\n")
        
        # Initiate authentication
        result = initiate_authentication(
            username=username,
            env=env,
        )
        
        # Display result
        print("\n" + "=" * 60)
        print("AUTHENTICATION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save auth token unless --no-save
        if not args.no_save:
            auth_token = result.get("authToken")
            if auth_token:
                save_auth_token(auth_token, env_path)
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        print("✓ Authentication initiation completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Authentication initiation failed: {e}")
        if logger:
            logger.exception("Authentication initiation failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_initiate_authentication(
    username: Optional[str] = None,
) -> APITestResult:
    """
    Test the authentication initiation endpoint.
    
    Args:
        username: Override username (uses env if None)
    
    Returns:
        APITestResult object
        
    Example:
        result = test_initiate_authentication(username="test_user")
        assert result.success
        assert "authToken" in result.response
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    import time
    
    result = APITestResult(test_name="Initiate Authentication")
    result.endpoint = "/onboarding/authentication/authenticate"
    
    try:
        # Load settings from .env
        env = load_env()
        
        # Get username
        if username is None:
            username = env.get("USERNAME")
        
        if not username:
            result.add_error("No username available (need to run enrollment first)")
            return result
        
        # Execute authentication initiation
        start_time = time.time()
        
        response_data = initiate_authentication(
            username=username,
            env=env,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Validate response
        if "authToken" not in response_data:
            result.add_error("Response missing authToken")
        
        # Store token in metadata
        auth_token = response_data.get("authToken")
        if auth_token:
            result.add_metadata("auth_token", auth_token)
            result.add_metadata("username", username)
        
        logger.info(f"✓ Authentication initiation test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Authentication initiation test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_initiate_authentication))
    else:
        main()