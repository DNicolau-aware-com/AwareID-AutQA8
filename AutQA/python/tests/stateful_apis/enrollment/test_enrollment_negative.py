"""
Enhanced Enrollment Negative Tests
Tests error handling and validation
"""
import pytest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.negative
class TestEnrollmentNegative:
    """Negative test cases for enrollment"""
    
    def test_enroll_missing_username(self, api_client, caplog):
        """Test enroll without username"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Enroll Missing Username (Negative)")
        logger.info("="*120)
        
        resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code == 400
        logger.info("✅ TEST PASSED\n")
    
    def test_enroll_empty_username(self, api_client, caplog):
        """Test enroll with empty username"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Enroll Empty Username (Negative)")
        logger.info("="*120)
        
        resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": "",
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code == 400
        logger.info("✅ TEST PASSED\n")
    
    def test_add_face_invalid_token(self, api_client, face_frames, workflow, caplog):
        """Test add face with invalid token"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Add Face Invalid Token (Negative)")
        logger.info("="*120)
        
        resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": "invalid-token",
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": "test"},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code in [400, 404, 500]
        logger.info("✅ TEST PASSED\n")
    
    def test_add_face_missing_token(self, api_client, face_frames, workflow, caplog):
        """Test add face without token"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Add Face Missing Token (Negative)")
        logger.info("="*120)
        
        resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": "test"},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code == 400
        logger.info("✅ TEST PASSED\n")
    
    def test_add_face_empty_frames(self, api_client, unique_username, workflow, caplog):
        """Test add face with empty frames"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Add Face Empty Frames (Negative)")
        logger.info("="*120)
        
        # Enroll first
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face with empty frames
        resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": []},
                },
            },
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code in [400, 500]
        logger.info("✅ TEST PASSED\n")
    
    def test_cancel_invalid_token(self, api_client, caplog):
        """Test cancel with invalid token"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Cancel Invalid Token (Negative)")
        logger.info("="*120)
        
        resp = api_client.http_client.post("/onboarding/enrollment/cancel", json={
            "enrollmentToken": "invalid-token"
        })
        
        logger.info(f"Expected failure: {resp.status_code}")
        assert resp.status_code in [400, 404, 500]
        logger.info("✅ TEST PASSED\n")
