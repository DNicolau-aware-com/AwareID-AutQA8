"""
Add device to enrollment.

Adds device fingerprint information to an enrollment session.
Supports device ID and optional public key for device binding.
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
    from autqa.services.enrollment_service import EnrollmentService
    from autqa.utils.cli import add_common_arguments, add_enrollment_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, get_enrollment_token
    from autqa.utils.errors import require_env
    from autqa.utils.logger import setup_logging, get_logger
    from autqa.utils.payload_builders import build_device_fingerprint
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None

from client import post


def add_device(
    enrollment_token: str,
    device_id: str,
    public_key: Optional[str] = None,
    platform: str = "web",
    browser: Optional[str] = None,
    os: Optional[str] = None,
    additional_data: Optional[Dict] = None,
) -> Dict[str, any]:
    """
    Add device information to enrollment.
    
    Args:
        enrollment_token: Enrollment token from initiate_enrollment
        device_id: Unique device identifier
        public_key: Optional public key for device binding
        platform: Platform type (web, mobile, desktop)
        browser: Browser name and version
        os: Operating system
        additional_data: Additional device metadata
    
    Returns:
        Response dictionary
        
    Raises:
        Exception: If device addition fails
        
    Example:
        result = add_device(
            enrollment_token="abc123",
            device_id="samsung001",
            platform="mobile",
            os="Android 12"
        )
    """
    if not enrollment_token:
        raise ValueError("enrollment_token is required")
    
    if not device_id:
        raise ValueError("device_id is required")
    
    # Build payload
    payload = {
        "enrollmentToken": enrollment_token,
        "deviceId": device_id,
    }
    
    # Add optional fields
    if public_key:
        payload["publicKey"] = public_key
    
    if platform:
        payload["platform"] = platform
    
    if browser:
        payload["browser"] = browser
    
    if os:
        payload["os"] = os
    
    if additional_data:
        payload.update(additional_data)
    
    print(f"[INFO] POST /onboarding/enrollment/addDevice")
    print(f"[INFO] Device ID: {device_id}")
    print(f"[INFO] Platform: {platform}")
    
    if logger:
        logger.info(f"Adding device {device_id} to enrollment")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Send request
    resp = post("/onboarding/enrollment/addDevice", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Add device failed: {resp.status_code}"
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
    
    print(f"✅ Device added successfully")
    if logger:
        logger.info("✓ Device added successfully")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Add device information to enrollment"
    )
    
    if FRAMEWORK_AVAILABLE:
        add_common_arguments(parser)
        add_enrollment_arguments(parser)
    else:
        parser.add_argument("--env-file", type=Path, help="Path to .env file")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--test", action="store_true", help="Run in test mode")
        parser.add_argument("--enrollment-token", type=str, help="Enrollment token")
    
    parser.add_argument(
        "--device-id",
        type=str,
        help="Unique device identifier (uses .env if not provided)",
    )
    
    parser.add_argument(
        "--public-key",
        type=str,
        help="Public key for device binding",
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
        
        # Get enrollment token
        if args.enrollment_token:
            enrollment_token = args.enrollment_token
        else:
            enrollment_token = env.get("ETOKEN") or env.get("ENROLLMENT_TOKEN")
        
        if not enrollment_token:
            print("[ERROR] Missing enrollment token (ETOKEN)")
            print("Please run initiate_enrollment.py first or provide --enrollment-token")
            sys.exit(1)
        
        # Get device ID
        device_id = args.device_id or env.get("DEVICE_ID") or "samsung001"
        
        # Get optional fields
        public_key = args.public_key or env.get("PUBLIC_KEY")
        browser = args.browser or env.get("BROWSER")
        os_info = args.os or env.get("OS")
        
        if FRAMEWORK_AVAILABLE:
            print_section("Add Device to Enrollment")
        else:
            print("\n" + "=" * 60)
            print("ADD DEVICE TO ENROLLMENT")
            print("=" * 60 + "\n")
        
        # Add device
        result = add_device(
            enrollment_token=enrollment_token,
            device_id=device_id,
            public_key=public_key,
            platform=args.platform,
            browser=browser,
            os=os_info,
        )
        
        # Display result
        print("\n" + "=" * 60)
        print("DEVICE ADDITION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save device ID to .env for verification later
        if FRAMEWORK_AVAILABLE:
            try:
                store = EnvStore(env_path)
                store.set("DEVICE_ID", device_id)
                print(f"[INFO] Saved DEVICE_ID to .env")
                if logger:
                    logger.info(f"Saved DEVICE_ID={device_id} to .env")
            except Exception as e:
                print(f"[WARNING] Failed to save DEVICE_ID: {e}")
        else:
            # Fallback save
            try:
                lines = env_path.read_text(encoding='utf-8').splitlines()
                found = False
                for i, line in enumerate(lines):
                    if line.startswith("DEVICE_ID="):
                        lines[i] = f"DEVICE_ID={device_id}"
                        found = True
                        break
                if not found:
                    lines.append(f"DEVICE_ID={device_id}")
                env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
                print(f"[INFO] Saved DEVICE_ID to .env")
            except Exception as e:
                print(f"[WARNING] Could not save DEVICE_ID: {e}")
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        print("✓ Device addition completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Device addition failed: {e}")
        if logger:
            logger.exception("Device addition failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_add_device(
    enrollment_token: Optional[str] = None,
    device_id: Optional[str] = None,
    platform: str = "web",
) -> APITestResult:
    """
    Test the add device endpoint.
    
    Args:
        enrollment_token: Override enrollment token (uses env if None)
        device_id: Override device ID (uses env if None)
        platform: Platform type
    
    Returns:
        APITestResult object
        
    Example:
        result = test_add_device(device_id="test_device_123")
        assert result.success
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    import time
    
    result = APITestResult(test_name="Add Device")
    result.endpoint = "/onboarding/enrollment/addDevice"
    
    try:
        # Load settings from .env
        env = load_env()
        
        # Get enrollment token
        if enrollment_token is None:
            enrollment_token = get_enrollment_token(env)
        
        if not enrollment_token:
            result.add_error("No enrollment token available")
            return result
        
        # Get device ID
        if device_id is None:
            device_id = env.get("DEVICE_ID") or "test_device_pytest"
        
        # Execute device addition
        start_time = time.time()
        
        response_data = add_device(
            enrollment_token=enrollment_token,
            device_id=device_id,
            platform=platform,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Store metadata
        result.add_metadata("device_id", device_id)
        result.add_metadata("platform", platform)
        
        logger.info(f"✓ Add device test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Add device test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_add_device))
    else:
        main()