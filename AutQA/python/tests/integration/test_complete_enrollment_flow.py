"""
Integration test for complete enrollment flow.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pytest
import time

from autqa.core.env_store import EnvStore
from autqa.core.config import default_env_path
from autqa.utils.env_loader import load_env
from autqa.utils.timing_helpers import smart_delay


@pytest.mark.integration
class TestCompleteEnrollmentFlow:
    """Integration tests for complete enrollment workflow."""
    
    # Configurable delays (tune these based on your API performance)
    DELAYS = {
        "after_initiate": 1.0,      # Usually fast
        "after_device": 1.5,        # Fast
        "after_face": 3.0,          # Liveness analysis takes time
        "after_document": 5.0,      # OCR processing takes longest
    }
    
    def test_full_enrollment_flow(self):
        """
        Test complete enrollment flow: initiate -> device -> face -> document.
        
        This is the main enrollment workflow that mimics a real user signup.
        """
        from generated.initiate_enrollment import initiate_enrollment
        from generated.add_device import add_device
        from generated.add_face import add_face, collect_face_frames
        from generated.add_document_ocr import add_document_ocr, normalize_base64, validate_base64
        
        print("\n" + "=" * 80)
        print("STARTING COMPLETE ENROLLMENT FLOW TEST")
        print("=" * 80)
        
        env = load_env()
        
        # ======================================================================
        # STEP 1: INITIATE ENROLLMENT
        # ======================================================================
        print("\n" + "-" * 80)
        print("STEP 1: INITIATE ENROLLMENT")
        print("-" * 80)
        
        enrollment_result = initiate_enrollment(
            username=None,
            email=None,
            generate_username=True,
            env=env,
        )
        
        assert "enrollmentToken" in enrollment_result, "Missing enrollmentToken"
        assert enrollment_result["enrollmentToken"], "enrollmentToken is empty"
        assert "username" in enrollment_result, "Missing username"
        
        enrollment_token = enrollment_result["enrollmentToken"]
        username = enrollment_result["username"]
        required_checks = enrollment_result.get("requiredChecks", [])
        
        print(f"✓ Enrollment initiated")
        print(f"  Username: {username}")
        print(f"  Token: {enrollment_token[:20]}...")
        print(f"  Required checks: {required_checks}")
        
        # Smart delay
        smart_delay(self.DELAYS["after_initiate"], "enrollment initialization")
        
        # ======================================================================
        # STEP 2: ADD DEVICE
        # ======================================================================
        print("\n" + "-" * 80)
        print("STEP 2: ADD DEVICE")
        print("-" * 80)
        
        device_id = f"test_device_{int(time.time())}"
        
        device_result = add_device(
            enrollment_token=enrollment_token,
            device_id=device_id,
            platform="web",
            browser="Chrome 120",
            os="Windows 11",
        )
        
        assert device_result is not None, "Device addition returned None"
        print(f"✓ Device added: {device_id}")
        
        # Smart delay
        smart_delay(self.DELAYS["after_device"], "device registration")
        
        # ======================================================================
        # STEP 3: ADD FACE
        # ======================================================================
        print("\n" + "-" * 80)
        print("STEP 3: ADD FACE")
        print("-" * 80)
        
        face_frames = collect_face_frames(num_frames=3, frame_interval_ms=30, env=env)
        
        assert face_frames is not None, "Failed to collect face frames"
        assert len(face_frames) > 0, "No face frames collected"
        
        print(f"  Collected {len(face_frames)} face frames")
        
        face_result = add_face(
            enrollment_token=enrollment_token,
            face_frames=face_frames,
            workflow="charlie4",
            username=username,
        )
        
        registration_code = face_result.get("registrationCode", "")
        
        if registration_code:
            print(f"✓ Face added - Registration Code: {registration_code}")
        else:
            print(f"✓ Face added (registration code pending)")
        
        # Smart delay - face liveness takes longer
        smart_delay(self.DELAYS["after_face"], "face liveness analysis")
        
        # ======================================================================
        # STEP 4: ADD DOCUMENT OCR
        # ======================================================================
        print("\n" + "-" * 80)
        print("STEP 4: ADD DOCUMENT OCR")
        print("-" * 80)
        
        front_image = env.get("DAN_DOC_FRONT", "").strip()
        back_image = env.get("DAN_DOC_BACK", "").strip()
        
        if not front_image:
            pytest.skip("DAN_DOC_FRONT not available - skipping document step")
        
        front_image = normalize_base64(front_image)
        is_valid, err_msg = validate_base64(front_image)
        assert is_valid, f"Front image validation failed: {err_msg}"
        
        if back_image:
            back_image = normalize_base64(back_image)
            is_valid, err_msg = validate_base64(back_image)
            assert is_valid, f"Back image validation failed: {err_msg}"
        
        print(f"  Front: {len(front_image)} chars")
        if back_image:
            print(f"  Back: {len(back_image)} chars")
        
        doc_result = add_document_ocr(
            enrollment_token=enrollment_token,
            front_image=front_image,
            back_image=back_image,
            workflow="charlie4",
            security_level=4,
        )
        
        assert doc_result is not None, "Document OCR returned None"
        
        if "registrationCode" in doc_result and doc_result["registrationCode"]:
            registration_code = doc_result["registrationCode"]
            print(f"✓ Document OCR completed - Registration Code: {registration_code}")
        else:
            print(f"✓ Document OCR completed")
        
        if "documentVerificationResult" in doc_result:
            print(f"  Verification: {doc_result['documentVerificationResult']}")
        
        # Smart delay - OCR processing takes longest
        smart_delay(self.DELAYS["after_document"], "document OCR and enrollment finalization")
        
        # ======================================================================
        # FINAL SUMMARY
        # ======================================================================
        print("\n" + "=" * 80)
        print("✓ ENROLLMENT FLOW COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"Username:           {username}")
        print(f"Enrollment Token:   {enrollment_token[:20]}...")
        print(f"Registration Code:  {registration_code or 'Pending'}")
        print(f"Device ID:          {device_id}")
        print(f"Face Frames:        {len(face_frames)}")
        print(f"Document Images:    {'Front + Back' if back_image else 'Front only'}")
        print("=" * 80)
        print(f"\n💡 Check admin portal now - enrollment should be complete!\n")
        
        # Validate registration code if all steps were required
        if "addDocument" in required_checks:
            assert registration_code, \
                "Expected registration code after all required steps"