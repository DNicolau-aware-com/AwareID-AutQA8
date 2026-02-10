"""
Initiate enrollment process.

Creates a new enrollment session and generates an enrollment token.
Automatically generates unique usernames and saves tokens to .env.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
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
    from autqa.utils.cli import add_common_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, save_enrollment_token
    from autqa.utils.logger import setup_logging, get_logger
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None

from client import post


def generate_unique_username(base: str = "dantest") -> str:
    """
    Generate unique username with timestamp and UUID.
    
    Args:
        base: Base username prefix
    
    Returns:
        Unique username (max 50 characters)
        
    Example:
        username = generate_unique_username("testuser")
        # Returns: testuser_20250204_143022_a3f8b2
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    username = f"{base}_{timestamp}_{unique_id}"
    
    # Limit to 50 characters
    username = username[:50]
    
    return username


def initiate_enrollment(
    username: Optional[str] = None,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    generate_username: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Initiate enrollment and get enrollment token.
    
    Args:
        username: Username (auto-generated if None and generate_username=True)
        email: Email address (auto-generated if None)
        first_name: First name (uses .env or default if None)
        last_name: Last name (uses .env or default if None)
        generate_username: Whether to auto-generate username if not provided
        env: Environment variables dict (loads from .env if None)
    
    Returns:
        Response dictionary containing enrollmentToken
        
    Raises:
        Exception: If enrollment initiation fails
        
    Example:
        result = initiate_enrollment(
            username="john_doe",
            email="john@example.com"
        )
        token = result["enrollmentToken"]
    """
    # Load environment if not provided
    if env is None:
        env_path = _ROOT / ".env"
        env = dotenv_values(env_path)
    
    # Generate or use provided username
    if username is None and generate_username:
        base_user = env.get("BASE_USERNAME", "dantest")
        username = generate_unique_username(base_user)
        print(f"[INFO] Generated unique username: {username}")
        if logger:
            logger.info(f"Generated unique username: {username}")
    elif username is None:
        raise ValueError("Username is required when generate_username=False")
    
    # Generate or use provided email
    if email is None:
        email = env.get("EMAIL") or f"{username}@example.com"
    
    # Get name fields
    if first_name is None:
        first_name = env.get("FIRSTNAME") or env.get("FIRST_NAME") or "Ionel"
    
    if last_name is None:
        last_name = env.get("LASTNAME") or env.get("LAST_NAME") or "Nelu"
    
    # Build payload
    payload = {
        "username": username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name
    }
    
    print(f"[INFO] POST /onboarding/enrollment/enroll")
    print(f"[INFO] Username: {username}")
    print(f"[INFO] Email: {email}")
    
    if logger:
        logger.info(f"Initiating enrollment for {username}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Send request
    resp = post("/onboarding/enrollment/enroll", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Enrollment initiation failed: {resp.status_code}"
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
    
    # Extract enrollment token
    enrollment_token = data.get("enrollmentToken") or data.get("etoken")
    
    if not enrollment_token:
        print("[ERROR] No enrollment token in response")
        print(json.dumps(data, indent=2))
        raise Exception("Response missing enrollmentToken")
    
    print(f"\n✅ Enrollment token: {enrollment_token[:20]}...{enrollment_token[-20:]}")
    if logger:
        logger.info(f"✓ Enrollment initiated successfully")
    
    # Add username to response for convenience
    data["username"] = username
    
    return data


def save_token_and_username(username: str, token: str, env_path: Optional[Path] = None) -> None:
    """
    Save enrollment token and username to .env file.
    
    Args:
        username: Username to save
        token: Enrollment token to save
        env_path: Optional path to .env file
    """
    if env_path is None:
        env_path = _ROOT / ".env"
    
    # Use framework EnvStore if available
    if FRAMEWORK_AVAILABLE:
        try:
            store = EnvStore(env_path)
            store.set_multiple({
                "USERNAME": username,
                "ETOKEN": token,
                "ENROLLMENT_TOKEN": token,
            })
            print(f"[INFO] Saved USERNAME and ENROLLMENT_TOKEN to .env")
            if logger:
                logger.info(f"Saved USERNAME={username} and ENROLLMENT_TOKEN to .env")
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
        
        lines = update_or_add(lines, "USERNAME", username)
        lines = update_or_add(lines, "ETOKEN", token)
        lines = update_or_add(lines, "ENROLLMENT_TOKEN", token)
        
        env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
        print(f"[INFO] Saved USERNAME and ENROLLMENT_TOKEN to .env")
        
    except Exception as e:
        print(f"[WARNING] Could not update .env: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Initiate enrollment and get enrollment token"
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
        help="Username (auto-generated if not provided)",
    )
    
    parser.add_argument(
        "--email",
        type=str,
        help="Email address",
    )
    
    parser.add_argument(
        "--first-name",
        type=str,
        help="First name",
    )
    
    parser.add_argument(
        "--last-name",
        type=str,
        help="Last name",
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save token to .env",
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
        env = dotenv_values(env_path)
        
        if FRAMEWORK_AVAILABLE:
            print_section("Enrollment Initiation")
        else:
            print("\n" + "=" * 60)
            print("ENROLLMENT INITIATION")
            print("=" * 60 + "\n")
        
        # Initiate enrollment
        result = initiate_enrollment(
            username=args.username,
            email=args.email,
            first_name=args.first_name,
            last_name=args.last_name,
            generate_username=(args.username is None),
            env=env,
        )
        
        # Display result
        print("\n" + "=" * 60)
        print("ENROLLMENT RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save token and username unless --no-save
        if not args.no_save:
            enrollment_token = result.get("enrollmentToken") or result.get("etoken")
            username = result.get("username")
            
            if enrollment_token and username:
                save_token_and_username(username, enrollment_token, env_path)
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        print("✓ Enrollment initiation completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Enrollment initiation failed: {e}")
        if logger:
            logger.exception("Enrollment initiation failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_initiate_enrollment(
    username: Optional[str] = None,
    email: Optional[str] = None,
    generate_username: bool = True,
) -> APITestResult:
    """
    Test the enrollment initiation endpoint.
    
    Args:
        username: Optional username (auto-generated if None)
        email: Optional email
        generate_username: Whether to auto-generate username
    
    Returns:
        APITestResult object
        
    Example:
        result = test_initiate_enrollment()
        assert result.success
        assert "enrollmentToken" in result.response
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    result = APITestResult(test_name="Initiate Enrollment")
    result.endpoint = "/onboarding/enrollment/enroll"
    
    try:
        # Execute enrollment initiation
        start_time = time.time()
        
        response_data = initiate_enrollment(
            username=username,
            email=email,
            generate_username=generate_username,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Validate response
        if "enrollmentToken" not in response_data and "etoken" not in response_data:
            result.add_error("Response missing enrollmentToken")
        
        if "username" not in response_data:
            result.add_warning("Response missing username")
        
        # Store token in metadata
        token = response_data.get("enrollmentToken") or response_data.get("etoken")
        if token:
            result.add_metadata("enrollment_token", token)
            result.add_metadata("username", response_data.get("username"))
        
        logger.info(f"✓ Enrollment initiation test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Enrollment initiation test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_initiate_enrollment))
    else:
        main()