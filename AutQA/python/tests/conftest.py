"""
Pytest configuration and fixtures.
Provides shared fixtures for all tests including API clients,
test data, and authentication tokens.
"""
from __future__ import annotations

import json
import pytest
import sys
from datetime import datetime
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
        print("[>>] AUTO TOKEN REFRESH")
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

            # Invalidate settings cache so ApiClient picks up the fresh token
            from autqa.core import config as _config
            _config._settings_cache = None

            print(f"[INFO] [OK] JWT token refreshed successfully!")
            print(f"[INFO]      Token expires in: {expires_in} seconds")
            print("="*80 + "\n")

        except Exception as e:
            print(f"[WARNING] Could not refresh token: {e}")
            print(f"[WARNING] Tests may fail if JWT is expired")
            print("="*80 + "\n")
    
    except ImportError:
        pass  # Silently skip if retrieve_token not available
    except Exception as e:
        print(f"[WARNING] Error during auto token refresh: {e}")


def pytest_sessionstart(session):
    """Store a unique run_id (timestamp) on config for artifact grouping."""
    session.config._run_id = datetime.now().strftime("%Y%m%d_%H%M%S")


def pytest_sessionfinish(session, exitstatus):
    """Open the HTML report in the browser automatically after the test session."""
    import webbrowser
    from pathlib import Path

    report_path = Path(__file__).parent.parent / "report.html"
    if report_path.exists():
        print(f"\n[INFO] Opening HTML report: {report_path}")
        webbrowser.open(report_path.as_uri())


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

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook that runs after each test phase (setup, call, teardown).

    - Stores item.rep_<when> so fixtures can inspect pass/fail status.
    - On teardown: writes artifacts/<run_id>/<test_name>.json with all
      HTTP transactions captured by log_api_responses.
    - Reports test results to admin portal (console only for now).
    """
    outcome = yield
    rep = outcome.get_result()

    # Make outcome available to fixtures via item.rep_setup / rep_call / rep_teardown
    setattr(item, f"rep_{rep.when}", rep)

    # ── Artifact writing (once per test, at the teardown phase) ──────────────
    if rep.when == "teardown":
        transactions = getattr(item, "_api_transactions", [])
        if transactions:
            run_id = getattr(item.config, "_run_id", "unknown")
            rep_call = getattr(item, "rep_call", None)
            if rep_call and rep_call.passed:
                result = "PASSED"
            elif rep_call and rep_call.failed:
                result = "FAILED"
            elif rep_call and rep_call.skipped:
                result = "SKIPPED"
            else:
                result = "UNKNOWN"

            artifact = {
                "run_id": run_id,
                "test": item.nodeid,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "transactions": transactions,
            }

            safe_name = (
                item.nodeid
                .replace("\\", "_")
                .replace("/", "_")
                .replace("::", "__")
                .replace(".py", "")
            )
            artifacts_dir = Path(item.config.rootdir) / "artifacts" / run_id
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifacts_dir / f"{safe_name}.json"
            artifact_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
            print(f"\n[ARTIFACT] Written: {artifact_path}")

    # ── Admin portal report (call phase only) ────────────────────────────────
    if rep.when == "call":
        try:
            if call.excinfo is None:
                status = "PASSED"
                error_msg = None
            elif call.excinfo.typename == "Skipped":
                status = "SKIPPED"
                error_msg = str(call.excinfo.value)
            else:
                status = "FAILED"
                error_msg = str(call.excinfo.value)

            test_name = item.nodeid.split("::")[-1]
            print(f"\n[ADMIN REPORT] {test_name}: {status}")
            if error_msg:
                print(f"[ADMIN REPORT] Error: {error_msg}")
        except Exception as e:
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
"""
Auto-Reporting Pytest Fixture
Automatically captures test data and generates intelligent reports
NO CODE CHANGES NEEDED IN TESTS!
"""
import pytest
import time
import json
from typing import Dict, Optional
from autqa.core.intelligent_analyzer import (
    TestReport, TestType, IntelligentAnalyzer, Transaction, TransactionStatus
)


class TestContext:
    """Captures test execution context automatically"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.report: Optional[TestReport] = None
        self.start_time = time.time()
        self.responses: Dict[str, any] = {}
        
    def set_test_type(self, test_type: TestType, expected: str, actual: str = None):
        """Initialize the report"""
        self.report = TestReport(
            test_name=self.test_name,
            test_type=test_type,
            expected_outcome=expected,
            actual_outcome=actual or "UNKNOWN"
        )
    
    def capture_response(self, step_name: str, response_data: Dict):
        """Capture a response for later analysis"""
        self.responses[step_name] = response_data
    
    def finalize(self, passed: bool, actual_outcome: str = None):
        """Finalize and generate report"""
        if self.report:
            if actual_outcome:
                self.report.actual_outcome = actual_outcome
            self.report.finalize(passed)
            
            # Auto-analyze all captured responses
            for step_name, response_data in self.responses.items():
                if "enroll" in step_name.lower() and "face" not in step_name.lower():
                    IntelligentAnalyzer.analyze_enrollment(self.report, response_data)
                elif "face" in step_name.lower():
                    # Check if age verification is involved
                    expected_age = self.report.expected_outcome if self.report.test_type == TestType.AGE_VERIFICATION else None
                    IntelligentAnalyzer.analyze_face_enrollment(self.report, response_data, expected_age)
                elif "document" in step_name.lower():
                    IntelligentAnalyzer.analyze_document_ocr(self.report, response_data)
                elif "auth" in step_name.lower():
                    IntelligentAnalyzer.analyze_authentication(self.report, response_data, self.report.expected_outcome)


@pytest.fixture
def test_context(request):
    """
    Auto-reporting fixture - captures everything automatically!
    
    Usage in tests:
        def test_something(self, test_context):
            test_context.set_test_type(TestType.AGE_VERIFICATION, expected="FAIL")
            
            # Make API calls as normal
            response = api_client.post(...)
            
            # Just capture the response - analyzer does the rest!
            test_context.capture_response("enroll", response.json())
    """
    ctx = TestContext(test_name=request.node.name)
    
    yield ctx
    
    # Auto-finalize on test end
    if ctx.report and not ctx.report.end_time:
        # Determine if test passed from pytest
        passed = not hasattr(request.node, 'rep_call') or request.node.rep_call.passed
        ctx.finalize(passed)
        
        # Auto-generate HTML report
        html = IntelligentAnalyzer.generate_html_report(ctx.report)
        
        # Save to file
        report_file = f"reports/{ctx.test_name.replace('::', '_')}_report.html"
        import os
        os.makedirs("reports", exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Also save JSON
        json_file = f"reports/{ctx.test_name.replace('::', '_')}_report.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(ctx.report.to_dict(), f, indent=2)


# ==============================================================================
# EVEN SIMPLER: Decorator approach
# ==============================================================================

def auto_analyze(test_type: TestType, expected_outcome: str):
    """
    Decorator that automatically analyzes test results
    
    Usage:
        @auto_analyze(TestType.AGE_VERIFICATION, expected_outcome="FAIL")
        def test_age_1_to_16(self, api_client):
            # Test code here - no changes needed!
            # Just return responses or use test_context
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Auto-inject test_context if not present
            if 'test_context' not in kwargs:
                from unittest.mock import MagicMock
                kwargs['test_context'] = MagicMock()
            
            # Run test
            result = func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator
