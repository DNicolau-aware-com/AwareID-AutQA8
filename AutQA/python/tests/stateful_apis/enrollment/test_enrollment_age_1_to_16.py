"""
Enhanced Enrollment Age 1-16 Test with Complete Validation
Face + Device enrollment with comprehensive transaction tracking
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
def test_enroll_with_age_1_to_16(
    api_client,
    unique_username,
    face_frames,
    workflow,
    env_vars,
    caplog,
):
    """
    Test enrollment with age 1-16 (child/teen only)
    Expected: FAIL (test face is ~50 years old)
    """
    
    caplog.set_level(logging.INFO)
    
    # Test configuration
    MIN_AGE = 1
    MAX_AGE = 16
    EXPECTED_RESULT = "FAIL"
    SCENARIO_NAME = "Child/Teen Only (1-16 years)"
    
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
    logger.info("ENROLLMENT AGE 1-16 VERIFICATION TEST")
    logger.info(f"Scenario: {SCENARIO_NAME}")
    logger.info(f"Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"Expected Result: {EXPECTED_RESULT}")
    logger.info(f"Test Started: {test_start_time.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    logger.info("🎯"*60)
    
    # ====================================================================
    # STEP 1: ADMIN CONFIGURATION
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
    enrollment['addDocument'] = False
    
    api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
    
    config_duration = (datetime.now() - step_start).total_seconds()
    
    transactions['config'] = {
        "id": "CONFIG",
        "timestamp": datetime.now(),
        "status": "✅ APPLIED",
        "duration": config_duration,
    }
    
    logger.info(f"✅ Configuration Applied:")
    logger.info(f"   Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"   Tolerance: 0 years (strict)")
    logger.info(f"   Duration: {config_duration:.2f}s")
    
    time.sleep(1)
    
    # ====================================================================
    # STEP 2: ENROLL USER
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
    enroll_timestamp = datetime.now()
    
    transactions['enroll'] = {
        "id": enroll_tx_id,
        "timestamp": enroll_timestamp,
        "status": "✅ SUCCESS",
        "duration": (enroll_timestamp - step_start).total_seconds(),
        "username": unique_username,
    }
    
    logger.info(f"Transaction ID: {enroll_tx_id}")
    logger.info(f"Status: ✅ SUCCESS")
    logger.info(f"Username: {unique_username}")
    logger.info(f"Duration: {transactions['enroll']['duration']:.2f}s")
    logger.info(f"Timestamp: {enroll_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    
    assert enrollment_token, "Enrollment token missing"
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
    
    device_data = device_response.json()
    device_tx_id = device_data.get("transactionId", "N/A")
    device_timestamp = datetime.now()
    
    transactions['device'] = {
        "id": device_tx_id,
        "timestamp": device_timestamp,
        "status": "✅ REGISTERED",
        "duration": (device_timestamp - step_start).total_seconds(),
        "device_id": device_id,
    }
    
    logger.info(f"Transaction ID: {device_tx_id}")
    logger.info(f"Status: ✅ REGISTERED")
    logger.info(f"Device ID: {device_id}")
    logger.info(f"Duration: {transactions['device']['duration']:.2f}s")
    logger.info(f"Timestamp: {device_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    
    assert device_response.status_code == 200
    time.sleep(1)
    
    # ====================================================================
    # STEP 4: ADD FACE (Age + Liveness)
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 4: Enrollment - Add Face (Age + Liveness Verification)")
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
    face_timestamp = datetime.now()
    
    # Extract data
    age_check = face_data.get("ageEstimationCheck", {})
    age_from_server = age_check.get("ageFromFaceLivenessServer")
    age_result = age_check.get("result", "UNKNOWN")
    age_config = age_check.get("ageEstimation", {})
    config_min_age = age_config.get("minAge")
    config_max_age = age_config.get("maxAge")
    
    liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
    liveness_decision = liveness_data.get("decision", "UNKNOWN")
    liveness_score = liveness_data.get("score_frr", "N/A")
    
    age_in_range = None
    if age_from_server and MIN_AGE and MAX_AGE:
        age_in_range = MIN_AGE <= age_from_server <= MAX_AGE
    
    face_status = "❌ FAILED: AGE" if age_result == "FAIL" else "✅ SUCCESS"
    
    transactions['face'] = {
        "id": face_tx_id,
        "timestamp": face_timestamp,
        "status": face_status,
        "duration": (face_timestamp - step_start).total_seconds(),
        "age": age_from_server,
        "age_result": age_result,
        "age_in_range": age_in_range,
        "liveness": liveness_decision,
        "liveness_score": liveness_score,
    }
    
    logger.info(f"Transaction ID: {face_tx_id}")
    logger.info(f"Status: {face_status}")
    logger.info(f"Age: {age_from_server} years")
    logger.info(f"Age Result: {age_result}")
    logger.info(f"Liveness: {liveness_decision} (score: {liveness_score})")
    logger.info(f"Duration: {transactions['face']['duration']:.2f}s")
    logger.info(f"Timestamp: {face_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    
    # ====================================================================
    # COMPREHENSIVE ANALYSIS
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("📊 COMPREHENSIVE ANALYSIS")
    logger.info("="*120)
    
    total_duration = (datetime.now() - test_start_time).total_seconds()
    
    logger.info(f"\n📋 Test Configuration:")
    logger.info(f"   Scenario: {SCENARIO_NAME}")
    logger.info(f"   Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"   Expected: {EXPECTED_RESULT}")
    
    logger.info(f"\n👤 Results:")
    logger.info(f"   Age: {age_from_server} years")
    logger.info(f"   Age Result: {age_result}")
    logger.info(f"   Liveness: {liveness_decision}")
    
    behavior_match = (age_result == EXPECTED_RESULT)
    logger.info(f"\n🎯 Expected vs Actual:")
    logger.info(f"   Expected: {EXPECTED_RESULT}")
    logger.info(f"   Actual: {age_result}")
    logger.info(f"   Match: {'✅ YES' if behavior_match else '❌ NO'}")
    
    # ====================================================================
    # TRANSACTION SUMMARY
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("📑 TRANSACTION SUMMARY")
    logger.info("="*120)
    
    for step_name, tx_data in transactions.items():
        logger.info(f"\n{step_name.upper()}:")
        logger.info(f"   Transaction ID: {tx_data['id']}")
        logger.info(f"   Status: {tx_data['status']}")
        logger.info(f"   Duration: {tx_data['duration']:.2f}s")
        logger.info(f"   Timestamp: {tx_data['timestamp'].strftime('%m/%d/%Y, %I:%M:%S %p')}")
    
    logger.info(f"\nTotal Duration: {total_duration:.2f}s")
    
    # ====================================================================
    # CRITICAL VALIDATIONS
    # ====================================================================
    logger.info("\n" + "🔥"*60)
    logger.info("CRITICAL VALIDATIONS")
    logger.info("🔥"*60)
    
    # 1. Liveness
    logger.info(f"\n1️⃣  Liveness Validation:")
    assert liveness_decision == "LIVE", f"Liveness failed: {liveness_decision}"
    logger.info(f"   ✅ PASSED ({liveness_decision})")
    
    # 2. Age Detection
    logger.info(f"\n2️⃣  Age Detection Validation:")
    assert age_from_server, "Age not detected"
    logger.info(f"   ✅ PASSED ({age_from_server} years)")
    
    # 3. Age Enforcement
    logger.info(f"\n3️⃣  Age Enforcement Validation:")
    if age_from_server and age_in_range is not None:
        if not age_in_range and age_result != "FAIL":
            pytest.fail(f"Age bypass: {age_from_server} outside {MIN_AGE}-{MAX_AGE} but got {age_result}")
    logger.info(f"   ✅ PASSED (Correctly enforced)")
    
    # 4. Configuration Integrity
    logger.info(f"\n4️⃣  Configuration Integrity:")
    assert config_min_age == MIN_AGE and config_max_age == MAX_AGE, "Config mismatch"
    logger.info(f"   ✅ PASSED (Config: {config_min_age}-{config_max_age})")
    
    # 5. Behavior Match
    logger.info(f"\n5️⃣  Behavior Match Validation:")
    assert behavior_match, f"Expected {EXPECTED_RESULT}, got {age_result}"
    logger.info(f"   ✅ PASSED")
    
    # ====================================================================
    # FINAL VERDICT
    # ====================================================================
    logger.info("\n" + "="*120)
    logger.info("🏁 FINAL VERDICT")
    logger.info("="*120)
    logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
    logger.info(f"   Scenario: {SCENARIO_NAME}")
    logger.info(f"   All validations: ✅ PASSED")
    logger.info(f"   Duration: {total_duration:.2f}s")
    logger.info("\n" + "="*120 + "\n")
