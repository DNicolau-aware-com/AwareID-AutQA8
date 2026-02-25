"""
Enhanced Age Verification Comprehensive Test with Full Validation
Face + Device enrollment with complete transaction tracking and validation
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
class TestAgeVerificationComprehensive:
    """
    Comprehensive age verification tests with Face + Device enrollment
    Includes full transaction tracking, validation, and detailed HTML reporting
    """
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", AGE_SCENARIOS)
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
        Test age verification with different age ranges
        
        Validates:
        - Age detection accuracy
        - Liveness detection (spoof prevention)
        - Age range enforcement
        - Configuration integrity
        - Transaction tracking
        """
        
        caplog.set_level(logging.INFO)
        
        # ====================================================================
        # TEST DATA PREPARATION
        # ====================================================================
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
        logger.info("AGE VERIFICATION COMPREHENSIVE TEST")
        logger.info(f"Scenario: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected Result: {expected_result}")
        logger.info(f"Test Started: {test_start_time.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        logger.info("🎯"*60)
        
        # ====================================================================
        # STEP 1: ADMIN CONFIGURATION
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 1: ADMIN CONFIGURATION")
        logger.info("="*120)
        step_start = datetime.now()
        
        # Get current config
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert config_response.status_code == 200, f"Failed to get config: {config_response.status_code}"
        
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        # Configure age verification
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
        
        # Set other workflows
        authentication = new_config.setdefault("onboardingOptions", {}).setdefault("authentication", {})
        authentication['verifyFace'] = True
        
        reenrollment = new_config.setdefault("onboardingOptions", {}).setdefault("reenrollment", {})
        reenrollment['verifyFace'] = True
        
        # Save configuration
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
        logger.info(f"   Device Enrollment: ✅ ENABLED")
        logger.info(f"   Document Enrollment: ❌ DISABLED")
        logger.info(f"   Duration: {config_duration:.2f}s")
        logger.info(f"   Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        time.sleep(1)  # Allow config to propagate
        
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
        
        # Track transaction
        transactions['enroll'] = {
            "transaction_id": enroll_tx_id,
            "timestamp": enroll_timestamp,
            "status": "✅ SUCCESS" if enrollment_token else "❌ FAILED",
            "duration_seconds": enroll_duration,
            "username": unique_username,
            "email": enroll_payload.get("email"),
        }
        
        logger.info(f"Transaction ID: {enroll_tx_id}")
        logger.info(f"Status: ✅ SUCCESS")
        logger.info(f"Username: {unique_username}")
        logger.info(f"Email: {enroll_payload.get('email')}")
        logger.info(f"Enrollment Token: {enrollment_token[:20]}..." if enrollment_token else "Token: MISSING")
        logger.info(f"Duration: {enroll_duration:.2f}s")
        logger.info(f"Timestamp: {enroll_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        assert enrollment_token, "Enrollment token missing - enrollment failed"
        
        time.sleep(1)
        
        # ====================================================================
        # STEP 3: ADD DEVICE
        # ====================================================================
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
        
        device_response = api_client.http_client.post(
            "/onboarding/enrollment/addDevice",
            json=device_payload
        )
        assert device_response.status_code == 200, f"Add device failed: {device_response.status_code}"
        
        device_data = device_response.json()
        device_tx_id = device_data.get("transactionId", "N/A")
        device_timestamp = datetime.now()
        device_duration = (device_timestamp - step_start).total_seconds()
        
        # Track transaction
        transactions['device'] = {
            "transaction_id": device_tx_id,
            "timestamp": device_timestamp,
            "status": "✅ DEVICE REGISTERED",
            "duration_seconds": device_duration,
            "device_id": device_id,
            "platform": "web",
        }
        
        logger.info(f"Transaction ID: {device_tx_id}")
        logger.info(f"Status: ✅ DEVICE REGISTERED")
        logger.info(f"Device ID: {device_id}")
        logger.info(f"Platform: web")
        logger.info(f"Duration: {device_duration:.2f}s")
        logger.info(f"Timestamp: {device_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        time.sleep(1)
        
        # ====================================================================
        # STEP 4: ADD FACE (Age + Liveness Verification)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 4: Enrollment - Add Face (Age + Liveness Verification)")
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
        
        # ====================================================================
        # EXTRACT VALIDATION DATA
        # ====================================================================
        
        # Age Estimation
        age_check = face_data.get("ageEstimationCheck", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        age_result = age_check.get("result", "UNKNOWN")
        age_config = age_check.get("ageEstimation", {})
        config_min_age = age_config.get("minAge")
        config_max_age = age_config.get("maxAge")
        config_enabled = age_config.get("enabled")
        
        # Liveness Detection
        liveness_results = face_data.get("faceLivenessResults", {}).get("video", {})
        liveness_data = liveness_results.get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        liveness_score = liveness_data.get("score_frr", "N/A")
        
        # Enrollment Status
        enrollment_status = face_data.get("enrollmentStatus")
        registration_code = face_data.get("registrationCode")
        
        # Determine overall status
        if age_result == "FAIL":
            face_status = "❌ FAILED: AGE OUT OF RANGE"
        elif liveness_decision != "LIVE":
            face_status = "❌ FAILED: LIVENESS CHECK"
        else:
            face_status = "✅ SUCCESS"
        
        # Calculate if age is in range
        age_in_range = None
        if age_from_server and min_age and max_age:
            age_in_range = min_age <= age_from_server <= max_age
        
        # Track transaction
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
        
        # Log main transaction
        logger.info(f"Transaction ID: {face_tx_id}")
        logger.info(f"Status: {face_status}")
        logger.info(f"Duration: {face_duration:.2f}s")
        logger.info(f"Timestamp: {face_timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}")
        
        # ====================================================================
        # SUB-TRANSACTION: AGE DETECTION
        # ====================================================================
        logger.info("\n" + "-"*120)
        logger.info("📸 Sub-Transaction: Age Detection")
        logger.info("-"*120)
        logger.info(f"   Detected Age: {age_from_server} years" if age_from_server else "   ⚠️  Age: NOT DETECTED")
        logger.info(f"   Required Range: {min_age}-{max_age} years")
        logger.info(f"   Config Enabled: {config_enabled}")
        logger.info(f"   Config Min Age: {config_min_age}")
        logger.info(f"   Config Max Age: {config_max_age}")
        logger.info(f"   Age Result: {age_result}")
        
        if age_from_server and age_in_range is not None:
            logger.info(f"   Age In Range: {'✅ YES' if age_in_range else '❌ NO'}")
            
            if not age_in_range:
                if age_from_server < min_age:
                    diff = min_age - age_from_server
                    logger.info(f"   Reason: {diff} years BELOW minimum ({min_age})")
                else:
                    diff = age_from_server - max_age
                    logger.info(f"   Reason: {diff} years ABOVE maximum ({max_age})")
        
        # ====================================================================
        # SUB-TRANSACTION: LIVENESS CHECK
        # ====================================================================
        logger.info("\n" + "-"*120)
        logger.info("🔴 Sub-Transaction: Liveness Check (Spoof Detection)")
        logger.info("-"*120)
        logger.info(f"   Liveness Decision: {liveness_decision}")
        logger.info(f"   Liveness Score (FRR): {liveness_score}")
        logger.info(f"   Status: {'✅ LIVE (Real person)' if liveness_decision == 'LIVE' else '❌ SPOOF DETECTED'}")
        
        # Additional liveness details
        if liveness_data:
            confidence = liveness_data.get("confidence")
            if confidence:
                logger.info(f"   Confidence: {confidence}")
        
        # ====================================================================
        # COMPREHENSIVE ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 COMPREHENSIVE ANALYSIS")
        logger.info("="*120)
        
        logger.info(f"\n📋 Test Configuration:")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age} years")
        logger.info(f"   Expected Result: {expected_result}")
        
        logger.info(f"\n👤 Detection Results:")
        if age_from_server:
            logger.info(f"   Detected Age: {age_from_server} years")
            logger.info(f"   Age In Range: {'✅ YES' if age_in_range else '❌ NO'}")
        else:
            logger.info(f"   Detected Age: ⚠️  NOT DETECTED")
        logger.info(f"   Age Verification Result: {age_result}")
        logger.info(f"   Liveness: {liveness_decision}")
        
        logger.info(f"\n🎯 Expected vs Actual:")
        logger.info(f"   Expected: {expected_result}")
        logger.info(f"   Actual: {age_result}")
        behavior_match = (age_result == expected_result)
        logger.info(f"   Match: {'✅ YES' if behavior_match else '❌ NO'}")
        
        # ====================================================================
        # TRANSACTION SUMMARY
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📑 COMPLETE TRANSACTION SUMMARY")
        logger.info("="*120)
        
        total_test_duration = (datetime.now() - test_start_time).total_seconds()
        
        for step_name, tx_data in transactions.items():
            logger.info(f"\n{step_name.upper()}:")
            logger.info(f"   Transaction ID: {tx_data['transaction_id']}")
            logger.info(f"   Status: {tx_data['status']}")
            logger.info(f"   Timestamp: {tx_data['timestamp'].strftime('%m/%d/%Y, %I:%M:%S %p')}")
            logger.info(f"   Duration: {tx_data['duration_seconds']:.2f}s")
            
            # Additional details per step
            if step_name == 'enroll':
                logger.info(f"   Username: {tx_data['username']}")
                logger.info(f"   Email: {tx_data['email']}")
            elif step_name == 'device':
                logger.info(f"   Device ID: {tx_data['device_id']}")
                logger.info(f"   Platform: {tx_data['platform']}")
            elif step_name == 'face':
                logger.info(f"   Age Detected: {tx_data['age_detected']}")
                logger.info(f"   Age Result: {tx_data['age_result']}")
                logger.info(f"   Liveness: {tx_data['liveness_decision']} (score: {tx_data['liveness_score']})")
                logger.info(f"   Enrollment Status: {tx_data['enrollment_status']}")
        
        logger.info(f"\n⏱️  Total Test Duration: {total_test_duration:.2f}s")
        logger.info(f"   Started: {test_start_time.strftime('%I:%M:%S %p')}")
        logger.info(f"   Completed: {datetime.now().strftime('%I:%M:%S %p')}")
        
        # ====================================================================
        # CRITICAL VALIDATIONS
        # ====================================================================
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATION CHECKS")
        logger.info("🔥"*60)
        
        validation_results = {
            "liveness": False,
            "age_detection": False,
            "age_enforcement": False,
            "config_integrity": False,
            "behavior_match": False,
        }
        
        # Validation 1: Liveness
        logger.info(f"\n1️⃣  LIVENESS VALIDATION:")
        if liveness_decision != "LIVE":
            logger.error(f"   🚨 LIVENESS FAILURE: {liveness_decision}")
            logger.error(f"   ⚠️  Possible spoof attack detected!")
            pytest.fail(f"Liveness check failed: Decision={liveness_decision}, Score={liveness_score}")
        else:
            logger.info(f"   ✅ Liveness PASSED: {liveness_decision}")
            logger.info(f"   Score: {liveness_score}")
            validation_results["liveness"] = True
        
        # Validation 2: Age Detection
        logger.info(f"\n2️⃣  AGE DETECTION VALIDATION:")
        if not age_from_server:
            logger.error(f"   🚨 AGE NOT DETECTED from face")
            pytest.fail("Age detection failed - no age returned from server")
        else:
            logger.info(f"   ✅ Age detected: {age_from_server} years")
            validation_results["age_detection"] = True
        
        # Validation 3: Age Enforcement
        logger.info(f"\n3️⃣  AGE VERIFICATION ENFORCEMENT:")
        if age_from_server and age_in_range is not None:
            # Check for security bypass
            if not age_in_range and age_result != "FAIL":
                logger.error(f"   🚨🚨🚨 CRITICAL: AGE VERIFICATION BYPASSED! 🚨🚨🚨")
                logger.error(f"   Age {age_from_server} is OUTSIDE range {min_age}-{max_age}")
                logger.error(f"   But result was: {age_result} (should be FAIL)")
                logger.error(f"   🔥 SECURITY RISK: Age restrictions not enforced!")
                pytest.fail(
                    f"AGE VERIFICATION BYPASS DETECTED: "
                    f"Age {age_from_server} outside {min_age}-{max_age} but got '{age_result}' instead of FAIL"
                )
            
            logger.info(f"   ✅ Age verification CORRECTLY enforced")
            logger.info(f"   Age {age_from_server} was correctly {'rejected' if not age_in_range else 'accepted'}")
            validation_results["age_enforcement"] = True
        
        # Validation 4: Configuration Integrity
        logger.info(f"\n4️⃣  CONFIGURATION INTEGRITY:")
        if config_min_age != min_age or config_max_age != max_age:
            logger.error(f"   🚨 CONFIGURATION MISMATCH")
            logger.error(f"   Expected: {min_age}-{max_age}")
            logger.error(f"   Server has: {config_min_age}-{config_max_age}")
            pytest.fail("Configuration not properly applied to server")
        else:
            logger.info(f"   ✅ Configuration correctly applied")
            logger.info(f"   Server age range: {config_min_age}-{config_max_age}")
            validation_results["config_integrity"] = True
        
        # Validation 5: Behavior Match
        logger.info(f"\n5️⃣  EXPECTED BEHAVIOR VALIDATION:")
        if not behavior_match:
            logger.error(f"   🚨 BEHAVIOR MISMATCH")
            logger.error(f"   Expected: {expected_result}")
            logger.error(f"   Actual: {age_result}")
            
            if expected_result == "FAIL" and age_result != "FAIL":
                pytest.fail(f"Expected FAIL but got {age_result} - age restrictions not working")
            elif expected_result == "PASS" and age_result == "FAIL":
                pytest.fail(f"Expected PASS but got FAIL - false rejection")
        else:
            logger.info(f"   ✅ Behavior matches expectation")
            logger.info(f"   Expected {expected_result}, got {age_result}")
            validation_results["behavior_match"] = True
        
        # ====================================================================
        # VALIDATION SUMMARY
        # ====================================================================
        logger.info(f"\n" + "-"*120)
        logger.info("✅ VALIDATION SUMMARY:")
        logger.info(f"   Liveness: {'✅ PASSED' if validation_results['liveness'] else '❌ FAILED'}")
        logger.info(f"   Age Detection: {'✅ PASSED' if validation_results['age_detection'] else '❌ FAILED'}")
        logger.info(f"   Age Enforcement: {'✅ PASSED' if validation_results['age_enforcement'] else '❌ FAILED'}")
        logger.info(f"   Config Integrity: {'✅ PASSED' if validation_results['config_integrity'] else '❌ FAILED'}")
        logger.info(f"   Behavior Match: {'✅ PASSED' if validation_results['behavior_match'] else '❌ FAILED'}")
        
        all_passed = all(validation_results.values())
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        
        if all_passed:
            logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
            logger.info(f"   Scenario: {scenario_name}")
            logger.info(f"   All validations: ✅ PASSED")
            logger.info(f"   Age verification: ✅ CORRECTLY ENFORCED")
            logger.info(f"   Liveness detection: ✅ WORKING")
            logger.info(f"   Security: ✅ NO BYPASSES DETECTED")
            logger.info(f"   Total duration: {total_test_duration:.2f}s")
        else:
            logger.error(f"\n❌❌❌ TEST FAILED ❌❌❌")
            logger.error(f"   Check validation failures above")
            failed = [k for k, v in validation_results.items() if not v]
            logger.error(f"   Failed validations: {', '.join(failed)}")
        
        logger.info("\n" + "="*120 + "\n")
        
        # Final assertion
        assert all_passed, f"Test failed - validations failed: {[k for k, v in validation_results.items() if not v]}"
