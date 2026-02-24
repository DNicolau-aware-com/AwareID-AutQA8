"""
Pytest configuration and fixtures.
Provides shared fixtures for all tests including API clients,
test data, and authentication tokens.
"""
from __future__ import annotations

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Try to import, but make optional for now
try:
    from autqa.core.api_client import ApiClient
    from autqa.core.config import get_settings
    from autqa.core.env_store import EnvStore
    FRAMEWORK_AVAILABLE = True
except ImportError as e:
    FRAMEWORK_AVAILABLE = False
    ApiClient = None
    import_error_msg = str(e)

# Try to import EnrollmentService
try:
    from autqa.services.enrollment_service import EnrollmentService
    ENROLLMENT_SERVICE_AVAILABLE = True
except ImportError:
    ENROLLMENT_SERVICE_AVAILABLE = False
    EnrollmentService = None


# ==============================================================================
# AUTO TOKEN REFRESH (runs once per session)
# ==============================================================================

def pytest_configure(config):
    """
    Pytest hook that runs before test collection.
    Automatically refreshes JWT token if expired or about to expire.
    """
    if not FRAMEWORK_AVAILABLE:
        print("[WARNING] Framework not available - skipping JWT refresh")
        return
    
    # Framework available - proceed with JWT refresh
    
    try:
        from generated.retrieve_token import retrieve_token
        from dotenv import dotenv_values
        
        env = dotenv_values()
        
        # Check if we have OAuth credentials
        if not all([env.get("BASEURL"), env.get("REALM_NAME"), 
                   env.get("CLIENT_ID"), env.get("CLIENT_SECRET")]):
            return  # Silently skip if credentials not available
        
        print("\n" + "="*80)
        print("?? AUTO TOKEN REFRESH")
        print("="*80)
        print("[INFO] Refreshing JWT token before running tests...")
        
        # Get a fresh token
        try:
            token_data = retrieve_token(
                base_url=env["BASEURL"],
                realm_name=env["REALM_NAME"],
                client_id=env["CLIENT_ID"],
                client_secret=env["CLIENT_SECRET"],
            )
            
            jwt = token_data["access_token"]
            expires_in = token_data.get("expires_in", "N/A")
            
            # Update .env file
            env_path = project_root / ".env"
            content = env_path.read_text(encoding='utf-8')
            lines = content.splitlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("JWT="):
                    lines[i] = f"JWT={jwt}"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"JWT={jwt}")
            
            env_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
            
            print(f"[INFO] ? JWT token refreshed successfully!")
            print(f"[INFO]    Token expires in: {expires_in} seconds")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"[WARNING] ??  Could not refresh token: {e}")
            print(f"[WARNING]    Tests may fail if JWT is expired")
            print("="*80 + "\n")
    
    except ImportError:
        pass  # Silently skip if retrieve_token not available
    except Exception as e:
        print(f"[WARNING] Error during auto token refresh: {e}")


# ==============================================================================
# SESSION-LEVEL FIXTURES (run once per test session)
# ==============================================================================

@pytest.fixture(scope="session")
def settings():
    """Load settings from .env file (once per session)."""
    return get_settings()


@pytest.fixture(scope="session")
def api_client_session():
    """
    API client that lasts for entire test session.
    Reuses the same token across all tests.
    """
    return ApiClient()


@pytest.fixture
def api_client():
    """
    Fresh API client for each test.
    Creates new client per test for isolation.
    """
    client = ApiClient()
    return client


@pytest.fixture
def enrollment_service(api_client):
    """
    Enrollment service for enrollment workflow tests.
    Provides high-level enrollment operations.
    """
    service = EnrollmentService(api_client)
    return service


@pytest.fixture
def env_store():
    """Environment store for reading/writing .env."""
    from autqa.core.config import default_env_path
    return EnvStore(default_env_path())


# ==============================================================================
# ADMIN PORTAL REPORTING (reports test results to admin API)
# ==============================================================================

