"""
Document OCR Test with Multiple Document Types
Tests both Driver License and Passport with biometricsInfo
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


# Test scenarios for different document types
DOCUMENT_SCENARIOS = [
    {
        "name": "Driver License (TX DL)",
        "doc_type": "Driver License",
        "face_env_var": "FACE",
        "doc_front_env_var": "DAN_DOC_FRONT",
        "doc_back_env_var": "DAN_DOC_BACK",
        "min_age": 18,
        "max_age": 101
    },
    {
        "name": "Passport (Romania)",
        "doc_type": "Passport",
        "face_env_var": "PASS_FACE_DAN",
        "doc_front_env_var": "PASS_FRONT_DAN",
        "doc_back_env_var": None,  # Passports typically don't have back
        "min_age": 18,
        "max_age": 101
    }
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.parametrize("scenario", DOCUMENT_SCENARIOS, ids=[s["name"] for s in DOCUMENT_SCENARIOS])
class TestMultipleDocumentTypes:
    """Test OCR with different document types"""
    
    def test_document_type_with_validation(
        self,
        api_client,
        unique_username,
        face_frames,
        workflow,
        env_vars,
        caplog,
        scenario
    ):
        """Test document OCR for specific document type"""
        
        caplog.set_level(logging.INFO)
        
        # Get images based on scenario
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
        logger.info(f"DOCUMENT TYPE: {scenario['name']}")
        logger.info(f"Document Type: {scenario['doc_type']}")
        logger.info(f"Age Range: {scenario['min_age']}-{scenario['max_age']}")
        logger.info("🎯"*60)
        
        # ====================================================================
        # SETUP
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("ENROLLMENT SETUP")
        logger.info("="*120)
        
        # Config
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
        
        # Enroll
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME", "Dan"),
            "lastName": env_vars.get("LASTNAME", "Nicolau"),
        })
        enrollment_token = enroll_response.json().get("enrollmentToken")
        logger.info(f"✅ Enrolled: {unique_username}")
        time.sleep(1)
        
        # Device
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": f"device_{int(time.time())}",
            "platform": "web"
        })
        logger.info("✅ Device registered")
        time.sleep(1)
        
        # Face
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
        logger.info(f"DOCUMENT OCR - {scenario['doc_type']}")
        logger.info("="*120)
        
        # Build document images
        doc_images = [{"lightingScheme": 6, "image": doc_front, "format": "JPG"}]
        if doc_back:
            doc_images.append({"lightingScheme": 6, "image": doc_back, "format": "JPG"})
        
        # Build payload
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
        
        logger.info(f"\n📋 Request Details:")
        logger.info(f"   Document Type: {scenario['doc_type']}")
        logger.info(f"   Images: {len(doc_images)} (front{' + back' if doc_back else ' only'})")
        logger.info(f"   Age Validation: {scenario['min_age']}-{scenario['max_age']}")
        logger.info(f"   Fields: * (all)")
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        doc_data = doc_response.json() if doc_response.status_code == 200 else {}
        
        # ====================================================================
        # RESPONSE SUMMARY
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 RESPONSE SUMMARY")
        logger.info("="*120)
        
        doc_verified = doc_data.get("documentVerificationResult")
        enrollment_status = doc_data.get("enrollmentStatus")
        match_result = doc_data.get("matchResult")
        match_score = doc_data.get("matchScore")
        registration_code = doc_data.get("registrationCode")
        
        logger.info(f"\n📄 Document Results:")
        logger.info(f"   Document Verified: {doc_verified}")
        logger.info(f"   Enrollment Status: {enrollment_status} ({['FAILED', 'PENDING', 'COMPLETE'][enrollment_status] if enrollment_status in [0,1,2] else 'UNKNOWN'})")
        logger.info(f"   Face Match: {match_result} (score: {match_score})")
        if registration_code:
            logger.info(f"   Registration Code: {registration_code}")
        
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
        # EXTRACTED FIELDS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📝 EXTRACTED FIELDS")
        logger.info("="*120)
        
        ocr_results = doc_data.get("ocrResults", {})
        documents_info = ocr_results.get("documentsInfo", {})
        field_types = documents_info.get("fieldType", [])
        
        # Also check alternate location
        if not field_types:
            field_types = ocr_results.get("fieldType", [])
        
        logger.info(f"\nTotal Fields: {len(field_types)}")
        
        if field_types:
            # Categorize
            identity_fields = []
            date_fields = []
            location_fields = []
            technical_fields = []
            other_fields = []
            
            for field in field_types:
                field_name = field.get("name", "Unknown")
                overall_result = field.get("overallResult", "UNDEFINED")
                field_result = field.get("fieldResult", {})
                
                visual = field_result.get("visual", "")
                barcode = field_result.get("barcode", "")
                mrz = field_result.get("mrz", "")
                
                value = visual or barcode or mrz
                
                # Categorize
                lower_name = field_name.lower()
                field_data = (field_name, value, overall_result)
                
                if any(word in lower_name for word in ["name", "surname", "given", "sex", "personal"]):
                    identity_fields.append(field_data)
                elif any(word in lower_name for word in ["date", "age", "expire", "issue", "birth", "month"]):
                    date_fields.append(field_data)
                elif any(word in lower_name for word in ["address", "city", "state", "place", "issuing", "nationality", "country"]):
                    location_fields.append(field_data)
                elif any(word in lower_name for word in ["mrz", "check", "digit", "class", "type", "optional", "document #"]):
                    technical_fields.append(field_data)
                else:
                    other_fields.append(field_data)
            
            # Display by category
            if identity_fields:
                logger.info(f"\n👤 IDENTITY FIELDS ({len(identity_fields)}):")
                for name, val, result in identity_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val if val else '[empty]'}")
            
            if date_fields:
                logger.info(f"\n📅 DATE FIELDS ({len(date_fields)}):")
                for name, val, result in date_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val if val else '[empty]'}")
            
            if location_fields:
                logger.info(f"\n🌍 LOCATION FIELDS ({len(location_fields)}):")
                for name, val, result in location_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val if val else '[empty]'}")
            
            if technical_fields:
                logger.info(f"\n🔧 TECHNICAL FIELDS ({len(technical_fields)}):")
                for name, val, result in technical_fields[:10]:  # Show first 10
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    if val:
                        logger.info(f"   {icon} {name}: {val}")
            
            if other_fields:
                logger.info(f"\n📦 OTHER FIELDS ({len(other_fields)}):")
                for name, val, result in other_fields[:5]:  # Show first 5
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    if val:
                        logger.info(f"   {icon} {name}: {val}")
        
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
        else:
            logger.info("   No validation rules results")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        
        logger.info(f"\n📋 Test: {scenario['name']}")
        logger.info(f"   Document Type: {scenario['doc_type']}")
        logger.info(f"   Overall Status: {ocr_analysis['overall_status']}")
        logger.info(f"   Critical Issues: {len(ocr_analysis['critical_issues'])}")
        logger.info(f"   Total Fields: {len(field_types)}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        logger.info("\n" + "="*120 + "\n")
        
        # Assertions
        assert doc_response.status_code == 200, f"OCR failed: {doc_response.status_code}"
