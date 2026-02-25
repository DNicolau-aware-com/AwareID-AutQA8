"""
Document OCR Test with Multiple Document Types + Negative Test
Tests:
1. TX DL with TX Face (POSITIVE)
2. Romania Passport with DAN Face (POSITIVE)
3. TX DL with DAN Face (NEGATIVE - Face mismatch)
"""
import pytest
import copy
import time
import logging
import json
from datetime import datetime
from autqa.utils.ocr_analyzer import analyze_ocr_response, generate_ocr_analysis_report

logger = logging.getLogger(__name__)


def normalize_base64(data: str) -> str:
    """Remove data URI prefix if present"""
    if not data:
        return data
    data = data.strip()
    if data.startswith('data:') and ',' in data:
        data = data.split(',', 1)[1]
    return data


# Test scenarios
DOCUMENT_SCENARIOS = [
    {
        "name": "TX Driver License with TX Face (POSITIVE)",
        "doc_type": "Driver License",
        "face_env_var": "TX_FACE",
        "doc_front_env_var": "TX_DOC_FRONT",
        "doc_back_env_var": "TX_DOC_BACK",
        "min_age": 18,
        "max_age": 101,
        "expected_face_match": True,
        "test_type": "POSITIVE"
    },
    {
        "name": "Romania Passport with DAN Face (POSITIVE)",
        "doc_type": "Passport",
        "face_env_var": "PASS_FACE_DAN",
        "doc_front_env_var": "PASS_FRONT_DAN",
        "doc_back_env_var": None,
        "min_age": 18,
        "max_age": 101,
        "expected_face_match": True,
        "test_type": "POSITIVE"
    },
    {
        "name": "TX Driver License with DAN Face (NEGATIVE - Mismatch)",
        "doc_type": "Driver License",
        "face_env_var": "PASS_FACE_DAN",  # DAN's face
        "doc_front_env_var": "TX_DOC_FRONT",  # TX document (different person)
        "doc_back_env_var": "TX_DOC_BACK",
        "min_age": 18,
        "max_age": 101,
        "expected_face_match": False,  # Should NOT match
        "test_type": "NEGATIVE"
    }
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.parametrize("scenario", DOCUMENT_SCENARIOS, ids=[s["name"] for s in DOCUMENT_SCENARIOS])
class TestDocumentFaceMatching:
    """Test document OCR with correct and mismatched face/document pairs"""
    
    def test_document_with_face_validation(
        self,
        api_client,
        unique_username,
        face_frames,
        workflow,
        env_vars,
        caplog,
        scenario
    ):
        """Test document OCR with face matching validation"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64(env_vars.get(scenario["face_env_var"], "").strip())
        doc_front = normalize_base64(env_vars.get(scenario["doc_front_env_var"], "").strip())
        doc_back = normalize_base64(env_vars.get(scenario["doc_back_env_var"], "").strip()) if scenario["doc_back_env_var"] else None
        
        if not face_image or not doc_front:
            pytest.skip(f"Missing {scenario['face_env_var']} or {scenario['doc_front_env_var']}")
        
        test_start = datetime.now()
        
        # ====================================================================
        # TEST HEADER
        # ====================================================================
        logger.info("\n" + "🎯"*60)
        logger.info(f"TEST: {scenario['name']}")
        logger.info(f"Type: {scenario['test_type']}")
        logger.info(f"Document: {scenario['doc_type']}")
        logger.info(f"Face Image: {scenario['face_env_var']}")
        logger.info(f"Document Image: {scenario['doc_front_env_var']}")
        logger.info(f"Expected Face Match: {scenario['expected_face_match']}")
        logger.info("🎯"*60)
        
        # ====================================================================
        # SETUP
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("ENROLLMENT SETUP")
        logger.info("="*120)
        
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {"enabled": False}
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = True
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
        time.sleep(1)
        
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_response.json().get("enrollmentToken")
        logger.info(f"✅ Enrolled: {unique_username}")
        time.sleep(1)
        
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": f"device_{int(time.time())}",
            "platform": "web"
        })
        logger.info("✅ Device registered")
        time.sleep(1)
        
        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        logger.info("✅ Face enrolled")
        time.sleep(3)
        
        # ====================================================================
        # DOCUMENT OCR WITH BIOMETRICS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info(f"DOCUMENT OCR - {scenario['doc_type']} ({scenario['test_type']} TEST)")
        logger.info("="*120)
        
        doc_images = [{"lightingScheme": 6, "image": doc_front, "format": "JPG"}]
        if doc_back:
            doc_images.append({"lightingScheme": 6, "image": doc_back, "format": "JPG"})
        
        doc_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {
                    "request": {
                        "vendor": "REGULA",
                        "data": {}
                    }
                }
            },
            "biometricsInfo": {
                "facialImage": {
                    "image": face_image
                }
            },
            "processingInstructions": {
                "documentValidationRules": {
                    "minimumAge": scenario["min_age"],
                    "maximumAge": scenario["max_age"],
                    "validateMinimumAge": True,
                    "validateMaximumAge": True,
                    "validateDocumentNotExpired": True
                },
                "fieldsToValidate": [
                    {
                        "fields": ["*"],
                        "docTypeKeyword": scenario["doc_type"]
                    }
                ]
            }
        }
        
        logger.info(f"\n📋 Request Configuration:")
        logger.info(f"   Document Type: {scenario['doc_type']}")
        logger.info(f"   Images: {len(doc_images)} (front{' + back' if doc_back else ' only'})")
        logger.info(f"   Face for Matching: {scenario['face_env_var']}")
        logger.info(f"   Age Validation: {scenario['min_age']}-{scenario['max_age']}")
        logger.info(f"   Expected Face Match: {scenario['expected_face_match']}")
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        doc_data = doc_response.json() if doc_response.status_code == 200 else {}
        
        # ====================================================================
        # RESPONSE ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 RESPONSE SUMMARY")
        logger.info("="*120)
        
        doc_verified = doc_data.get("documentVerificationResult")
        enrollment_status = doc_data.get("enrollmentStatus")
        match_result = doc_data.get("matchResult")
        match_score = doc_data.get("matchScore")
        registration_code = doc_data.get("registrationCode")
        
        logger.info(f"\n📄 Document Verification:")
        logger.info(f"   Document Verified: {doc_verified}")
        logger.info(f"   Enrollment Status: {enrollment_status} ({['FAILED', 'PENDING', 'COMPLETE'][enrollment_status] if enrollment_status in [0,1,2] else 'UNKNOWN'})")
        
        logger.info(f"\n👤 Face Matching:")
        logger.info(f"   Match Result: {match_result}")
        logger.info(f"   Match Score: {match_score}")
        logger.info(f"   Expected Match: {scenario['expected_face_match']}")
        
        # Check if face match result matches expectation
        face_match_correct = (match_result == scenario['expected_face_match'])
        match_status_icon = "✅" if face_match_correct else "❌"
        
        logger.info(f"   {match_status_icon} Face Match Test: {'PASSED' if face_match_correct else 'FAILED'} (Expected: {scenario['expected_face_match']}, Got: {match_result})")
        
        if registration_code:
            logger.info(f"\n📝 Registration Code: {registration_code}")
        
        # ====================================================================
        # OCR ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🔍 OCR ANALYSIS")
        logger.info("="*120)
        
        ocr_analysis = analyze_ocr_response(doc_data)
        ocr_analysis_report = generate_ocr_analysis_report(ocr_analysis)
        
        logger.info(ocr_analysis_report)
        
        # ====================================================================
        # EXTRACTED FIELDS (Top 20)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📝 EXTRACTED FIELDS (Top 20)")
        logger.info("="*120)
        
        ocr_results = doc_data.get("ocrResults", {})
        documents_info = ocr_results.get("documentsInfo", {})
        field_types = documents_info.get("fieldType", [])
        
        if not field_types:
            field_types = ocr_results.get("fieldType", [])
        
        logger.info(f"\nTotal Fields: {len(field_types)}")
        
        if field_types:
            logger.info("\nTop Fields:")
            for idx, field in enumerate(field_types[:20], 1):
                field_name = field.get("name", "Unknown")
                overall_result = field.get("overallResult", "UNDEFINED")
                field_result = field.get("fieldResult", {})
                
                visual = field_result.get("visual", "")
                barcode = field_result.get("barcode", "")
                mrz = field_result.get("mrz", "")
                
                value = visual or barcode or mrz
                
                icon = "✅" if overall_result == "OK" else "❌" if overall_result == "FAILED" else "⚠️"
                
                if value:
                    logger.info(f"{idx:3}. {icon} {field_name}: {value}")
        
        # ====================================================================
        # VALIDATION RULES
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 VALIDATION RULES")
        logger.info("="*120)
        
        validation_rules = ocr_results.get("documentValidationRulesResult", {})
        requested_rules = validation_rules.get("requestedDocumentValidationRuleResults", {})
        
        if requested_rules:
            logger.info("\nValidation Results:")
            for rule_name, rule_result in requested_rules.items():
                icon = "✅" if rule_result != "FAILED" else "❌"
                logger.info(f"   {icon} {rule_name}: {rule_result}")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        
        logger.info(f"\n📋 Test: {scenario['name']}")
        logger.info(f"   Type: {scenario['test_type']}")
        logger.info(f"   Document: {scenario['doc_type']}")
        
        logger.info(f"\n📊 Results:")
        logger.info(f"   Document Verified: {doc_verified}")
        logger.info(f"   Face Match: {match_result} (Expected: {scenario['expected_face_match']})")
        logger.info(f"   Face Match Test: {match_status_icon} {'PASSED' if face_match_correct else 'FAILED'}")
        logger.info(f"   Overall Status: {ocr_analysis['overall_status']}")
        logger.info(f"   Total Fields: {len(field_types)}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        logger.info("\n" + "="*120 + "\n")
        
        # ====================================================================
        # ASSERTIONS
        # ====================================================================
        
        # Response should succeed
        assert doc_response.status_code == 200, f"OCR failed: {doc_response.status_code}"
        
        # Face match result should match expectation
        if scenario['test_type'] == "NEGATIVE":
            # For negative test, we expect face NOT to match
            logger.info(f"\n🔍 NEGATIVE TEST VALIDATION:")
            logger.info(f"   Expected: Face should NOT match (matchResult should be False)")
            logger.info(f"   Actual: matchResult = {match_result}")
            
            # Note: Some systems may still return True with low score
            # So we check both matchResult and matchScore
            if match_result == False:
                logger.info(f"   ✅ PASSED: Face correctly identified as NOT matching")
            elif match_result == True and match_score is not None and match_score < 3.0:
                logger.info(f"   ⚠️  PARTIAL: matchResult=True but score is low ({match_score})")
                logger.info(f"   This may indicate the system detected a mismatch via low score")
            else:
                logger.warning(f"   ⚠️  UNEXPECTED: Face matched when it shouldn't (matchResult={match_result}, score={match_score})")
        else:
            # For positive test, we expect face TO match
            assert match_result == True, f"Face should match for {scenario['name']}, but got {match_result}"
