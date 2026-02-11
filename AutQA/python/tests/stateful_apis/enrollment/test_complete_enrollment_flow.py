import pytest
from tests.utils.settings_validator import validate_enrollment_flow


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCompleteEnrollmentFlow:

    def test_complete_flow(self, api_client, unique_username, face_frames, workflow, env_vars):
        """
        Complete enrollment: initiate + add face.
        Validates portal settings match test implementation.
        """
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
        print(f"\n>>> STEP 1: POST /onboarding/enrollment/enroll")

        enroll_response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=enroll_payload
        )

        assert enroll_response.status_code == 200, (
            f"Step 1 failed: {enroll_response.status_code} - {enroll_response.text}"
        )
        data = enroll_response.json()
        enrollment_token = data.get("enrollmentToken")
        required_checks = data.get("requiredChecks", [])
        
        assert enrollment_token, "Missing enrollmentToken"
        print(f"✅ Step 1 - Initiated | Token: {enrollment_token[:20]}...")
        print(f"   Required checks: {required_checks}")

        # VALIDATE SETTINGS - Test only implements addFace
        test_implements = ['addFace']
        validate_enrollment_flow(required_checks, test_implements)

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
        print(f"\n>>> STEP 2: POST /onboarding/enrollment/addFace")

        face_response = api_client.http_client.post(
            "/onboarding/enrollment/addFace",
            json=face_payload
        )

        assert face_response.status_code == 200, (
            f"Step 2 failed: {face_response.status_code} - {face_response.text}"
        )

        face_data = face_response.json()
        print(f"\n✅ Step 2 - Face added | Fields: {list(face_data.keys())}")

        if "registrationCode" in face_data:
            print(f"   Registration code: {face_data['registrationCode']}")
        else:
            print(f"   No registration code yet (enrollment may need more steps)")

    def test_settings_match_portal(self, enrollment_settings):
        """Verify test suite reflects current portal settings."""
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
