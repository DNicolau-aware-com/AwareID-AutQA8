"""
Complete Test Suite for Enrollment and Authentication Flows.

Runs comprehensive end-to-end tests covering:
- Complete enrollment flow (initiate -> device -> face -> document)
- Complete authentication flow (initiate -> verify face -> verify device)
- Error handling and edge cases
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Ensure parent directory is on path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Import generated scripts
from generated.initiate_enrollment import initiate_enrollment
from generated.add_device import add_device
from generated.add_face import add_face, collect_face_frames
from generated.add_document_ocr import add_document_ocr, normalize_base64, validate_base64
from generated.initiate_authentication import initiate_authentication
from generated.verify_face import verify_face, collect_face_frames_for_verification
from generated.verify_device import verify_device

from autqa.utils.env_loader import load_env
from autqa.utils.logger import setup_logging, get_logger
from autqa.utils.timing_helpers import smart_delay

logger = get_logger(__name__)


class TestResult:
    """Container for test results."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict = {}
        self.execution_time = 0.0
    
    def add_error(self, error: str):
        """Add error message."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add warning message."""
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value):
        """Add metadata."""
        self.metadata[key] = value
    
    def mark_success(self):
        """Mark test as successful."""
        self.success = True
    
    def __str__(self):
        status = "✅ PASSED" if self.success else "❌ FAILED"
        return f"{status} - {self.test_name} ({self.execution_time:.2f}s)"


