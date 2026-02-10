"""
Shared fixtures for Document Verification tests.
"""

import pytest
import json


@pytest.fixture
def doc_verification_base_path():
    """Base path for document verification endpoints."""
    return "/documentVerification"


@pytest.fixture
def document_image_base64(env_store):
    """Get document front image from .env file (OCR_FRONT)."""
    # Try OCR_FRONT first (new standard)
    doc_b64 = env_store.get("OCR_FRONT")
    
    # Fallback to old variable names if OCR_FRONT not found
    if not doc_b64:
        doc_b64 = (
            env_store.get("TX_DL_FRONT_b64") or
            env_store.get("TX_DL_FRONT_B64") or
            env_store.get("DAN_DOC_FRONT")
        )
    
    if not doc_b64:
        pytest.skip("OCR_FRONT not found in .env file")
    
    return doc_b64


@pytest.fixture
def document_image_rear_base64(env_store):
    """Get document rear image from .env file (OCR_BACK)."""
    # Try OCR_BACK first (new standard)
    doc_b64 = env_store.get("OCR_BACK")
    
    # Fallback to old variable names if OCR_BACK not found
    if not doc_b64:
        doc_b64 = (
            env_store.get("TX_DL_BACK_b64") or
            env_store.get("TX_DL_BACK_B64") or
            env_store.get("DAN_DOC_BACK")
        )
    
    # If still not found, fallback to front image
    if not doc_b64:
        doc_b64 = env_store.get("OCR_FRONT") or env_store.get("TX_DL_FRONT_b64")
        if not doc_b64:
            pytest.skip("OCR_BACK not found in .env file")
    
    return doc_b64


@pytest.fixture
def face_image_base64(env_store):
    """Get face image from .env file (OCR_FACE) for biometric comparison."""
    # Try OCR_FACE first (new standard)
    face_b64 = env_store.get("OCR_FACE")
    
    # Fallback to old variable names if OCR_FACE not found
    if not face_b64:
        face_b64 = (
            env_store.get("TX_DL_FACE_B64") or
            env_store.get("FACE")
        )
    
    if not face_b64:
        pytest.skip("OCR_FACE not found in .env file")
    
    return face_b64


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
            if 'documentImage' in payload:
                if 'image' in payload['documentImage']:
                    img = payload['documentImage']['image']
                    payload['documentImage']['image'] = f"{img[:50]}... (truncated, length: {len(img)})"
            
            if 'documentsInfo' in payload:
                if 'documentImage' in payload['documentsInfo']:
                    for doc in payload['documentsInfo']['documentImage']:
                        if 'image' in doc:
                            img = doc['image']
                            doc['image'] = f"{img[:50]}... (truncated, length: {len(img)})"
            
            if 'biometricsInfo' in payload:
                if 'facialImage' in payload['biometricsInfo']:
                    if 'image' in payload['biometricsInfo']['facialImage']:
                        img = payload['biometricsInfo']['facialImage']['image']
                        payload['biometricsInfo']['facialImage']['image'] = f"{img[:50]}... (truncated, length: {len(img)})"
            
            print(f"?? Request Body:")
            print(json.dumps(payload, indent=2))
        
        response = original_post(url, **kwargs)
        
        print(f"\n?? Response Status: {response.status_code}")
        try:
            response_data = response.json()
            # Truncate long image fields in response
            if 'frontImg' in response_data and response_data.get('frontImg'):
                response_data['frontImg'] = f"{response_data['frontImg'][:50]}... (truncated)"
            if 'rearImg' in response_data and response_data.get('rearImg'):
                response_data['rearImg'] = f"{response_data['rearImg'][:50]}... (truncated)"
            if 'portraitImage' in response_data and response_data.get('portraitImage'):
                response_data['portraitImage'] = f"{response_data['portraitImage'][:50]}... (truncated)"
            
            # Check nested portraitImage in biometricsAuthenticationResult
            if 'biometricsAuthenticationResult' in response_data:
                bio = response_data['biometricsAuthenticationResult']
                if 'portraitImage' in bio and bio.get('portraitImage'):
                    bio['portraitImage'] = f"{bio['portraitImage'][:50]}... (truncated)"
            
            # Check nested portraitImage in documentAuthenticationResult
            if 'documentAuthenticationResult' in response_data:
                doc = response_data['documentAuthenticationResult']
                if 'portraitImage' in doc and doc.get('portraitImage'):
                    doc['portraitImage'] = f"{doc['portraitImage'][:50]}... (truncated)"
                if 'signatureImage' in doc and doc.get('signatureImage'):
                    doc['signatureImage'] = f"{doc['signatureImage'][:50]}... (truncated)"
            
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
    
    yield
    
    api_client.http_client.post = original_post
    api_client.http_client.get = original_get
