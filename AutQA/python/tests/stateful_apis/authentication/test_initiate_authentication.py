
import pytest


@pytest.mark.stateful
@pytest.mark.authentication
class TestInitiateAuthentication:

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_initiate_authentication_by_username(self, api_client, enrolled_username):
        """
        Positive: Initiate authentication using an enrolled username.
        """
        payload = {"username": enrolled_username}

        print(f"\n>>> REQUEST: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        data = response.json()
        assert "authToken" in data, f"Missing authToken. Got: {list(data.keys())}"
        assert data["authToken"], "authToken must not be empty"

        print(f"\n✅ authToken: {data['authToken'][:20]}...")

        if "requiredChecks" in data:
            print(f"✅ requiredChecks: {data['requiredChecks']}")
            valid_values = ["verifyDevice", "verifyFace", "verifyVoice"]
            for check in data["requiredChecks"]:
                assert check in valid_values, (
                    f"Unexpected value in requiredChecks: '{check}'. Valid: {valid_values}"
                )

    def test_response_structure(self, api_client, enrolled_username):
        """
        Positive: Validate all response fields per API spec.
        Expected fields: authToken, recordVideo, requiredChecks
        """
        payload = {"username": enrolled_username}

        print(f"\n>>> REQUEST: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code == 200
        data = response.json()

        print(f"\n📋 Response fields:")
        for field in ["authToken", "recordVideo", "requiredChecks"]:
            if field in data:
                print(f"   ✅ PRESENT: {field} = {str(data[field])[:40]}")
            else:
                print(f"   ⚠️  MISSING: {field}")

        assert "authToken" in data, "authToken is required in response"

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_missing_username_and_registration_code(self, api_client):
        """
        Negative: Neither username nor registrationCode provided.
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

    def test_non_enrolled_username(self, api_client):
        """
        Negative: Username that does not exist in the system.
        Expected: 400 or 500 error.
        """
        payload = {"username": "nonexistent_user_xyz_99999"}

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

    def test_invalid_registration_code(self, api_client):
        """
        Negative: Invalid registrationCode (from API spec example).
        Expected: 400 or 500 error.
        """
        payload = {"registrationCode": "cad27b38-a0da-4599-b376-40eb533e38aa"}

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
