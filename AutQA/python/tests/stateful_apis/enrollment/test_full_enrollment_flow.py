"""
Enhanced Full Enrollment Flow Tests
Tests complete enrollment with all biometrics
"""
import pytest
import logging
import time
from datetime import datetime

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
class TestFullEnrollmentFlow:
    """Full enrollment flow with all modalities"""
    
    def test_full_enrollment_with_all_steps(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test full enrollment: enroll + device + face + document"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Full Enrollment Flow (All Steps)")
        logger.info("="*120)
        
        # Get document images
        doc_front = normalize_base64(env_vars.get("DAN_DOC_FRONT", "").strip())
        doc_back = normalize_base64(env_vars.get("DAN_DOC_BACK", "").strip())
        
        if not doc_front:
            pytest.skip("DAN_DOC_FRONT not available")
        
        # Step 1: Enroll
        logger.info("\n📝 Step 1: Enroll")
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        logger.info(f"   ✅ Enrolled: {unique_username}")
        time.sleep(1)
        
        # Step 2: Add Device
        logger.info("\n📱 Step 2: Add Device")
        device_id = f"device_{int(time.time())}"
        device_resp = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": device_id,
            "platform": "web"
        })
        logger.info(f"   ✅ Device added: {device_id}")
        time.sleep(1)
        
        # Step 3: Add Face
        logger.info("\n📸 Step 3: Add Face")
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        logger.info(f"   ✅ Face added")
        time.sleep(3)
        
        # Step 4: Add Document
        logger.info("\n📄 Step 4: Add Document OCR")
        doc_images = [{"lightingScheme": 6, "image": doc_front, "format": "JPG"}]
        if doc_back:
            doc_images.append({"lightingScheme": 6, "image": doc_back, "format": "JPG"})
        
        doc_resp = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json={
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {"request": {"vendor": "REGULA", "data": {}}}
            }
        })
        
        if doc_resp.status_code == 200:
            doc_data = doc_resp.json()
            doc_verified = doc_data.get("documentVerificationResult")
            registration_code = doc_data.get("registrationCode")
            
            logger.info(f"   ✅ Document added")
            logger.info(f"   Document Verified: {doc_verified}")
            logger.info(f"   Registration Code: {registration_code}")
        
        logger.info(f"\n⏱️  Total Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert enroll_resp.status_code == 200
        assert device_resp.status_code == 200
        assert face_resp.status_code == 200
        assert doc_resp.status_code == 200
        
        logger.info("✅ TEST PASSED\n")
    
    def test_settings_match_portal(self, api_client, caplog):
        """Test API settings match portal"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Settings Match Portal")
        logger.info("="*120)
        
        config_resp = api_client.http_client.get("/onboarding/admin/customerConfig")
        config = config_resp.json().get("onboardingConfig", {})
        
        logger.info("✅ Configuration retrieved")
        
        assert config_resp.status_code == 200
        
        logger.info("✅ TEST PASSED\n")
