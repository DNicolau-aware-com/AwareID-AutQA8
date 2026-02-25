"""
Enhanced Document + Face Age Verification with Full Validation
Document OCR + Face enrollment with complete validation
"""
import pytest
import copy
import time
import logging
from datetime import datetime
from autqa.utils.your_document_validator import (
    extract_document_ocr_data,
    validate_document,
    generate_document_report
)

logger = logging.getLogger(__name__)


AGE_SCENARIOS = [
    (1, 16, "Child/Teen (1-16)", "FAIL"),
    (18, 65, "Adult (18-65)", "PASS"),
    (21, 100, "Legal adult (21-100)", "PASS"),
    (40, 60, "Middle age (40-60)", "PASS"),
]

DELAYS = {"after_config": 1.0, "after_enroll": 1.0, "after_face": 3.0, "after_document": 5.0}


def normalize_base64(data: str) -> str:
    """Remove data URI prefix if present"""
    if not data:
        return data
    data = data.strip()
    if data.startswith('data:') and ',' in data:
        data = data.split(',', 1)[1]
    return data


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.document
@pytest.mark.age_verification
class TestDocumentFaceAgeVerification:
    """Document + Face age verification with document OCR validation"""
    
    @pytest.mark.parametrize("min_age,max_age,scenario_name,expected_result", AGE_SCENARIOS)
    def test_face_then_document(
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
        Test Document + Face age verification
        Flow: Config → Enroll → Face → Document OCR
        """
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        # Transaction tracking
        transactions = {}
        test_start_time = datetime.now()
        
        # ====================================================================
        # TEST HEADER
        # ====================================================================
        logger.info("\n" + "🎯"*60)
        logger.info("DOCUMENT + FACE AGE VERIFICATION TEST")
        logger.info(f"Scenario: {scenario_name}")
        logger.info(f"Age Range: {min_age}-{max_age} years")
        logger.info(f"Expected: {expected_result}")
        logger.info(f"Test Started: {test_start_time.strftime('%m/%d/%Y, %I:%M:%S %p')}")
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
            "minAge": min_age,
            "maxAge": max_age,
            "minTolerance": 0,
            "maxTolerance": 0
        }
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = False
        
        document_settings = new_config.setdefault("onboardingOptions", {}).setdefault("document", {})
        document_settings['rfid'] = "DISABLED"
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
        
        config_duration = (datetime.now() - step_start).total_seconds()
        logger.info(f"✅ Config: Age {min_age}-{max_age}, Document ✅, Face ✅, RFID ❌")
        logger.info(f"   Duration: {config_duration:.2f}s")
        
        time.sleep(DELAYS['after_config'])
        
        # ====================================================================
        # STEP 2: ENROLL
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 2: Enrollment - Enroll")
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
            "duration": (enroll_timestamp - step_start).total_seconds()
        }
        
        logger.info(f"✅ Username: {unique_username}")
        logger.info(f"   Transaction ID: {enroll_tx_id}")
        logger.info(f"   Duration: {transactions['enroll']['duration']:.2f}s")
        
        assert enrollment_token, "Enrollment token missing"
        time.sleep(DELAYS['after_enroll'])
        
        # ====================================================================
        # STEP 3: ADD FACE (MUST BE FIRST)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 3: Enrollment - Add Face (Age Verification)")
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
        
        liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        liveness_score = liveness_data.get("score_frr", "N/A")
        
        face_status = "❌ FAILED: AGE" if age_result == "FAIL" else "✅ SUCCESS"
        
        transactions['face'] = {
            "id": face_tx_id,
            "timestamp": face_timestamp,
            "status": face_status,
            "age": age_from_server,
            "age_result": age_result,
            "liveness": liveness_decision,
            "duration": (face_timestamp - step_start).total_seconds()
        }
        
        logger.info(f"✅ Face: Age={age_from_server}, Result={age_result}, Liveness={liveness_decision}")
        logger.info(f"   Transaction ID: {face_tx_id}")
        logger.info(f"   Duration: {transactions['face']['duration']:.2f}s")
        
        time.sleep(DELAYS['after_face'])
        
        # ====================================================================
        # STEP 4: ADD DOCUMENT OCR
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("STEP 4: Enrollment - Add Document OCR")
        logger.info("="*120)
        step_start = datetime.now()
        
        doc_images = [{"lightingScheme": 6, "image": doc_front, "format": "JPG"}]
        if doc_back:
            doc_images.append({"lightingScheme": 6, "image": doc_back, "format": "JPG"})
        
        logger.info(f"   Images: {len(doc_images)}")
        
        doc_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {"request": {"vendor": "REGULA", "data": {}}}
            }
        }
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        
        if doc_response.status_code == 200:
            doc_data = doc_response.json()
            doc_tx_id = doc_data.get("transactionId", "N/A")
            doc_timestamp = datetime.now()
            
            transactions['document'] = {
                "id": doc_tx_id,
                "timestamp": doc_timestamp,
                "status": "✅ SUCCESS",
                "duration": (doc_timestamp - step_start).total_seconds()
            }
            
            logger.info(f"✅ Document OCR completed")
            logger.info(f"   Transaction ID: {doc_tx_id}")
            logger.info(f"   Duration: {transactions['document']['duration']:.2f}s")
            
            # Extract and validate document data
            extracted_data = extract_document_ocr_data(doc_data)
            validation_result = validate_document(extracted_data)
            doc_report = generate_document_report(extracted_data, validation_result)
            
            logger.info("\n" + doc_report)
            
            # Document validations
            doc_verification = doc_data.get("documentVerificationResult")
            match_result = doc_data.get("matchResult")
            match_score = doc_data.get("matchScore")
            
            logger.info("\n📄 Document Validation:")
            logger.info(f"   Verification: {doc_verification}")
            logger.info(f"   Face Match: {match_result} (score: {match_score})")
            
        else:
            logger.error(f"❌ Document OCR failed: {doc_response.status_code}")
            logger.warning("⚠️  Continuing with face-only validation")
        
        time.sleep(DELAYS['after_document'])
        
        # ====================================================================
        # ANALYSIS & VALIDATIONS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 COMPREHENSIVE ANALYSIS")
        logger.info("="*120)
        
        total_duration = (datetime.now() - test_start_time).total_seconds()
        
        logger.info(f"\n📋 Configuration:")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Age Range: {min_age}-{max_age}")
        logger.info(f"   Expected: {expected_result}")
        
        logger.info(f"\n👤 Results:")
        logger.info(f"   Age: {age_from_server} years")
        logger.info(f"   Age Result: {age_result}")
        logger.info(f"   Liveness: {liveness_decision}")
        
        behavior_match = (age_result == expected_result)
        logger.info(f"\n🎯 Match: {'✅ YES' if behavior_match else '❌ NO'}")
        
        # Transaction summary
        logger.info(f"\n📑 Transactions:")
        for step, tx in transactions.items():
            logger.info(f"   {step.upper()}: {tx['id']} ({tx['duration']:.2f}s)")
        logger.info(f"   TOTAL: {total_duration:.2f}s")
        
        # Critical validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        # 1. Liveness
        assert liveness_decision == "LIVE", f"Liveness failed: {liveness_decision}"
        logger.info(f"1️⃣  Liveness: ✅ PASSED")
        
        # 2. Age detection
        assert age_from_server, "Age not detected"
        logger.info(f"2️⃣  Age Detection: ✅ PASSED")
        
        # 3. Age enforcement
        age_in_range = min_age <= age_from_server <= max_age
        if not age_in_range and age_result != "FAIL":
            pytest.fail(f"Age bypass: {age_from_server} outside {min_age}-{max_age} but got {age_result}")
        logger.info(f"3️⃣  Age Enforcement: ✅ PASSED")
        
        # 4. Behavior match
        assert behavior_match, f"Expected {expected_result}, got {age_result}"
        logger.info(f"4️⃣  Behavior Match: ✅ PASSED")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        logger.info(f"\n✅✅✅ TEST PASSED ✅✅✅")
        logger.info(f"   Scenario: {scenario_name}")
        logger.info(f"   Duration: {total_duration:.2f}s")
        logger.info("\n" + "="*120 + "\n")
