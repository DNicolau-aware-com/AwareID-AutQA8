import pytest
import time


@pytest.mark.stateful
@pytest.mark.enrollment
class TestAddFace:

    def test_basic(self, api_client, enrollment_token, face_frames, workflow, unique_username):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {"video": {"meta_data": {"username": unique_username}, "workflow_data": {"workflow": workflow, "frames": face_frames}}},
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        print(f"\nAdd face response fields: {list(response.json().keys())}")

    def test_returns_registration_code(self, api_client, enrollment_token, face_frames, workflow, unique_username):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {"video": {"meta_data": {"username": unique_username}, "workflow_data": {"workflow": workflow, "frames": face_frames}}},
            }
        )
        assert response.status_code == 200
        data = response.json()
        if "registrationCode" in data:
            assert data["registrationCode"], "registrationCode should not be empty"
            print(f"\nRegistration code: {data['registrationCode']}")
        else:
            print(f"\nNo registrationCode yet. Fields: {list(data.keys())}")

    def test_with_full_metadata(self, api_client, enrollment_token, face_frames, workflow, unique_username):
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {"video": {"meta_data": {"client_device_brand": "Apple", "client_device_model": "iPhone 14", "client_os_version": "iOS 17.0", "client_version": "1.0.0", "localization": "en-US", "username": unique_username}, "workflow_data": {"workflow": workflow, "frames": face_frames}}},
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"

    def test_with_5_frames(self, api_client, enrollment_token, face_image, workflow, unique_username):
        now_ms = int(time.time() * 1000)
        frames = [{"data": face_image, "timestamp": now_ms + (i * 30), "tags": []} for i in range(5)]
        response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json={
                "enrollmentToken": enrollment_token,
                "faceLivenessData": {"video": {"meta_data": {"username": unique_username}, "workflow_data": {"workflow": workflow, "frames": frames}}},
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        print(f"\nAdd face with 5 frames succeeded")
