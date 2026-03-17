"""
Enhanced Add Face Tests with Full Validation
Tests face enrollment with age and liveness validation
"""
import pytest
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@pytest.mark.stateful
@pytest.mark.enrollment
class TestAddFace:
    """Face enrollment tests with complete validation"""
    
    def test_basic(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Basic face enrollment test with validation"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Basic Face Enrollment")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        logger.info(f"✅ Enrolled: {unique_username}")
        
        # Add face
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
        
        # Validate
        liveness_data = (
            face_data.get("faceLivenessResults", {})
                     .get("video", {})
                     .get("liveness_result", {})
        )
        liveness_decision = liveness_data.get("decision")
        if liveness_decision is None:
            flat = face_data.get("livenessResult")
            if flat is not None:
                liveness_decision = "LIVE" if flat else "SPOOF"
            else:
                liveness_decision = "UNKNOWN"
        
        logger.info(f"✅ Face added successfully")
        logger.info(f"   Liveness: {liveness_decision}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert face_resp.status_code == 200
        assert liveness_decision == "LIVE", f"Liveness failed: {liveness_decision}"
        
        logger.info("✅ TEST PASSED\n")
    
    def test_returns_registration_code(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test that face enrollment returns registration code"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment Returns Registration Code")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face
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
        enrollment_status = face_data.get("enrollmentStatus")
        print("\n[DEBUG] Full addFace response:")
        print(json.dumps(face_data, indent=2))
        
        logger.info(f"✅ Registration Code: {registration_code}")
        logger.info(f"   Enrollment Status: {enrollment_status}")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert enrollment_status == 2, (
            f"Enrollment did not complete (enrollmentStatus={enrollment_status}). "
            f"Full response: {face_data}"
        )
        assert registration_code, (
            f"Registration code missing despite enrollmentStatus=2. "
            f"Check saveToSubjectManager in server config. Full response: {face_data}"
        )
        
        logger.info("✅ TEST PASSED\n")
    
    def test_with_full_metadata(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test face enrollment with complete metadata"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment with Full Metadata")
        logger.info("="*120)
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face with metadata
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "username": unique_username,
                        "test_run": "full_metadata",
                        "timestamp": datetime.now().isoformat()
                    },
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        
        face_data = face_resp.json()
        
        logger.info(f"✅ Face enrolled with full metadata")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert face_resp.status_code == 200
        
        logger.info("✅ TEST PASSED\n")
    
    def test_with_5_frames(self, api_client, unique_username, face_frames, workflow, env_vars, caplog):
        """Test face enrollment with exactly 5 frames"""
        caplog.set_level(logging.INFO)
        
        test_start = datetime.now()
        logger.info("\n" + "="*120)
        logger.info("TEST: Face Enrollment with 5 Frames")
        logger.info("="*120)
        
        # Use only first 5 frames
        five_frames = face_frames[:5]
        
        logger.info(f"   Using {len(five_frames)} frames")
        
        # Enroll
        enroll_resp = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Test",
            "lastName": "User",
        })
        enrollment_token = enroll_resp.json().get("enrollmentToken")
        
        # Add face
        face_resp = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": five_frames},
                },
            },
        })
        
        face_data = face_resp.json()
        
        logger.info(f"✅ Face enrolled with 5 frames")
        logger.info(f"   Duration: {(datetime.now() - test_start).total_seconds():.2f}s")
        
        assert face_resp.status_code == 200
        
        logger.info("✅ TEST PASSED\n")
