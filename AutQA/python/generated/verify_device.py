"""
Verify device for authentication.

Uses the authentication token (AUTHTOKEN) from initiate_authentication
to verify device fingerprint and complete device-based authentication.
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


def verify_device(
    auth_token: str,
    device_id: str,
    platform: str = "web",
    browser: Optional[str] = None,
    os: Optional[str] = None,
    additional_data: Optional[Dict] = None,
) -> Dict[str, any]:
    """
    Verify device for authentication.
    
    Args:
        auth_token: Authentication token from initiate_authentication
        device_id: Device identifier (should match enrollment device)
        platform: Platform type (web, mobile, desktop)
        browser: Browser name and version
        os: Operating system
        additional_data: Additional device metadata
    
    Returns:
        Response dictionary with verification result
        
    Raises:
        Exception: If device verification fails
        
    Example:
        result = verify_device(
            auth_token="abc123",
            device_id="samsung001",
            platform="mobile",
            os="Android 12"
        )
        verified = result.get("verified")
    """
    if not auth_token:
        raise ValueError("auth_token is required")
    
    if not device_id:
        raise ValueError("device_id is required")
    
    # Build payload
    payload = {
        "deviceId": device_id,
    }
    
    # Add optional fields
    if platform:
        payload["platform"] = platform
    
    if browser:
        payload["browser"] = browser
    
    if os:
        payload["os"] = os
    
    if additional_data:
        payload.update(additional_data)
    
    print(f"[INFO] POST /onboarding/authentication/verifyDevice")
    print(f"[INFO] Device ID: {device_id}")
    print(f"[INFO] Platform: {platform}")
    
    if logger:
        logger.info(f"Verifying device {device_id}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Send request with AUTHTOKEN header
    resp = post(
        "/onboarding/authentication/verifyDevice",
        json=payload,
        extra_headers={"AUTHTOKEN": auth_token}
    )
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Device verification failed: {resp.status_code}"
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
    
    # Check verification result
    verified = data.get("verified", False)
    
    if verified:
        print(f"\n✅ Device verified successfully!")
        if logger:
            logger.info("✓ Device verified successfully")
    else:
        print(f"\n⚠️ Device verification failed")
        if logger:
            logger.warning("Device verification failed")
    
    # Display verification details
    if "verificationResult" in data:
        print(f"   Verification Result: {data['verificationResult']}")
    
    if "matchScore" in data:
        print(f"   Match Score: {data['matchScore']}")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify device for authentication"
    )
    
    if FRAMEWORK_AVAILABLE:
        add_common_arguments(parser)
    else:
        parser.add_argument("--env-file", type=Path, help="Path to .env file")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--test", action="store_true", help="Run in test mode")
    
    parser.add_argument(
        "--auth-token",
        type=str,
        help="Authentication token (uses AUTHTOKEN from .env if not provided)",
    )
    
    parser.add_argument(
        "--device-id",
        type=str,
        help="Device identifier (uses DEVICE_ID from .env if not provided)",
    )
    
    parser.add_argument(
        "--platform",
        type=str,
        default="web",
        choices=["web", "mobile", "desktop"],
        help="Platform type (default: web)",
    )
    
    parser.add_argument(
        "--browser",
        type=str,
        help="Browser name and version",
    )
    
    parser.add_argument(
        "--os",
        type=str,
        help="Operating system",
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
        
        # Get auth token
        if args.auth_token:
            auth_token = args.auth_token
        else:
            auth_token = env.get("AUTHTOKEN") or env.get("AUTH_TOKEN")
        
        if not auth_token:
            print("[ERROR] No authentication token found")
            print("Please run initiate_authentication.py first or provide --auth-token")
            sys.exit(1)
        
        # Get device ID
        if args.device_id:
            device_id = args.device_id
        else:
            device_id = env.get("DEVICE_ID")
        
        if not device_id:
            print("[ERROR] No device ID provided")
            print("Please provide --device-id or set DEVICE_ID in .env")
            sys.exit(1)
        
        # Get optional parameters
        browser = args.browser or env.get("BROWSER")
        os_info = args.os or env.get("OS")
        
        if FRAMEWORK_AVAILABLE:
            print_section("Verify Device")
        else:
            print("\n" + "=" * 60)
            print("VERIFY DEVICE")
            print("=" * 60 + "\n")
        
        print(f"Device ID: {device_id}")
        print(f"Platform: {args.platform}\n")
        
        # Verify device
        result = verify_device(
            auth_token=auth_token,
            device_id=device_id,
            platform=args.platform,
            browser=browser,
            os=os_info,
        )
        
        # Display result
        print("\n" + "=" * 60)
        print("VERIFICATION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        # Check if verified
        if result.get("verified"):
            print("✓ Device verification completed successfully\n")
        else:
            print("⚠️ Device verification failed\n")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] Device verification failed: {e}")
        if logger:
            logger.exception("Device verification failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def verify_device(
    auth_token: str,
    device_id: str,
    platform: str = "web",
    browser: Optional[str] = None,
    os: Optional[str] = None,
    additional_data: Optional[Dict] = None,
) -> Dict[str, any]:
    """Verify device for authentication."""
    
    if not auth_token:
        raise ValueError("auth_token is required")
    
    if not device_id:
        raise ValueError("device_id is required")
    
    # Build payload
    payload = {"deviceId": device_id}
    
    if platform:
        payload["platform"] = platform
    if browser:
        payload["browser"] = browser
    if os:
        payload["os"] = os
    if additional_data:
        payload.update(additional_data)
    
    print(f"[INFO] POST /onboarding/authentication/verifyDevice")
    print(f"[INFO] Device ID: {device_id}")
    print(f"[INFO] Platform: {platform}")
    
    if logger:
        logger.info(f"Verifying device {device_id}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    print("\nPayload:")
    print(json.dumps(payload, indent=2))
    print()
    
        # Send request with AUTHTOKEN header
    

    payload["authToken"] = auth_token
    
    resp = post("/onboarding/authentication/verifyDevice", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Device verification failed: {resp.status_code}"
        print(f"[ERROR] {error_msg}")
        try:
            error_data = resp.json()
            print(json.dumps(error_data, indent=2))
        except:
            print(resp.text)
        if logger:
            logger.error(f"{error_msg} - {resp.text}")
        raise Exception(f"{error_msg}")
    
    # Parse response
    try:
        data = resp.json()
    except Exception as e:
        raise Exception(f"Failed to parse response: {e}")
    
    # Check verification result
    verified = data.get("verified", False)
    
    if verified:
        print(f"\n✅ Device verified successfully!")
        if logger:
            logger.info("✓ Device verified successfully")
    else:
        print(f"\n⚠️ Device verification failed")
        if logger:
            logger.warning("Device verification failed")
    
    # Display details
    if "verificationResult" in data:
        print(f"   Verification Result: {data['verificationResult']}")
    
    if "matchScore" in data:
        print(f"   Match Score: {data['matchScore']}")
    
    return data  