"""
Document OCR Test with Biometrics Info - Enhanced
Shows complete response structure and extracts all fields
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


@pytest.mark.stateful
@pytest.mark.enrollment
class TestDocumentWithBiometrics:
    """Test document OCR with biometricsInfo included"""
    
    def test_document_ocr_with_biometrics_and_validation(
        self,
        api_client,
        unique_username,
        face_frames,
        workflow,
        env_vars,
        caplog,
    ):
        """Test document OCR using biometricsInfo format"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64(env_vars.get("FACE", "").strip())
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not face_image or not doc_front:
            pytest.skip("Missing FACE or DAN_DOC_FRONT")
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("DOCUMENT OCR WITH BIOMETRICS INFO FORMAT")
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
        logger.info(f"Enrolled: {unique_username}")
        time.sleep(1)
        
        # Device
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": f"device_{int(time.time())}",
            "platform": "web"
        })
        logger.info("Device registered")
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
        logger.info("Face enrolled")
        time.sleep(3)
        
        # Build document images
        doc_images = [{"lightingScheme": 6, "image": doc_front, "format": "JPG"}]
        if doc_back:
            doc_images.append({"lightingScheme": 6, "image": doc_back, "format": "JPG"})
        
        # Build payload with biometricsInfo
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
                    "minimumAge": 18,
                    "maximumAge": 101,
                    "validateMinimumAge": True,
                    "validateMaximumAge": True,
                    "validateDocumentNotExpired": True
                },
                "fieldsToValidate": [
                    {
                        "fields": ["*"],
                        "docTypeKeyword": "Driver License"
                    }
                ]
            }
        }
        
        logger.info("\n" + "="*120)
        logger.info("REQUEST DETAILS")
        logger.info("="*120)
        logger.info(f"Document Images: {len(doc_images)}")
        logger.info(f"Biometrics: Face image included")
        logger.info(f"Age Range: 18-101")
        logger.info(f"Document Type: Driver License")
        logger.info(f"Fields: * (all)")
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        doc_data = doc_response.json() if doc_response.status_code == 200 else {}
        
        # ====================================================================
        # RAW RESPONSE (for debugging field structure)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("RAW RESPONSE STRUCTURE")
        logger.info("="*120)
        
        try:
            doc_data_clean = copy.deepcopy(doc_data)
            
            # Remove base64 images for readability
            if "ocrResults" in doc_data_clean:
                ocr = doc_data_clean["ocrResults"]
                if "documentsInfo" in ocr:
                    if "documentPhotoBase64" in ocr["documentsInfo"]:
                        ocr["documentsInfo"]["documentPhotoBase64"] = "[REMOVED]"
                if "portraitImage" in ocr:
                    doc_data_clean["ocrResults"]["portraitImage"] = "[REMOVED]"
                if "signatureImage" in ocr:
                    doc_data_clean["ocrResults"]["signatureImage"] = "[REMOVED]"
            
            logger.info(json.dumps(doc_data_clean, indent=2))
        except Exception as e:
            logger.warning(f"Could not format JSON: {e}")
        
        logger.info("="*120)
        
        # Response summary
        logger.info("\n" + "="*120)
        logger.info("RESPONSE SUMMARY")
        logger.info("="*120)
        
        doc_verified = doc_data.get("documentVerificationResult")
        enrollment_status = doc_data.get("enrollmentStatus")
        match_result = doc_data.get("matchResult")
        match_score = doc_data.get("matchScore")
        registration_code = doc_data.get("registrationCode")
        
        logger.info(f"Document Verified: {doc_verified}")
        logger.info(f"Enrollment Status: {enrollment_status}")
        logger.info(f"Face Match: {match_result} (score: {match_score})")
        if registration_code:
            logger.info(f"Registration Code: {registration_code}")
        
        # OCR Analysis
        logger.info("\n" + "="*120)
        logger.info("OCR ANALYSIS")
        logger.info("="*120)
        
        ocr_analysis = analyze_ocr_response(doc_data)
        ocr_analysis_report = generate_ocr_analysis_report(ocr_analysis)
        
        logger.info(ocr_analysis_report)
        
        # Field extraction - check multiple possible locations
        logger.info("\n" + "="*120)
        logger.info("EXTRACTED FIELDS (Searching all locations)")
        logger.info("="*120)
        
        ocr_results = doc_data.get("ocrResults", {})
        
        # Location 1: ocrResults.documentsInfo.fieldType
        documents_info = ocr_results.get("documentsInfo", {})
        field_types = documents_info.get("fieldType", [])
        
        logger.info(f"\nLocation 1 (ocrResults.documentsInfo.fieldType): {len(field_types)} fields")
        
        # Location 2: ocrResults.fieldType (sometimes fields are here)
        field_types_2 = ocr_results.get("fieldType", [])
        logger.info(f"Location 2 (ocrResults.fieldType): {len(field_types_2)} fields")
        
        # Use whichever has fields
        all_fields = field_types if len(field_types) > 0 else field_types_2
        
        logger.info(f"\n📊 Total Fields Found: {len(all_fields)}")
        
        if all_fields:
            logger.info("\n📋 Field Results:")
            
            # Categorize fields
            identity_fields = []
            date_fields = []
            location_fields = []
            other_fields = []
            
            for idx, field in enumerate(all_fields, 1):
                field_name = field.get("name", "Unknown")
                overall_result = field.get("overallResult", "UNDEFINED")
                field_result = field.get("fieldResult", {})
                
                visual = field_result.get("visual", "")
                barcode = field_result.get("barcode", "")
                mrz = field_result.get("mrz", "")
                
                value = visual or barcode or mrz
                
                status_icon = "✅" if overall_result == "OK" else "❌" if overall_result == "FAILED" else "⚠️"
                
                # Categorize
                lower_name = field_name.lower()
                if any(word in lower_name for word in ["name", "surname", "given", "sex", "personal"]):
                    identity_fields.append((field_name, value, overall_result))
                elif any(word in lower_name for word in ["date", "age", "expire", "issue", "birth"]):
                    date_fields.append((field_name, value, overall_result))
                elif any(word in lower_name for word in ["address", "city", "state", "place", "issuing"]):
                    location_fields.append((field_name, value, overall_result))
                else:
                    other_fields.append((field_name, value, overall_result))
                
                if value and idx <= 50:  # Show first 50
                    logger.info(f"{idx:3}. {status_icon} {field_name}: {value}")
            
            # Show categorized summary
            logger.info("\n" + "="*120)
            logger.info("FIELDS BY CATEGORY")
            logger.info("="*120)
            
            if identity_fields:
                logger.info(f"\n👤 IDENTITY ({len(identity_fields)} fields):")
                for name, val, result in identity_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val}")
            
            if date_fields:
                logger.info(f"\n📅 DATES ({len(date_fields)} fields):")
                for name, val, result in date_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val}")
            
            if location_fields:
                logger.info(f"\n🌍 LOCATION ({len(location_fields)} fields):")
                for name, val, result in location_fields:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    logger.info(f"   {icon} {name}: {val}")
            
            if other_fields and len(other_fields) <= 20:
                logger.info(f"\n📦 OTHER ({len(other_fields)} fields):")
                for name, val, result in other_fields[:20]:
                    icon = "✅" if result == "OK" else "❌" if result == "FAILED" else "⚠️"
                    if val:
                        logger.info(f"   {icon} {name}: {val}")
        else:
            logger.info("\n⚠️  No fields found in response!")
            logger.info("   Check if fieldsToValidate is working correctly")
        
        # Validation rules
        logger.info("\n" + "="*120)
        logger.info("VALIDATION RULES")
        logger.info("="*120)
        
        validation_rules = ocr_results.get("documentValidationRulesResult", {})
        requested_rules = validation_rules.get("requestedDocumentValidationRuleResults", {})
        
        if requested_rules:
            logger.info("\nValidation Results:")
            for rule_name, rule_result in requested_rules.items():
                status_icon = "✅" if rule_result != "FAILED" else "❌"
                logger.info(f"   {status_icon} {rule_name}: {rule_result}")
        
        logger.info("\n" + "="*120)
        logger.info("FINAL VERDICT")
        logger.info("="*120)
        logger.info(f"Overall Status: {ocr_analysis['overall_status']}")
        logger.info(f"Critical Issues: {len(ocr_analysis['critical_issues'])}")
        logger.info(f"Total Fields: {len(all_fields)}")
        logger.info(f"Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        logger.info("="*120 + "\n")
        
        assert doc_response.status_code == 200
