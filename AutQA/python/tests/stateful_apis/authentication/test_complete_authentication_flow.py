import pytest
from tests.utils.settings_validator import validate_authentication_flow


@pytest.mark.stateful
@pytest.mark.authentication
class TestCompleteAuthenticationFlow:

    def test_complete_flow_live(self, api_client, enrolled_username, face_frames, workflow):
        """
        Complete authentication with LIVE image.
        Validates portal settings match test implementation.
        """
        print(f"\n{'='*60}")
        print("COMPLETE AUTHENTICATION FLOW - LIVE IMAGE")
        print(f"{'='*60}")
        print(f"Username: {enrolled_username} | Workflow: {workflow}")

        # Step 1: Initiate authentication
        auth_payload = {"username": enrolled_username}
        print(f"\n>>> STEP 1: POST /onboarding/authentication/authenticate")

        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=auth_payload
        )

        assert auth_response.status_code == 200, (
            f"Step 1 failed: {auth_response.status_code} - {auth_response.text}"
        )
        data = auth_response.json()
        auth_token = data.get("authToken")
        required_checks = data.get("requiredChecks", [])
        
        assert auth_token, "Missing authToken"
        print(f"✅ Step 1 - Auth initiated | Token: {auth_token[:20]}...")
        print(f"   Required checks: {required_checks}")

        # VALIDATE SETTINGS - Test only implements verifyFace
        test_implements = ['verifyFace']
        validate_authentication_flow(required_checks, test_implements)

        # Step 2: Verify face
        verify_payload = {
            "authToken": auth_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {
                        "username": enrolled_username,
                    },
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }
        print(f"\n>>> STEP 2: POST /onboarding/authentication/verifyFace")

        verify_response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=verify_payload
        )

        assert verify_response.status_code == 200, (
            f"Step 2 failed: {verify_response.status_code} - {verify_response.text}"
        )
        result = verify_response.json()

        # Log results
        print(f"\n📋 Results:")
        print(f"   livenessResult: {result.get('livenessResult')}")
        print(f"   matchResult:    {result.get('matchResult')}")
        print(f"   matchScore:     {result.get('matchScore')}%")

        # Assertions
        assert result.get("livenessResult") is True, "Expected live person"
        print(f"\n✅ Authentication PASSED - LIVE person confirmed")

    def test_complete_flow_spoof(self, api_client, enrolled_username, env_vars, workflow):
        """Complete authentication with SPOOF image - should detect spoof."""
        spoof_image = env_vars.get("SPOOF") or env_vars.get("SPOOF_FACE")
        if not spoof_image:
            pytest.skip("SPOOF image not in .env")

        if spoof_image.startswith("data:image"):
            spoof_image = spoof_image.split(",")[1]

        import time
        now_ms = int(time.time() * 1000)
        spoof_frames = [
            {"data": spoof_image.strip(), "timestamp": now_ms + (i * 30), "tags": []}
            for i in range(3)
        ]

        print(f"\n{'='*60}")
        print("COMPLETE AUTHENTICATION FLOW - SPOOF IMAGE")
        print(f"{'='*60}")

        # Initiate
        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json={"username": enrolled_username}
        )
        assert auth_response.status_code == 200
        auth_token = auth_response.json()["authToken"]

        # Verify with spoof
        verify_response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json={
                "authToken": auth_token,
                "faceLivenessData": {
                    "video": {
                        "meta_data": {"username": enrolled_username},
                        "workflow_data": {"workflow": workflow, "frames": spoof_frames},
                    },
                },
            }
        )

        assert verify_response.status_code == 200
        result = verify_response.json()

        print(f"\n📋 Results:")
        print(f"   livenessResult: {result.get('livenessResult')}")

        assert result.get("livenessResult") is False, "Expected spoof detection"
        print(f"\n✅ SPOOF correctly detected")
