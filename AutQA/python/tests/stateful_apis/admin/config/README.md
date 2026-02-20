# Admin Configuration Tests

Complete test suite for AwareID Admin Portal configuration settings.

## 📋 Overview

This test suite provides comprehensive coverage of all admin configuration settings including:
- Document verification settings
- Age estimation configuration
- Duplicate prevention settings
- Enrollment toggles (face, device, document, voice, PIN)
- System parameters (max devices, auth attempts)
- Configuration dependencies and validation rules

## 📁 Test Files
```
tests/stateful_apis/admin/config/
├── README.md                           # This file
├── conftest.py                         # Test fixtures and delays
├── test_complete_suite.py              # ⭐ Main test suite (ALL tests)
├── test_document_simple.py             # Document-specific tests
├── test_age_estimation.py              # Age verification tests
├── test_duplicate_prevention.py        # Duplicate detection tests
├── test_enrollment_toggles.py          # Enrollment toggle tests
├── test_other_parameters.py            # System parameter tests
├── test_preset_configs.py              # Preset configuration tests
├── test_dependency_rules.py            # Dependency validation tests
└── test_all_toggles.py                 # Toggle test templates
```

## 🚀 Quick Start

### Run All Tests
```powershell
# Run complete suite and open HTML report in Edge
pytest tests/stateful_apis/admin/config/test_complete_suite.py -v --html=admin_report.html --self-contained-html; start msedge admin_report.html
```

### Run Specific Category
```powershell
# Document tests only
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestDocumentSettings -v --html=document_report.html --self-contained-html

# Age estimation tests only
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestAgeEstimation -v --html=age_report.html --self-contained-html

# Enrollment toggles only
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestEnrollmentToggles -v --html=enrollment_report.html --self-contained-html
```

### Run by Marker
```powershell
# Run all document-related tests
pytest tests/stateful_apis/admin/config/ -m document -v --html=report.html --self-contained-html

# Run all dependency tests
pytest tests/stateful_apis/admin/config/ -m dependencies -v --html=report.html --self-contained-html
```

## 🏷️ Test Markers

Tests are organized with pytest markers for easy filtering:

- `@pytest.mark.document` - Document verification tests
- `@pytest.mark.age` - Age estimation tests
- `@pytest.mark.duplicate` - Duplicate prevention tests
- `@pytest.mark.enrollment` - Enrollment toggle tests
- `@pytest.mark.parameters` - System parameter tests
- `@pytest.mark.dependencies` - Dependency validation tests
- `@pytest.mark.stateful` - Tests that modify state
- `@pytest.mark.admin` - Admin configuration tests

**Usage:**
```powershell
pytest -m "document and admin" -v
pytest -m "not dependencies" -v
```

## 📊 Test Categories

### 1. Document Settings (TestDocumentSettings)
**Tests:** 6 core + parametrized variants

- ✅ Enable/disable document upload (`addDocument`)
- ✅ Set ICAO verification modes (DISABLED, OPTIONAL, MANDATORY)
- ✅ Configure OCR portrait-selfie match threshold (1.5-3.0)
- ✅ Configure RFID portrait-selfie match threshold (2.0-3.5)
- ✅ Disable document with dependencies

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestDocumentSettings::test_set_ocr_portrait_threshold -v
```

### 2. Age Estimation (TestAgeEstimation)
**Tests:** 4 core + parametrized variants

- ✅ Enable/disable age estimation
- ✅ Set age range (min/max age)
- ✅ Configure age tolerance (0-5 years)

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestAgeEstimation -v
```

### 3. Duplicate Prevention (TestDuplicatePrevention)
**Tests:** 3 core + parametrized variants

- ✅ Enable/disable duplicate prevention
- ✅ Set match threshold (70-99%)

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestDuplicatePrevention -v
```

### 4. Enrollment Toggles (TestEnrollmentToggles)
**Tests:** 10 parametrized tests

- ✅ Enable/disable `addFace`
- ✅ Enable/disable `addDevice`
- ✅ Enable/disable `addDocument`
- ✅ Enable/disable `addVoice`
- ✅ Enable/disable `addPIN`

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestEnrollmentToggles -v
```