def pytest_runtest_makereport(item, call):
    """
    Pytest hook that runs after each test phase (setup, call, teardown).
    Reports test results to admin portal API.
    """
    if call.when != "call":
        # Only report actual test execution, not setup/teardown
        return
    
    try:
        # Determine test outcome
        if call.excinfo is None:
            status = "PASSED"
            error_msg = None
        elif call.excinfo.typename == "Skipped":
            status = "SKIPPED"
            error_msg = str(call.excinfo.value)
        else:
            status = "FAILED"
            error_msg = str(call.excinfo.value)
        
        # Get test details
        test_name = item.nodeid.split("::")[-1]  # Just the test function name
        test_file = item.nodeid.split("::")[0]   # File path
        
        # TODO: Replace with your actual admin API endpoint
        # This is where you need to send the test result
        # Example:
        # import requests
        # admin_api_url = "https://your-admin-portal.com/api/test-results"
        # payload = {
        #     "test_name": test_name,
        #     "test_file": test_file,
        #     "status": status,
        #     "error": error_msg,
        #     "timestamp": datetime.now().isoformat()
        # }
        # requests.post(admin_api_url, json=payload)
        
        print(f"\n[ADMIN REPORT] {test_name}: {status}")
        if error_msg:
            print(f"[ADMIN REPORT] Error: {error_msg}")
            
    except Exception as e:
        # Don't fail tests if reporting fails
        print(f"\n[WARNING] Failed to report to admin portal: {e}")


# ==============================================================================
# ADMIN PORTAL REPORTING - Dynamic Status Handling
# ==============================================================================