class TestSuite:
    """Main test suite runner."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.env = load_env()
        
        # Test data storage
        self.enrollment_token: Optional[str] = None
        self.username: Optional[str] = None
        self.registration_code: Optional[str] = None
        self.device_id: Optional[str] = None
        self.auth_token: Optional[str] = None
    
    def log(self, message: str):
        """Print message if verbose."""
        if self.verbose:
            print(f"  {message}")
        logger.info(message)
    
    def print_section(self, title: str):
        """Print section header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    
    def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "🚀" * 40)
        print("STARTING COMPLETE TEST SUITE")
        print("🚀" * 40)
        
        start_time = time.time()
        
        # Run enrollment flow
        self.test_complete_enrollment_flow()
        
        # Run authentication flow
        self.test_complete_authentication_flow()
        
        # Run error handling tests
        self.test_error_handling()
        
        total_time = time.time() - start_time
        
        # Print summary
        self.print_summary(total_time)
    
    def test_complete_enrollment_flow(self):
        """Test complete enrollment workflow."""
        self.print_section("TEST: COMPLETE ENROLLMENT FLOW")
        result = TestResult("Complete Enrollment Flow")
        start_time = time.time()
        
        try:
            # Step 1: Initiate enrollment
            self.log("Step 1: Initiating enrollment...")
            enrollment_result = initiate_enrollment(
                generate_username=True,
                env=self.env,
            )
            
            if not enrollment_result or "enrollmentToken" not in enrollment_result:
                result.add_error("Failed to get enrollment token")
                self.results.append(result)
                return
            
            self.enrollment_token = enrollment_result["enrollmentToken"]
            self.username = enrollment_result["username"]
            
            self.log(f"✓ Enrollment initiated - Username: {self.username}")
            result.add_metadata("username", self.username)
            result.add_metadata("enrollment_token", self.enrollment_token)
            
            smart_delay(1.0, "enrollment initialization")
            
            # Step 2: Add device
            self.log("Step 2: Adding device...")
            self.device_id = f"test_device_{int(time.time())}"
            
            device_result = add_device(
                enrollment_token=self.enrollment_token,
                device_id=self.device_id,
                platform="web",
            )
            
            if not device_result:
                result.add_error("Failed to add device")
                self.results.append(result)
                return
            
            self.log(f"✓ Device added - ID: {self.device_id}")
            result.add_metadata("device_id", self.device_id)
            
            smart_delay(1.5, "device registration")
            
            # Step 3: Add face
            self.log("Step 3: Adding face...")
            face_frames = collect_face_frames(num_frames=3, env=self.env)
            
            if not face_frames:
                result.add_error("Failed to collect face frames")
                self.results.append(result)
                return
            
            face_result = add_face(
                enrollment_token=self.enrollment_token,
                face_frames=face_frames,
                workflow="charlie4",
                username=self.username,
            )
            
            self.registration_code = face_result.get("registrationCode", "")
            self.log(f"✓ Face added - Frames: {len(face_frames)}")
            result.add_metadata("registration_code", self.registration_code)
            
            smart_delay(3.0, "face liveness analysis")
            
            # Step 4: Add document (optional)
            self.log("Step 4: Adding document OCR (if available)...")
            front_image = self.env.get("DAN_DOC_FRONT", "").strip()
            
            if front_image:
                front_image = normalize_base64(front_image)
                back_image = self.env.get("DAN_DOC_BACK", "").strip()
                if back_image:
                    back_image = normalize_base64(back_image)
                
                doc_result = add_document_ocr(
                    enrollment_token=self.enrollment_token,
                    front_image=front_image,
                    back_image=back_image,
                    workflow="charlie4",
                    security_level=4,
                )
                
                if "registrationCode" in doc_result and doc_result["registrationCode"]:
                    self.registration_code = doc_result["registrationCode"]
                
                self.log(f"✓ Document OCR completed")
                result.add_metadata("document_verified", True)
                
                smart_delay(5.0, "document OCR and enrollment finalization")
            else:
                self.log("⚠ Document images not available - skipping")
                result.add_warning("Document OCR skipped - no images in .env")
            
            # Validate final state
            if self.registration_code:
                self.log(f"✓ Enrollment complete - Registration Code: {self.registration_code}")
                result.mark_success()
            else:
                result.add_warning("No registration code received")
            
        except Exception as e:
            result.add_error(f"Enrollment flow failed: {e}")
            logger.exception("Enrollment flow error")
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        print(f"\n{result}")
    
    def test_complete_authentication_flow(self):
        """Test complete authentication workflow."""
        self.print_section("TEST: COMPLETE AUTHENTICATION FLOW")
        result = TestResult("Complete Authentication Flow")
        start_time = time.time()
        
        if not self.username:
            result.add_error("No username from enrollment - cannot test authentication")
            self.results.append(result)
            return
        
        try:
            # Step 1: Initiate authentication
            self.log(f"Step 1: Initiating authentication for {self.username}...")
            auth_result = initiate_authentication(
                username=self.username,
                env=self.env,
            )
            
            if not auth_result or "authToken" not in auth_result:
                result.add_error("Failed to get auth token")
                self.results.append(result)
                return
            
            self.auth_token = auth_result["authToken"]
            self.log(f"✓ Authentication initiated - Token: {self.auth_token[:20]}...")
            result.add_metadata("auth_token", self.auth_token)
            
            smart_delay(1.0, "authentication initialization")
            
            # Step 2: Verify face
            self.log("Step 2: Verifying face...")
            face_frames = collect_face_frames_for_verification(
                num_frames=3,
                env=self.env,
            )
            
            if not face_frames:
                result.add_error("Failed to collect face frames for verification")
                self.results.append(result)
                return
            
            face_verify_result = verify_face(
                auth_token=self.auth_token,
                face_frames=face_frames,
                workflow="charlie4",
                username=self.username,
                min_match_score=25.0,
            )
            
            face_verified = face_verify_result.get("verified", False)
            match_score = face_verify_result.get("matchScore", 0)
            
            if face_verified:
                self.log(f"✓ Face verified - Match score: {match_score}%")
                result.add_metadata("face_verified", True)
                result.add_metadata("match_score", match_score)
            else:
                result.add_error(f"Face verification failed - Score: {match_score}%")
            
            smart_delay(2.0, "face verification processing")
            
            # Step 3: Verify device (optional - if device ID available)
            if self.device_id:
                self.log(f"Step 3: Verifying device {self.device_id}...")
                
                device_verify_result = verify_device(
                    auth_token=self.auth_token,
                    device_id=self.device_id,
                    platform="web",
                )
                
                device_verified = device_verify_result.get("verified", False)
                
                if device_verified:
                    self.log(f"✓ Device verified")
                    result.add_metadata("device_verified", True)
                else:
                    result.add_warning("Device verification failed")
                    result.add_metadata("device_verified", False)
            else:
                self.log("⚠ No device ID - skipping device verification")
                result.add_warning("Device verification skipped")
            
            # Mark success if face verified
            if face_verified:
                result.mark_success()
            
        except Exception as e:
            result.add_error(f"Authentication flow failed: {e}")
            logger.exception("Authentication flow error")
        
        result.execution_time = time.time() - start_time
        self.results.append(result)
        print(f"\n{result}")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        self.print_section("TEST: ERROR HANDLING")
        
        # Test 1: Invalid enrollment token
        result1 = TestResult("Error Handling - Invalid Enrollment Token")
        start_time = time.time()
        
        try:
            self.log("Testing invalid enrollment token...")
            add_device(
                enrollment_token="invalid_token_12345",
                device_id="test_device",
            )
            result1.add_error("Should have raised exception for invalid token")
        except Exception as e:
            if "failed" in str(e).lower() or "500" in str(e):
                self.log("✓ Correctly rejected invalid enrollment token")
                result1.mark_success()
            else:
                result1.add_error(f"Unexpected error: {e}")
        
        result1.execution_time = time.time() - start_time
        self.results.append(result1)
        print(f"\n{result1}")
        
        # Test 2: Empty face frames
        result2 = TestResult("Error Handling - Empty Face Frames")
        start_time = time.time()
        
        try:
            self.log("Testing empty face frames...")
            add_face(
                enrollment_token="dummy_token",
                face_frames=[],
            )
            result2.add_error("Should have raised exception for empty frames")
        except ValueError as e:
            if "empty" in str(e).lower():
                self.log("✓ Correctly rejected empty face frames")
                result2.mark_success()
            else:
                result2.add_error(f"Unexpected error: {e}")
        except Exception as e:
            result2.add_error(f"Unexpected error type: {e}")
        
        result2.execution_time = time.time() - start_time
        self.results.append(result2)
        print(f"\n{result2}")
        
        # Test 3: Missing document images
        result3 = TestResult("Error Handling - Missing Document Images")
        start_time = time.time()
        
        try:
            self.log("Testing missing document images...")
            add_document_ocr(
                enrollment_token="dummy_token",
                front_image="",
            )
            result3.add_error("Should have raised exception for missing images")
        except ValueError:
            self.log("✓ Correctly rejected missing document images")
            result3.mark_success()
        except Exception as e:
            result3.add_error(f"Unexpected error: {e}")
        
        result3.execution_time = time.time() - start_time
        self.results.append(result3)
        print(f"\n{result3}")
    
    def print_summary(self, total_time: float):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Total Time: {total_time:.2f}s")
        
        if failed > 0:
            print("\n" + "-" * 80)
            print("FAILED TESTS:")
            print("-" * 80)
            for result in self.results:
                if not result.success:
                    print(f"\n{result.test_name}:")
                    for error in result.errors:
                        print(f"  ❌ {error}")
                    for warning in result.warnings:
                        print(f"  ⚠️  {warning}")
        
        print("\n" + "-" * 80)
        print("DETAILED RESULTS:")
        print("-" * 80)
        for result in self.results:
            print(f"\n{result}")
            if result.metadata:
                print("  Metadata:")
                for key, value in result.metadata.items():
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"    {key}: {value}")
            if result.warnings:
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")
        
        print("\n" + "=" * 80)
        if failed == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ {failed} TEST(S) FAILED")
        print("=" * 80 + "\n")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run complete test suite for enrollment and authentication"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Log file path",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Save test results to JSON file",
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(
        level="DEBUG" if args.verbose else "INFO",
        log_file=args.log_file,
    )
    
    # Run test suite
    suite = TestSuite(verbose=args.verbose)
    suite.run_all_tests()
    
    # Save results if requested
    if args.output:
        results_data = {
            "total_tests": len(suite.results),
            "passed": sum(1 for r in suite.results if r.success),
            "failed": sum(1 for r in suite.results if not r.success),
            "tests": [
                {
                    "name": r.test_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "errors": r.errors,
                    "warnings": r.warnings,
                    "metadata": r.metadata,
                }
                for r in suite.results
            ],
        }
        
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results_data, indent=2), encoding='utf-8')
        print(f"\n[INFO] Test results saved to {args.output}")
    
    # Exit with error code if any tests failed
    failed = sum(1 for r in suite.results if not r.success)
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()