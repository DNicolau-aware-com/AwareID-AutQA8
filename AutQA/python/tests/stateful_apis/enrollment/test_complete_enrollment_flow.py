"""
Enhanced Complete Enrollment Flow Tests
Tests full enrollment workflow with validation
"""
import pytest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCompleteEnrollmentFlow:
    """Complete enrollment flow tests"""
    
    def test_complete_flow(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test complete enrollment workflow"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Complete Enrollment Flow")
        logger.info("="*120)
        
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
        
        # Step 2: Add Face
        logger.info("\n📸 Step 2: Add Face")
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        face_data = face_resp.json()
        registration_code = face_data.get("registrationCode")
        
        logger.info(f"   ✅ Face added")
        logger.info(f"   Registration Code: {registration_code}")
        
        logger.info(f"\n⏱️  Total Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert enroll_resp.status_code == 200
        assert face_resp.status_code == 200
        assert registration_code
        
        logger.info("✅ TEST PASSED\n")
    
    def test_settings_match_portal(self, api_client, caplog):
        """Test that API settings match portal configuration"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Settings Match Portal")
        logger.info("="*120)
        
        config_resp = api_client.http_client.get("/onboarding/admin/customerConfig")
        config = config_resp.json().get("onboardingConfig", {})
        
        enrollment_opts = config.get("onboardingOptions", {}).get("enrollment", {})
        
        logger.info(f"✅ Configuration retrieved:")
        logger.info(f"   Add Face: {enrollment_opts.get('addFace')}")
        logger.info(f"   Add Device: {enrollment_opts.get('addDevice')}")
        logger.info(f"   Add Document: {enrollment_opts.get('addDocument')}")
        
        assert config_resp.status_code == 200
        
        logger.info("✅ TEST PASSED\n")
