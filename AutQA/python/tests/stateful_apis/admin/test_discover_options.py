import pytest
import json


@pytest.mark.stateful
@pytest.mark.admin
class TestDiscoverEnrollmentOptions:
    """
    Discover all available enrollment, authentication, and re-enrollment options.
    Use this to see what settings are configurable.
    """

    def test_discover_all_onboarding_options(self, api_client):
        """
        Discover all onboarding options and their current values.
        Saves results to a JSON file for test generation.
        """
        print(f"\n{'='*80}")
        print("DISCOVERING ALL ONBOARDING OPTIONS")
        print(f"{'='*80}")

        # Get current config
        response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response.status_code == 200

        data = response.json()
        onboarding_config = data.get("onboardingConfig", {})
        onboarding_options = onboarding_config.get("onboardingOptions", {})

        # Extract all sections
        enrollment = onboarding_options.get("enrollment", {})
        authentication = onboarding_options.get("authentication", {})
        reenrollment = onboarding_options.get("reenrollment", {})

        print(f"\n📋 ENROLLMENT OPTIONS:")
        for key, value in enrollment.items():
            status = "✅ ENABLED" if value else "❌ DISABLED" if isinstance(value, bool) else f"VALUE: {value}"
            print(f"   {key}: {status}")

        print(f"\n🔐 AUTHENTICATION OPTIONS:")
        for key, value in authentication.items():
            status = "✅ ENABLED" if value else "❌ DISABLED" if isinstance(value, bool) else f"VALUE: {value}"
            print(f"   {key}: {status}")

        print(f"\n🔄 RE-ENROLLMENT OPTIONS:")
        for key, value in reenrollment.items():
            status = "✅ ENABLED" if value else "❌ DISABLED" if isinstance(value, bool) else f"VALUE: {value}"
            print(f"   {key}: {status}")

        # Save to file for analysis
        discovery_data = {
            "enrollment": enrollment,
            "authentication": authentication,
            "reenrollment": reenrollment,
            "other_config": {
                "maxDeviceIds": onboarding_config.get("maxDeviceIds"),
                "maxAuthenticationAttempts": onboarding_config.get("maxAuthenticationAttempts"),
                "saveToSubjectManager": onboarding_config.get("saveToSubjectManager"),
                "recordEnrollmentVideo": onboarding_config.get("recordEnrollmentVideo"),
                "recordAuthenticationVideo": onboarding_config.get("recordAuthenticationVideo"),
                "recordRenrollmentVideo": onboarding_config.get("recordRenrollmentVideo"),
            }
        }

        # Save to outputs
        import os
        output_file = "/mnt/user-data/outputs/discovered_options.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            json.dump(discovery_data, f, indent=4)

        print(f"\n💾 Saved to: {output_file}")
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Total enrollment options: {len(enrollment)}")
        print(f"Total authentication options: {len(authentication)}")
        print(f"Total re-enrollment options: {len(reenrollment)}")
        print(f"\nUse this data to generate parametrized tests!")
