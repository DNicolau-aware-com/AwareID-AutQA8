"""
Add face video frames via /onboarding/enrollment/addFace endpoint.

This script sends face frames with timestamps for liveness verification.
Supports loading frames from sample files or environment variables.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import dotenv_values

# Ensure parent directory is on path for imports
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Try to import framework utilities (optional)
try:
    from autqa.core.env_store import EnvStore
    from autqa.core.test_runner import APITestResult, run_single_test, validate_registration_code
    from autqa.services.enrollment_service import EnrollmentService
    from autqa.utils.cli import add_common_arguments, add_enrollment_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, get_enrollment_token, get_face_image, get_env, save_registration_code
    from autqa.utils.errors import require_env
    from autqa.utils.logger import setup_logging, get_logger
    from autqa.utils.payload_builders import build_face_frame_object, build_face_liveness_payload
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None
    
    # Fallback implementation of build_face_frame_object
    def build_face_frame_object(base64_data: str, timestamp: Optional[int] = None) -> Dict:
        """Fallback implementation of build_face_frame_object."""
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        return {
            "data": base64_data,
            "timestamp": timestamp,
            "tags": [],
        }

from client import post


def collect_face_frames(
    face_image: Optional[str] = None,
    num_frames: int = 3,
    frame_interval_ms: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> Optional[List[Dict]]:
    """
    Collect face frame objects with timestamps for liveness verification.
    
    Loads from FACE environment variable or provided image and creates
    frames with timestamp deltas to simulate video sequence.
    
    Args:
        face_image: Base64 face image (loads from env if None)
        num_frames: Number of frames to create (default: 3)
        frame_interval_ms: Interval between frames in milliseconds (default: 30)
        env: Environment variables dict (loads from .env if None)
    
    Returns:
        List of frame objects [{"data": b64, "tags": [], "timestamp": ms}, ...]
        or None if no face image available.
        
    Example:
        frames = collect_face_frames(num_frames=5, frame_interval_ms=50)
    """
    # Load from environment if not provided
    if face_image is None:
        if env is None:
            if FRAMEWORK_AVAILABLE:
                env = load_env()
            else:
                env = dotenv_values(_ROOT / ".env")
        
        if FRAMEWORK_AVAILABLE:
            face_image = get_face_image(env)
        else:
            face_image = env.get("FACE", "").strip()
    
    if not face_image:
        print("[ERROR] No face image provided. Set FACE environment variable.")
        if logger:
            logger.error("No face image provided. Set FACE environment variable.")
        return None
    
    print(f"[INFO] Loaded face image from environment ({len(face_image)} chars)")
    if logger:
        logger.debug(f"Loaded face image from FACE environment variable ({len(face_image)} chars)")
    
    # Validate base64 (optional, but helps catch issues early)
    invalid_chars = [c for c in face_image if not (c.isalnum() or c in '+/=')]
    if invalid_chars:
        print(f"[WARNING] Base64 contains unexpected characters: {set(invalid_chars)}")
        if logger:
            logger.warning(f"Base64 contains unexpected characters: {set(invalid_chars)}")
    
    # Create frame objects with timestamps (simulating video capture)
    now_ms = int(time.time() * 1000)
    frames = []
    
    for i in range(num_frames):
        timestamp = now_ms + (i * frame_interval_ms)
        frame = build_face_frame_object(face_image, timestamp=timestamp)
        frames.append(frame)
    
    print(f"[INFO] Created {len(frames)} face frames")
    if logger:
        logger.info(f"Created {len(frames)} face frames")
    
    return frames


def add_face(
    enrollment_token: str,
    face_frames: List[Dict],
    workflow: str = "charlie4",
    username: Optional[str] = None,
) -> Dict[str, any]:
    """
    Add face liveness data to enrollment.
    
    Args:
        enrollment_token: Enrollment token from initiate_enrollment
        face_frames: List of face frame objects
        workflow: Workflow identifier (default: charlie4)
        username: Optional username for metadata
    
    Returns:
        Response dictionary containing registrationCode
        
    Raises:
        Exception: If face addition fails
        
    Example:
        result = add_face(
            enrollment_token="abc123",
            face_frames=[frame1, frame2, frame3],
            username="john_doe"
        )
        reg_code = result["registrationCode"]
    """
    if not enrollment_token:
        raise ValueError("enrollment_token is required")
    
    if not face_frames:
        raise ValueError("face_frames list cannot be empty")
    
    # Build payload
    payload = {
        "enrollmentToken": enrollment_token,
        "faceLivenessData": {
            "video": {
                "meta_data": {
                    "username": username or "unknown_user",
                },
                "workflow_data": {
                    "workflow": workflow,
                    "frames": face_frames,
                },
            },
        },
    }
    
    print(f"[INFO] POST /onboarding/enrollment/addFace")
    print(f"[INFO] Username: {username or 'unknown_user'}")
    print(f"[INFO] Workflow: {workflow}")
    print(f"[INFO] Frames: {len(face_frames)}")
    
    if logger:
        logger.info(f"Adding {len(face_frames)} face frames to enrollment")
        logger.debug(f"Full payload size: {len(json.dumps(payload))} bytes")
    
    # Preview payload (truncated for readability)
    preview_payload = copy.deepcopy(payload["faceLivenessData"]["video"]["workflow_data"])
    for frame in preview_payload.get("frames", []):
        if isinstance(frame.get("data"), str):
            frame_data = frame.get("data")
            frame["data"] = frame_data[:80] + "..." if len(frame_data) > 80 else frame_data
    
    print("\nPayload Preview:")
    print(json.dumps(preview_payload, indent=2)[:1000])
    print()
    
    # Send request
    resp = post("/onboarding/enrollment/addFace", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Add face failed: {resp.status_code}"
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
    
    # Check for registration code and show full response if missing
    registration_code = data.get("registrationCode")
    
    if registration_code:
        print(f"✅ Registration code: {registration_code}")
        if logger:
            logger.info(f"✓ Received registration code: {registration_code}")
    else:
        # Show detailed warning with full response
        print("\n" + "⚠️" * 40)
        print("WARNING: No registration code in response")
        print("⚠️" * 40)
        
        # Check if field exists but is empty
        if "registrationCode" in data:
            print("   - Field 'registrationCode' exists but is EMPTY or NULL")
        else:
            print("   - Field 'registrationCode' is MISSING from response")
        
        # Show what fields ARE present
        print(f"\n   Fields present in response: {list(data.keys())}")
        
        # Show full response data for debugging
        print("\n" + "=" * 80)
        print("FULL RESPONSE DATA (for debugging):")
        print("=" * 80)
        print(json.dumps(data, indent=2))
        print("=" * 80)
        
        # Log warning
        if logger:
            logger.warning("No registration code in response")
            logger.debug(f"Full response: {json.dumps(data, indent=2)}")
        
        # Provide helpful context
        print("\n💡 This usually means:")
        print("   1. Enrollment is not yet complete (more steps required)")
        print("   2. Document OCR step is still pending")
        print("   3. Registration code will be provided after all required steps")
        print("=" * 80 + "\n")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Add face video frames (addFace) for enrollment"
    )
    
    if FRAMEWORK_AVAILABLE:
        add_common_arguments(parser)
        add_enrollment_arguments(parser)
    else:
        parser.add_argument("--env-file", type=Path, help="Path to .env file")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--test", action="store_true", help="Run in test mode")
        parser.add_argument("--enrollment-token", type=str, help="Enrollment token")
        parser.add_argument("--workflow", type=str, default="charlie4", help="Workflow")
        parser.add_argument("--username", type=str, help="Username")
    
    parser.add_argument(
        "--num-frames",
        type=int,
        default=3,
        help="Number of frames to create (default: 3)",
    )
    
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=30,
        help="Interval between frames in milliseconds (default: 30)",
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save registration code to .env",
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
        if hasattr(args, 'enrollment_token') and args.enrollment_token:
            enrollment_token = args.enrollment_token
        else:
            if FRAMEWORK_AVAILABLE:
                enrollment_token = get_enrollment_token(env)
                require_env(enrollment_token, "ETOKEN")
            else:
                enrollment_token = env.get("ETOKEN") or env.get("ENROLLMENT_TOKEN")
                if not enrollment_token:
                    print("[ERROR] Missing enrollment token (ETOKEN)")
                    print("Please run initiate_enrollment.py first or provide --enrollment-token")
                    sys.exit(1)
        
        # Get workflow and username
        workflow = getattr(args, 'workflow', None) or env.get("WORKFLOW", "charlie4")
        username = getattr(args, 'username', None) or env.get("USERNAME", "unknown_user")
        
        # Collect face frames
        print("\n" + "=" * 60)
        print("COLLECTING FACE FRAMES")
        print("=" * 60 + "\n")
        
        frames = collect_face_frames(
            num_frames=args.num_frames,
            frame_interval_ms=args.frame_interval,
            env=env,
        )
        
        if not frames:
            print("[ERROR] Failed to collect face frames")
            sys.exit(1)
        
        if FRAMEWORK_AVAILABLE:
            print_section("Add Face to Enrollment")
        else:
            print("\n" + "=" * 60)
            print("ADD FACE TO ENROLLMENT")
            print("=" * 60 + "\n")
        
        # Add face
        result = add_face(
            enrollment_token=enrollment_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
        )
        
        # Display result (will be shown in add_face if no reg code)
        print("\n" + "=" * 60)
        print("FACE ADDITION RESULT")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save registration code unless --no-save
        if not args.no_save:
            registration_code = result.get("registrationCode")
            if registration_code:
                if FRAMEWORK_AVAILABLE:
                    save_registration_code(registration_code, env_path)
                else:
                    # Fallback save
                    try:
                        lines = env_path.read_text(encoding='utf-8').splitlines()
                        found = False
                        for i, line in enumerate(lines):
                            if line.startswith("REGISTRATION_CODE="):
                                lines[i] = f"REGISTRATION_CODE={registration_code}"
                                found = True
                                break
                        if not found:
                            lines.append(f"REGISTRATION_CODE={registration_code}")
                        env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
                        print(f"[INFO] Saved REGISTRATION_CODE to .env")
                    except Exception as e:
                        print(f"[WARNING] Failed to save REGISTRATION_CODE: {e}")
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        print("✓ Face addition completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Face addition failed: {e}")
        if logger:
            logger.exception("Face addition failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_add_face(
    enrollment_token: Optional[str] = None,
    face_image: Optional[str] = None,
    workflow: str = "charlie4",
    username: Optional[str] = None,
    num_frames: int = 3,
) -> APITestResult:
    """
    Test the add face endpoint.
    
    Args:
        enrollment_token: Override enrollment token (uses env if None)
        face_image: Override face image (uses env if None)
        workflow: Workflow identifier
        username: Username for metadata
        num_frames: Number of frames to create
    
    Returns:
        APITestResult object
        
    Example:
        result = test_add_face(num_frames=5)
        assert result.success
        assert "registrationCode" in result.response
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    result = APITestResult(test_name="Add Face")
    result.endpoint = "/onboarding/enrollment/addFace"
    
    try:
        # Load settings from .env
        env = load_env()
        
        # Get enrollment token
        if enrollment_token is None:
            enrollment_token = get_enrollment_token(env)
        
        if not enrollment_token:
            result.add_error("No enrollment token available")
            return result
        
        # Collect face frames
        frames = collect_face_frames(
            face_image=face_image,
            num_frames=num_frames,
            env=env,
        )
        
        if not frames:
            result.add_error("Failed to collect face frames")
            return result
        
        # Get username
        if username is None:
            username = env.get("USERNAME", "test_user")
        
        # Execute face addition
        start_time = time.time()
        
        response_data = add_face(
            enrollment_token=enrollment_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Validate response
        validation_errors = validate_registration_code(response_data)
        if validation_errors:
            for error in validation_errors:
                result.add_error(error)
        
        # Store metadata
        if "registrationCode" in response_data:
            result.add_metadata("registration_code", response_data["registrationCode"])
        
        result.add_metadata("num_frames", num_frames)
        result.add_metadata("workflow", workflow)
        
        logger.info(f"✓ Add face test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Add face test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_add_face))
    else:
        main()


