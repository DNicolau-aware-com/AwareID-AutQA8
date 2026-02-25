"""
Enhanced Enrollment with Age Verification (1-101 years)
Tests enrollment accepting all ages with complete validation
"""
import pytest
import copy
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.age_verification
def test_enroll_with_age_verification_1_to_101(
    api_client,
    unique_username,
    face_frames,
    workflow,
    env_vars,
    caplog,
):
    """
    Test enrollment with age 1-101 (all ages allowed)
    Expected: PASS
    """
    
    caplog.set_level(logging.INFO)
    
    # Test configuration
    MIN_AGE = 1
    MAX_AGE = 101
    EXPECTED_RESULT = "PASS"
    SCENARIO_NAME = "All Ages (1-101 years)"
    
    face_image_base64 = env_vars.get("FACE")
    if not face_image_base64:
        pytest.skip("FACE not found in .env")
    
    if face_image_base64.startswith('data:'):
        face_image_base64 = face_image_base64.split(',')[1]
    
    # Transaction tracking
    transactions = {}
    test_start_time = datetime.now()
    
    # ====================================================================
    # TEST HEADER
    # ====================================================================
    logger.info("\n" + "🎯"*60)
    logger.info("ENROLLMENT WITH AGE VERIFICATION TEST (1-101)")
    logger.info(f"Scenario: {SCENARIO_NAME}")
    logger.info(f"Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"Expected: {EXPECTED_RESULT}")
    logger.info("🎯"*60)
    
    # ====================================================================
    # STEP 1: CONFIG
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 1: ADMIN CONFIGURATION")
    logger.info("="*120)
    step_start = datetime.now()
    
    config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
    current_config = config_response.json().get("onboardingConfig", {})
    new_config = copy.deepcopy(current_config)
    
    enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
    enrollment["ageEstimation"] = {
        "enabled": True,
        "minAge": MIN_AGE,
        "maxAge": MAX_AGE,
        "minTolerance": 0,
        "maxTolerance": 0
    }
    enrollment['addFace'] = True
    enrollment['addDevice'] = True
    
    api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
    
    config_duration = (datetime.now() - step_start).total_seconds()
    
    transactions['config'] = {
        "id": "CONFIG",
        "timestamp": datetime.now(),
        "status": "✅ APPLIED",
        "duration": config_duration,
    }
    
    logger.info(f"✅ Config: Age {MIN_AGE}-{MAX_AGE}, Duration: {config_duration:.2f}s")
    time.sleep(1)
    
    # ====================================================================
    # STEP 2: ENROLL
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 2: Enrollment - Enroll User")
    logger.info("="*120)
    step_start = datetime.now()
    
    enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
        "username": unique_username,
        "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
        "firstName": env_vars.get("FIRSTNAME") or "Test",
        "lastName": env_vars.get("LASTNAME") or "User",
    })
    
    enroll_data = enroll_response.json()
    enrollment_token = enroll_data.get("enrollmentToken")
    enroll_tx_id = enroll_data.get("transactionId", "N/A")
    
    transactions['enroll'] = {
        "id": enroll_tx_id,
        "timestamp": datetime.now(),
        "status": "✅ SUCCESS",
        "duration": (datetime.now() - step_start).total_seconds(),
    }
    
    logger.info(f"✅ Username: {unique_username}, TX: {enroll_tx_id}")
    assert enrollment_token
    time.sleep(1)
    
    # ====================================================================
    # STEP 3: ADD DEVICE
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 3: Enrollment - Add Device")
    logger.info("="*120)
    step_start = datetime.now()
    
    device_id = f"device_{int(time.time())}"
    device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
        "enrollmentToken": enrollment_token,
        "deviceId": device_id,
        "platform": "web"
    })
    
    device_tx_id = device_response.json().get("transactionId", "N/A")
    
    transactions['device'] = {
        "id": device_tx_id,
        "timestamp": datetime.now(),
        "status": "✅ REGISTERED",
        "duration": (datetime.now() - step_start).total_seconds(),
    }
    
    logger.info(f"✅ Device: {device_id}, TX: {device_tx_id}")
    assert device_response.status_code == 200
    time.sleep(1)
    
    # ====================================================================
    # STEP 4: ADD FACE
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 4: Enrollment - Add Face (Age + Liveness)")
    logger.info("="*120)
    step_start = datetime.now()
    
    face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json={
        "enrollmentToken": enrollment_token,
        "faceLivenessData": {
            "video": {
                "meta_data": {"username": unique_username},
                "workflow_data": {"workflow": workflow, "frames": face_frames},
            },
        },
    })
    
    face_data = face_response.json() if face_response.status_code == 200 else {}
    face_tx_id = face_data.get("transactionId", "N/A")
    
    # Extract data
    age_check = face_data.get("ageEstimationCheck", {})
    age_from_server = age_check.get("ageFromFaceLivenessServer")
    age_result = age_check.get("result", "UNKNOWN")
    
    liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
    liveness_decision = liveness_data.get("decision", "UNKNOWN")
    liveness_score = liveness_data.get("score_frr", "N/A")
    
    transactions['face'] = {
        "id": face_tx_id,
        "timestamp": datetime.now(),
        "status": "✅ SUCCESS" if age_result == EXPECTED_RESULT else "❌ FAILED",
        "duration": (datetime.now() - step_start).total_seconds(),
        "age": age_from_server,
        "age_result": age_result,
        "liveness": liveness_decision,
    }
    
    logger.info(f"✅ Age: {age_from_server}, Result: {age_result}, Liveness: {liveness_decision}, TX: {face_tx_id}")
    
    # ====================================================================
    # COMPREHENSIVE ANALYSIS
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("📊 COMPREHENSIVE ANALYSIS")
    logger.info("="*120)
    
    total_duration = (datetime.now() - test_start_time).total_seconds()
    
    logger.info(f"\nConfiguration: {SCENARIO_NAME}")
    logger.info(f"Results: Age={age_from_server}, Result={age_result}, Liveness={liveness_decision}")
    logger.info(f"Total Duration: {total_duration:.2f}s")
    
    # ====================================================================
    # CRITICAL VALIDATIONS
    # ====================================================================
    logger.info("\n" + "🔥"*60)
    logger.info("CRITICAL VALIDATIONS")
    logger.info("🔥"*60)
    
    # 1. Liveness
    assert liveness_decision == "LIVE", f"Liveness failed: {liveness_decision}"
    logger.info(f"1️⃣  Liveness: ✅ PASSED")
    
    # 2. Age detection
    assert age_from_server, "Age not detected"
    logger.info(f"2️⃣  Age Detection: ✅ PASSED")
    
    # 3. Age result (should PASS for 1-101)
    assert age_result == EXPECTED_RESULT, f"Expected {EXPECTED_RESULT}, got {age_result}"
    logger.info(f"3️⃣  Age Result: ✅ PASSED ({age_result})")
    
    # ====================================================================
    # FINAL VERDICT
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("🏁 FINAL VERDICT")
    logger.info("="*120)
    logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
    logger.info(f"   Duration: {total_duration:.2f}s")
    logger.info("\n" + "="*120 + "\n")
