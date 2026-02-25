"""
Comprehensive Field Validation Test - All Options
Tests document OCR with all available validation rules and field checks
"""
import pytest
import copy
import time
import logging
import json
from datetime import datetime
from autqa.utils.your_document_validator import (
    extract_document_ocr_data,
    validate_document,
    generate_document_report
)
from autqa.utils.ocr_analyzer import analyze_ocr_response, generate_ocr_analysis_report

logger = logging.getLogger(__name__)


def normalize_base64(data: str) -> str:
    """Remove data URI prefix if present"""
    if not data:
        return data
    data = data.strip()
    if data.startswith('data:') and ',' in data:
        data = data.split(',', 1)[1]
    return data


# ============================================================================
# TEST SCENARIOS - Different validation configurations
# ============================================================================

VALIDATION_SCENARIOS = [
    {
        "name": "Minimal Validation - Expiry Only",
        "description": "Only check if document is expired",
        "processingInstructions": {
            "documentValidationRules": {
                "validateDocumentNotExpired": True
            }
        }
    },
    {
        "name": "Age Validation - Adult Only (18+)",
        "description": "Validate minimum age 18, no maximum",
        "processingInstructions": {
            "documentValidationRules": {
                "minimumAge": 18,
                "validateMinimumAge": True,
                "validateDocumentNotExpired": True
            }
        }
    },
    {
        "name": "Age Range Validation (21-65)",
        "description": "Validate age between 21-65 years",
        "processingInstructions": {
            "documentValidationRules": {
                "minimumAge": 21,
                "maximumAge": 65,
                "validateMinimumAge": True,
                "validateMaximumAge": True,
                "validateDocumentNotExpired": True
            }
        }
    },
    {
        "name": "Complete Validation - All Fields",
        "description": "Validate ALL fields with wildcard",
        "processingInstructions": {
            "documentValidationRules": {
                "minimumAge": 18,
                "maximumAge": 101,
                "validateMinimumAge": True,
                "validateMaximumAge": True,
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": ["*"],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    },
    {
        "name": "Specific Fields - Identity Only",
        "description": "Validate only critical identity fields",
        "processingInstructions": {
            "documentValidationRules": {
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": [
                        "Document #",
                        "Surname",
                        "Given names",
                        "Date of birth",
                        "Sex",
                        "Nationality"
                    ],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    },
    {
        "name": "Specific Fields - Dates Only",
        "description": "Validate only date-related fields",
        "processingInstructions": {
            "documentValidationRules": {
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": [
                        "Date of birth",
                        "Date of issue",
                        "Date of expiry"
                    ],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    },
    {
        "name": "Specific Fields - Location Data",
        "description": "Validate location/address fields",
        "processingInstructions": {
            "documentValidationRules": {
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": [
                        "Place of Birth",
                        "Issuing State",
                        "Nationality"
                    ],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    },
    {
        "name": "MRZ Validation Only",
        "description": "Validate machine-readable zone",
        "processingInstructions": {
            "documentValidationRules": {
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": [
                        "MRZ Lines"
                    ],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    },
    {
        "name": "Maximum Validation - Everything",
        "description": "All rules + all fields + strict checks",
        "processingInstructions": {
            "documentValidationRules": {
                "minimumAge": 18,
                "maximumAge": 100,
                "validateMinimumAge": True,
                "validateMaximumAge": True,
                "validateDocumentNotExpired": True
            },
            "fieldsToValidate": [
                {
                    "fields": [
                        "Document #",
                        "Surname",
                        "Given names",
                        "Date of birth",
                        "Date of issue",
                        "Date of expiry",
                        "Sex",
                        "Nationality",
                        "Issuing State",
                        "Personal #",
                        "Place of Birth",
                        "MRZ Lines"
                    ],
                    "docTypeKeyword": "Passport"
                }
            ]
        }
    }
]


@pytest.mark.stateful
@pytest.mark.enrollment
@pytest.mark.passport
@pytest.mark.parametrize("scenario", VALIDATION_SCENARIOS, ids=[s["name"] for s in VALIDATION_SCENARIOS])
class TestComprehensiveFieldValidation:
    """Test all field validation options"""
    
    def test_field_validation_scenario(
        self,
        api_client,
        unique_username,
        face_frames,
        workflow,
        env_vars,
        caplog,
        scenario
    ):
        """Test document validation with specific scenario"""
        
        caplog.set_level(logging.INFO)
        
        # Get images
        passport_front = normalize_base64(env_vars.get("PASS_FRONT_DAN", "").strip())
        
        if not passport_front:
            pytest.skip("Missing PASS_FRONT_DAN in .env")
        
        test_start_time = datetime.now()
        
        # ====================================================================
        # TEST HEADER
        # ====================================================================
        logger.info("\n" + "🎯"*60)
        logger.info(f"FIELD VALIDATION TEST: {scenario['name']}")
        logger.info(f"Description: {scenario['description']}")
        logger.info("🎯"*60)
        
        # ====================================================================
        # QUICK ENROLLMENT (Abbreviated)
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("ENROLLMENT SETUP")
        logger.info("="*120)
        
        # Config
        config_response = api_client.http_client.get("/onboarding/admin/customerConfig")
        current_config = config_response.json().get("onboardingConfig", {})
        new_config = copy.deepcopy(current_config)
        
        enrollment = new_config.setdefault("onboardingOptions", {}).setdefault("enrollment", {})
        enrollment["ageEstimation"] = {"enabled": False, "minAge": 1, "maxAge": 101}
        enrollment['addDocument'] = True
        enrollment['addFace'] = True
        enrollment['addDevice'] = True
        
        api_client.http_client.post("/onboarding/admin/customerConfig", json={"onboardingConfig": new_config})
        time.sleep(1)
        
        # Enroll
        enroll_response = api_client.http_client.post("/onboarding/enrollment/enroll", json={
            "username": unique_username,
            "email": f"{unique_username}@example.com",
            "firstName": "Dan",
            "lastName": "Nicolau",
        })
        enrollment_token = enroll_response.json().get("enrollmentToken")
        time.sleep(1)
        
        # Device
        device_response = api_client.http_client.post("/onboarding/enrollment/addDevice", json={
            "enrollmentToken": enrollment_token,
            "deviceId": f"device_{int(time.time())}",
            "platform": "web"
        })
        time.sleep(1)
        
        # Face
        face_response = api_client.http_client.post("/onboarding/enrollment/addFace", json={
            "enrollmentToken": enrollment_token,
            "faceLivenessData": {
                "video": {
                    "meta_data": {"username": unique_username},
                    "workflow_data": {"workflow": workflow, "frames": face_frames},
                },
            },
        })
        time.sleep(3)
        
        logger.info("✅ Enrollment setup complete")
        
        # ====================================================================
        # DOCUMENT WITH PROCESSING INSTRUCTIONS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("DOCUMENT OCR WITH VALIDATION SCENARIO")
        logger.info("="*120)
        
        doc_images = [{"lightingScheme": 6, "image": passport_front, "format": "JPG"}]
        
        doc_payload = {
            "enrollmentToken": enrollment_token,
            "documentsInfo": {
                "documentImage": doc_images,
                "documentPayload": {
                    "request": {
                        "vendor": "REGULA",
                        "data": {}
                    }
                }
            },
            "processingInstructions": scenario["processingInstructions"]
        }
        
        # Log processing instructions
        logger.info("\n📋 Processing Instructions:")
        logger.info(json.dumps(scenario["processingInstructions"], indent=2))
        
        doc_response = api_client.http_client.post("/onboarding/enrollment/addDocumentOCR", json=doc_payload)
        doc_data = doc_response.json() if doc_response.status_code == 200 else {}
        
        # ====================================================================
        # COMPREHENSIVE ANALYSIS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🔍 COMPREHENSIVE OCR ANALYSIS")
        logger.info("="*120)
        
        ocr_analysis = analyze_ocr_response(doc_data)
        ocr_analysis_report = generate_ocr_analysis_report(ocr_analysis)
        
        logger.info(ocr_analysis_report)
        
        # ====================================================================
        # VALIDATION RULES RESULTS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📊 VALIDATION RULES RESULTS")
        logger.info("="*120)
        
        ocr_results = doc_data.get("ocrResults", {})
        validation_rules = ocr_results.get("documentValidationRulesResult", {})
        requested_rules = validation_rules.get("requestedDocumentValidationRuleResults", {})
        
        if requested_rules:
            logger.info("\nValidation Rule Results:")
            for rule_name, rule_result in requested_rules.items():
                status_icon = "✅" if rule_result != "FAILED" else "❌"
                logger.info(f"   {status_icon} {rule_name}: {rule_result}")
        else:
            logger.info("   No validation rules applied")
        
        # ====================================================================
        # FIELD VALIDATION RESULTS
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("📝 FIELD VALIDATION RESULTS")
        logger.info("="*120)
        
        documents_info = ocr_results.get("documentsInfo", {})
        field_types = documents_info.get("fieldType", [])
        
        validated_fields = 0
        ok_fields = 0
        failed_fields = 0
        undefined_fields = 0
        
        logger.info(f"\nTotal Fields: {len(field_types)}")
        
        for field in field_types:
            field_name = field.get("name")
            overall_result = field.get("overallResult")
            
            validated_fields += 1
            if overall_result == "OK":
                ok_fields += 1
            elif overall_result == "FAILED":
                failed_fields += 1
            else:
                undefined_fields += 1
        
        logger.info(f"\n📊 Field Statistics:")
        logger.info(f"   Total Fields: {validated_fields}")
        logger.info(f"   ✅ OK: {ok_fields}")
        logger.info(f"   ❌ FAILED: {failed_fields}")
        logger.info(f"   ⚠️  UNDEFINED: {undefined_fields}")
        
        # ====================================================================
        # FINAL VERDICT
        # ====================================================================
        logger.info("\n" + "="*120)
        logger.info("🏁 FINAL VERDICT")
        logger.info("="*120)
        
        logger.info(f"\n📋 Scenario: {scenario['name']}")
        logger.info(f"   Description: {scenario['description']}")
        
        logger.info(f"\n📊 Results:")
        logger.info(f"   Overall Status: {ocr_analysis['overall_status']}")
        logger.info(f"   Critical Issues: {len(ocr_analysis['critical_issues'])}")
        logger.info(f"   Field Issues: {len(ocr_analysis['field_issues'])}")
        logger.info(f"   Warnings: {len(ocr_analysis['warnings'])}")
        
        logger.info(f"\n⏱️  Duration: {(datetime.now() - test_start_time).total_seconds():.2f}s")
        
        logger.info("\n" + "="*120 + "\n")
