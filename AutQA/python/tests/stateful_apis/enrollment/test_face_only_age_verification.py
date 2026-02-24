"""
Face-Only Age Verification Test Suite (No Device)
Tests age verification with face enrollment only - device disabled
"""
import pytest
import copy
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# TEST DATA: Age scenarios for face-only enrollment
# ============================================================================
FACE_ONLY_AGE_SCENARIOS = [
    # (min_age, max_age, test_description, expected_result_for_age_50)
    (1, 16, "Child/Teen only (1-16)", "FAIL"),
    (18, 65, "Adult working age (18-65)", "PASS"),
    (21, 100, "Legal adult (21-100)", "PASS"),
    (1, 30, "Young person (1-30)", "FAIL"),
    (40, 60, "Middle age (40-60)", "PASS"),
    (65, 120, "Senior only (65-120)", "FAIL"),
    (1, 101, "All ages (1-101)", "PASS"),
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.face_only
@pytest.mark.age_verification
class TestFaceOnlyAgeVerification:
    """Age verification with FACE ONLY (device disabled)"""
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", FACE_ONLY_AGE_SCENARIOS)
    def test_face_only_age_verification(
        self, 
        api_client, 
        unique_username, 
        face_frames, 
        workflow, 
        env_vars, 
        caplog,
        min_age,
        max_age,
        scenario_name,
        expected_result
    ):
        """
        Face-only enrollment with age verification
        
        Configuration:
        -  Face enrollment: ENABLED
        -  Device enrollment: DISABLED
        -  Age verification: ENABLED (varies by scenario)
        
        Tests that age verification works correctly with face-only enrollment
        """
        
        caplog.set_level(logging.INFO)
        
        face_image_base64 = env_vars.get("FACE")
        if not face_image_base64:
            pytest.skip("FACE not found in .env")
        
        if face_image_base64.startswith('data:'):
            face_image_base64 = face_image_base64.split(',')[1]
        
        # ====================================================================
        # TEST SCENARIO HEADER
        # ====================================================================
        logger.info("\n" + ""*60)
        logger.info(f"FACE-ONLY ENROLLMENT TEST: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected Result: {expected_result}")
        logger.info(f"Device Enrollment: DISABLED")
        logger.info(""*60)
        
        # ====================================================================
        # STEP 1: CONFIGURE ADMIN - FACE ONLY, NO DEVICE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(f"STEP 1: CONFIGURE ADMIN - FACE ONLY")
        logger.info("="*120)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        
        # Configure age estimation
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": min_age,
            "maxAge": max_age,
            "minTolerance": 0,
            "maxTolerance": 0
        }
        
        # FACE ONLY - disable device
        enrollment['addFace'] = True
        enrollment['addDevice'] = False  #  DISABLED
        enrollment['addDocument'] = False
        enrollment['addVoice'] = False
        enrollment['addPIN'] = False
        
        authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        authentication['verifyFace'] = True
        
        reenrollment = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenrollment['verifyFace'] = True
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        
        logger.info(f" Admin configured: {scenario_name}")
        logger.info(f"   Enrollment Mode: FACE ONLY")
        logger.info(f"   Add Face:  ENABLED")
        logger.info(f"   Add Device:  DISABLED")
        logger.info(f"   Add Document:  DISABLED")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected Result: {expected_result}")
        
        time.sleep(2)
        
        # Verify config saved
        verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        verified_enrollment = verify_response.json().get("onboardingConfig", {}).get("onboardingOptions", {}).get("enrollment", {})
        
        assert verified_enrollment.get("addFace") == True, "Face enrollment not enabled"
        assert verified_enrollment.get("addDevice") == False, "Device enrollment not disabled"
        
        logger.info(f"\n Verified configuration:")
        logger.info(f"   addFace: {verified_enrollment.get('addFace')}")
        logger.info(f"   addDevice: {verified_enrollment.get('addDevice')}")
        
        # ====================================================================
        # STEP 2: ENROLLMENT - ENROLL
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 2: Enrollment - Enroll")
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
        required_checks = enroll_data.get("requiredChecks", [])
        
        logger.info(f"ID: {enroll_data.get('transactionId', 'N/A')}")
        logger.info(f" Enrollment initiated: {unique_username}")
        logger.info(f"   Required Checks: {required_checks}")
        logger.info(f"   Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        # Verify device NOT required
        if 'addDevice' in required_checks:
            logger.error(f" ERROR: addDevice in required checks but should be disabled!")
            pytest.fail("Device enrollment required but should be disabled")
        
        logger.info(f"    Confirmed: Device NOT in required checks")
        
        assert enroll_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ENROLLMENT - ADD FACE (ONLY STEP - NO DEVICE)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: Enrollment - Add Face (NO DEVICE STEP)")
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
        
        logger.info(f"   Skipping device enrollment (disabled in config)")
        logger.info(f"   Proceeding directly to face enrollment...")
        
        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json=face_payload)
        
        if face_response.status_code == 200:
            face_data = face_response.json()
        else:
            face_data = face_response.json() if face_response.text else {}
        
        face_tx_id = face_data.get("transactionId", face_data.get("id", "N/A"))
        
        logger.info(f"ID: {face_tx_id}")
        logger.info(f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        # ====================================================================
        # EXTRACT VERIFICATION DATA
        # ====================================================================
        age_check = face_data.get("ageEstimationCheck", {})
        age_estimation_config = age_check.get("ageEstimation", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        actual_result = age_check.get("result", "UNKNOWN")
        
        # Liveness
        liveness_result_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_result_data.get("decision", "UNKNOWN")
        liveness_score = liveness_result_data.get("score_frr", "N/A")
        
        enrollment_status = face_data.get("enrollmentStatus", -1)
        
        # Determine face status
        if actual_result == "FAIL":
            face_status = " Failed: AGE ESTIMATION"
        elif actual_result in ["PASS", "SUCCESS"]:
            face_status = " SUCCESS"
        elif face_response.status_code != 200:
            face_status = f" Failed: {face_data.get('errorMsg', 'Unknown')}"
        else:
            face_status = " SUCCESS"
        
        logger.info(f"Status: {face_status}")
        logger.info(f"Result: {actual_result}")
        
        # ====================================================================
        # ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" FACE-ONLY ENROLLMENT ANALYSIS")
        logger.info("="*120)
        
        logger.info(f"\n Configuration:")
        logger.info(f"   Mode: FACE ONLY (no device)")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected Result: {expected_result}")
        
        logger.info(f"\n Detection Results:")
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
        logger.info(f"   Actual Result: {actual_result}")
        logger.info(f"   Liveness: {liveness_decision}")
        logger.info(f"   Enrollment Status: {enrollment_status}")
        
        # Compare expected vs actual
        behavior_match = actual_result == expected_result
        
        logger.info(f"\n Expected vs Actual:")
        logger.info(f"   Expected: {expected_result}")
        logger.info(f"   Actual: {actual_result}")
        logger.info(f"   Match: {' YES' if behavior_match else ' NO'}")
        
        # Explain why
        if age_from_server:
            age_in_range = min_age <= age_from_server <= max_age
            
            logger.info(f"\n Analysis:")
            logger.info(f"   Age {age_from_server} is {' WITHIN' if age_in_range else ' OUTSIDE'} range {min_age}-{max_age}")
            
            if not age_in_range:
                if age_from_server < min_age:
                    difference = min_age - age_from_server
                    logger.info(f"   Reason: {difference} years below minimum ({min_age})")
                else:
                    difference = age_from_server - max_age
                    logger.info(f"   Reason: {difference} years above maximum ({max_age})")
        
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
        logger.info(f"  Status: {' OUT OF RANGE' if actual_result == 'FAIL' else ' IN RANGE'}")
        
        logger.info("\n  " + "-"*116)
        logger.info("   Check Liveness")
        logger.info("  " + "-"*116)
        logger.info(f"  Liveness Decision: {liveness_decision}")
        logger.info(f"  Live Score: {liveness_score}")
        logger.info(f"  Status: {' LIVE' if liveness_decision == 'LIVE' else ' NOT LIVE'}")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" FINAL VERDICT - FACE-ONLY ENROLLMENT")
        logger.info("="*120)
        
        logger.info(f"\n Enrollment Process:")
        logger.info(f"   Username: {unique_username}")
        logger.info(f"   Mode: FACE ONLY (no device)")
        logger.info(f"   Liveness: {liveness_decision}")
        logger.info(f"   Enrollment Status: {enrollment_status}")
        
        logger.info(f"\n Age Verification:")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Required Range: {min_age}-{max_age} years")
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Detected Age: N/A")
        logger.info(f"   Result: {actual_result}")
        
        if behavior_match:
            logger.info(f"\n TEST PASSED ")
            logger.info(f"   Expected: {expected_result}")
            logger.info(f"   Actual: {actual_result}")
            logger.info(f"    Face-only enrollment behaves correctly for {scenario_name}")
        else:
            logger.error(f"\n TEST FAILED ")
            logger.error(f"   Expected: {expected_result}")
            logger.error(f"   Actual: {actual_result}")
            logger.error(f"    Behavior mismatch in face-only mode")
        
        # ====================================================================
        # CRITICAL ASSERTIONS
        # ====================================================================
        logger.info("\n" + ""*60)
        logger.info("CRITICAL VALIDATION CHECKS")
        logger.info(""*60)
        
        # Liveness check
        if liveness_decision != "LIVE":
            logger.error(f"\n LIVENESS FAILURE: {liveness_decision}")
            pytest.fail(f"Face-only enrollment liveness failed for '{scenario_name}': {liveness_decision}")
        else:
            logger.info(f"\n Liveness verified: {liveness_decision}")
        
        # Expected behavior check
        if not behavior_match:
            logger.error(f"\n BEHAVIOR MISMATCH IN FACE-ONLY MODE")
            logger.error(f"   Scenario: {scenario_name} ({min_age}-{max_age})")
            logger.error(f"   Detected Age: {age_from_server}")
            logger.error(f"   Expected: {expected_result}")
            logger.error(f"   Actual: {actual_result}")
            
            if expected_result == "FAIL" and actual_result != "FAIL":
                logger.error(f"\n    Age verification NOT enforced in face-only mode!")
                pytest.fail(
                    f"Face-only mode - Age verification not enforced for '{scenario_name}': "
                    f"Age {age_from_server} outside {min_age}-{max_age} but got {actual_result}"
                )
            elif expected_result == "PASS" and actual_result == "FAIL":
                logger.error(f"\n     False rejection in face-only mode")
                pytest.fail(
                    f"Face-only mode - False rejection for '{scenario_name}': "
                    f"Age {age_from_server} within {min_age}-{max_age} but got {actual_result}"
                )
        else:
            logger.info(f" Face-only enrollment behavior correct: {expected_result}")
        
        logger.info(f"\n" + "="*120)
        logger.info(f" Face-only test '{scenario_name}' completed")
        logger.info(f"="*120 + "\n")


@pytest.fixture(autouse=True, scope="function")
def cleanup():
    yield
    time.sleep(3)
