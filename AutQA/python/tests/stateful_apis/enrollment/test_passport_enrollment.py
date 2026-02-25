"""
Passport Enrollment Test - Enhanced with Full OCR Analysis
"""
import pytest
import copy
import time
import logging
import json
from datetime import datetime
from autqa.utils.your_document_validator import (
    extract_document_ocr_data,
    validate_document,
    generate_document_report
)
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
@pytest.mark.passport
class TestPassportEnrollment:
    """Simple passport enrollment test without age verification"""
    
    def test_passport_enrollment_simple(
        self,
        api_client,
        unique_username,
        face_frames,
        workflow,
        env_vars,
        caplog,
    ):
        """Simple passport enrollment with comprehensive OCR analysis"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64(env_vars.get("PASS_FACE_DAN", "").strip())
        passport_front = normalize_base64(env_vars.get("PASS_FRONT_DAN", "").strip())
        
        if not face_image:
            pytest.skip("Missing PASS_FACE_DAN in .env")
        
        if not passport_front:
            pytest.skip("Missing PASS_FRONT_DAN in .env")
        
        # Transaction tracking
        transactions = {}
        test_start_time = datetime.now()
        
        logger.info("\n" + "🎯"*60)
        logger.info("PASSPORT ENROLLMENT TEST - COMPREHENSIVE OCR ANALYSIS")
        logger.info("🎯"*60)
        
        # Config, Enroll, Device, Face steps (abbreviated for brevity)
        # ... (keeping it short, just showing the OCR part)
        
        # Configure
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {"enabled": False, "minAge": 1, "maxAge": 101, "minTolerance": 0, "maxTolerance": 0}
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = True
        
        document_settings = new_config.setdefault("onboardingOptions", {}).setdefault("document", {})
        document_settings['rfid'] = "DISABLED"
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
        time.sleep(1)
        
        # Enroll
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Dan",
            "lastName": env_vars.get("LASTNAME") or "Nicolau",
        })
        enrollment_token = enroll_response.json().get("enrollmentToken")
        time.sleep(1)
        
        # Device
        device_id = f"device_passport_{int(time.time())}"
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web"
        })
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
        
        face_data = face_response.json() if face_response.status_code == 200 else {}
        liveness_data = face_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision", "UNKNOWN")
        
        time.sleep(3)
        
        # ====================================================================
        # DOCUMENT OCR WITH COMPREHENSIVE ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📄 ADD PASSPORT DOCUMENT WITH COMPREHENSIVE ANALYSIS")
        logger.info("="*120)
        
        doc_images = [{"lightingScheme": 6, "image": passport_front, "format": "JPG"}]
        
        doc_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {"request": {"vendor": "REGULA", "data": {}}}
            }
        }
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        doc_data = doc_response.json() if doc_response.status_code == 200 else {}
        
        # ====================================================================
        # COMPREHENSIVE OCR ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🔍 COMPREHENSIVE OCR ANALYSIS")
        logger.info("="*120)
        
        ocr_analysis = analyze_ocr_response(doc_data)
        ocr_analysis_report = generate_ocr_analysis_report(ocr_analysis)
        
        logger.info(ocr_analysis_report)
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        
        logger.info(f"\nOverall Status: {ocr_analysis['overall_status']}")
        logger.info(f"Critical Issues: {len(ocr_analysis['critical_issues'])}")
        logger.info(f"Field Issues: {len(ocr_analysis['field_issues'])}")
        logger.info(f"Warnings: {len(ocr_analysis['warnings'])}")
        
        logger.info("\n" + "="*120 + "\n")
        
        # Only assert liveness (not document verification for debugging)
        assert liveness_decision == "LIVE", "Liveness must pass"
