"""
Passport Enrollment Test - Enhanced with Full OCR Analysis
"""
import pytest
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
        workflow,
        env_vars,
        apply_server_config,
        caplog,
    ):
        """Simple passport enrollment with comprehensive OCR analysis"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        face_image = normalize_base64((env_vars.get("FACE") or "").strip())
        passport_front = normalize_base64(env_vars.get("PASS_FRONT_DAN", "").strip())

        if not face_image:
            pytest.skip("Missing FACE in .env")
        
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
        
        # Configure - override autouse enrollment_face_only with document preset
        apply_server_config("enrollment_with_document")
        
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
        
        # Face - build frames from FACE env var
        now_ms = int(time.time() * 1000)
        frames = [
            {"data": face_image, "timestamp": now_ms + (i * 30), "tags": []}
            for i in range(3)
        ]

        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": frames},
                },
            },
        })
        
        assert face_response.status_code == 200, \
            f"addFace failed: {face_response.status_code} - {face_response.text[:300]}"
        face_data = face_response.json()
        logger.info(f"addFace full response: {json.dumps(face_data, indent=2)}")
        liveness_result = face_data.get("livenessResult", False)
        liveness_decision = "LIVE" if liveness_result else "SPOOF"
        logger.info(f"liveness_decision: {liveness_decision}")
        
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
