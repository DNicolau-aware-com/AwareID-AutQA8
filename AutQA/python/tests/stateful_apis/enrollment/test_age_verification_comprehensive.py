"""
Comprehensive Age Verification Test Suite
Data-driven tests for all age scenarios with expected behavior validation
"""
import pytest
import copy
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================================
# TEST DATA: Different age ranges and expected outcomes
# ============================================================================
AGE_TEST_SCENARIOS = [
    # (min_age, max_age, test_description, expected_result_for_age_50)
    (1, 16, "Child/Teen only (1-16)", "FAIL"),       # Age 50 should FAIL
    (18, 65, "Adult working age (18-65)", "PASS"),   # Age 50 should PASS
    (21, 100, "Legal adult (21-100)", "PASS"),       # Age 50 should PASS
    (1, 30, "Young person (1-30)", "FAIL"),          # Age 50 should FAIL
    (40, 60, "Middle age (40-60)", "PASS"),          # Age 50 should PASS
    (65, 120, "Senior only (65-120)", "FAIL"),       # Age 50 should FAIL
    (1, 101, "All ages (1-101)", "PASS"),            # Age 50 should PASS
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.age_verification
class TestAgeVerificationComprehensive:
    """Comprehensive age verification test suite with multiple scenarios"""
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", AGE_TEST_SCENARIOS)
    def test_age_verification_scenarios(
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
        Comprehensive test for age verification with multiple scenarios
        
        Tests different age ranges and validates expected behavior:
        - If age is in range  should PASS
        - If age is out of range  should FAIL
        
        FAILS the test if actual behavior doesn't match expected behavior
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
        logger.info(f"TEST SCENARIO: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected Result for Age 50: {expected_result}")
        logger.info(""*60)
        
        # ====================================================================
        # STEP 1: CONFIGURE ADMIN WITH TEST SCENARIO RANGE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(f"STEP 1: CONFIGURE ADMIN - {scenario_name} ({min_age}-{max_age} years)")
        logger.info("="*120)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": min_age,
            "maxAge": max_age,
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
        
        logger.info(f" Admin configured: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected Result: {expected_result}")
        time.sleep(2)
        
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
        
        logger.info(f" Enrollment initiated: {unique_username}")
        assert enroll_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ENROLLMENT - ADD DEVICE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: Enrollment - Add Device")
        logger.info("="*120)
        
        device_id = f"device_{int(time.time())}"
        device_payload = {
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web"
        }
        
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json=device_payload)
        
        logger.info(f" Device registered: {device_id}")
        assert device_response.status_code == 200
        time.sleep(1)
        
        # ====================================================================
        # STEP 4: ENROLLMENT - ADD FACE
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 4: Enrollment - Add Face (with Age Verification)")
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
        
        if face_response.status_code == 200:
            face_data = face_response.json()
        else:
            face_data = face_response.json() if face_response.text else {}
        
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
        
        # ====================================================================
        # ANALYSIS AND COMPARISON
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" VERIFICATION ANALYSIS")
        logger.info("="*120)
        
        logger.info(f"\n Test Configuration:")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected Result: {expected_result}")
        
        logger.info(f"\n Actual Detection:")
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
        logger.info(f"   Actual Result: {actual_result}")
        logger.info(f"   Liveness: {liveness_decision}")
        
        # Determine if behavior matches expectation
        behavior_match = actual_result == expected_result
        
        logger.info(f"\n Expected vs Actual:")
        logger.info(f"   Expected: {expected_result}")
        logger.info(f"   Actual: {actual_result}")
        logger.info(f"   Match: {' YES' if behavior_match else ' NO'}")
        
        # ====================================================================
        # DETAILED REASON ANALYSIS
        # ====================================================================
        if age_from_server:
            age_in_range = min_age <= age_from_server <= max_age
            
            logger.info(f"\n Why This Result:")
            logger.info(f"   Age {age_from_server} is {' WITHIN' if age_in_range else ' OUTSIDE'} range {min_age}-{max_age}")
            
            if not age_in_range:
                if age_from_server < min_age:
                    difference = min_age - age_from_server
                    logger.info(f"   Reason: {difference} years below minimum ({min_age})")
                else:
                    difference = age_from_server - max_age
                    logger.info(f"   Reason: {difference} years above maximum ({max_age})")
            
            if age_in_range and expected_result == "PASS":
                logger.info(f"    EXPECTED: Age in range, should pass")
            elif not age_in_range and expected_result == "FAIL":
                logger.info(f"    EXPECTED: Age out of range, should fail")
        
        # ====================================================================
        # LIVENESS CHECK
        # ====================================================================
        logger.info(f"\n Liveness Verification:")
        logger.info(f"   Decision: {liveness_decision}")
        logger.info(f"   Score: {liveness_score}")
        logger.info(f"   Status: {' LIVE' if liveness_decision == 'LIVE' else ' NOT LIVE / SPOOF'}")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(" FINAL VERDICT")
        logger.info("="*120)
        
        if behavior_match:
            logger.info(f"\n TEST PASSED ")
            logger.info(f"   Scenario: {scenario_name}")
            logger.info(f"   Expected: {expected_result}")
            logger.info(f"   Actual: {actual_result}")
            logger.info(f"    System behavior matches expected outcome")
        else:
            logger.error(f"\n TEST FAILED ")
            logger.error(f"   Scenario: {scenario_name}")
            logger.error(f"   Expected: {expected_result}")
            logger.error(f"   Actual: {actual_result}")
            logger.error(f"    System behavior does NOT match expected outcome")
        
        # ====================================================================
        # CRITICAL ASSERTIONS
        # ====================================================================
        logger.info("\n" + ""*60)
        logger.info("CRITICAL VALIDATION CHECKS")
        logger.info(""*60)
        
        # Check liveness
        if liveness_decision != "LIVE":
            logger.error(f"\n LIVENESS FAILURE: Decision was '{liveness_decision}'")
            pytest.fail(f"Liveness check failed for scenario '{scenario_name}': {liveness_decision}")
        else:
            logger.info(f"\n Liveness verified: {liveness_decision}")
        
        # Check expected behavior
        if not behavior_match:
            logger.error(f"\n BEHAVIOR MISMATCH")
            logger.error(f"   Scenario: {scenario_name} ({min_age}-{max_age} years)")
            logger.error(f"   Detected Age: {age_from_server} years")
            logger.error(f"   Expected: {expected_result}")
            logger.error(f"   Actual: {actual_result}")
            
            if expected_result == "FAIL" and actual_result != "FAIL":
                logger.error(f"\n    SECURITY RISK: Age verification NOT enforced!")
                logger.error(f"   Age {age_from_server} is outside {min_age}-{max_age} but enrollment succeeded")
                pytest.fail(
                    f"Age verification not enforced for '{scenario_name}': "
                    f"Age {age_from_server} outside {min_age}-{max_age} but got {actual_result} (expected {expected_result})"
                )
            elif expected_result == "PASS" and actual_result == "FAIL":
                logger.error(f"\n     FALSE REJECTION: Valid age was rejected")
                pytest.fail(
                    f"False rejection for '{scenario_name}': "
                    f"Age {age_from_server} within {min_age}-{max_age} but got {actual_result} (expected {expected_result})"
                )
        else:
            logger.info(f" Behavior matches expected outcome: {expected_result}")
        
        logger.info(f"\n" + "="*120)
        logger.info(f" Test scenario '{scenario_name}' completed successfully")
        logger.info(f"="*120 + "\n")


@pytest.fixture(autouse=True, scope="function")
def cleanup():
    yield
    time.sleep(3)
