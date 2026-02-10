"""
Shared fixtures for Face Matcher (Nexaface) tests.
"""

import pytest
import json


@pytest.fixture
def face_matcher_base_path():
    """Base path for nexaface endpoints."""
    return "/nexaface"


@pytest.fixture
def face_image_base64(env_store):
    """Get face image from .env file (TX_DL_FACE_B64)."""
    face_b64 = env_store.get("TX_DL_FACE_B64")
    if not face_b64:
        pytest.skip("TX_DL_FACE_B64 not found in .env file")
    return face_b64


@pytest.fixture
def probe_face_image(env_store):
    """Get probe face image - uses TX_DL_FACE_B64."""
    return env_store.get("TX_DL_FACE_B64") or pytest.skip("TX_DL_FACE_B64 not found")


@pytest.fixture
def gallery_face_image(env_store):
    """Get gallery face image - uses TX_DL_FACE_B64."""
    return env_store.get("TX_DL_FACE_B64") or pytest.skip("TX_DL_FACE_B64 not found")


@pytest.fixture(autouse=True)
def log_api_responses(api_client):
    """
    Automatically log all API requests and responses.
    
    This fixture runs for every test in this directory (autouse=True).
    """
    original_post = api_client.http_client.post
    original_get = api_client.http_client.get
    
    def logged_post(url, **kwargs):
        print(f"\n{'='*80}")
        print(f"?? POST {url}")
        
        if 'json' in kwargs:
            payload = kwargs['json'].copy()
            # Truncate long base64 strings for readability
            if 'probe' in payload and 'VISIBLE_FRONTAL' in payload.get('probe', {}):
                probe_img = payload['probe']['VISIBLE_FRONTAL']
                payload['probe']['VISIBLE_FRONTAL'] = f"{probe_img[:50]}... (truncated, length: {len(probe_img)})"
            if 'gallery' in payload and 'VISIBLE_FRONTAL' in payload.get('gallery', {}):
                gallery_img = payload['gallery']['VISIBLE_FRONTAL']
                payload['gallery']['VISIBLE_FRONTAL'] = f"{gallery_img[:50]}... (truncated, length: {len(gallery_img)})"
            if 'encounter' in payload and 'VISIBLE_FRONTAL' in payload.get('encounter', {}):
                enc_img = payload['encounter']['VISIBLE_FRONTAL']
                payload['encounter']['VISIBLE_FRONTAL'] = f"{enc_img[:50]}... (truncated, length: {len(enc_img)})"
            
            print(f"?? Request Body:")
            print(json.dumps(payload, indent=2))
        
        response = original_post(url, **kwargs)
        
        print(f"\n?? Response Status: {response.status_code}")
        try:
            response_data = response.json()
            # Truncate long template exports
            if 'export' in response_data and len(response_data.get('export', '')) > 100:
                response_data['export'] = f"{response_data['export'][:50]}... (truncated, length: {len(response_data['export'])})"
            print(f"?? Response Body:")
            print(json.dumps(response_data, indent=2))
        except:
            print(f"?? Response Text: {response.text[:500]}")
        
        print(f"{'='*80}\n")
        return response
    
    def logged_get(url, **kwargs):
        print(f"\n{'='*80}")
        print(f"?? GET {url}")
        
        response = original_get(url, **kwargs)
        
        print(f"?? Response Status: {response.status_code}")
        print(f"?? Response: {response.text}")
        print(f"{'='*80}\n")
        
        return response
    
    api_client.http_client.post = logged_post
    api_client.http_client.get = logged_get
    
    yield  # Test runs here
    
    # Restore original methods after test
    api_client.http_client.post = original_post
    api_client.http_client.get = original_get
