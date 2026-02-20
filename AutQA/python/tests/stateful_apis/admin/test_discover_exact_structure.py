import pytest
import json


@pytest.mark.stateful
@pytest.mark.admin
class TestDiscoverExactStructure:
    """
    Discover the EXACT structure your API returns.
    This will show us where age/duplicate settings actually are.
    """

    def test_get_full_config_structure(self, api_client):
        """
        Get complete config and save to file for analysis.
        """
        print(f"\n{'='*80}")
        print("DISCOVERING EXACT API STRUCTURE")
        print(f"{'='*80}")

        response = api_client.http_client.get("/onboarding/admin/customerConfig")
        assert response.status_code == 200

        full_data = response.json()
        
        print(f"\n📋 COMPLETE API RESPONSE:")
        print(json.dumps(full_data, indent=4))

        # Save to file
        import os
        output_dir = "/mnt/user-data/outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "full_customer_config.json")
        with open(output_file, "w") as f:
            json.dump(full_data, f, indent=4)

        print(f"\n💾 Saved to: full_customer_config.json")

        # Print structure analysis
        config = full_data.get("onboardingConfig", {})
        
        print(f"\n📊 TOP-LEVEL CONFIG KEYS:")
        for key in config.keys():
            value = config[key]
            value_type = type(value).__name__
            print(f"   {key}: {value_type}")

        # Show onboardingOptions structure
        options = config.get("onboardingOptions", {})
        print(f"\n📊 ONBOARDING OPTIONS:")
        print(f"   enrollment: {list(options.get('enrollment', {}).keys())}")
        print(f"   authentication: {list(options.get('authentication', {}).keys())}")
        print(f"   reenrollment: {list(options.get('reenrollment', {}).keys())}")

        # Look for age/duplicate fields EVERYWHERE
        print(f"\n🔍 SEARCHING FOR AGE/DUPLICATE FIELDS:")
        
        def find_fields(obj, prefix=""):
            """Recursively find all fields containing age/duplicate keywords"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    
                    # Check if key contains our keywords
                    if any(keyword in key.lower() for keyword in ['age', 'duplicate', 'prevent', 'threshold']):
                        print(f"   ✅ FOUND: {full_key} = {value}")
                    
                    # Recurse
                    if isinstance(value, (dict, list)):
                        find_fields(value, full_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_fields(item, f"{prefix}[{i}]")

        find_fields(full_data)

        print(f"\n{'='*80}")
        print(f"Now check the downloaded file to see the complete structure!")
        print(f"{'='*80}")
