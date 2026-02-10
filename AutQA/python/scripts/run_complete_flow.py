"""
Run complete enrollment and authentication flow.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from generated.initiate_enrollment import initiate_enrollment
from generated.add_device import add_device
from generated.add_face import add_face, collect_face_frames
from generated.add_document_ocr import add_document_ocr, normalize_base64, validate_base64
from generated.initiate_authentication import initiate_authentication
from generated.verify_face import verify_face, collect_face_frames_for_verification
from autqa.utils.env_loader import load_env
from autqa.utils.timing_helpers import smart_delay
import time
import json


def print_response(title: str, data: dict):
    """Print response data in a nice format."""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    print(json.dumps(data, indent=2))
    print(f"{'='*80}\n")


def main():
    print("\n" + "=" * 80)
    print("COMPLETE ENROLLMENT AND AUTHENTICATION FLOW")
    print("=" * 80)
    
    env = load_env()
    registration_code = None
    
    # ENROLLMENT
    print("\n" + "🔵" * 40)
    print("PHASE 1: ENROLLMENT")
    print("🔵" * 40)
    
    # 1. Initiate enrollment
    print("\n" + "-" * 80)
    print("STEP 1: INITIATE ENROLLMENT")
    print("-" * 80)
    
    enrollment = initiate_enrollment(generate_username=True, env=env)
    token = enrollment["enrollmentToken"]
    username = enrollment["username"]
    required_checks = enrollment.get("requiredChecks", [])
    
    print(f"\n✅ Enrollment Initiated Successfully!")
    print(f"   Username: {username}")
    print(f"   Enrollment Token: {token[:30]}...")
    print(f"\n📋 Required Checks: {required_checks}")
    
    if not required_checks:
        print("   ⚠️  WARNING: No required checks specified - enrollment might be auto-complete")
    else:
        print(f"   ℹ️  You must complete: {', '.join(required_checks)}")
    
    print_response("FULL ENROLLMENT RESPONSE", enrollment)
    
    smart_delay(1.0, "enrollment initialization")
    
    # 2. Add device (if required)
    device_id = None
    if not required_checks or "addDevice" in required_checks:
        print("\n" + "-" * 80)
        print("STEP 2: ADD DEVICE")
        print("-" * 80)
        
        device_id = f"test_device_{int(time.time())}"
        device_result = add_device(
            enrollment_token=token,
            device_id=device_id,
            platform="web",
            browser="Chrome 120",
            os="Windows 11"
        )
        
        print(f"\n✅ Device Added Successfully!")
        print(f"   Device ID: {device_id}")
        print_response("FULL DEVICE RESPONSE", device_result)
        
        smart_delay(1.5, "device registration")
    else:
        print("\n⏭️  STEP 2: ADD DEVICE - SKIPPED (not required)")
    
    # 3. Add face (if required)
    if not required_checks or "addFace" in required_checks:
        print("\n" + "-" * 80)
        print("STEP 3: ADD FACE")
        print("-" * 80)
        
        frames = collect_face_frames(num_frames=3, env=env)
        if not frames:
            print("❌ ERROR: Failed to collect face frames")
            sys.exit(1)
        
        face_result = add_face(
            enrollment_token=token,
            face_frames=frames,
            username=username,
            workflow="charlie4"
        )
        
        print(f"\n✅ Face Added Successfully!")
        print(f"   Frames Uploaded: {len(frames)}")
        
        # Check for registration code
        if "registrationCode" in face_result:
            registration_code = face_result.get("registrationCode", "")
            if registration_code:
                print(f"   🎟️  Registration Code: {registration_code}")
            else:
                print(f"   ⚠️  Registration code field present but EMPTY")
        else:
            print(f"   ⚠️  No registration code field in response")
        
        print_response("FULL FACE RESPONSE", face_result)
        
        smart_delay(3.0, "face liveness analysis")
    else:
        print("\n⏭️  STEP 3: ADD FACE - SKIPPED (not required)")
    
    # 4. Add document OCR (if required)
    if not required_checks or "addDocument" in required_checks:
        print("\n" + "-" * 80)
        print("STEP 4: ADD DOCUMENT OCR")
        print("-" * 80)
        
        front_image = env.get("DAN_DOC_FRONT", "").strip()
        back_image = env.get("DAN_DOC_BACK", "").strip()
        
        if not front_image:
            print("❌ ERROR: DAN_DOC_FRONT not found in .env")
            print("   Document is REQUIRED but no image available!")
            
            if "addDocument" in required_checks:
                print("   ⚠️  Cannot complete enrollment without document!")
                sys.exit(1)
        else:
            front_image = normalize_base64(front_image)
            if back_image:
                back_image = normalize_base64(back_image)
            
            print(f"   📄 Front image: {len(front_image)} characters")
            if back_image:
                print(f"   📄 Back image: {len(back_image)} characters")
            
            doc_result = add_document_ocr(
                enrollment_token=token,
                front_image=front_image,
                back_image=back_image,
                workflow="charlie4",
                security_level=4,
            )
            
            print(f"\n✅ Document OCR Completed Successfully!")
            
            # Check for registration code in document response
            if "registrationCode" in doc_result:
                new_reg_code = doc_result.get("registrationCode", "")
                if new_reg_code:
                    registration_code = new_reg_code
                    print(f"   🎟️  Registration Code: {registration_code}")
                else:
                    print(f"   ⚠️  Registration code field present but EMPTY")
            else:
                print(f"   ⚠️  No registration code field in response")
            
            # Show document verification details
            if "documentVerificationResult" in doc_result:
                print(f"   📋 Document Verified: {doc_result['documentVerificationResult']}")
            
            if "enrollmentStatus" in doc_result:
                print(f"   📊 Enrollment Status: {doc_result['enrollmentStatus']}")
            
            print_response("FULL DOCUMENT RESPONSE", doc_result)
            
            smart_delay(5.0, "document OCR and enrollment finalization")
    else:
        print("\n⏭️  STEP 4: ADD DOCUMENT OCR - SKIPPED (not required)")
    
    # Check enrollment completion
    print("\n" + "=" * 80)
    print("ENROLLMENT COMPLETION CHECK")
    print("=" * 80)
    
    if registration_code:
        print(f"✅ ENROLLMENT COMPLETE!")
        print(f"   🎟️  Registration Code: {registration_code}")
    else:
        print(f"⚠️  ENROLLMENT MAY BE INCOMPLETE")
        print(f"   No registration code received")
        print(f"   Required checks were: {required_checks}")
        
        # Check if we can still proceed
        if required_checks and any(check in required_checks for check in ["addDocument", "addFace", "addDevice"]):
            missing = [check for check in required_checks if check in ["addDocument", "addFace", "addDevice"]]
            if missing:
                print(f"   ❌ Missing required steps: {missing}")
                print(f"   Cannot proceed to authentication!")
                sys.exit(1)
    
    # AUTHENTICATION
    print("\n" + "🟢" * 40)
    print("PHASE 2: AUTHENTICATION")
    print("🟢" * 40)
    
    # 5. Initiate authentication
    print("\n" + "-" * 80)
    print("STEP 5: INITIATE AUTHENTICATION")
    print("-" * 80)
    
    try:
        auth = initiate_authentication(username=username, env=env)
        auth_token = auth["authToken"]
        
        print(f"\n✅ Authentication Initiated Successfully!")
        print(f"   Username: {username}")
        print(f"   Auth Token: {auth_token[:30]}...")
        print_response("FULL AUTHENTICATION RESPONSE", auth)
        
        smart_delay(1.0, "authentication initialization")
        
    except Exception as e:
        print(f"\n❌ AUTHENTICATION INITIATION FAILED!")
        print(f"   Error: {e}")
        print(f"\n💡 This usually means enrollment is not complete.")
        print(f"   Required checks: {required_checks}")
        print(f"   Registration code: {registration_code or 'NONE'}")
        sys.exit(1)
    
    # 6. Verify face
    print("\n" + "-" * 80)
    print("STEP 6: VERIFY FACE")
    print("-" * 80)
    
    verify_frames = collect_face_frames_for_verification(num_frames=3, env=env)
    if not verify_frames:
        print("❌ ERROR: Failed to collect face frames for verification")
        sys.exit(1)
    
    face_verify = verify_face(
        auth_token=auth_token,
        face_frames=verify_frames,
        username=username,
        min_match_score=25.0
    )
    
    face_verified = face_verify.get("verified", False)
    match_score = face_verify.get("matchScore", 0)
    
    print(f"\n{'✅' if face_verified else '⚠️'} Face Verification {'PASSED' if face_verified else 'FAILED'}!")
    print(f"   Match Score: {match_score}%")
    print(f"   Liveness: {face_verify.get('livenessResult', 'N/A')}")
    print_response("FULL FACE VERIFICATION RESPONSE", face_verify)
    
    smart_delay(2.0, "face verification processing")
    
    # FINAL SUMMARY
    print("\n" + "🎉" * 40)
    print("COMPLETE FLOW SUMMARY")
    print("🎉" * 40)
    print(f"""
📊 ENROLLMENT:
   Username:           {username}
   Registration Code:  {registration_code or 'N/A'}
   Device ID:          {device_id or 'N/A'}
   Required Checks:    {', '.join(required_checks) if required_checks else 'None'}

🔐 AUTHENTICATION:
   Auth Token:         {auth_token[:30]}...
   Face Verified:      {'✅ YES' if face_verified else '❌ NO'}
   Face Match Score:   {match_score}%

{'✅ ALL TESTS PASSED!' if face_verified else '⚠️ SOME TESTS HAD WARNINGS'}
    """)
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()