### 5. System Parameters (TestSystemParameters)
**Tests:** 11 parametrized tests

- ✅ Set max device IDs (1, 2, 3, 5, 10)
- ✅ Set max authentication attempts (1-10)

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestSystemParameters -v
```

### 6. Dependency Rules (TestDependencyRules)
**Tests:** 2 core tests

- ✅ Enable face with correct dependency order
- ✅ Disable face (all settings at once)

**Example:**
```powershell
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestDependencyRules -v
```

## ⚙️ Configuration Dependencies

### Face Enrollment Dependencies

**Enable Order (Sequential):**
```
Step 1: authentication.verifyFace = true
Step 2: reenrollment.verifyFace = true
Step 3: enrollment.addFace = true
```

**Disable Order (All at once):**
```
Single request with ALL THREE:
- enrollment.addFace = false
- reenrollment.verifyFace = false
- authentication.verifyFace = false
```

**⚠️ Important:** System enforces rule: "When enrollment.addFace is false, neither authentication.verifyFace or reEnrollment.verifyFace can be true"

### Document Dependencies

**Disable Order:**
```
Step 1: icaoVerification = DISABLED
Step 2: addDocument = false
```

## 🔧 Test Configuration

### Smart Delays
Tests include automatic delays to protect the admin portal:
- **2 seconds** between individual tests
- **5 seconds** between test classes

Configured in `conftest.py`:
```python
@pytest.fixture(autouse=True, scope="function")
def delay_between_tests():
    yield
    time.sleep(2)
```

### API Client
Tests use the `api_client` fixture with retry logic:
```python
api_client.http_client.get("/onboarding/admin/customerConfig")
api_client.http_client.post("/onboarding/admin/customerConfig", json=config)
```

## ⚠️ Known Issues

### Backend Errors (Causing ~80% Failure Rate)

1. **Duplicate JSON Key Error (500)**
```
   "errorMsg": "Duplicate key \"serviceVersion\" at 3184"
```
   - Affects: GET `/onboarding/admin/customerConfig`
   - Impact: Cannot read current config

2. **Null Authentication Object (500)**
```
   "errorMsg": "Cannot invoke \"...isVerifyFace()\" because \"authentication\" is null"
```
   - Affects: POST `/onboarding/admin/customerConfig`
   - Impact: Cannot save configuration changes

3. **Session Timeout (401)**
   - Occurs: During long test runs (>5 minutes)
   - Impact: Authentication expires mid-test

4. **Empty Response (JSONDecodeError)**
   - Occurs: Server crashes or times out
   - Impact: Cannot parse response

### Tests That Work
Despite backend issues, these tests consistently pass:
- ✅ OCR portrait threshold settings
- ✅ RFID portrait threshold settings
- ✅ Some parametrized tests (when backend is stable)

## 📈 Test Execution

### Expected Results

**Current State (with backend issues):**
```
Total: ~60 tests
Passed: ~12 (20%)
Failed: ~48 (80%)
Reason: Backend API errors (not test failures)
```

**Expected State (after backend fixes):**
```
Total: ~60 tests
Passed: ~57 (95%)
Failed: ~3 (5%)
Reason: Legitimate configuration issues
```

### Sample Output
```
tests/stateful_apis/admin/config/test_complete_suite.py::TestDocumentSettings::test_set_ocr_portrait_threshold[2.5] PASSED
tests/stateful_apis/admin/config/test_complete_suite.py::TestDocumentSettings::test_enable_add_document FAILED
tests/stateful_apis/admin/config/test_complete_suite.py::TestAgeEstimation::test_set_age_tolerance[2] FAILED
```

## 🐛 Debugging

### View Detailed Errors
```powershell
# Show full traceback
pytest tests/stateful_apis/admin/config/ -v --tb=long

