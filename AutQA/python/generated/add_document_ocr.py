"""
Add document with OCR via /onboarding/enrollment/addDocumentOCR endpoint.

This script sends document images to the server for full OCR processing.
Supports multiple images (front & back), file input, and environment variables.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
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
    from autqa.utils.env_loader import load_env, get_enrollment_token, get_env
    from autqa.utils.errors import require_env
    from autqa.utils.logger import setup_logging, get_logger
    FRAMEWORK_AVAILABLE = True
    logger = get_logger(__name__)
except ImportError:
    FRAMEWORK_AVAILABLE = False
    logger = None

from client import post


def normalize_base64(b64_str: str) -> str:
    """Remove whitespace and common prefixes from base64 string."""
    if not b64_str:
        return ""
    
    # Remove whitespace
    b64_str = "".join(b64_str.split())
    
    # Remove data URI prefix if present
    prefixes = ["data:image/jpeg;base64,", "data:image/png;base64,", "data:image/jpg;base64,"]
    for prefix in prefixes:
        if b64_str.startswith(prefix):
            b64_str = b64_str[len(prefix):]
    
    return b64_str


def validate_base64(b64_str: str) -> tuple[bool, str]:
    """
    Validate base64 string.
    
    Returns:
        (is_valid, error_message)
    """
    if not b64_str:
        return False, "Empty base64 string"
    
    # Check for invalid characters
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    invalid_chars = [c for c in b64_str if c not in valid_chars]
    
    if invalid_chars:
        return False, f"Invalid characters: {set(invalid_chars)}"
    
    return True, ""


def load_base64_from_file(file_path: Path) -> str:
    """Load base64 string from file."""
    content = file_path.read_text(encoding='utf-8').strip()
    return normalize_base64(content)


def add_document_ocr(
    enrollment_token: str,
    front_image: str,
    back_image: Optional[str] = None,
    format: str = "jpg",
    lighting_scheme: int = 6,
    already_cropped: bool = False,
    workflow: str = "charlie4",
    security_level: int = 4,
    minimum_age: int = 0,
    maximum_age: int = 0,
    validate_not_expired: bool = True,
) -> Dict[str, any]:
    """
    Add document with OCR processing to enrollment.
    
    Args:
        enrollment_token: Enrollment token
        front_image: Base64 encoded front image
        back_image: Optional base64 encoded back image
        format: Image format (jpg, png)
        lighting_scheme: Lighting scheme code (default: 6)
        already_cropped: Whether images are already cropped
        workflow: Liveness workflow (default: charlie4)
        security_level: Security level (default: 4)
        minimum_age: Minimum age requirement
        maximum_age: Maximum age requirement
        validate_not_expired: Whether to validate document not expired
    
    Returns:
        Response dictionary with OCR results
        
    Raises:
        Exception: If document OCR fails
        
    Example:
        result = add_document_ocr(
            enrollment_token="abc123",
            front_image="base64_front_data",
            back_image="base64_back_data",
            workflow="charlie4",
            security_level=4
        )
    """
    if not enrollment_token:
        raise ValueError("enrollment_token is required")
    
    if not front_image:
        raise ValueError("front_image is required")
    
    # Build document images array
    document_images = [
        {
            "lightingScheme": lighting_scheme,
            "image": front_image,
            "format": format,
        }
    ]
    
    if back_image:
        document_images.append({
            "lightingScheme": lighting_scheme,
            "image": back_image,
            "format": format,
        })
    
    # Build payload
    payload = {
        "enrollmentToken": enrollment_token,
        "documentsInfo": {
            "documentImage": document_images,
            "documentPayload": {
                "request": {
                    "vendor": "REGULA",
                    "data": {},
                }
            },
            "processParam": {
                "alreadyCropped": already_cropped
            }
        },
        "processingInstructions": {
            "documentValidationRules": {
                "checkLiveness": True,
                "workflow": workflow,
                "securityLevel": security_level,
                "minimumAge": minimum_age,
                "maximumAge": maximum_age,
                "validateDocumentNotExpired": validate_not_expired,
                "fieldsToValidate": []
            }
        }
    }
    
    print(f"[INFO] POST /onboarding/enrollment/addDocumentOCR")
    print(f"[INFO] Images: {len(document_images)} (front{' + back' if back_image else ' only'})")
    print(f"[INFO] Format: {format}, Lighting: {lighting_scheme}")
    print(f"[INFO] Workflow: {workflow}, Security Level: {security_level}")
    
    if logger:
        logger.info(f"Adding document OCR ({len(document_images)} images)")
        logger.debug(f"Full payload size: {len(json.dumps(payload))} bytes")
    
    # Preview payload (redacted base64)
    preview = copy.deepcopy(payload)
    for img in preview["documentsInfo"]["documentImage"]:
        img_data = img["image"]
        img["image"] = img_data[:120] + "..." if len(img_data) > 120 else img_data
    
    print("\nPayload Preview:")
    print(json.dumps(preview, indent=2))
    print()
    
    # Send request
    resp = post("/onboarding/enrollment/addDocumentOCR", json=payload)
    
    print(f"[INFO] Status: {resp.status_code}")
    if logger:
        logger.info(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        error_msg = f"Add document OCR failed: {resp.status_code}"
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
    
    # Print useful summary
    summary_keys = [
        "enrollmentStatus", "documentVerificationResult", "registrationCode",
        "icaoVerificationResult", "matchResult", "matchScore", "retryDocumentCapture"
    ]
    summary = {k: data.get(k) for k in summary_keys if k in data}
    
    if summary:
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for k, v in summary.items():
            print(f"  {k}: {v}")
        print("=" * 60)
    
    # Print OCR results if available
    if "ocrResults" in data:
        print("\n" + "=" * 60)
        print("OCR RESULTS")
        print("=" * 60)
        ocr = data.get("ocrResults", {})
        for k in ["validDocument", "mrzPresence", "rfidPresence", "documentName", "documentID"]:
            if k in ocr:
                print(f"  {k}: {ocr.get(k)}")
        print("=" * 60)
    
    # Check for registration code
    registration_code = data.get("registrationCode")
    if registration_code:
        print(f"\n✅ Registration code: {registration_code}")
        if logger:
            logger.info(f"✓ Received registration code: {registration_code}")
    else:
        print(f"\n⚠️  No registration code in response")
        if logger:
            logger.warning("No registration code in response")
    
    print(f"\n✅ Document OCR completed")
    if logger:
        logger.info("✓ Document OCR completed successfully")
    
    return data


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Add document with OCR (addDocumentOCR) for enrollment"
    )
    
    if FRAMEWORK_AVAILABLE:
        add_common_arguments(parser)
        add_enrollment_arguments(parser)  # This already adds --workflow and --username
    else:
        parser.add_argument("--env-file", type=Path, help="Path to .env file")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--test", action="store_true", help="Run in test mode")
        parser.add_argument("--enrollment-token", type=str, help="Enrollment token")
        parser.add_argument("--workflow", type=str, help="Workflow (default: charlie4)")
        parser.add_argument("--username", type=str, help="Username")
    
    parser.add_argument(
        "--front-image",
        type=Path,
        help="Path to front image file (base64 text file)",
    )
    
    parser.add_argument(
        "--back-image",
        type=Path,
        help="Path to back image file (base64 text file)",
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["jpg", "jpeg", "png"],
        help="Image format (default: jpg)",
    )
    
    parser.add_argument(
        "--lighting",
        type=int,
        help="Lighting scheme code (default: 6)",
    )
    
    parser.add_argument(
        "--already-cropped",
        action="store_true",
        help="Images are already cropped",
    )
    
    parser.add_argument(
        "--security-level",
        type=int,
        choices=[1, 2, 3, 4],
        help="Security level 1-4 (default: 4)",
    )
    
    parser.add_argument(
        "--min-age",
        type=int,
        default=0,
        help="Minimum age requirement (default: 0)",
    )
    
    parser.add_argument(
        "--max-age",
        type=int,
        default=0,
        help="Maximum age requirement (default: 0)",
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
        
        # Get front image
        if args.front_image:
            print(f"[INFO] Loading front image from file: {args.front_image}")
            front_image = load_base64_from_file(args.front_image)
        else:
            print(f"[INFO] Loading front image from .env (DAN_DOC_FRONT)")
            front_image = env.get("DAN_DOC_FRONT", "").strip()
            if not front_image:
                print("[ERROR] No front document image provided")
                print("Use --front-image or set DAN_DOC_FRONT in .env")
                sys.exit(1)
        
        # Validate front image
        front_image = normalize_base64(front_image)
        is_valid, err_msg = validate_base64(front_image)
        if not is_valid:
            print(f"[ERROR] Front image has invalid base64: {err_msg}")
            sys.exit(1)
        
        print(f"[INFO] Front image validated: {len(front_image)} characters")
        
        # Get back image (optional)
        back_image = None
        if args.back_image:
            print(f"[INFO] Loading back image from file: {args.back_image}")
            back_image = load_base64_from_file(args.back_image)
        else:
            back_image = env.get("DAN_DOC_BACK", "").strip()
            if back_image:
                print(f"[INFO] Loading back image from .env (DAN_DOC_BACK)")
        
        if back_image:
            back_image = normalize_base64(back_image)
            is_valid, err_msg = validate_base64(back_image)
            if not is_valid:
                print(f"[ERROR] Back image has invalid base64: {err_msg}")
                sys.exit(1)
            print(f"[INFO] Back image validated: {len(back_image)} characters")
        else:
            print(f"[INFO] No back image provided (optional)")
        
        # Get other parameters
        format = args.format or env.get("DOCUMENT_FORMAT", "jpg")
        lighting = args.lighting if args.lighting is not None else int(env.get("DOCUMENT_LIGHTING", "6"))
        already_cropped = args.already_cropped or env.get("DOCUMENT_ALREADY_CROPPED", "false").lower() in ("1", "true", "yes")
        workflow = getattr(args, 'workflow', None) or env.get("WORKFLOW", "charlie4")
        security_level = args.security_level if args.security_level is not None else int(env.get("DOC_SECURITY_LEVEL", "4"))
        
        if FRAMEWORK_AVAILABLE:
            print_section("Add Document OCR to Enrollment")
        else:
            print("\n" + "=" * 60)
            print("ADD DOCUMENT OCR TO ENROLLMENT")
            print("=" * 60 + "\n")
        
        # Add document OCR
        result = add_document_ocr(
            enrollment_token=enrollment_token,
            front_image=front_image,
            back_image=back_image,
            format=format,
            lighting_scheme=lighting,
            already_cropped=already_cropped,
            workflow=workflow,
            security_level=security_level,
            minimum_age=args.min_age,
            maximum_age=args.max_age,
        )
        
        # Display full result
        print("\n" + "=" * 60)
        print("FULL RESPONSE")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60 + "\n")
        
        # Save registration code to .env if present
        registration_code = result.get("registrationCode")
        if registration_code:
            try:
                if FRAMEWORK_AVAILABLE:
                    store = EnvStore(env_path)
                    store.set("REGISTRATION_CODE", registration_code)
                    print(f"[INFO] Saved REGISTRATION_CODE to .env")
                else:
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
        
        print("✓ Document OCR addition completed successfully\n")
        
    except Exception as e:
        print(f"\n[ERROR] Document OCR addition failed: {e}")
        if logger:
            logger.exception("Document OCR addition failed")
        sys.exit(1)


# ==============================================================================
# TEST MODE
# ==============================================================================

def test_add_document_ocr(
    enrollment_token: Optional[str] = None,
    front_image: Optional[str] = None,
    back_image: Optional[str] = None,
    workflow: str = "charlie4",
) -> APITestResult:
    """
    Test the add document OCR endpoint.
    
    Args:
        enrollment_token: Override enrollment token (uses env if None)
        front_image: Override front image (uses env if None)
        back_image: Override back image (uses env if None)
        workflow: Workflow identifier
    
    Returns:
        APITestResult object
        
    Example:
        result = test_add_document_ocr()
        assert result.success
        assert "registrationCode" in result.response
    """
    if not FRAMEWORK_AVAILABLE:
        print("[ERROR] Test mode requires framework modules")
        sys.exit(1)
    
    import time
    
    result = APITestResult(test_name="Add Document OCR")
    result.endpoint = "/onboarding/enrollment/addDocumentOCR"
    
    try:
        # Load settings from .env
        env = load_env()
        
        # Get enrollment token
        if enrollment_token is None:
            enrollment_token = get_enrollment_token(env)
        
        if not enrollment_token:
            result.add_error("No enrollment token available")
            return result
        
        # Get images
        if front_image is None:
            front_image = env.get("DAN_DOC_FRONT", "").strip()
        
        if not front_image:
            result.add_error("No front document image available")
            return result
        
        front_image = normalize_base64(front_image)
        
        if back_image is None:
            back_image = env.get("DAN_DOC_BACK", "").strip()
        
        if back_image:
            back_image = normalize_base64(back_image)
        
        # Execute document OCR addition
        start_time = time.time()
        
        response_data = add_document_ocr(
            enrollment_token=enrollment_token,
            front_image=front_image,
            back_image=back_image,
            workflow=workflow,
        )
        
        result.execution_time = time.time() - start_time
        result.status_code = 200
        result.response = response_data
        
        # Store metadata
        result.add_metadata("has_back_image", bool(back_image))
        result.add_metadata("workflow", workflow)
        
        if "documentVerificationResult" in response_data:
            result.add_metadata("verification_result", response_data["documentVerificationResult"])
        
        if "registrationCode" in response_data:
            result.add_metadata("registration_code", response_data["registrationCode"])
        
        logger.info(f"✓ Add document OCR test passed ({result.execution_time:.3f}s)")
        
    except Exception as e:
        result.add_error(str(e))
        logger.error(f"✗ Add document OCR test failed: {e}")
    
    return result


if __name__ == "__main__":
    # Check if running in test mode
    if "--test" in sys.argv:
        if not FRAMEWORK_AVAILABLE:
            print("[ERROR] Test mode requires framework modules")
            sys.exit(1)
        sys.exit(run_single_test(test_add_document_ocr))
    else:
        main()