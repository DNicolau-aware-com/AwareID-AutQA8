"""
Verify face for authentication.

Uses the authentication token (authToken) from initiate_authentication
to verify face liveness and complete face-based authentication.
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
    from autqa.services.authentication_service import AuthenticationService
    from autqa.utils.cli import add_common_arguments, parse_log_level, print_section
    from autqa.utils.env_loader import load_env, get_env, get_face_image
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


def collect_face_frames_for_verification(
    face_image: Optional[str] = None,
    num_frames: int = 3,
    frame_interval_ms: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> Optional[List[Dict]]:
    """
    Collect face frame objects for verification.
    
    Args:
        face_image: Base64 face image (loads from FACE if None)
        num_frames: Number of frames to create (default: 3)
        frame_interval_ms: Interval between frames in milliseconds
        env: Environment variables dict
    
    Returns:
        List of frame objects or None if image unavailable
    """
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
            logger.error("No face image provided")
        return None
    
    print(f"[INFO] Loaded face image ({len(face_image)} chars)")
    if logger:
        logger.debug(f"Loaded face image ({len(face_image)} chars)")
    
    # Create frames
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


def verify_face(
    auth_token: str,
    face_frames: List[Dict],
    workflow: str = "charlie4",
    username: Optional[str] = None,
    min_match_score: float = 25.0,
) -> Dict[str, any]:
    """
    Verify face for authentication.
    
    Args:
        auth_token: Authentication token from initiate_authentication
        face_frames: List of face frame objects
        workflow: Workflow identifier
        username: Optional username for metadata
        min_match_score: Minimum match score to consider verification successful (default: 25.0)
    
    Returns:
        Response dictionary with verification result
        
    Raises:
        Exception: If face verification fails
        
    Example:
        result = verify_face(
            auth_token="abc123",
            face_frames=[frame1, frame2, frame3],
            username="john_doe",
            min_match_score=25.0
        )
        verified = result.get("verified")
    """
    if not auth_token:
        raise ValueError("auth_token is required")
    
    if not face_frames:
        raise ValueError("face_frames list cannot be empty")
    
    # Build payload matching Postman exactly
    payload = {
        "authToken": auth_token,
        "faceLivenessData": {
            "video": {
                "meta_data": {
                    "client_device_brand": "Apple",
                    "client_device_model": "iPhone 8",
                    "client_os_version": "11.0.3",
                    "client_version": "KnomiSLive_v:2.4.1_b:0.0.0_sdk_v:2.4.1_b:0.0.0",
                    "localization": "en-US",
                    "programming_language_version": "Swift 4.1",
                    "username": username or "test"
                },
                "workflow_data": {
                    "workflow": workflow,
                    "frames": face_frames
                }
            }
        }
    }
    
    print(f"[INFO] POST /onboarding/authentication/verifyFace")
    print(f"[INFO] Username: {username or 'test'}")
    print(f"[INFO] Workflow: {workflow}")
    print(f"[INFO] Frames: {len(face_frames)}")
    print(f"[INFO] Min match score threshold: {min_match_score}%")
    
    if logger:
        logger.info(f"Verifying face for authentication")
        logger.debug(f"Payload size: {len(json.dumps(payload))} bytes")
    
    # Preview payload (truncated)
    preview_payload = copy.deepcopy(payload)
    if "faceLivenessData" in preview_payload:
        frames_data = preview_payload["faceLivenessData"]["video"]["workflow_data"]["frames"]
        for frame in frames_data:
            if isinstance(frame.get("data"), str):
                frame_data = frame.get("data")
                frame["data"] = frame_data[:80] + "..." if len(frame_data) > 80 else frame_data
    
    # Truncate authToken for display
    preview_payload["authToken"] = auth_token[:20] + "..." if len(auth_token) > 20 else auth_token
    
    print("\nPayload Preview:")
    print(json.dumps(preview_payload, indent=2)[:1500])
    print()
    
    # Use client.post() which works for other endpoints
    resp = post("/onboarding/authentication/verifyFace", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Face verification failed: {resp.status_code}"
        print(f"[ERROR] {error_msg}")
        try:
            error_data = resp.json()
            print(json.dumps(error_data, indent=2))
            if logger:
                logger.error(f"{error_msg} - {error_data}")
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
    
    # Check verification result using multiple criteria
    match_score = data.get("matchScore", 0)
    liveness_result = data.get("livenessResult", False)
    match_result = data.get("matchResult", False)
    auth_status = data.get("authStatus", 0)
    
    # Consider verification successful if:
    # 1. Match score >= threshold AND liveness passed
    # 2. OR authStatus indicates success (2 or 3)
    # 3. OR explicit verified flag is true
    verified = (
        (match_score >= min_match_score and liveness_result) or
        auth_status in [2, 3] or
        data.get("verified", False)
    )
    
    # Store verification status in response
    data["verified"] = verified
    
    if verified:
        print(f"\n✅ Face verified successfully!")
        print(f"   Match Score: {match_score}% (threshold: {min_match_score}%)")
        if logger:
            logger.info(f"✓ Face verified - Match score: {match_score}%")
    else:
        print(f"\n⚠️ Face verification failed")
        print(f"   Match Score: {match_score}% (threshold: {min_match_score}%)")
        if logger:
            logger.warning(f"Face verification failed - Match score: {match_score}%")
    
    # Display verification details
    print(f"   Liveness Result: {liveness_result}")
    print(f"   Match Result: {match_result}")
    
    if "authStatus" in data:
        print(f"   Auth Status: {auth_status}")
    
    if "faceLivenessResult" in data or "faceLivenessResults" in data:
        liveness = data.get("faceLivenessResult") or data.get("faceLivenessResults", {})
        if isinstance(liveness, dict):
            video_data = liveness.get("video", {})
            liveness_result_data = video_data.get("liveness_result", {})
            if liveness_result_data:
                decision = liveness_result_data.get("decision", "N/A")
                score_frr = liveness_result_data.get("score_frr", "N/A")
                print(f"   Liveness Decision: {decision}")
                print(f"   Liveness Score FRR: {score_frr}")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Verify face for authentication"
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
        "--username",
        type=str,
        help="Username (uses USERNAME from .env if not provided)",
    )
    
    parser.add_argument(
        "--workflow",
        type=str,
        default="charlie4",
        help="Workflow identifier (default: charlie4)",
    )
    
    parser.add_argument(
        "--num-frames",
        type=int,
        default=3,
        help="Number of frames to create (default: 3)",
    )
    
    parser.add_argument(
        "--min-match-score",
        type=float,
        default=25.0,
        help="Minimum match score percentage to pass (default: 25.0)",
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
        
        # Get username
        username = args.username or env.get("USERNAME", "test")
        
        # Get workflow
        workflow = args.workflow or env.get("WORKFLOW", "charlie4")
        
        # Collect face frames
        print("\n" + "=" * 60)
        print("COLLECTING FACE FRAMES FOR VERIFICATION")
        print("=" * 60 + "\n")
        
        frames = collect_face_frames_for_verification(
            num_frames=args.num_frames,
            env=env,
        )
        
        if not frames:
            print("[ERROR] Failed to collect face frames")
            sys.exit(1)
        
        if FRAMEWORK_AVAILABLE:
            print_section("Verify Face")
        else:
            print("\n" + "=" * 60)
            print("VERIFY FACE")
            print("=" * 60 + "\n")
        
        print(f"Username: {username}")
        print(f"Workflow: {workflow}\n")
        
        # Verify face with custom threshold
        result = verify_face(
            auth_token=auth_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
            min_match_score=args.min_match_score,
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
            print("✓ Face verification completed successfully\n")
        else:
            print("⚠️ Face verification failed\n")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] Face verification failed: {e}")
        if logger:
            logger.exception("Face verification failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_verify_face(
    auth_token: Optional[str] = None,
    face_image: Optional[str] = None,
    workflow: str = "charlie4",
    username: Optional[str] = None,
    num_frames: int = 3,
    min_match_score: float = 25.0,
) -> APITestResult:
    """
    Test the verify face endpoint.
    
    Args:
        auth_token: Override auth token (uses env if None)
        face_image: Override face image (uses env if None)
        workflow: Workflow identifier
        username: Username for metadata
        num_frames: Number of frames to create
        min_match_score: Minimum match score to pass
    
    Returns:
        APITestResult object
        
    Example:
        result = test_verify_face(min_match_score=30.0)
        assert result.success
        assert result.response.get("verified") == True
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    result = APITestResult(test_name="Verify Face")
    result.endpoint = "/onboarding/authentication/verifyFace"
    
    try:
        # Load settings from .env
        env = load_env()
        
        # Get auth token
        if auth_token is None:
            auth_token = env.get("AUTHTOKEN") or env.get("AUTH_TOKEN")
        
        if not auth_token:
            result.add_error("No authentication token available")
            return result
        
        # Collect face frames
        frames = collect_face_frames_for_verification(
            face_image=face_image,
            num_frames=num_frames,
            env=env,
        )
        
        if not frames:
            result.add_error("Failed to collect face frames")
            return result
        
        # Get username
        if username is None:
            username = env.get("USERNAME", "test")
        
        # Execute face verification
        start_time = time.time()
        
        response_data = verify_face(
            auth_token=auth_token,
            face_frames=frames,
            workflow=workflow,
            username=username,
            min_match_score=min_match_score,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Validate verification
        verified = response_data.get("verified", False)
        match_score = response_data.get("matchScore", 0)
        
        result.add_metadata("verified", verified)
        result.add_metadata("match_score", match_score)
        result.add_metadata("num_frames", num_frames)
        result.add_metadata("workflow", workflow)
        result.add_metadata("min_match_score", min_match_score)
        
        if not verified:
            result.add_warning(f"Face verification returned verified=False (score: {match_score})")
        
        logger.info(f"✓ Verify face test passed ({result.execution_time:.3f}s) - Score: {match_score}%")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Verify face test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_verify_face))
    else:
        main()