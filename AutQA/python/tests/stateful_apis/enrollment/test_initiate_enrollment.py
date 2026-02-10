
import pytest


@pytest.mark.stateful
@pytest.mark.enrollment
class TestInitiateEnrollment:

    # ==========================================================================
    # POSITIVE TEST
    # ==========================================================================

    def test_initiate_enrollment(self, api_client):
        """
        Positive: Initiate enrollment with all fields.
        Verifies userExistsAlready = false for a new user.
        """
        payload = {
            "username": "TroyKohler",
            "email": "TroyKohler@mireya.netinfo",
            "firstName": "Troy",
            "lastName": "Kohler",
            "phoneNumber": "+17742961793",
        }
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        data = response.json()
        assert "enrollmentToken" in data, f"Missing enrollmentToken. Got: {list(data.keys())}"
        assert data["enrollmentToken"], "enrollmentToken must not be empty"
        assert "userExistsAlready" in data, (
            f"Response missing userExistsAlready. Got: {list(data.keys())}"
        )
        assert data["userExistsAlready"] is False, (
            f"New user should have userExistsAlready=false. Got: {data['userExistsAlready']}"
        )
        print(f"\n✅ userExistsAlready: {data['userExistsAlready']} (correct - this is a new user)")

        # Cleanup
        api_client.http_client.post(
            "/onboarding/enrollment/cancel",
            json={"enrollmentToken": data["enrollmentToken"]}
        )

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_missing_username(self, api_client):
        """Negative: Missing required field username."""
        payload = {
            "email": "TroyKohler@mireya.netinfo",
            "firstName": "Troy",
            "lastName": "Kohler",
            "phoneNumber": "+17742961793",
        }
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
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

    def test_missing_email(self, api_client):
        """Negative: Missing required field email."""
        payload = {
            "username": "TroyKohler",
            "firstName": "Troy",
            "lastName": "Kohler",
            "phoneNumber": "+17742961793",
        }
        print(f"\n>>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
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

    def test_duplicate_username(self, api_client):
        """
        Negative: Initiate enrollment for an already enrolled user.
        Uses TESTETSTETS which is already fully enrolled in the system.
        Expected: 200 with userExistsAlready = true.
        """
        payload = {
            "username": "TESTETSTETS",
            "email": "TESTETSTETS@example.com",
            "firstName": "Test",
            "lastName": "User",
        }

        print(f"\n>>> REQUEST: POST /onboarding/enrollment/enroll")
        print(f">>> PAYLOAD: {payload}")

        response = api_client.http_client.post(
            "/onboarding/enrollment/enroll",
            json=payload
        )

        print(f"\n<<< STATUS:   {response.status_code}")
        print(f"<<< RESPONSE: {response.json()}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        data = response.json()

        assert "userExistsAlready" in data, (
            f"Response missing userExistsAlready. Got: {list(data.keys())}"
        )
        assert data["userExistsAlready"] is True, (
            f"TESTETSTETS is already enrolled - userExistsAlready should be true. Got: {data['userExistsAlready']}"
        )
        print(f"\n✅ userExistsAlready: {data['userExistsAlready']} (correct - user already enrolled)")

        # Cleanup token if returned
        if data.get("enrollmentToken"):
            api_client.http_client.post(
                "/onboarding/enrollment/cancel",
                json={"enrollmentToken": data["enrollmentToken"]}
            )
        if data.get("reEnrollmentToken"):
            api_client.http_client.post(
                "/onboarding/enrollment/cancel",
                json={"enrollmentToken": data["reEnrollmentToken"]}
            )