def pytest_runtest_logreport(report):
    """
    Hook that captures test results and reports them to admin portal.
    Handles dynamic statuses from server (passed, pending, canceled, error, etc.)
    """
    # Only report on the actual test execution (call phase)
    if report.when != "call":
        return
    
    # Get test details
    test_name = report.nodeid.split("::")[-1] if "::" in report.nodeid else report.nodeid
    test_file = report.nodeid.split("::")[0] if "::" in report.nodeid else ""
    
    # Determine pytest status
    if report.passed:
        pytest_status = "PASSED"
    elif report.failed:
        pytest_status = "FAILED"
    elif report.skipped:
        pytest_status = "SKIPPED"
    else:
        pytest_status = "UNKNOWN"
    
    # Try to extract server response status if available
    server_status = None
    response_code = None
    
    if hasattr(report, "longreprtext") and report.longreprtext:
        text = report.longreprtext
        
        # Try to extract HTTP status code
        import re
        status_match = re.search(r'status["\s:]+(\d+)', text, re.IGNORECASE)
        if status_match:
            response_code = int(status_match.group(1))
        
        # Try to extract server status message
        # Patterns: "status": "pending", {"status": "canceled"}, etc.
        status_pattern = re.search(r'["\']status["\']\s*:\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
        if status_pattern:
            server_status = status_pattern.group(1)
    
    # Build comprehensive status info
    status_info = {
        "test_name": test_name,
        "test_file": test_file,
        "pytest_status": pytest_status,
        "server_status": server_status,
        "response_code": response_code
    }
    
    # Print to console
    print(f"\n[ADMIN REPORT] {test_name}: {pytest_status}")
    if server_status:
        print(f"[ADMIN REPORT] Server Status: {server_status}")
    if response_code:
        print(f"[ADMIN REPORT] Response Code: {response_code}")
    
    # If there's an error, show brief message
    if report.failed and hasattr(report, "longreprtext"):
        error_lines = report.longreprtext.split("\n")
        for line in error_lines:
            if "AssertionError:" in line or "Error:" in line:
                error_msg = line.strip()[:200]  # Limit length
                print(f"[ADMIN REPORT] Error: {error_msg}")
                break
    
    # TODO: Send to your admin API
    # This is where you POST the comprehensive status
    # try:
    #     import requests
    #     from datetime import datetime
    #     
    #     admin_url = "https://qa8.awareid.com/api/test-results"
    #     payload = {
    #         "test_name": test_name,
    #         "test_file": test_file,
    #         "pytest_status": pytest_status,
    #         "server_status": server_status,
    #         "response_code": response_code,
    #         "timestamp": datetime.now().isoformat(),
    #         "allure_uuid": getattr(report, "nodeid", None)
    #     }
    #     
    #     requests.post(admin_url, json=payload, timeout=5)
    # except Exception as e:
    #     # Don't fail tests if reporting fails
    #     print(f"[ADMIN REPORT] Warning: Failed to send to portal: {e}")
    
    return status_info



# ==============================================================================
# DOCUMENT & FACE IMAGE FIXTURES - Based on actual .env variables
# ==============================================================================

@pytest.fixture
def document_image_base64(env_vars):
    """
    Document front image in base64 format.
    Priority: TX_DL_FRONT_b64 > DAN_DOC_FRONT > OCR_FRONT
    """
    doc_front = (
        env_vars.get("TX_DL_FRONT_b64") or
        env_vars.get("DAN_DOC_FRONT") or
        env_vars.get("OCR_FRONT")
    )
    
    if not doc_front:
        pytest.skip("No document front image found in .env")
    
    if doc_front.startswith('data:'):
        doc_front = doc_front.split(',')[1]
    
    return doc_front


@pytest.fixture
def document_image_rear_base64(env_vars):
    """
    Document back image in base64 format.
    Priority: TX_DL_BACK_b64 > DAN_DOC_BACK > OCR_BACK
    """
    doc_back = (
        env_vars.get("TX_DL_BACK_b64") or
        env_vars.get("DAN_DOC_BACK") or
        env_vars.get("OCR_BACK")
    )
    
    if doc_back and doc_back.startswith('data:'):
        doc_back = doc_back.split(',')[1]
    
    return doc_back


@pytest.fixture
def face_image_base64(env_vars):
    """
    Face image in base64 format.
    Priority: TX_DL_FACE_B64 > FACE > OCR_FACE
    """
    face = (
        env_vars.get("TX_DL_FACE_B64") or
        env_vars.get("FACE") or
        env_vars.get("OCR_FACE")
    )
    
    if not face:
        pytest.skip("No face image found in .env")
    
    if face.startswith('data:'):
        face = face.split(',')[1]
    
    return face


# Individual fixtures for each env variable
@pytest.fixture
def spoof_image(env_vars):
    """SPOOF base64 image"""
    img = env_vars.get("SPOOF")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def dan_doc_front(env_vars):
    """DAN_DOC_FRONT base64 image"""
    img = env_vars.get("DAN_DOC_FRONT")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def dan_doc_back(env_vars):
    """DAN_DOC_BACK base64 image"""
    img = env_vars.get("DAN_DOC_BACK")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def face_image(env_vars):
    """FACE base64 image"""
    img = env_vars.get("FACE")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def tx_dl_front(env_vars):
    """TX_DL_FRONT_b64 base64 image"""
    img = env_vars.get("TX_DL_FRONT_b64")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def tx_dl_back(env_vars):
    """TX_DL_BACK_b64 base64 image"""
    img = env_vars.get("TX_DL_BACK_b64")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def tx_dl_face(env_vars):
    """TX_DL_FACE_B64 base64 image"""
    img = env_vars.get("TX_DL_FACE_B64")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def ocr_front(env_vars):
    """OCR_FRONT base64 image"""
    img = env_vars.get("OCR_FRONT")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def ocr_back(env_vars):
    """OCR_BACK base64 image"""
    img = env_vars.get("OCR_BACK")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img


@pytest.fixture
def ocr_face(env_vars):
    """OCR_FACE base64 image"""
    img = env_vars.get("OCR_FACE")
    if img and img.startswith('data:'):
        return img.split(',')[1]
    return img
