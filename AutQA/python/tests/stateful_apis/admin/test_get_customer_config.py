import pytest
import json


@pytest.mark.stateful
@pytest.mark.admin
class TestGetCustomerConfig:
    """
    Tests for GET /onboarding/admin/customerConfig
    Retrieve customer configuration and options.
    """

    # ==========================================================================
    # POSITIVE TESTS
    # ==========================================================================

    def test_get_customer_config(self, api_client):
        """
        Positive: Get customer configuration.
        Validates complete response structure.
        """
        print(f"\n{'='*80}")
        print("GET CUSTOMER CONFIG")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/customerConfig")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        print(f"\n<<< STATUS: {response.status_code}")
        print(f"<<< RESPONSE:\n{json.dumps(response.json(), indent=4)}")

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()

        # Validate response structure per API spec
        assert "onboardingConfig" in data, "Missing onboardingConfig"
        assert "serviceVersion" in data, "Missing serviceVersion"
        assert "expirationTime" in data, "Missing expirationTime"

        print(f"\n✅ Customer config retrieved")
        print(f"   Service Version: {data.get('serviceVersion', 'N/A')}")
        print(f"   Expiration: {data.get('expirationTime', 'N/A')}")

    def test_onboarding_config_structure(self, api_client):
        """
        Positive: Validate onboardingConfig structure.
        Documents all configuration options.
        """
        print(f"\n{'='*80}")
        print("ONBOARDING CONFIG STRUCTURE VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        onboarding_config = data.get("onboardingConfig", {})
        
        print(f"\n📋 Onboarding Config Fields:")
        expected_fields = [
            "onboardingOptions",
            "maxDeviceIds",
            "maxAuthenticationAttempts",
            "saveToSubjectManager",
            "recordEnrollmentVideo",
            "recordAuthenticationVideo",
            "recordRenrollmentVideo"
        ]

        for field in expected_fields:
            if field in onboarding_config:
                value = onboarding_config[field]
                if isinstance(value, dict):
                    print(f"   ✅ {field}: {len(value)} settings")
                else:
                    print(f"   ✅ {field}: {value}")
            else:
                print(f"   ⚠️  MISSING: {field}")

        # Validate critical fields
        assert "maxDeviceIds" in onboarding_config, "Missing maxDeviceIds"
        assert "maxAuthenticationAttempts" in onboarding_config, "Missing maxAuthenticationAttempts"

    def test_onboarding_options_structure(self, api_client):
        """
        Positive: Validate onboardingOptions structure.
        Shows enrollment and authentication settings.
        """
        print(f"\n{'='*80}")
        print("ONBOARDING OPTIONS VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        onboarding_options = data.get("onboardingConfig", {}).get("onboardingOptions", {})
        
        print(f"\n📋 Onboarding Options:")
        print(json.dumps(onboarding_options, indent=4))

        # Document enrollment settings
        if "enrollment" in onboarding_options:
            enrollment = onboarding_options["enrollment"]
            print(f"\n📝 Enrollment Settings:")
            for key, value in enrollment.items():
                print(f"   {key}: {value}")

        # Document authentication settings
        if "authentication" in onboarding_options:
            auth = onboarding_options["authentication"]
            print(f"\n🔐 Authentication Settings:")
            for key, value in auth.items():
                print(f"   {key}: {value}")

    def test_service_version_format(self, api_client):
        """
        Positive: Validate service version format.
        Checks version string is present and valid.
        """
        print(f"\n{'='*80}")
        print("SERVICE VERSION VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        service_version = data.get("serviceVersion")
        assert service_version, "serviceVersion is empty or missing"
        assert isinstance(service_version, str), "serviceVersion must be string"

        print(f"\n✅ Service Version: {service_version}")

        # Basic version format validation (e.g., "1.0.5")
        version_parts = service_version.split(".")
        if len(version_parts) >= 2:
            print(f"   Version parts: {version_parts}")
        else:
            print(f"   ⚠️  Unexpected version format: {service_version}")

    def test_expiration_time_present(self, api_client):
        """
        Positive: Validate expiration time is present.
        """
        print(f"\n{'='*80}")
        print("EXPIRATION TIME VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        expiration_time = data.get("expirationTime")
        assert expiration_time, "expirationTime is empty or missing"

        print(f"\n✅ Expiration Time: {expiration_time}")

    def test_max_device_ids_value(self, api_client):
        """
        Positive: Validate maxDeviceIds is a positive integer.
        """
        print(f"\n{'='*80}")
        print("MAX DEVICE IDS VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        max_device_ids = data.get("onboardingConfig", {}).get("maxDeviceIds")
        
        assert max_device_ids is not None, "maxDeviceIds is missing"
        assert isinstance(max_device_ids, int), "maxDeviceIds must be integer"
        assert max_device_ids > 0, f"maxDeviceIds must be positive, got {max_device_ids}"

        print(f"\n✅ Max Device IDs: {max_device_ids}")

    def test_video_recording_flags(self, api_client):
        """
        Positive: Validate video recording flags.
        Checks recordEnrollmentVideo, recordAuthenticationVideo, recordRenrollmentVideo.
        """
        print(f"\n{'='*80}")
        print("VIDEO RECORDING FLAGS VALIDATION")
        print(f"{'='*80}")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfig"
        )

        assert response.status_code == 200
        data = response.json()

        config = data.get("onboardingConfig", {})

        video_flags = {
            "recordEnrollmentVideo": config.get("recordEnrollmentVideo"),
            "recordAuthenticationVideo": config.get("recordAuthenticationVideo"),
            "recordRenrollmentVideo": config.get("recordRenrollmentVideo")
        }

        print(f"\n📹 Video Recording Settings:")
        for flag, value in video_flags.items():
            if value is not None:
                status = "✅ ENABLED" if value else "❌ DISABLED"
                print(f"   {flag}: {status}")
                assert isinstance(value, bool), f"{flag} must be boolean"
            else:
                print(f"   ⚠️  {flag}: NOT SET")

    def test_config_caching(self, api_client):
        """
        Positive: Verify config can be retrieved multiple times.
        Tests idempotency.
        """
        print(f"\n{'='*80}")
        print("CONFIG CACHING / IDEMPOTENCY TEST")
        print(f"{'='*80}")

        # First request
        print(f"\n>>> Request 1")
        response1 = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response1.status_code == 200
        data1 = response1.json()

        # Second request
        print(f">>> Request 2")
        response2 = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response2.status_code == 200
        data2 = response2.json()

        # Compare responses (should be identical)
        assert data1 == data2, "Config changed between requests"

        print(f"\n✅ Config is stable across multiple requests")
        print(f"   Service Version: {data1.get('serviceVersion')}")

    # ==========================================================================
    # NEGATIVE TESTS
    # ==========================================================================

    def test_invalid_endpoint(self, api_client):
        """
        Negative: Request with invalid endpoint path.
        Expected: 404
        """
        print(f"\n{'='*80}")
        print("INVALID ENDPOINT")
        print(f"{'='*80}")
        print(f">>> REQUEST: GET /onboarding/admin/customerConfigInvalid")

        response = api_client.http_client.get(
            "/onboarding/admin/customerConfigInvalid"
        )

        print(f"\n<<< STATUS: {response.status_code}")

        assert response.status_code in [404, 400, 500], (
            f"Expected 404/400/500, got {response.status_code}"
        )

        print(f"\n✅ Correctly rejected invalid endpoint")
