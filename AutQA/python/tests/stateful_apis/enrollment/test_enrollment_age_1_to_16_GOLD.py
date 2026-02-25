"""
GOLD STANDARD Test: Age Verification 1-16 with Complete Validation
This is the template for all future enrollment tests
Includes: Age, Liveness, Transaction tracking, Timestamps, All assertions
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
def test_enroll_with_age_1_to_16_gold_standard(
    api_client,
    unique_username,
    face_frames,
    workflow,
    env_vars,
    caplog,
):
    """
    GOLD STANDARD Test: Complete age verification with all validations
    
    Test Flow:
    1. Configure admin (age 1-16)
    2. Enroll user
    3. Add device
    4. Add face (with age + liveness validation)
    5. Extract ALL transaction data
    6. Validate ALL results
    7. Generate comprehensive report
    """
    
    caplog.set_level(logging.INFO)
    
    # ========================================================================
    # TEST DATA
    # ========================================================================
    face_image_base64 = env_vars.get("FACE")
    if not face_image_base64:
        pytest.skip("FACE not found in .env")
    
    if face_image_base64.startswith('data:'):
        face_image_base64 = face_image_base64.split(',')[1]
    
    # Test configuration
    MIN_AGE = 1
    MAX_AGE = 16
    EXPECTED_RESULT = "FAIL"  # Our test face is age 50
    SCENARIO_NAME = "Child/Teen Only (1-16 years)"
    
    # ========================================================================
    # TEST HEADER
    # ========================================================================
    logger.info("\n" + "🎯"*60)
    logger.info("GOLD STANDARD AGE VERIFICATION TEST")
    logger.info(f"Scenario: {SCENARIO_NAME}")
    logger.info(f"Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"Expected: {EXPECTED_RESULT}")
    logger.info("🎯"*60)
    
    # Transaction tracker
    transactions = {}
    start_time = datetime.now()
    
    # ========================================================================
    # STEP 1: CONFIGURE ADMIN
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info(f"STEP 1: ADMIN CONFIGURATION")
    logger.info("="*120)
    step_start = datetime.now()
    
    config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
    current_config = config_response.json().get("onboardingConfig", {})
    new_config = copy.deepcopy(current_config)
    
    # Configure age verification
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
    
    # Configure other workflows
    authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
    authentication['verifyFace'] = True
    
    reenrollment = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
    reenrollment['verifyFace'] = True
    
    update_response = api_client.http_client.post(
        "/onboarding/admin/customerConfig",
        json={"onboardingConfig": new_config}
    )
    
    # Log configuration
    logger.info(f"✅ Configuration saved:")
    logger.info(f"   Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"   Tolerance: 0 years")
    logger.info(f"   Face: ✅ ENABLED")
    logger.info(f"   Device: ✅ ENABLED")
    logger.info(f"   Document: ❌ DISABLED")
    logger.info(f"   Duration: {(datetime.now() - step_start).total_seconds():.2f}s")
    
    time.sleep(1)
    
    # ========================================================================
    # STEP 2: ENROLLMENT - ENROLL
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 2: Enrollment - Enroll")
    logger.info("="*120)
    step_start = datetime.now()
    
    enroll_payload = {
        "username": unique_username,
        "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
        "firstName": env_vars.get("FIRSTNAME") or "Test",
        "lastName": env_vars.get("LASTNAME") or "User",
    }
    
    enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json=enroll_payload)
    enroll_data = enroll_response.json()
    enrollment_token = enroll_data.get("enrollmentToken")
    
    # Capture transaction
    enroll_tx_id = enroll_data.get("transactionId", "N/A")
    enroll_timestamp = datetime.now()
    transactions['enroll'] = {
        "id": enroll_tx_id,
        "timestamp": enroll_timestamp,
        "status": "SUCCESS" if enrollment_token else "FAILED",
        "data": enroll_data
    }
    
    logger.info(f"Transaction ID: {enroll_tx_id}")
    logger.info(f"Status: ✅ SUCCESS")
    logger.info(f"Username: {unique_username}")
    logger.info(f"Timestamp: {enroll_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    logger.info(f"Duration: {(datetime.now() - step_start).total_seconds():.2f}s")
    
    assert enroll_response.status_code == 200, f"Enroll failed: {enroll_response.status_code}"
    assert enrollment_token, "Enrollment token missing"
    
    time.sleep(1)
    
    # ========================================================================
    # STEP 3: ENROLLMENT - ADD DEVICE
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 3: Enrollment - Add Device")
    logger.info("="*120)
    step_start = datetime.now()
    
    device_id = f"device_{int(time.time())}"
    device_payload = {
        "enrollmentToken": enrollment_token,
        "deviceId": device_id,
        "platform": "web"
    }
    
    device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json=device_payload)
    device_data = device_response.json()
    
    # Capture transaction
    device_tx_id = device_data.get("transactionId", "N/A")
    device_timestamp = datetime.now()
    transactions['device'] = {
        "id": device_tx_id,
        "timestamp": device_timestamp,
        "status": "Device registered",
        "data": device_data
    }
    
    logger.info(f"Transaction ID: {device_tx_id}")
    logger.info(f"Status: ✅ Device registered")
    logger.info(f"Device ID: {device_id}")
    logger.info(f"Platform: web")
    logger.info(f"Timestamp: {device_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    logger.info(f"Duration: {(datetime.now() - step_start).total_seconds():.2f}s")
    
    assert device_response.status_code == 200, f"Add device failed: {device_response.status_code}"
    
    time.sleep(1)
    
    # ========================================================================
    # STEP 4: ENROLLMENT - ADD FACE (with Age + Liveness)
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("STEP 4: Enrollment - Add Face (Age Verification + Liveness Check)")
    logger.info("="*120)
    step_start = datetime.now()
    
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
    face_data = face_response.json() if face_response.status_code == 200 else {}
    
    face_tx_id = face_data.get("transactionId", "N/A")
    face_timestamp = datetime.now()
    
    # ========================================================================
    # EXTRACT ALL DATA
    # ========================================================================
    
    # Age Estimation
    age_check = face_data.get("ageEstimationCheck", {})
    age_from_server = age_check.get("ageFromFaceLivenessServer")
    actual_result = age_check.get("result", "UNKNOWN")
    age_config = age_check.get("ageEstimation", {})
    config_min_age = age_config.get("minAge")
    config_max_age = age_config.get("maxAge")
    
    # Liveness Detection
    liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
    liveness_decision = liveness_data.get("decision", "UNKNOWN")
    liveness_score = liveness_data.get("score_frr", "N/A")
    
    # Enrollment Status
    enrollment_status = face_data.get("enrollmentStatus")
    registration_code = face_data.get("registrationCode")
    
    # Determine status
    if actual_result == "FAIL":
        face_status = "❌ FAILED: AGE ESTIMATION"
    elif liveness_decision != "LIVE":
        face_status = "❌ FAILED: LIVENESS"
    else:
        face_status = "✅ SUCCESS"
    
    # Capture transaction
    transactions['face'] = {
        "id": face_tx_id,
        "timestamp": face_timestamp,
        "status": face_status,
        "age_detected": age_from_server,
        "age_result": actual_result,
        "liveness_decision": liveness_decision,
        "liveness_score": liveness_score,
        "enrollment_status": enrollment_status,
        "data": face_data
    }
    
    # Log main transaction
    logger.info(f"Transaction ID: {face_tx_id}")
    logger.info(f"Status: {face_status}")
    logger.info(f"Timestamp: {face_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
    logger.info(f"Duration: {(datetime.now() - step_start).total_seconds():.2f}s")
    
    # ========================================================================
    # SUB-TRANSACTIONS: Age Detection
    # ========================================================================
    logger.info("\n" + "-"*120)
    logger.info("📸 Sub-Transaction: Analyze Image (Age Detection)")
    logger.info("-"*120)
    logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
    logger.info(f"   Required Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"   Configuration Match: minAge={config_min_age}, maxAge={config_max_age}")
    logger.info(f"   Age Result: {actual_result}")
    
    if age_from_server:
        age_in_range = MIN_AGE <= age_from_server <= MAX_AGE
        logger.info(f"   Age In Range: {'✅ YES' if age_in_range else '❌ NO'}")
        
        if not age_in_range:
            if age_from_server < MIN_AGE:
                diff = MIN_AGE - age_from_server
                logger.info(f"   Reason: {diff} years BELOW minimum ({MIN_AGE})")
            else:
                diff = age_from_server - MAX_AGE
                logger.info(f"   Reason: {diff} years ABOVE maximum ({MAX_AGE})")
                logger.info(f"   TO PASS: Use face image aged {MIN_AGE}-{MAX_AGE} years")
    
    # ========================================================================
    # SUB-TRANSACTIONS: Liveness Check
    # ========================================================================
    logger.info("\n" + "-"*120)
    logger.info("🔴 Sub-Transaction: Check Liveness (Spoof Detection)")
    logger.info("-"*120)
    logger.info(f"   Liveness Decision: {liveness_decision}")
    logger.info(f"   Liveness Score (FRR): {liveness_score}")
    logger.info(f"   Status: {'✅ LIVE' if liveness_decision == 'LIVE' else '❌ NOT LIVE'}")
    
    # Additional liveness details if available
    if "liveness_result" in liveness_data:
        logger.info(f"   Confidence: {liveness_data.get('confidence', 'N/A')}")
    
    # ========================================================================
    # COMPREHENSIVE ANALYSIS
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("📊 COMPREHENSIVE ANALYSIS")
    logger.info("="*120)
    
    logger.info(f"\n📋 Test Configuration:")
    logger.info(f"   Scenario: {SCENARIO_NAME}")
    logger.info(f"   Age Range: {MIN_AGE}-{MAX_AGE} years")
    logger.info(f"   Expected Result: {EXPECTED_RESULT}")
    
    logger.info(f"\n👤 Actual Results:")
    logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
    logger.info(f"   Age Verification: {actual_result}")
    logger.info(f"   Liveness Check: {liveness_decision}")
    logger.info(f"   Enrollment Status: {enrollment_status} ({['FAILED', 'PENDING', 'COMPLETE'][enrollment_status] if enrollment_status in [0,1,2] else 'UNKNOWN'})")
    
    behavior_match = actual_result == EXPECTED_RESULT
    
    logger.info(f"\n🎯 Expected vs Actual:")
    logger.info(f"   Expected: {EXPECTED_RESULT}")
    logger.info(f"   Actual: {actual_result}")
    logger.info(f"   Match: {'✅ YES' if behavior_match else '❌ NO'}")
    
    # ========================================================================
    # TRANSACTION SUMMARY
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("📑 TRANSACTION SUMMARY")
    logger.info("="*120)
    
    total_time = (datetime.now() - start_time).total_seconds()
    
    for step_name, tx_data in transactions.items():
        logger.info(f"\n{step_name.upper()}:")
        logger.info(f"   Transaction ID: {tx_data['id']}")
        logger.info(f"   Status: {tx_data['status']}")
        logger.info(f"   Timestamp: {tx_data['timestamp'].strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        if 'age_detected' in tx_data:
            logger.info(f"   Age Detected: {tx_data['age_detected']}")
            logger.info(f"   Age Result: {tx_data['age_result']}")
            logger.info(f"   Liveness: {tx_data['liveness_decision']} (score: {tx_data['liveness_score']})")
    
    logger.info(f"\nTotal Test Duration: {total_time:.2f}s")
    
    # ========================================================================
    # CRITICAL VALIDATIONS
    # ========================================================================
    logger.info("\n" + "🔥"*60)
    logger.info("CRITICAL VALIDATION CHECKS")
    logger.info("🔥"*60)
    
    # Validation 1: Liveness Check
    logger.info(f"\n1️⃣  LIVENESS VALIDATION:")
    if liveness_decision != "LIVE":
        logger.error(f"   🚨 LIVENESS FAILURE: {liveness_decision}")
        logger.error(f"   This could be a spoof attack!")
        pytest.fail(f"Liveness check failed: {liveness_decision}")
    else:
        logger.info(f"   ✅ Liveness verified: {liveness_decision}")
        logger.info(f"   Score: {liveness_score}")
    
    # Validation 2: Age Detection
    logger.info(f"\n2️⃣  AGE DETECTION VALIDATION:")
    if not age_from_server:
        logger.error(f"   🚨 AGE NOT DETECTED")
        pytest.fail("Age was not detected from face")
    else:
        logger.info(f"   ✅ Age detected: {age_from_server} years")
    
    # Validation 3: Age Verification Enforcement
    logger.info(f"\n3️⃣  AGE VERIFICATION ENFORCEMENT:")
    if age_from_server:
        age_in_range = MIN_AGE <= age_from_server <= MAX_AGE
        
        # Check for bypass
        if not age_in_range and actual_result != "FAIL":
            logger.error(f"   🚨🚨🚨 AGE VERIFICATION NOT ENFORCED! 🚨🚨🚨")
            logger.error(f"   Age {age_from_server} is outside {MIN_AGE}-{MAX_AGE}")
            logger.error(f"   But enrollment result was: {actual_result}")
            logger.error(f"   SECURITY RISK: Age restrictions can be bypassed!")
            pytest.fail(
                f"Age verification bypassed: Age {age_from_server} outside {MIN_AGE}-{MAX_AGE} "
                f"but got result '{actual_result}' (expected {EXPECTED_RESULT})"
            )
        
        logger.info(f"   ✅ Age verification correctly enforced")
        logger.info(f"   Age {age_from_server} correctly {'rejected' if not age_in_range else 'accepted'}")
    
    # Validation 4: Expected Behavior Match
    logger.info(f"\n4️⃣  EXPECTED BEHAVIOR VALIDATION:")
    if not behavior_match:
        logger.error(f"   🚨 BEHAVIOR MISMATCH")
        logger.error(f"   Expected: {EXPECTED_RESULT}")
        logger.error(f"   Actual: {actual_result}")
        
        if EXPECTED_RESULT == "FAIL" and actual_result != "FAIL":
            pytest.fail(f"Expected age verification to FAIL, but got {actual_result}")
        elif EXPECTED_RESULT == "PASS" and actual_result == "FAIL":
            pytest.fail(f"Expected age verification to PASS, but got {actual_result}")
    else:
        logger.info(f"   ✅ Behavior matches expectation")
        logger.info(f"   Expected {EXPECTED_RESULT}, got {actual_result}")
    
    # Validation 5: Configuration Integrity
    logger.info(f"\n5️⃣  CONFIGURATION INTEGRITY:")
    if config_min_age != MIN_AGE or config_max_age != MAX_AGE:
        logger.error(f"   🚨 CONFIGURATION MISMATCH")
        logger.error(f"   Expected: {MIN_AGE}-{MAX_AGE}")
        logger.error(f"   Got: {config_min_age}-{config_max_age}")
        pytest.fail("Age configuration was not properly set")
    else:
        logger.info(f"   ✅ Configuration correctly applied")
        logger.info(f"   Age range: {config_min_age}-{config_max_age}")
    
    # ========================================================================
    # FINAL VERDICT
    # ========================================================================
    logger.info("\n" + "="*120)
    logger.info("🏁 FINAL VERDICT")
    logger.info("="*120)
    
    if behavior_match and liveness_decision == "LIVE" and age_from_server:
        logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
        logger.info(f"   Scenario: {SCENARIO_NAME}")
        logger.info(f"   Age verification: ✅ CORRECTLY ENFORCED")
        logger.info(f"   Liveness detection: ✅ WORKING")
        logger.info(f"   All validations: ✅ PASSED")
        logger.info(f"   Test duration: {total_time:.2f}s")
    else:
        logger.error(f"\n❌❌❌ TEST FAILED ❌❌❌")
        logger.error(f"   Check errors above for details")
    
    logger.info("\n" + "="*120 + "\n")
