
import pytest


@pytest.mark.stateful
@pytest.mark.authentication
class TestCancelAuthentication:

    # ==========================================================================
    # POSITIVE TEST
    # ==========================================================================

    def test_cancel_authentication(self, api_client, enrolled_username):
        """
        Positive: Cancel an active authentication session.
        First initiates authentication to get a valid authToken, then cancels it.
        """
        # Step 1: Initiate authentication to get a valid token
        auth_payload = {"username": enrolled_username}

        print(f"\n>>> STEP 1: POST /onboarding/authentication/authenticate")
        print(f">>> PAYLOAD: {auth_payload}")

        auth_response = api_client.http_client.post(
            "/onboarding/authentication/authenticate",
            json=auth_payload
        )

        print(f"\n<<< STATUS:   {auth_response.status_code}")
        print(f"<<< RESPONSE: {auth_response.json()}")

        assert auth_response.status_code == 200, (
            f"Auth initiation failed: {auth_response.status_code} - {auth_response.text}"
        )
        auth_token = auth_response.json().get("authToken")
        assert auth_token, "authToken must not be empty"

        # Step 2: Cancel authentication
        cancel_payload = {"authToken": auth_token}

        print(f"\n>>> STEP 2: POST /onboarding/authentication/cancel")
        print(f">>> PAYLOAD: {cancel_payload}")

        cancel_response = api_client.http_client.post(
            "/onboarding/authentication/cancel",
            json=cancel_payload
        )

        print(f"\n<<< STATUS:   {cancel_response.status_code}")
        print(f"<<< RESPONSE: {cancel_response.text}")

        assert cancel_response.status_code in [200, 204], (
            f"Expected 200/204, got {cancel_response.status_code}. Response: {cancel_response.text}"
        )
        print(f"\n✅ Authentication cancelled successfully")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_missing_auth_token(self, api_client):
        """
        Negative: Cancel without authToken field.
        Expected: 400 INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR
        """
        payload = {}

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

    def test_invalid_auth_token(self, api_client):
        """
        Negative: Cancel with an invalid/fake authToken.
        Expected: 400 or 500 error.
        """
        payload = {"authToken": "9336b7b9-6a37-4aca-91b0-10b929e5c340"}

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