# Show captured output
pytest tests/stateful_apis/admin/config/ -v -s

# Stop on first failure
pytest tests/stateful_apis/admin/config/ -v -x
```

### Check Specific Test
```powershell
# Run single test with verbose output
pytest tests/stateful_apis/admin/config/test_complete_suite.py::TestDocumentSettings::test_enable_add_document -vv -s
```

### Generate Reports
```powershell
# HTML report
pytest tests/stateful_apis/admin/config/ --html=report.html --self-contained-html

# JUnit XML (for CI/CD)
pytest tests/stateful_apis/admin/config/ --junitxml=report.xml

# JSON report
pip install pytest-json-report
pytest tests/stateful_apis/admin/config/ --json-report --json-report-file=report.json
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Admin Config Tests
  run: |
    pytest tests/stateful_apis/admin/config/test_complete_suite.py \
      --html=admin_report.html \
      --self-contained-html \
      -v

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: test-report
    path: admin_report.html
```

### Azure DevOps Example
```yaml
- task: PowerShell@2
  inputs:
    script: |
      pytest tests/stateful_apis/admin/config/test_complete_suite.py `
        --html=admin_report.html `
        --self-contained-html
```

## 📚 Additional Resources

### Test Data
Sample configuration payloads are in the test files:
```python
# Document config example
{
  "onboardingConfig": {
    "onboardingOptions": {
      "enrollment": {
        "addDocument": true,
        "icaoVerification": "MANDATORY"
      }
    }
  }
}
```

### API Documentation
- Endpoint: `/onboarding/admin/customerConfig`
- Methods: GET, POST
- Authentication: Required (session-based)

### Related Tests
- Authentication tests: `tests/stateful_apis/authentication/`
- Enrollment tests: `tests/stateful_apis/enrollment/`

## 🤝 Contributing

### Adding New Tests

1. **Add to complete suite:**
```python
   def test_new_setting(self, api_client):
       """Test description"""
       # Your test code
```

2. **Use appropriate marker:**
```python
   @pytest.mark.admin
   @pytest.mark.yourcategory
```

3. **Follow naming convention:**
   - `test_enable_*` - Enable features
   - `test_disable_*` - Disable features
   - `test_set_*` - Set values

### Test Template
```python
def test_set_new_parameter(self, api_client):
    """Set new parameter description"""
    print("\n" + "="*80)
    print("SET NEW PARAMETER")
    print("="*80)
    
    # Get current config
    current_response = api_client.http_client.get("/onboarding/admin/customerConfig")
    current_config = current_response.json().get("onboardingConfig", {})
    new_config = copy.deepcopy(current_config)
    
    # Modify config
    new_config['newParameter'] = value
    
    # Update
    update_response = api_client.http_client.post(
        "/onboarding/admin/customerConfig",
        json={"onboardingConfig": new_config}
    )
    
    # Assert
    assert update_response.status_code == 200
    
    # Verify
    verify_response = api_client.http_client.get("/onboarding/admin/customerConfig")
    verified = verify_response.json().get("onboardingConfig", {}).get("newParameter")
    assert verified == value
```

## 📞 Support

**Issues with tests?**
1. Check if backend API is accessible
2. Verify authentication is valid
3. Review the HTML report for detailed errors
4. Check known issues section above

**Backend team contact:**
- Report duplicate JSON key issue
- Report null authentication object issue
- Request session timeout increase for test runs

## 📝 Changelog

### 2026-02-20
- ✅ Created complete test suite with all admin tests
- ✅ Added smart delays to protect admin portal
- ✅ Organized tests by category with markers
- ✅ Documented dependency rules
- ✅ Added comprehensive README

---

**Last Updated:** 2026-02-20  
**Test Count:** ~60 tests  
**Coverage:** All admin configuration settings  
**Status:** Active development (backend issues pending)
