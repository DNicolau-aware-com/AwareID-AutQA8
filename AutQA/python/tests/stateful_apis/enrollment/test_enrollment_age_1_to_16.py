"""
Enrollment Test with Age Verification: Min 1, Max 16
WITH ASSERTIONS: Fails test if age verification or liveness checks are not enforced
"""
import pytest
import copy
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.age_verification
class TestEnrollmentAgeRange1To16:
    """Test enrollment with age verification 1-16 years - enforces proper validation"""
    
    def test_enroll_with_age_1_to_16(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """
        Enrollment flow with strict validation:
        - FAILS TEST if age is outside 1-16 but enrollment succeeds
        - FAILS TEST if liveness is not LIVE
        """
        
        caplog.set_level(logging.INFO)
        
        face_image_base64 = env_vars.get("FACE")
        if not face_image_base64:
            pytest.skip("FACE not found in .env")
        
        if face_image_base64.startswith('data:'):
            face_image_base64 = face_image_base64.split(',')[1]
        
        # ====================================================================
        # ADMIN CONFIG
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("ADMIN CONFIGURATION - AGE RANGE 1-16")
        logger.info("="*120)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": 1,
            "maxAge": 16,
            "minTolerance": 0,
            "maxTolerance": 0
        }
        enrollment['addFace'] = True
        enrollment['addDevice'] = True
        enrollment['addDocument'] = False
        
        authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        authentication['verifyFace'] = True
        
        reenrollment = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenrollment['verifyFace'] = True
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        logger.info(" Admin configured: Age range 1-16 years")
        time.sleep(2)
        
        # ====================================================================
        # STEP 1: ENROLLMENT - ENROLL
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 1: Enrollment - Enroll")
        logger.info("="*120)
        
        enroll_payload = {
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
        
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json=enroll_payload)
        enroll_data = enroll_response.json()
        enrollment_token = enroll_data.get("enrollmentToken")
        enroll_tx_id = enroll_data.get("transactionId", enroll_data.get("id", "N/A"))
        
        logger.info(f"ID: {enroll_tx_id}")
        logger.info(f"Status: {' SUCCESS' if enroll_response.status_code == 200 else ' FAILED'}")
        logger.info(f"Username: {unique_username}")
        logger.info(f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        assert enroll_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 2: ENROLLMENT - ADD DEVICE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 2: Enrollment - Add Device")
        logger.info("="*120)
        
        device_id = f"device_{int(time.time())}"
        device_payload = {
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web",
            "browser": "Chrome",
            "os": "Windows"
        }
        
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json=device_payload)
        device_data = device_response.json() if device_response.status_code == 200 else {}
        device_tx_id = device_data.get("transactionId", device_data.get("id", "N/A"))
        
        logger.info(f"ID: {device_tx_id}")
        logger.info(f"Status: {' Device registered' if device_response.status_code == 200 else ' FAILED'}")
        logger.info(f"Device ID: {device_id}")
        logger.info(f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        assert device_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ENROLLMENT - ADD FACE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: Enrollment - Add Face")
        logger.info("="*120)
        
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
        
        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json=face_payload)
        
        # Parse response
        if face_response.status_code == 200:
            face_data = face_response.json()
        else:
            face_data = face_response.json() if face_response.text else {}
        
        face_tx_id = face_data.get("transactionId", face_data.get("id", "N/A"))
        
        # ====================================================================
        # EXTRACT DATA
        # ====================================================================
        age_check = face_data.get("ageEstimationCheck", {})
        age_estimation_config = age_check.get("ageEstimation", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        enrollment_result = age_check.get("result", "UNKNOWN")
        
        age_enabled = age_estimation_config.get("enabled", False)
        min_age = age_estimation_config.get("minAge", 0)
        max_age = age_estimation_config.get("maxAge", 0)
        min_tolerance = age_estimation_config.get("minTolerance", 0)
        max_tolerance = age_estimation_config.get("maxTolerance", 0)
        
        # Liveness data
        liveness_result_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_result_data.get("decision", "UNKNOWN")
        liveness_score = liveness_result_data.get("score_frr", "N/A")
        
        # Determine status
        if enrollment_result == "FAIL":
            face_status = " Failed: AGE ESTIMATION"
        elif enrollment_result in ["PASS", "SUCCESS"]:
            face_status = " SUCCESS"
        elif face_response.status_code != 200:
            error_msg = face_data.get("errorMsg", "Unknown error")
            face_status = f" Failed: {error_msg}"
        else:
            face_status = " SUCCESS"
        
        logger.info(f"ID: {face_tx_id}")
        logger.info(f"Status: {face_status}")
        logger.info(f"Result: {enrollment_result}")
        logger.info(f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        # ====================================================================
        # AGE VERIFICATION ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" AGE VERIFICATION ANALYSIS")
        logger.info("="*120)
        
        logger.info("\n Age Estimation Configuration:")
        logger.info(f"   Enabled: {age_enabled}")
        logger.info(f"   Min Age: {min_age} years")
        logger.info(f"   Max Age: {max_age} years")
        logger.info(f"   Min Tolerance: {min_tolerance}")
        logger.info(f"   Max Tolerance: {max_tolerance}")
        
        logger.info("\n Detected Age:")
        logger.info(f"   Age from Face Liveness Server: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
        
        logger.info("\n Verification Result:")
        logger.info(f"   Result: {enrollment_result}")
        
        # ====================================================================
        # DETAILED FAILURE/SUCCESS REASON
        # ====================================================================
        effective_min = min_age - min_tolerance
        effective_max = max_age + max_tolerance
        
        if enrollment_result == "FAIL" and age_from_server:
            logger.info("\n" + "="*120)
            logger.info(" FAILURE REASON")
            logger.info("="*120)
            
            logger.info(f"\n Configuration:")
            logger.info(f"   Age must be between {min_age} and {max_age} years")
            
            logger.info(f"\n What Was Detected:")
            logger.info(f"   Detected Age: {age_from_server} years")
            
            if age_from_server < effective_min:
                difference = effective_min - age_from_server
                logger.info(f"\n FAILURE TYPE: TOO YOUNG")
                logger.info(f"   Detected age ({age_from_server} years) is {difference} years below minimum ({effective_min} years)")
            elif age_from_server > effective_max:
                difference = age_from_server - effective_max
                logger.info(f"\n FAILURE TYPE: TOO OLD")
                logger.info(f"   Detected age ({age_from_server} years) is {difference} years ABOVE maximum ({effective_max} years)")
                logger.info(f"   The person appears to be {age_from_server} years old")
                logger.info(f"   But the system only accepts ages up to {max_age} years")
            
            logger.info(f"\n TO PASS THIS VERIFICATION:")
            logger.info(f"    Person's detected age must be between {min_age} and {max_age} years")
            logger.info(f"    Current detected age of {age_from_server} years is OUTSIDE this range")
            
        elif enrollment_result in ["PASS", "SUCCESS"]:
            logger.info("\n" + "="*120)
            logger.info(" SUCCESS REASON")
            logger.info("="*120)
            logger.info(f"\n Configuration: Age must be between {min_age} and {max_age} years")
            logger.info(f" Detected Age: {age_from_server} years")
            logger.info(f"\n VERIFICATION PASSED:")
            logger.info(f"   Detected age ({age_from_server} years) is within the allowed range ({min_age}-{max_age} years)")
        
        # ====================================================================
        # LIVENESS CHECK ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" LIVENESS CHECK ANALYSIS")
        logger.info("="*120)
        
        logger.info(f"\nLiveness Decision: {liveness_decision}")
        logger.info(f"Liveness Score: {liveness_score}")
        
        if liveness_decision != "LIVE":
            logger.info(f"\n  WARNING: Liveness check indicates potential SPOOF or NON-LIVE image")
            logger.info(f"   Decision: {liveness_decision}")
            logger.info(f"   This means the face may be:")
            logger.info(f"    A photo of a photo")
            logger.info(f"    A video replay")
            logger.info(f"    A mask")
            logger.info(f"    A synthetic/deepfake image")
        else:
            logger.info(f"\n Liveness check PASSED - Real live person detected")
        
        # ====================================================================
        # SUB-TRANSACTIONS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" SUB-TRANSACTIONS")
        logger.info("="*120)
        
        logger.info("\n  " + "-"*116)
        logger.info("   Analyze Image")
        logger.info("  " + "-"*116)
        logger.info(f"  Estimated Age: {age_from_server} years" if age_from_server else "  Estimated Age: NOT AVAILABLE")
        logger.info(f"  Age Range: {min_age}-{max_age} years")
        logger.info(f"  Status: {' OUT OF RANGE' if enrollment_result == 'FAIL' else ' IN RANGE'}")
        logger.info(f"  Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        logger.info("\n  " + "-"*116)
        logger.info("   Check Liveness")
        logger.info("  " + "-"*116)
        logger.info(f"  Liveness Decision: {liveness_decision}")
        logger.info(f"  Live Score: {liveness_score}")
        logger.info(f"  Status: {' LIVE' if liveness_decision == 'LIVE' else ' NOT LIVE / SPOOF'}")
        logger.info(f"  Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" FINAL SUMMARY")
        logger.info("="*120)
        
        logger.info(f"\n Enrollment Process:")
        logger.info(f"   Username: {unique_username}")
        logger.info(f"   Device: {device_id}")
        logger.info(f"   Liveness: {liveness_decision}")
        
        logger.info(f"\n Age Verification:")
        logger.info(f"   Required Range: {min_age}-{max_age} years")
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Detected Age: N/A")
        logger.info(f"   Result: {enrollment_result}")
        
        if enrollment_result == "FAIL":
            logger.info(f"\n TEST EXPECTED BEHAVIOR: ENROLLMENT CORRECTLY REJECTED")
            logger.info(f"   The system correctly rejected enrollment due to age verification failure")
        elif enrollment_result in ["PASS", "SUCCESS"]:
            logger.info(f"\n ENROLLMENT SUCCESSFUL")
        
        logger.info("="*120 + "\n")
        
        # ====================================================================
        # CRITICAL ASSERTIONS - FAIL TEST IF VALIDATIONS NOT ENFORCED
        # ====================================================================
        logger.info("\n" + ""*60)
        logger.info("CRITICAL VALIDATION CHECKS")
        logger.info(""*60 + "\n")
        
        # ASSERTION 1: Check liveness enforcement
        if liveness_decision != "LIVE":
            logger.error(f"\n CRITICAL FAILURE: LIVENESS CHECK FAILED")
            logger.error(f"="*120)
            logger.error(f"   Liveness Decision: {liveness_decision}")
            logger.error(f"   Expected: LIVE")
            logger.error(f"     SECURITY RISK: System accepted a non-live or spoofed image")
            logger.error(f"     ACTION REQUIRED: Investigate why liveness check was bypassed")
            logger.error(f"="*120)
            pytest.fail(
                f" LIVENESS CHECK FAILED: Decision was '{liveness_decision}' (expected 'LIVE'). "
                f"This indicates a potential spoof attack or non-live image was accepted. "
                f"INVESTIGATE IMMEDIATELY!"
            )
        else:
            logger.info(f" ASSERTION PASSED: Liveness check enforced (Decision: {liveness_decision})")
        
        # ASSERTION 2: Check age verification enforcement
        if age_from_server and age_enabled:
            age_in_range = effective_min <= age_from_server <= effective_max
            
            if not age_in_range and enrollment_result != "FAIL":
                logger.error(f"\n CRITICAL FAILURE: AGE VERIFICATION NOT ENFORCED")
                logger.error(f"="*120)
                logger.error(f"   Detected Age: {age_from_server} years")
                logger.error(f"   Required Range: {min_age}-{max_age} years")
                logger.error(f"   Enrollment Result: {enrollment_result}")
                logger.error(f"   Expected Result: FAIL")
                logger.error(f"     SECURITY RISK: System accepted age outside allowed range")
                logger.error(f"     ACTION REQUIRED: Age verification is configured but not enforced")
                logger.error(f"="*120)
                
                difference = abs(age_from_server - (max_age if age_from_server > max_age else min_age))
                logger.error(f"\n   Age is {difference} years {'above maximum' if age_from_server > max_age else 'below minimum'}")
                
                pytest.fail(
                    f" AGE VERIFICATION NOT ENFORCED: Person aged {age_from_server} years "
                    f"(outside range {min_age}-{max_age}) was allowed to enroll. "
                    f"Expected enrollment to FAIL but got '{enrollment_result}'. "
                    f"INVESTIGATE IMMEDIATELY!"
                )
            else:
                logger.info(f" ASSERTION PASSED: Age verification enforced correctly")
        
        logger.info(f"\n" + "="*120)
        logger.info(f" ALL CRITICAL VALIDATIONS PASSED ")
        logger.info(f"="*120 + "\n")
        
        # Log full response
        logger.info("\n Full Add Face Response:")
        logger.info(json.dumps(face_data, indent=2))


@pytest.fixture(autouse=True, scope="function")
def cleanup():
    yield
    time.sleep(3)
