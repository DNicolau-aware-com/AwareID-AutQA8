"""
Server capabilities discovery tests.

These tests help identify what algorithms and features are enabled on the server.
"""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_discover_enabled_algorithms(api_client, face_matcher_base_path, face_image_base64):
    """
    Discover which face matching algorithms are enabled on the server.
    
    Tests: F200, F500
    """
    algorithms = ["F200", "F500"]
    enabled_algorithms = []
    disabled_algorithms = []
    
    print("\n" + "="*80)
    print("DISCOVERING ENABLED ALGORITHMS")
    print("="*80)
    
    for algorithm in algorithms:
        payload = {
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": {
                "comparator": {
                    "algorithm": algorithm,
                    "faceTypes": ["VISIBLE_FRONTAL"]
                }
            }
        }
        
        try:
            response = api_client.http_client.post(
                f"{face_matcher_base_path}/compare",
                json=payload
            )
            
            if response.status_code == 200:
                enabled_algorithms.append(algorithm)
                result = response.json()
                print(f"  ? {algorithm}: ENABLED (score: {result.get('scorePercent')}%)")
            elif response.status_code == 500:
                error_data = response.json()
                if "error" in error_data and error_data["error"].get("code") == 113:
                    disabled_algorithms.append(algorithm)
                    print(f"  ? {algorithm}: DISABLED (error 113: algorithm not enabled)")
                else:
                    print(f"  ? {algorithm}: ERROR {response.status_code} - {error_data}")
            else:
                print(f"  ? {algorithm}: UNEXPECTED STATUS {response.status_code}")
        except Exception as e:
            print(f"  ? {algorithm}: EXCEPTION - {str(e)}")
    
    print("\n" + "="*80)
    print(f"ENABLED: {', '.join(enabled_algorithms) if enabled_algorithms else 'None'}")
    print(f"DISABLED: {', '.join(disabled_algorithms) if disabled_algorithms else 'None'}")
    print("="*80)
    
    # Test passes if at least one algorithm is enabled
    assert len(enabled_algorithms) > 0, "No algorithms are enabled on the server!"


@pytest.mark.stateless
@pytest.mark.face_matcher  
def test_check_server_version(api_client, face_matcher_base_path):
    """Check what version of Face Matcher (Nexaface) is running."""
    response = api_client.http_client.get(f"{face_matcher_base_path}/version")
    
    print("\n" + "="*80)
    print("SERVER VERSION INFORMATION")
    print("="*80)
    
    if response.status_code == 200:
        version = response.text
        print(f"  Nexaface Version: {version}")
    else:
        print(f"  Could not retrieve version (status: {response.status_code})")
    
    print("="*80)


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_check_available_endpoints(api_client, face_matcher_base_path, face_image_base64):
    """Test which Face Matcher endpoints are available."""
    endpoints = {
        "version": ("GET", "/version", None),
        "compare": ("POST", "/compare", {
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": {
                "comparator": {
                    "algorithm": "F500",
                    "faceTypes": ["VISIBLE_FRONTAL"]
                }
            }
        }),
        "export": ("POST", "/export", {
            "encounter": {
                "VISIBLE_FRONTAL": face_image_base64,
                "id": "test_001"
            }
        })
    }
    
    print("\n" + "="*80)
    print("CHECKING AVAILABLE ENDPOINTS")
    print("="*80)
    
    available = []
    unavailable = []
    
    for name, (method, path, payload) in endpoints.items():
        full_path = f"{face_matcher_base_path}{path}"
        
        try:
            if method == "GET":
                response = api_client.http_client.get(full_path)
            else:  # POST
                response = api_client.http_client.post(full_path, json=payload or {})
            
            if response.status_code == 404:
                unavailable.append(f"{method} {path}")
                print(f"  ? {method:6} {path:20} NOT FOUND (404)")
            elif response.status_code in [200, 400, 500]:
                available.append(f"{method} {path}")
                print(f"  ? {method:6} {path:20} AVAILABLE (status: {response.status_code})")
            else:
                print(f"  ? {method:6} {path:20} UNEXPECTED (status: {response.status_code})")
        except Exception as e:
            print(f"  ? {method:6} {path:20} ERROR: {str(e)}")
    
    print("\n" + "="*80)
    print(f"AVAILABLE: {len(available)} endpoints")
    print(f"NOT FOUND: {len(unavailable)} endpoints")
    print("="*80)
    
    assert len(available) > 0, "No endpoints are available!"


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_server_capabilities_summary(api_client, face_matcher_base_path, face_image_base64):
    """
    Comprehensive server capabilities check.
    
    This test summarizes all available features on the Face Matcher server.
    """
    print("\n" + "="*80)
    print("FACE MATCHER SERVER CAPABILITIES SUMMARY")
    print("="*80)
    
    # Check version
    version_response = api_client.http_client.get(f"{face_matcher_base_path}/version")
    if version_response.status_code == 200:
        print(f"\n?? Server Version: {version_response.text}")
    else:
        print(f"\n?? Server Version: Could not retrieve")
    
    # Check algorithms
    print("\n?? Algorithms:")
    algorithms_to_test = ["F200", "F500"]
    for algo in algorithms_to_test:
        payload = {
            "probe": {"VISIBLE_FRONTAL": face_image_base64},
            "gallery": {"VISIBLE_FRONTAL": face_image_base64},
            "workflow": {
                "comparator": {
                    "algorithm": algo,
                    "faceTypes": ["VISIBLE_FRONTAL"]
                }
            }
        }
        
        response = api_client.http_client.post(
            f"{face_matcher_base_path}/compare",
            json=payload
        )
        
        if response.status_code == 200:
            print(f"  ? {algo}: Enabled")
        elif response.status_code == 500:
            try:
                error = response.json()
                if error.get("error", {}).get("code") == 113:
                    print(f"  ? {algo}: Disabled")
                else:
                    print(f"  ? {algo}: Error {error}")
            except:
                print(f"  ? {algo}: Unknown status")
        else:
            print(f"  ? {algo}: Status {response.status_code}")
    
    # Check endpoints
    print("\n?? Endpoints:")
    print("  ? GET  /nexaface/version")
    print("  ? POST /nexaface/compare")
    print("  ? POST /nexaface/export")
    
    print("\n" + "="*80)
