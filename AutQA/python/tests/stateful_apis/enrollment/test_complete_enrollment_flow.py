
import pytest


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCompleteEnrollmentFlow:

    def test_complete_flow(self, api_client, unique_username, face_frames, workflow, env_vars):
        """Complete enrollment: initiate + add face."""
        print(f"\n{'='*60}")
        print("COMPLETE ENROLLMENT FLOW")
        print(f"{'='*60}")
        print(f"Username: {unique_username} | Workflow: {workflow}")

        # Step 1: Initiate enrollment
        enroll_payload = {
            "username": unique_username,
            "email": env_vars.get("EMAIL") or f"{unique_username}@example.com",
            "firstName": env_vars.get("FIRSTNAME") or "Test",
            "lastName": env_vars.get("LASTNAME") or "User",
        }
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> PAYLOAD: {enroll_payload}")

        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=enroll_payload
        )
        print(f"\n<<< STATUS:   {enroll_response.status_code}")
        print(f"<<< RESPONSE: {enroll_response.json()}")

        assert enroll_response.status_code == 200, (
            f"Step 1 failed: {enroll_response.status_code} - {enroll_response.text}"
        )
        enrollment_token = enroll_response.json().get("enrollmentToken")
        assert enrollment_token, "Missing enrollmentToken"

        # Step 2: Add face
        face_payload = {
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/addFace")
        print(f">>> PAYLOAD (token): {enrollment_token[:20]}...")

        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json=face_payload
        )
        print(f"\n<<< STATUS:   {face_response.status_code}")
        print(f"<<< RESPONSE: {face_response.json()}")

        assert face_response.status_code == 200, (
            f"Step 2 failed: {face_response.status_code} - {face_response.text}"
        )

        # Cleanup: cancel enrollment
        print(f"\n>>> CLEANUP: POST /onboarding/enrollment/cancel")
        cancel_response = api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json={"enrollmentToken": enrollment_token}
        )
        print(f"<<< STATUS: {cancel_response.status_code}")

    def test_settings_match_portal(self, enrollment_settings):
        """Verify test suite matches current portal settings."""
        print(f"\n{'='*60}")
        print("ENROLLMENT SETTINGS (from portal)")
        print(f"{'='*60}")
        for key, value in enrollment_settings.items():
            if value is True: print(f"  ENABLED:  {key}")
            elif value is False: print(f"  DISABLED: {key}")
            else: print(f"  VALUE:    {key} = {value}")

        assert enrollment_settings["add_face"] is True
        assert enrollment_settings["prevent_duplicate_enrollments"] is True
        assert enrollment_settings["add_document"] is False
