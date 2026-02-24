"""
Enrollment Test with Custom Admin Configuration
Tests enrollment flow when admin settings require: age 1-101, face + device only
"""
import pytest
import copy
import time
import json

@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.integration
class TestEnrollmentWithCustomAgeRange:
    """Test enrollment with custom age verification (1-101 years) and face + device"""
    
    def test_enroll_with_age_verification_1_to_101(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Enrollment test with custom admin configuration:
        - Age range: 1-101 years
        - Required: Face + Device
        - Disabled: Document, Voice, PIN
        
        This test verifies enrollment works correctly with extreme age ranges
        and analyzes if age verification causes failures.
        """
        
        # ====================================================================
        # PREREQUISITE: VERIFY ADMIN CONFIGURATION
        # ====================================================================
        print("\n" + "="*80)
        print("PREREQUISITE: VERIFY ADMIN CONFIGURATION")
        print("="*80)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        config = config_response.json().get("onboardingConfig", {}).get("onboardingOptions", {})
        
        age_settings = config.get("ageEstimation", {})
        enrollment_settings = config.get("enrollment", {})
        
        print("\n Current Admin Settings:")
        print(f"   Age Verification: {age_settings.get('enabled')}")
        print(f"   Age Range: {age_settings.get('minAge')}-{age_settings.get('maxAge')}")
        print(f"   Face Required: {enrollment_settings.get('addFace')}")
        print(f"   Device Required: {enrollment_settings.get('addDevice')}")
        print(f"   Document Required: {enrollment_settings.get('addDocument')}")
        
        # Warn if settings don't match test expectations
        if age_settings.get('minAge') != 1 or age_settings.get('maxAge') != 101:
            print(f"\n  WARNING: Age range is {age_settings.get('minAge')}-{age_settings.get('maxAge')}")
            print(f"   Expected: 1-101")
            print(f"   Run admin config test first to set correct range")
        
        # ====================================================================
        # STEP 1: INITIATE ENROLLMENT
        # ====================================================================
        enroll_payload = {
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
        
        print(f"\n{'='*80}")
        print("STEP 1: INITIATE ENROLLMENT")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> Username: {unique_username}")
        
        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=enroll_payload
        )
        
        print(f"\n<<< RESPONSE Status: {enroll_response.status_code}")
        enroll_data = enroll_response.json()
        print(f"<<< Response:")
        print(json.dumps(enroll_data, indent=2))
        
        assert enroll_response.status_code == 200, (
            f" Failed to initiate enrollment: {enroll_response.status_code}\n{enroll_data}"
        )
        
        enrollment_token = enroll_data.get("enrollmentToken")
        required_checks = enroll_data.get("requiredChecks", [])
        
        print(f"\n Enrollment initiated")
        print(f"   Token: {enrollment_token[:30]}...")
        print(f"   Required: {required_checks}")
        
        # ====================================================================
        # STEP 2: ADD DEVICE
        # ====================================================================
        device_id = f"test_device_{int(time.time())}"
        
        device_payload = {
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web",
            "browser": "Chrome",
            "os": "Windows"
        }
        
        print(f"\n{'='*80}")
        print("STEP 2: ADD DEVICE")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/addDevice")
        print(f">>> Device ID: {device_id}")
        
        device_response = api_client.http_client.post(
            "/onboarding/enrollment/addDevice",
            json=device_payload
        )
        
        print(f"\n<<< RESPONSE Status: {device_response.status_code}")
        
        if device_response.status_code != 200:
            print(f" Device enrollment failed: {device_response.text}")
            pytest.fail(f"Device enrollment failed: {device_response.text}")
        
        print(f" Device added: {device_id}")
        
        # ====================================================================
        # STEP 3: ADD FACE WITH AGE VERIFICATION ANALYSIS
        # ====================================================================
        face_payload = {
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }
        
        print(f"\n{'='*80}")
        print("STEP 3: ADD FACE (WITH AGE VERIFICATION)")
        print(f"{'='*80}")
        print(f">>> REQUEST: POST /onboarding/enrollment/addFace")
        print(f">>> Frames: {len(face_frames)}")
        print(f">>> Expected Age Range: 1-101 years")
        
        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json=face_payload
        )
        
        print(f"\n<<< RESPONSE Status: {face_response.status_code}")
        
        try:
            face_data = face_response.json()
            print(f"<<< Full Response:")
            print(json.dumps(face_data, indent=2))
        except:
            face_data = {}
            print(f"<<< Response Text: {face_response.text}")
        
        # ====================================================================
        # DETAILED ANALYSIS
        # ====================================================================
        print(f"\n{'='*80}")
        print(" ENROLLMENT ANALYSIS")
        print(f"{'='*80}")
        
        if face_response.status_code == 200:
            # Extract data (handle both dict and primitive types)
            liveness_result = face_data.get("livenessResult", {})
            age_verification = face_data.get("ageVerification", {})
            quality_checks = face_data.get("qualityChecks", {})
            registration_code = face_data.get("registrationCode")
            
            # Liveness (handle if it's a boolean or dict)
            print("\n Liveness Detection:")
            if isinstance(liveness_result, bool):
                is_live = liveness_result
                liveness_score = "N/A"
                liveness_confidence = "N/A"
            elif isinstance(liveness_result, dict):
                is_live = liveness_result.get("isLive", False)
                liveness_score = liveness_result.get("score", "N/A")
                liveness_confidence = liveness_result.get("confidence", "N/A")
            else:
                is_live = False
                liveness_score = "N/A"
                liveness_confidence = "N/A"
            print(f"   Status: {' LIVE' if is_live else ' NOT LIVE'}")
            print(f"   Score: {liveness_score}")
            print(f"   Confidence: {liveness_confidence}")
            
            # Age Verification (MAIN FOCUS) - handle dict or primitive
            print("\n Age Verification Analysis:")
            if isinstance(age_verification, dict):
                age_enabled = age_verification.get("enabled", False)
                estimated_age = age_verification.get("estimatedAge")
                age_passed = age_verification.get("passed")
                age_min = age_verification.get("minAge")
                age_max = age_verification.get("maxAge")
                age_confidence = age_verification.get("confidence", "N/A")
            else:
                age_enabled = False
                estimated_age = None
                age_passed = None
                age_min = None
                age_max = None
                age_confidence = "N/A"
            
            print(f"   Enabled: {' YES' if age_enabled else ' NO'}")
            
            if estimated_age is not None:
                print(f"   Estimated Age: {estimated_age} years")
                print(f"   Allowed Range: {age_min}-{age_max} years")
                print(f"   Confidence: {age_confidence}")
                print(f"   Result: {' PASSED' if age_passed else ' FAILED'}")
                
                # Detailed age analysis
                if age_passed:
                    print(f"\n    Age Verification PASSED")
                    print(f"      {estimated_age} is within range {age_min}-{age_max}")
                else:
                    print(f"\n    Age Verification FAILED")
                    print(f"      {estimated_age} is OUTSIDE range {age_min}-{age_max}")
                    
                    if estimated_age < age_min:
                        print(f"      Reason: Too young ({estimated_age} < {age_min})")
                    elif estimated_age > age_max:
                        print(f"      Reason: Too old ({estimated_age} > {age_max})")
            else:
                print(f"     No age estimation in response")
            
            # Quality Checks
            print("\n Quality Checks:")
            if quality_checks and isinstance(quality_checks, dict):
                for check, result in quality_checks.items():
                    if isinstance(result, dict):
                        status = "" if result.get("passed", result) else ""
                    else:
                        status = "" if result else ""
                    print(f"   {status} {check}: {result}")
            else:
                print("   No quality checks or non-dict format")
            
            # Registration Code
            if registration_code:
                print(f"\n  Registration Code: {registration_code}")
            
            # Overall verdict
            print(f"\n{'='*80}")
            print("FINAL VERDICT")
            print(f"{'='*80}")
            
            all_passed = is_live and (age_passed if age_passed is not None else True)
            
            if all_passed:
                print(" ENROLLMENT SUCCESSFUL")
                print(f"   Username: {unique_username}")
                print(f"   Device: {device_id}")
                print(f"   Face: Enrolled (Age: {estimated_age})")
                if registration_code:
                    print(f"   Code: {registration_code}")
            else:
                failure_reasons = []
                if not is_live:
                    failure_reasons.append("Liveness check failed")
                if age_passed == False:
                    failure_reasons.append(f"Age {estimated_age} outside range {age_min}-{age_max}")
                
                print(" ENROLLMENT FAILED")
                print(f"   Reasons:")
                for reason in failure_reasons:
                    print(f"   - {reason}")
                
                pytest.fail(f"Enrollment failed: {', '.join(failure_reasons)}")
            
        else:
            # Error response
            print(f"\n FACE ENROLLMENT FAILED")
            print(f"   Status: {face_response.status_code}")
            
            error_code = face_data.get("errorCode", "UNKNOWN")
            error_msg = face_data.get("errorMsg", face_response.text)
            
            print(f"   Error Code: {error_code}")
            print(f"   Error Message: {error_msg}")
            
            # Check error type
            if "age" in error_msg.lower():
                print(f"\n    AGE-RELATED ERROR")
                print(f"      Check if estimated age is within 1-101 range")
            elif "liveness" in error_msg.lower():
                print(f"\n    LIVENESS-RELATED ERROR")
                print(f"      Face images may not pass liveness detection")
            
            pytest.fail(f"Face enrollment API error: {error_msg}")
        
        print(f"\n{'='*80}")


@pytest.fixture(autouse=True, scope="function")
def delay_after_enrollment():
    """Add delay after enrollment"""
    yield
    time.sleep(3)

