import pytest


@pytest.mark.stateful
@pytest.mark.enrollment
class TestEnrollmentNegative:

    def test_enroll_missing_username(self, api_client):
        response = api_client.http_client.post("/onboarding/enrollment/enroll", json={})
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"

    def test_enroll_empty_username(self, api_client):
        response = api_client.http_client.post("/onboarding/enrollment/enroll", json={"username": ""})
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"

    def test_add_face_invalid_token(self, api_client, face_frames, workflow):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={"enrollmentToken": "invalid_token_12345", "faceLivenessData": {"video": {"meta_data": {"username": "test"}, "workflow_data": {"workflow": workflow, "frames": face_frames}}}}
        )
        assert response.status_code in [400, 401, 404, 422, 500], f"Expected error status, got {response.status_code}"

    def test_add_face_missing_token(self, api_client, face_frames, workflow):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={"faceLivenessData": {"video": {"meta_data": {"username": "test"}, "workflow_data": {"workflow": workflow, "frames": face_frames}}}}
        )
        assert response.status_code in [400, 401, 422], f"Expected error status, got {response.status_code}"

    def test_add_face_empty_frames(self, api_client, enrollment_token, workflow, unique_username):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={"enrollmentToken": enrollment_token, "faceLivenessData": {"video": {"meta_data": {"username": unique_username}, "workflow_data": {"workflow": workflow, "frames": []}}}}
        )
        assert response.status_code in [400, 422, 500], f"Expected error status for empty frames, got {response.status_code}"

    def test_cancel_invalid_token(self, api_client):
        response = api_client.http_client.post("/onboarding/enrollment/cancel", json={"enrollmentToken": "invalid_token_99999"})
        assert response.status_code in [400, 401, 404, 422, 500], f"Expected error status, got {response.status_code}"
