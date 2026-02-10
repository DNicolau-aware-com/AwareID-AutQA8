
import pytest
import uuid



@pytest.mark.stateful
@pytest.mark.authentication
class TestAuthenticationNegative:

    def test_non_enrolled_user(self, api_client):
        """
        Negative: Authenticate with a username that does not exist.
        Expected: 400 or 500 error.
        """
        payload = {"username": f"nonexistent_{uuid.uuid4().hex[:8]}"}

        print(f"\n>>> REQUEST: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")

    def test_missing_username_and_registration_code(self, api_client):
        """
        Negative: Authenticate with empty payload.
        Expected: 400 or 500 error.
        """
        payload = {}

        print(f"\n>>> REQUEST: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")

    def test_verify_face_invalid_token(self, api_client, face_frames, workflow):
        """
        Negative: verifyFace with an invalid authToken.
        Expected: 400 or 500 error.
        """
        payload = {
            "authToken": "invalid_auth_token_99999",
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": "test"},
                    "workflow_data": {
                        "workflow": workflow,
                        "frames": face_frames,
                    },
                },
            },
        }

        print(f"\n>>> REQUEST: POST /onboarding/authentication/verifyFace")
        print(f">>> PAYLOAD (authToken): {payload['authToken']}")

        response = api_client.http_client.post(
            "/onboarding/authentication/verifyFace",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")

    def test_cancel_invalid_token(self, api_client):
        """
        Negative: Cancel with an invalid authToken.
        Expected: 400 or 500 error.
        """
        payload = {"authToken": "invalid_token_99999"}

        print(f"\n>>> REQUEST: POST /onboarding/authentication/cancel")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/authentication/cancel",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data
        assert "status" in data
        assert "timestamp" in data
        print(f"\n✅ errorCode: {data['errorCode']}")
        print(f"   errorMsg:  {data['errorMsg'][:100]}")
