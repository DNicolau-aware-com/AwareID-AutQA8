
import pytest


@pytest.mark.stateful
@pytest.mark.enrollment
class TestCancelEnrollment:

    # ==========================================================================
    # POSITIVE TEST
    # ==========================================================================

    def test_cancel_enrollment(self, api_client):
        """
        Positive: Cancel an active enrollment session.
        First initiates enrollment to get a valid token, then cancels it.
        """
        # Step 1: Initiate enrollment to get a valid token
        enroll_payload = {
            "username": "TroyKohler",
            "email": "TroyKohler@mireya.netinfo",
            "firstName": "Troy",
            "lastName": "Kohler",
            "phoneNumber": "+17742961793",
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
            f"Enrollment should succeed first. Got: {enroll_response.status_code}. Response: {enroll_response.text}"
        )
        token = enroll_response.json().get("enrollmentToken")
        assert token, "enrollmentToken must not be empty"

        # Step 2: Cancel enrollment
        cancel_payload = {"enrollmentToken": token}
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/cancel")
        print(f">>> PAYLOAD: {cancel_payload}")

        cancel_response = api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json=cancel_payload
        )
        print(f"\n<<< STATUS:   {cancel_response.status_code}")
        print(f"<<< RESPONSE: {cancel_response.text}")

        assert cancel_response.status_code in [200, 204], (
            f"Expected 200/204, got {cancel_response.status_code}. Response: {cancel_response.text}"
        )

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_missing_enrollment_token(self, api_client):
        """
        Negative: Cancel without enrollmentToken field.
        Expected: 400 INPUT_FORMAT_ERROR or INPUT_VALUES_ERROR
        """
        payload = {}
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/cancel")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json=payload
        )
        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data, "Error response must contain errorCode"
        assert "errorMsg" in data, "Error response must contain errorMsg"
        assert "status" in data, "Error response must contain status"
        assert "timestamp" in data, "Error response must contain timestamp"

    def test_invalid_enrollment_token(self, api_client):
        """
        Negative: Cancel with an invalid/fake enrollmentToken.
        Expected: 400 or 500 with error response.
        """
        payload = {"enrollmentToken": "9336b7b9-6a37-4aca-91b0-10b929e5c340"}
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/cancel")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json=payload
        )
        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code in [400, 500], (
            f"Expected 400/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data, "Error response must contain errorCode"
        assert "errorMsg" in data, "Error response must contain errorMsg"
        assert "status" in data, "Error response must contain status"
        assert "timestamp" in data, "Error response must contain timestamp"

