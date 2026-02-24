"""
Quick test to find where age estimation data is stored/accessible
"""
import pytest

class TestFindAgeEstimationEndpoints:
    
    def test_check_admin_endpoints_for_age_data(self, api_client):
        """Check various admin endpoints for age estimation data"""
        
        print("\n" + "="*80)
        print("SEARCHING FOR AGE ESTIMATION DATA")
        print("="*80)
        
        endpoints_to_check = [
            "/onboarding/admin/transactions",
            "/onboarding/admin/audit",
            "/onboarding/admin/enrollments",
            "/onboarding/admin/users",
            "/onboarding/admin/metrics",
            "/onboarding/admin/analytics",
        ]
        
        for endpoint in endpoints_to_check:
            print(f"\n[CHECK] {endpoint}")
            try:
                response = api_client.http_client.get(endpoint)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    # Check if age-related data exists
                    response_text = str(data).lower()
                    if "age" in response_text or "estimation" in response_text:
                        print(f"    FOUND age-related data!")
                        print(f"   Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                elif response.status_code == 404:
                    print(f"    Endpoint not found")
                else:
                    print(f"     Status: {response.status_code}")
            except Exception as e:
                print(f"    Error: {e}")
