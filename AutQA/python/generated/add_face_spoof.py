"""
Add face video frames with spoof detection via /onboarding/enrollment/addFace endpoint.

This script sends face frames with intentional spoof attempts to test anti-spoofing
capabilities. Typically uses a mix of legitimate and spoof images.

Workflow patterns:
- [legitimate, legitimate, spoof] - Test spoof detection
- [spoof, spoof, spoof] - Test full spoof rejection
- [legitimate, spoof, legitimate] - Test mixed scenarios
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
    from autqa.core.test_runner import APITestResult, run_single_test
    from autqa.services.enrollment_service import EnrollmentService
    from autqa.utils.cli import add_common_arguments, add_enrollment_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, get_enrollment_token, get_face_image, get_env, save_registration_code
    from autqa.utils.errors import require_env
    from autqa.utils.logger import setup_logging, get_logger
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None
    
    # Fallback implementation
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

# Try to import or use fallback
try:
    from autqa.utils.payload_builders import build_face_frame_object
except ImportError:
    pass  # Use fallback defined above


def collect_face_frames_with_spoof(
    legitimate_image: Optional[str] = None,
    spoof_image: Optional[str] = None,
    pattern: str = "legit-legit-spoof",
    env: Optional[Dict[str, str]] = None,
) -> Optional[List[Dict]]:
    """
    Collect face frame objects with spoof detection testing.
    
    Creates frames according to the specified pattern to test anti-spoofing.
    
    Args:
        legitimate_image: Base64 legitimate face image (loads from FACE if None)
        spoof_image: Base64 spoof image (loads from SPOOF if None)
        pattern: Frame pattern - options:
            - "legit-legit-spoof": [legitimate, legitimate, spoof]
            - "spoof-spoof-spoof": [spoof, spoof, spoof]
            - "legit-spoof-legit": [legitimate, spoof, legitimate]
            - "all-legit": [legitimate, legitimate, legitimate] (control)
        env: Environment variables dict (loads from .env if None)
    
    Returns:
        List of frame objects or None if images unavailable
        
    Example:
        frames = collect_face_frames_with_spoof(pattern="legit-legit-spoof")
    """
    # Load from environment if not provided
    if env is None:
        if FRAMEWORK_AVAILABLE:
            env = load_env()
        else:
            env = dotenv_values(_ROOT / ".env")
    
    # Get legitimate face image
    if legitimate_image is None:
        if FRAMEWORK_AVAILABLE:
            legitimate_image = get_face_image(env)
        else:
            legitimate_image = env.get("SPOOF", "").strip()
    
    if not legitimate_image:
        print("[ERROR] No legitimate face image provided. Set FACE environment variable.")
        if logger:
            logger.error("No legitimate face image provided")
        return None
    
    print(f"[INFO] Loaded legitimate face image ({len(legitimate_image)} chars)")
    if logger:
        logger.debug(f"Loaded legitimate face image ({len(legitimate_image)} chars)")
    
    # Get spoof image
    if spoof_image is None:
        spoof_image = env.get("SPOOF", "").strip()
    
    if not spoof_image:
        print("[ERROR] No spoof image provided. Set SPOOF environment variable.")
        if logger:
            logger.error("No spoof image provided")
        return None
    
    print(f"[INFO] Loaded spoof image ({len(spoof_image)} chars)")
    if logger:
        logger.debug(f"Loaded spoof image ({len(spoof_image)} chars)")
    
    # Create frames based on pattern
    now_ms = int(time.time() * 1000)
    frames = []
    
    if pattern == "legit-legit-spoof":
        frames = [
            build_face_frame_object(spoof_image, timestamp=now_ms),
            build_face_frame_object(legitimate_image, timestamp=now_ms + 30),
            build_face_frame_object(spoof_image, timestamp=now_ms + 60),
        ]
        frame_labels = ["SPOOF", "LEGITIMATE", "SPOOF"]
    
    elif pattern == "spoof-spoof-spoof":
        frames = [
            build_face_frame_object(spoof_image, timestamp=now_ms),
            build_face_frame_object(spoof_image, timestamp=now_ms + 30),
            build_face_frame_object(spoof_image, timestamp=now_ms + 60),
        ]
        frame_labels = ["SPOOF", "SPOOF", "SPOOF"]
    
    elif pattern == "legit-spoof-legit":
        frames = [
            build_face_frame_object(legitimate_image, timestamp=now_ms),
            build_face_frame_object(spoof_image, timestamp=now_ms + 30),
            build_face_frame_object(legitimate_image, timestamp=now_ms + 60),
        ]
        frame_labels = ["LEGITIMATE", "SPOOF", "LEGITIMATE"]
    
    elif pattern == "all-legit":
        frames = [
            build_face_frame_object(legitimate_image, timestamp=now_ms),
            build_face_frame_object(legitimate_image, timestamp=now_ms + 30),
            build_face_frame_object(legitimate_image, timestamp=now_ms + 60),
        ]
        frame_labels = ["LEGITIMATE", "LEGITIMATE", "LEGITIMATE"]
    
    else:
        print(f"[ERROR] Unknown pattern: {pattern}")
        return None
    
    print(f"[INFO] Created {len(frames)} frames with pattern: {pattern}")
    print(f"[INFO] Frame sequence: {frame_labels}")
    
    if logger:
        logger.info(f"Created {len(frames)} frames with pattern: {pattern}")
        logger.info(f"Frame sequence: {frame_labels}")
    
    return frames


def add_face_spoof(
    enrollment_token: str,
    face_frames: List[Dict],
    workflow: str = "charlie4",
    username: Optional[str] = None,
) -> Dict[str, any]:
    """
    Add face frames with spoof detection testing.
    
    Args:
        enrollment_token: Enrollment token
        face_frames: List of face frame objects (with spoof images)
        workflow: Workflow identifier
        username: Optional username for metadata
    
    Returns:
        Response dictionary with liveness/spoof detection results
        
    Raises:
        Exception: If face addition fails
        
    Example:
        result = add_face_spoof(
            enrollment_token="abc123",
            face_frames=spoof_frames,
            username="test_user"
        )
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
    
    print(f"[INFO] POST /onboarding/enrollment/addFace (with spoof detection)")
    print(f"[INFO] Username: {username or 'unknown_user'}")
    print(f"[INFO] Workflow: {workflow}")
    print(f"[INFO] Frames: {len(face_frames)}")
    
    if logger:
        logger.info(f"Adding {len(face_frames)} face frames with spoof detection")
        logger.debug(f"Full payload size: {len(json.dumps(payload))} bytes")
    
    # Preview payload (truncated)
    preview_payload = copy.deepcopy(payload["faceLivenessData"]["video"]["workflow_data"])
    for i, frame in enumerate(preview_payload.get("frames", [])):
        if isinstance(frame.get("data"), str):
            frame_data = frame.get("data")
            frame["data"] = frame_data[:80] + "..." if len(frame_data) > 80 else frame_data
    
    print("\nPayload Preview:")
    print(json.dumps(preview_payload, indent=2)[:1500])
    print()
    
    # Send request
    resp = post("/onboarding/enrollment/addFace", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Add face spoof failed: {resp.status_code}"
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
    
    # Display spoof detection results
    print("\n" + "=" * 60)
    print("SPOOF DETECTION RESULTS")
    print("=" * 60)
    
    if "faceLivenessResult" in data:
        liveness = data.get("faceLivenessResult", {})
        for key in ["passed", "score", "liveness_passed", "is_live", "confidence"]:
            if key in liveness:
                print(f"  {key}: {liveness.get(key)}")
    
    if "enrollmentStatus" in data:
        print(f"  enrollmentStatus: {data.get('enrollmentStatus')}")
    
    if "registrationCode" in data:
        reg_code = data.get("registrationCode")
        if reg_code:
            print(f"  registrationCode: {reg_code}")
    
    print("=" * 60)
    
    # Check for registration code
    registration_code = data.get("registrationCode")
    if registration_code:
        print(f"\n✅ Registration code received (spoof may have been accepted): {registration_code}")
        if logger:
            logger.warning(f"Registration code received despite spoof: {registration_code}")
    else:
        print(f"\n✅ No registration code (spoof likely detected)")
        if logger:
            logger.info("No registration code - spoof likely detected")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Add face frames with spoof detection (addFace with SPOOF) for enrollment"
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
        "--pattern",
        type=str,
        choices=["legit-legit-spoof", "spoof-spoof-spoof", "legit-spoof-legit", "all-legit"],
        default="legit-legit-spoof",
        help="Frame pattern for spoof testing (default: legit-legit-spoof)",
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
        
        # Collect face frames with spoof
        print("\n" + "=" * 60)
        print("COLLECTING FACE FRAMES WITH SPOOF DETECTION")
        print("=" * 60)
        print(f"Pattern: {args.pattern}")
        print()
        
        frames = collect_face_frames_with_spoof(
            pattern=args.pattern,
            env=env,
        )
        
        if not frames:
            print("[ERROR] Failed to collect face frames with spoof")
            sys.exit(1)
        
        if FRAMEWORK_AVAILABLE:
            print_section("Add Face with Spoof Detection")
        else:
            print("\n" + "=" * 60)
            print("ADD FACE WITH SPOOF DETECTION")
            print("=" * 60 + "\n")
        
        # Add face with spoof
        result = add_face_spoof(
            enrollment_token=enrollment_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
        )
        
        # Display full result
        print("\n" + "=" * 60)
        print("FULL RESPONSE")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save to output file if requested
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
            print(f"[INFO] Saved response to {args.output}")
        
        print("✓ Face spoof test completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Face spoof test failed: {e}")
        if logger:
            logger.exception("Face spoof test failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_add_face_spoof(
    enrollment_token: Optional[str] = None,
    legitimate_image: Optional[str] = None,
    spoof_image: Optional[str] = None,
    pattern: str = "legit-legit-spoof",
    workflow: str = "charlie4",
    username: Optional[str] = None,
) -> APITestResult:
    """
    Test the add face spoof endpoint.
    
    Args:
        enrollment_token: Override enrollment token (uses env if None)
        legitimate_image: Override legitimate image (uses env if None)
        spoof_image: Override spoof image (uses env if None)
        pattern: Frame pattern for testing
        workflow: Workflow identifier
        username: Username for metadata
    
    Returns:
        APITestResult object
        
    Example:
        result = test_add_face_spoof(pattern="spoof-spoof-spoof")
        assert result.success
        # Should NOT have registration code if spoof detected
        assert "registrationCode" not in result.response or not result.response["registrationCode"]
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    result = APITestResult(test_name=f"Add Face Spoof ({pattern})")
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
        
        # Collect face frames with spoof
        frames = collect_face_frames_with_spoof(
            legitimate_image=legitimate_image,
            spoof_image=spoof_image,
            pattern=pattern,
            env=env,
        )
        
        if not frames:
            result.add_error("Failed to collect face frames with spoof")
            return result
        
        # Get username
        if username is None:
            username = env.get("USERNAME", "test_user_spoof")
        
        # Execute face spoof addition
        start_time = time.time()
        
        response_data = add_face_spoof(
            enrollment_token=enrollment_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Store metadata
        result.add_metadata("pattern", pattern)
        result.add_metadata("num_frames", len(frames))
        result.add_metadata("workflow", workflow)
        
        # Check spoof detection
        has_reg_code = "registrationCode" in response_data and response_data["registrationCode"]
        result.add_metadata("registration_code_received", has_reg_code)
        
        if "faceLivenessResult" in response_data:
            liveness = response_data["faceLivenessResult"]
            result.add_metadata("liveness_result", liveness)
        
        # Validate based on pattern
        if "spoof" in pattern.lower() and has_reg_code:
            result.add_warning(f"Registration code received despite spoof in pattern: {pattern}")
        
        logger.info(f"✓ Add face spoof test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Add face spoof test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_add_face_spoof))
    else:
        main()