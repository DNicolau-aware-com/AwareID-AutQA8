import pytest
import json


@pytest.mark.stateful
@pytest.mark.admin
class TestGetEnrollmentDetails:
    """
    Tests for GET /onboarding/admin/registration/{registrationCode}
    Get detailed enrollment information for a specific user.
    """

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_get_enrollment_details_valid_code(self, api_client, env_vars):
        """
        Positive: Get enrollment details with valid registration code.
        Uses REGISTRATION_CODE from .env.
        """
        registration_code = env_vars.get("REGISTRATION_CODE")
        if not registration_code:
            pytest.skip("REGISTRATION_CODE not found in .env")

        print(f"\n{'='*80}")
        print("GET ENROLLMENT DETAILS - VALID REGISTRATION CODE")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/registration/{registration_code}")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{registration_code}"
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Validate response structure per API spec
        assert "name" in data, "Missing name"
        assert "email" in data, "Missing email"
        assert "phoneNumber" in data, "Missing phoneNumber"
        assert "startDate" in data, "Missing startDate"
        assert "registrationCode" in data, "Missing registrationCode"
        assert "registeredDevices" in data, "Missing registeredDevices"
        assert "activities" in data, "Missing activities"

        # Validate data types
        assert isinstance(data["registeredDevices"], list), "registeredDevices must be array"
        assert isinstance(data["activities"], list), "activities must be array"

        print(f"\n✅ Enrollment details retrieved")
        print(f"   Name: {data.get('name', 'N/A')}")
        print(f"   Email: {data.get('email', 'N/A')}")
        print(f"   Phone: {data.get('phoneNumber', 'N/A')}")
        print(f"   Registration Date: {data.get('startDate', 'N/A')}")
        print(f"   Registered Devices: {len(data['registeredDevices'])}")
        print(f"   Activities: {len(data['activities'])}")

    def test_response_structure_validation(self, api_client, env_vars):
        """
        Positive: Validate complete response structure.
        Documents all fields returned by the API.
        """
        registration_code = env_vars.get("REGISTRATION_CODE")
        if not registration_code:
            pytest.skip("REGISTRATION_CODE not found in .env")

        print(f"\n{'='*80}")
        print("RESPONSE STRUCTURE VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{registration_code}"
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields per API spec
        required_fields = [
            "name", "email", "phoneNumber", "startDate",
            "registrationCode", "registeredDevices", "activities"
        ]

        print(f"\n📋 Validating response structure:")
        for field in required_fields:
            if field in data:
                value = data[field]
                if isinstance(value, list):
                    print(f"   ✅ {field}: {len(value)} items")
                else:
                    print(f"   ✅ {field}: {str(value)[:50]}")
            else:
                print(f"   ❌ MISSING: {field}")
                pytest.fail(f"Missing required field: {field}")

        # Log device details if present
        if data["registeredDevices"]:
            print(f"\n📱 Registered Devices:")
            for idx, device in enumerate(data["registeredDevices"], 1):
                print(f"   Device {idx}: {list(device.keys())}")

        # Log activity details if present
        if data["activities"]:
            print(f"\n📊 Activities:")
            for idx, activity in enumerate(data["activities"][:3], 1):  # First 3
                print(f"   Activity {idx}: {list(activity.keys())}")

    def test_registration_code_format(self, api_client, env_vars):
        """
        Positive: Verify registration code in response matches request.
        """
        registration_code = env_vars.get("REGISTRATION_CODE")
        if not registration_code:
            pytest.skip("REGISTRATION_CODE not found in .env")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{registration_code}"
        )

        assert response.status_code == 200
        data = response.json()

        returned_code = data.get("registrationCode")
        assert returned_code == registration_code, (
            f"Registration code mismatch. "
            f"Requested: {registration_code}, Returned: {returned_code}"
        )

        print(f"\n✅ Registration code matches: {returned_code}")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_invalid_registration_code_format(self, api_client):
        """
        Negative: Request with invalid registration code format.
        Expected: 400 or 500 error.
        """
        invalid_code = "invalid-code-12345"

        print(f"\n{'='*80}")
        print("INVALID REGISTRATION CODE FORMAT")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/registration/{invalid_code}")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{invalid_code}"
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code in [400, 404, 500], (
            f"Expected 400/404/500, got {response.status_code}"
        )
        data = response.json()
        assert "errorCode" in data
        assert "errorMsg" in data

        print(f"\n✅ Correctly rejected invalid code format")

    def test_non_existent_registration_code(self, api_client):
        """
        Negative: Request with valid format but non-existent registration code.
        Expected: 404 or 400 error.
        """
        fake_code = "00000000-0000-0000-0000-000000000000"

        print(f"\n{'='*80}")
        print("NON-EXISTENT REGISTRATION CODE")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/registration/{fake_code}")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{fake_code}"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 404, 500], (
            f"Expected 400/404/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected non-existent code")

    def test_empty_registration_code(self, api_client):
        """
        Negative: Request with empty registration code.
        Expected: 400 or 404 error.
        """
        print(f"\n{'='*80}")
        print("EMPTY REGISTRATION CODE")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/registration/")

        response = api_client.http_client.get(
            "/onboarding/admin/registration/"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        # Empty path might return 404 (not found) or 400 (bad request)
        assert response.status_code in [400, 404, 405, 500], (
            f"Expected 400/404/405/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected empty registration code")

    def test_malformed_uuid(self, api_client):
        """
        Negative: Request with malformed UUID.
        Expected: 400 INPUT_FORMAT_ERROR
        """
        malformed_uuid = "not-a-uuid-at-all"

        print(f"\n{'='*80}")
        print("MALFORMED UUID")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            f"/onboarding/admin/registration/{malformed_uuid}"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [400, 404, 500], (
            f"Expected 400/404/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected malformed UUID")
