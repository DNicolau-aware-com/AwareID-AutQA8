"""
Enhanced Cancel Enrollment Tests
Tests enrollment cancellation with transaction tracking
"""
import pytest
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCancelEnrollment:
    """Enrollment cancellation tests"""
    
    def test_cancel_enrollment(self, api_client, unique_username, caplog):
        """Test canceling an active enrollment"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Cancel Active Enrollment")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        enroll_tx_id = enroll_resp.json().get("transactionId", "N/A")
        
        logger.info(f"✅ Enrolled: {unique_username}")
        logger.info(f"   Transaction ID: {enroll_tx_id}")
        logger.info(f"   Token: {enrollment_token[:20]}...")
        
        # Cancel
        cancel_resp = api_client.http_client.post("/onboarding/enrollment/cancel", json={
            "enrollmentToken": enrollment_token
        })
        
        logger.info(f"\n✅ Canceled enrollment")
        logger.info(f"   Status: {cancel_resp.status_code}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert cancel_resp.status_code == 200, f"Cancel failed: {cancel_resp.status_code}"
        logger.info("1️⃣  Cancel Status: ✅ PASSED (200)")
        
        logger.info("\n✅ TEST PASSED\n")
    
    def test_missing_enrollment_token(self, api_client, caplog):
        """Test cancel with missing token"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Cancel with Missing Token (Negative Test)")
        logger.info("="*120)
        
        # Cancel without token
        cancel_resp = api_client.http_client.post("/onboarding/enrollment/cancel", json={})
        
        logger.info(f"✅ Expected failure: {cancel_resp.status_code}")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert cancel_resp.status_code == 400, f"Expected 400, got {cancel_resp.status_code}"
        logger.info("1️⃣  Error Status: ✅ PASSED (400)")
        
        logger.info("\n✅ TEST PASSED\n")
    
    def test_invalid_enrollment_token(self, api_client, caplog):
        """Test cancel with invalid token"""
        caplog.set_level(logging.INFO)
        
        logger.info("\n" + "="*120)
        logger.info("TEST: Cancel with Invalid Token (Negative Test)")
        logger.info("="*120)
        
        # Cancel with fake token
        cancel_resp = api_client.http_client.post("/onboarding/enrollment/cancel", json={
            "enrollmentToken": "invalid-token-12345"
        })
        
        logger.info(f"✅ Expected failure: {cancel_resp.status_code}")
        
        # Validations
        logger.info("\n" + "🔥"*60)
        logger.info("CRITICAL VALIDATIONS")
        logger.info("🔥"*60)
        
        assert cancel_resp.status_code in [400, 404, 500], f"Expected error, got {cancel_resp.status_code}"
        logger.info("1️⃣  Error Status: ✅ PASSED (Error returned)")
        
        logger.info("\n✅ TEST PASSED\n")
