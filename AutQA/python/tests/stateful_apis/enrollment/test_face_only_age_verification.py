"""
Enhanced Face-Only Age Verification Test with Full Validation
Face enrollment without device - complete transaction tracking and validation
"""
import pytest
import copy
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# Test scenarios: (minAge, maxAge, scenario_name, expected_result)
AGE_SCENARIOS = [
    (1, 16, "Child/Teen (1-16)", "FAIL"),
    (18, 65, "Adult (18-65)", "PASS"),
    (21, 100, "Legal adult (21-100)", "PASS"),
    (1, 30, "Young (1-30)", "FAIL"),
    (40, 60, "Middle age (40-60)", "PASS"),
    (65, 120, "Senior (65-120)", "FAIL"),
    (1, 101, "All ages (1-101)", "PASS"),
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.age_verification
class TestFaceOnlyAgeVerification:
    """
    Face-only age verification tests (no device enrollment)
    Tests minimal enrollment path with age + liveness validation
    """
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", AGE_SCENARIOS)
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
        Test age verification with FACE ONLY (no device)
        
        Validates:
        - Age detection accuracy
        - Liveness detection
        - Age range enforcement
        - Minimal enrollment workflow
        """
        
        caplog.set_level(logging.INFO)
        
        # Test data
        face_image_base64 = env_vars.get("FACE")
        if not face_image_base64:
            pytest.skip("FACE image not found in .env")
        
        if face_image_base64.startswith('data:'):
            face_image_base64 = face_image_base64.split(',')[1]
        
        # Transaction tracking
        transactions = {}
        test_start_time = datetime.now()
        
        # ====================================================================
        # TEST HEADER
        # ====================================================================
        logger.info("\n" + "🎯"*60)
        logger.info("FACE-ONLY AGE VERIFICATION TEST")
        logger.info(f"Scenario: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected Result: {expected_result}")
        logger.info(f"Workflow: FACE ONLY (no device)")
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
        assert config_response.status_code == 200, f"Failed to get config: {config_response.status_code}"
        
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        # Configure age verification - FACE ONLY
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {
            "enabled": True,
            "minAge": min_age,
            "maxAge": max_age,
            "minTolerance": 0,
            "maxTolerance": 0
        }
        enrollment['addFace'] = True
        enrollment['addDevice'] = False  # DISABLED for face-only test
        enrollment['addDocument'] = False
        
        authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        authentication['verifyFace'] = True
        
        update_response = api_client.http_client.post(
            "/onboarding/admin/customerConfig",
            json={"onboardingConfig": new_config}
        )
        assert update_response.status_code == 200, f"Config update failed: {update_response.status_code}"
        
        config_duration = (datetime.now() - step_start).total_seconds()
        
        logger.info(f"✅ Configuration Applied:")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Tolerance: 0 years (strict)")
        logger.info(f"   Face Enrollment: ✅ ENABLED")
        logger.info(f"   Device Enrollment: ❌ DISABLED (face-only mode)")
        logger.info(f"   Document Enrollment: ❌ DISABLED")
        logger.info(f"   Duration: {config_duration:.2f}s")
        logger.info(f"   Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        time.sleep(1)
        
        # ====================================================================
        # STEP 2: ENROLL USER
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 2: Enrollment - Enroll User")
        logger.info("="*120)
        step_start = datetime.now()
        
        enroll_payload = {
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
        
        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=enroll_payload
        )
        assert enroll_response.status_code == 200, f"Enrollment failed: {enroll_response.status_code}"
        
        enroll_data = enroll_response.json()
        enrollment_token = enroll_data.get("enrollmentToken")
        enroll_tx_id = enroll_data.get("transactionId", "N/A")
        enroll_timestamp = datetime.now()
        enroll_duration = (enroll_timestamp - step_start).total_seconds()
        
        transactions['enroll'] = {
            "transaction_id": enroll_tx_id,
            "timestamp": enroll_timestamp,
            "status": "✅ SUCCESS",
            "duration_seconds": enroll_duration,
            "username": unique_username,
        }
        
        logger.info(f"Transaction ID: {enroll_tx_id}")
        logger.info(f"Status: ✅ SUCCESS")
        logger.info(f"Username: {unique_username}")
        logger.info(f"Duration: {enroll_duration:.2f}s")
        logger.info(f"Timestamp: {enroll_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        assert enrollment_token, "Enrollment token missing"
        
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ADD FACE (Age + Liveness) - FINAL STEP
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: Enrollment - Add Face (FINAL STEP - No Device)")
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
        
        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json=face_payload
        )
        
        face_data = face_response.json() if face_response.status_code == 200 else {}
        face_tx_id = face_data.get("transactionId", "N/A")
        face_timestamp = datetime.now()
        face_duration = (face_timestamp - step_start).total_seconds()
        
        # Extract validation data
        age_check = face_data.get("ageEstimationCheck", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        age_result = age_check.get("result", "UNKNOWN")
        age_config = age_check.get("ageEstimation", {})
        config_min_age = age_config.get("minAge")
        config_max_age = age_config.get("maxAge")
        
        liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        liveness_score = liveness_data.get("score_frr", "N/A")
        
        enrollment_status = face_data.get("enrollmentStatus")
        registration_code = face_data.get("registrationCode")
        
        if age_result == "FAIL":
            face_status = "❌ FAILED: AGE OUT OF RANGE"
        elif liveness_decision != "LIVE":
            face_status = "❌ FAILED: LIVENESS CHECK"
        else:
            face_status = "✅ SUCCESS - ENROLLMENT COMPLETE"
        
        age_in_range = None
        if age_from_server and min_age and max_age:
            age_in_range = min_age <= age_from_server <= max_age
        
        transactions['face'] = {
            "transaction_id": face_tx_id,
            "timestamp": face_timestamp,
            "status": face_status,
            "duration_seconds": face_duration,
            "age_detected": age_from_server,
            "age_result": age_result,
            "age_in_range": age_in_range,
            "liveness_decision": liveness_decision,
            "liveness_score": liveness_score,
            "enrollment_status": enrollment_status,
            "registration_code": registration_code,
        }
        
        logger.info(f"Transaction ID: {face_tx_id}")
        logger.info(f"Status: {face_status}")
        logger.info(f"Duration: {face_duration:.2f}s")
        logger.info(f"Timestamp: {face_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        logger.info(f"Enrollment Status: {enrollment_status} ({['FAILED', 'PENDING', 'COMPLETE'][enrollment_status] if enrollment_status in [0,1,2] else 'UNKNOWN'})")
        if registration_code:
            logger.info(f"Registration Code: {registration_code}")
        
        # Sub-transactions
        logger.info("\n" + "-"*120)
        logger.info("📸 Sub-Transaction: Age Detection")
        logger.info("-"*120)
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   ⚠️  Age: NOT DETECTED")
        logger.info(f"   Required Range: {min_age}-{max_age} years")
        logger.info(f"   Age Result: {age_result}")
        
        if age_from_server and age_in_range is not None:
            logger.info(f"   Age In Range: {'✅ YES' if age_in_range else '❌ NO'}")
            
            if not age_in_range:
                if age_from_server < min_age:
                    diff = min_age - age_from_server
                    logger.info(f"   Reason: {diff} years BELOW minimum")
                else:
                    diff = age_from_server - max_age
                    logger.info(f"   Reason: {diff} years ABOVE maximum")
        
        logger.info("\n" + "-"*120)
        logger.info("🔴 Sub-Transaction: Liveness Check")
        logger.info("-"*120)
        logger.info(f"   Liveness Decision: {liveness_decision}")
        logger.info(f"   Liveness Score: {liveness_score}")
        logger.info(f"   Status: {'✅ LIVE' if liveness_decision == 'LIVE' else '❌ SPOOF DETECTED'}")
        
        # ====================================================================
        # ANALYSIS & VALIDATIONS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 ANALYSIS & VALIDATION")
        logger.info("="*120)
        
        logger.info(f"\n📋 Configuration:")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected: {expected_result}")
        
        logger.info(f"\n👤 Results:")
        logger.info(f"   Age: {age_from_server} years" if age_from_server else "   Age: NOT DETECTED")
        logger.info(f"   Age Result: {age_result}")
        logger.info(f"   Liveness: {liveness_decision}")
        
        behavior_match = (age_result == expected_result)
        logger.info(f"\n🎯 Match: {'✅ YES' if behavior_match else '❌ NO'} (Expected: {expected_result}, Got: {age_result})")
        
        # Transaction summary
        total_duration = (datetime.now() - test_start_time).total_seconds()
        logger.info(f"\n⏱️  Total Duration: {total_duration:.2f}s")
        
        # Critical validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        # Validation results
        validations_passed = []
        validations_failed = []
        
        # 1. Liveness
        logger.info(f"\n1️⃣  Liveness Validation:")
        if liveness_decision != "LIVE":
            logger.error(f"   ❌ FAILED ({liveness_decision})")
            validations_failed.append("Liveness")
            pytest.fail(f"Liveness check failed: {liveness_decision}")
        else:
            logger.info(f"   ✅ PASSED ({liveness_decision})")
            validations_passed.append("Liveness")
        
        # 2. Age detection
        logger.info(f"\n2️⃣  Age Detection Validation:")
        if not age_from_server:
            logger.error(f"   ❌ FAILED (No age detected)")
            validations_failed.append("Age Detection")
            pytest.fail("Age not detected")
        else:
            logger.info(f"   ✅ PASSED ({age_from_server} years)")
            validations_passed.append("Age Detection")
        
        # 3. Age enforcement
        logger.info(f"\n3️⃣  Age Enforcement Validation:")
        if age_from_server and age_in_range is not None:
            if not age_in_range and age_result != "FAIL":
                logger.error(f"   ❌ FAILED (BYPASS DETECTED)")
                validations_failed.append("Age Enforcement")
                pytest.fail(f"Age verification bypass: {age_from_server} outside {min_age}-{max_age} but got {age_result}")
            else:
                logger.info(f"   ✅ PASSED (Correctly enforced)")
                validations_passed.append("Age Enforcement")
        
        # 4. Config integrity
        logger.info(f"\n4️⃣  Configuration Integrity Validation:")
        if config_min_age != min_age or config_max_age != max_age:
            logger.error(f"   ❌ FAILED (Mismatch)")
            validations_failed.append("Config Integrity")
            pytest.fail("Configuration mismatch")
        else:
            logger.info(f"   ✅ PASSED")
            validations_passed.append("Config Integrity")
        
        # 5. Behavior match
        logger.info(f"\n5️⃣  Behavior Match Validation:")
        if not behavior_match:
            logger.error(f"   ❌ FAILED")
            validations_failed.append("Behavior Match")
            pytest.fail(f"Expected {expected_result}, got {age_result}")
        else:
            logger.info(f"   ✅ PASSED")
            validations_passed.append("Behavior Match")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Validations Passed: {len(validations_passed)}/5")
        logger.info(f"   Duration: {total_duration:.2f}s")
        logger.info("\n" + "="*120 + "\n")
