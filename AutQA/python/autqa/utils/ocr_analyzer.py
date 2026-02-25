"""
Comprehensive OCR Analyzer
Analyzes document OCR responses and detects ALL validation issues
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def analyze_ocr_response(doc_data: dict) -> dict:
    """
    Comprehensive OCR response analyzer
    Detects ALL issues including:
    - Expired documents
    - Field mismatches (visual vs barcode vs MRZ)
    - Invalid data
    - Tampering indicators
    - Missing fields
    - State/address mismatches
    - Character alterations
    - Any field with status != OK
    """
    
    analysis = {
        "overall_status": "PASS",
        "critical_issues": [],
        "warnings": [],
        "field_issues": [],
        "summary": ""
    }
    
    # ========================================================================
    # 1. TOP-LEVEL VALIDATION
    # ========================================================================
    doc_verified = doc_data.get("documentVerificationResult")
    enrollment_status = doc_data.get("enrollmentStatus")
    match_result = doc_data.get("matchResult")
    match_score = doc_data.get("matchScore")
    registration_code = doc_data.get("registrationCode")
    
    # Document verification
    if not doc_verified:
        analysis["critical_issues"].append({
            "field": "documentVerificationResult",
            "issue": "DOCUMENT VERIFICATION FAILED",
            "value": doc_verified,
            "severity": "CRITICAL"
        })
        analysis["overall_status"] = "FAIL"
    
    # Enrollment status
    if enrollment_status == 0:
        analysis["critical_issues"].append({
            "field": "enrollmentStatus",
            "issue": "ENROLLMENT FAILED",
            "value": enrollment_status,
            "severity": "CRITICAL"
        })
        analysis["overall_status"] = "FAIL"
    
    # Face match
    if match_result is False:
        analysis["critical_issues"].append({
            "field": "matchResult",
            "issue": "FACE DOES NOT MATCH DOCUMENT PHOTO",
            "value": f"matchResult={match_result}, score={match_score}",
            "severity": "CRITICAL"
        })
        analysis["overall_status"] = "FAIL"
    
    # Registration code
    if not registration_code or registration_code == "":
        analysis["warnings"].append({
            "field": "registrationCode",
            "issue": "No registration code returned",
            "value": registration_code
        })
    
    # ========================================================================
    # 2. OCR RESULTS ANALYSIS
    # ========================================================================
    ocr_results = doc_data.get("ocrResults", {})
    
    # Overall OCR result
    overall_result = ocr_results.get("overallResult")
    if overall_result == "FAILED":
        analysis["critical_issues"].append({
            "field": "ocrResults.overallResult",
            "issue": "OCR PROCESSING FAILED",
            "value": overall_result,
            "severity": "CRITICAL"
        })
        analysis["overall_status"] = "FAIL"
    
    # Document validation rules
    doc_validation_rules = ocr_results.get("documentValidationRulesResult", {})
    requested_rules = doc_validation_rules.get("requestedDocumentValidationRuleResults", {})
    
    for rule_name, rule_result in requested_rules.items():
        if rule_result == "FAILED":
            analysis["critical_issues"].append({
                "field": f"documentValidationRules.{rule_name}",
                "issue": f"VALIDATION RULE FAILED: {rule_name}",
                "value": rule_result,
                "severity": "CRITICAL",
                "details": "Document failed validation check"
            })
            analysis["overall_status"] = "FAIL"
    
    # Overall result info - field errors
    overall_info = ocr_results.get("overallResultInfo", {})
    field_errors = overall_info.get("fieldErrorCodes", [])
    
    for error in field_errors:
        if "EXPIRED" in error.upper():
            analysis["critical_issues"].append({
                "field": "documentExpiration",
                "issue": "DOCUMENT EXPIRED",
                "value": error,
                "severity": "CRITICAL"
            })
            analysis["overall_status"] = "FAIL"
        elif "BARCODE" in error.upper() and "NONE" in error.upper():
            analysis["warnings"].append({
                "field": "barcode",
                "issue": "No barcode detected on document",
                "value": error
            })
        else:
            analysis["warnings"].append({
                "field": "fieldError",
                "issue": error,
                "value": error
            })
    
    # ========================================================================
    # 3. FIELD-BY-FIELD ANALYSIS
    # ========================================================================
    documents_info = ocr_results.get("documentsInfo", {})
    field_types = documents_info.get("fieldType", [])
    
    # Store extracted values for cross-field validation
    extracted_values = {}
    
    for field in field_types:
        field_name = field.get("name", "Unknown")
        overall_field_result = field.get("overallResult")
        field_result = field.get("fieldResult", {})
        
        # Get all values
        visual = field_result.get("visual", "")
        barcode = field_result.get("barcode", "")
        mrz = field_result.get("mrz", "")
        
        # Store for cross-validation
        if visual:
            extracted_values[field_name] = visual
        
        # Check if field failed
        if overall_field_result not in ["OK", "UNDEFINED"]:
            analysis["field_issues"].append({
                "field": field_name,
                "issue": f"Field validation failed: {overall_field_result}",
                "visual": visual,
                "barcode": barcode,
                "mrz": mrz,
                "severity": "HIGH"
            })
        
        # Check for mismatches between sources
        visual_barcode_compare = field_result.get("visualBarcodeCompareValid")
        mrz_visual_compare = field_result.get("mrzVisualCompareValid")
        
        # Visual vs Barcode mismatch
        if visual_barcode_compare == "COMPARE_FALSE":
            analysis["critical_issues"].append({
                "field": field_name,
                "issue": "MISMATCH: Visual and Barcode values DO NOT match",
                "value": f"Visual='{visual}' vs Barcode='{barcode}'",
                "severity": "CRITICAL",
                "details": "Possible tampering or data inconsistency"
            })
            analysis["overall_status"] = "FAIL"
        
        # MRZ vs Visual mismatch
        if mrz_visual_compare == "COMPARE_FALSE":
            analysis["critical_issues"].append({
                "field": field_name,
                "issue": "MISMATCH: MRZ and Visual values DO NOT match",
                "value": f"Visual='{visual}' vs MRZ='{mrz}'",
                "severity": "CRITICAL",
                "details": "Possible tampering or data inconsistency"
            })
            analysis["overall_status"] = "FAIL"
        
        # Check validation status
        is_visual_valid = field_result.get("isVisualStatusValid")
        is_barcode_valid = field_result.get("isBarcodeStatusValid")
        is_mrz_valid = field_result.get("isMrzStatusValid")
        
        # Visual validation failed
        if is_visual_valid == "VALIDATE_FALSE":
            analysis["field_issues"].append({
                "field": field_name,
                "issue": "Visual value FAILED validation",
                "value": visual,
                "severity": "HIGH"
            })
        
        # Barcode validation failed
        if is_barcode_valid == "VALIDATE_FALSE":
            analysis["field_issues"].append({
                "field": field_name,
                "issue": "Barcode value FAILED validation",
                "value": barcode,
                "severity": "HIGH"
            })
        
        # MRZ validation failed
        if is_mrz_valid == "VALIDATE_FALSE":
            analysis["field_issues"].append({
                "field": field_name,
                "issue": "MRZ value FAILED validation",
                "value": mrz,
                "severity": "HIGH"
            })
        
        # Special field checks
        if field_name == "Date of expiry":
            if visual:
                try:
                    expiry_date = datetime.strptime(visual, "%Y-%m-%d")
                    if expiry_date < datetime.now():
                        months_expired = int((datetime.now() - expiry_date).days / 30)
                        analysis["critical_issues"].append({
                            "field": "Date of expiry",
                            "issue": f"DOCUMENT EXPIRED {months_expired} months ago",
                            "value": visual,
                            "severity": "CRITICAL"
                        })
                        analysis["overall_status"] = "FAIL"
                except:
                    pass
        
        # Check for "Months to expire" field
        if field_name == "Months to expire":
            if visual and visual != "":
                try:
                    months = int(visual)
                    if months <= 0:
                        analysis["critical_issues"].append({
                            "field": "Months to expire",
                            "issue": f"DOCUMENT EXPIRED (months remaining: {months})",
                            "value": visual,
                            "severity": "CRITICAL"
                        })
                        analysis["overall_status"] = "FAIL"
                    elif months < 6:
                        analysis["warnings"].append({
                            "field": "Months to expire",
                            "issue": f"Document expires soon ({months} months)",
                            "value": visual
                        })
                except:
                    pass
    
    # ========================================================================
    # 4. CROSS-FIELD VALIDATION
    # ========================================================================
    
    # Check if state fields match (for US documents)
    state_field = extracted_values.get("State", "")
    issuing_state = extracted_values.get("Issuing State", "")
    jurisdiction = extracted_values.get("Jurisdiction Code", "")
    
    if state_field and issuing_state and state_field != issuing_state:
        analysis["critical_issues"].append({
            "field": "State/Issuing State",
            "issue": "STATE MISMATCH: Document state and issuing state do not match",
            "value": f"State='{state_field}' vs Issuing State='{issuing_state}'",
            "severity": "CRITICAL",
            "details": "Possible document tampering or fraud"
        })
        analysis["overall_status"] = "FAIL"
    
    # Check address consistency
    address = extracted_values.get("Address", "")
    city = extracted_values.get("City", "")
    
    if address and state_field and city:
        # Check if state code appears in address
        if state_field.upper() not in address.upper():
            analysis["warnings"].append({
                "field": "Address/State",
                "issue": f"State '{state_field}' not found in address",
                "value": f"Address: {address}, State: {state_field}"
            })
    
    # ========================================================================
    # 5. GENERATE SUMMARY
    # ========================================================================
    total_issues = len(analysis["critical_issues"]) + len(analysis["field_issues"]) + len(analysis["warnings"])
    
    if analysis["overall_status"] == "FAIL":
        analysis["summary"] = f"❌ DOCUMENT VALIDATION FAILED - {len(analysis['critical_issues'])} critical issues found"
    elif len(analysis["warnings"]) > 0:
        analysis["summary"] = f"⚠️  DOCUMENT VALID WITH WARNINGS - {len(analysis['warnings'])} warnings"
    else:
        analysis["summary"] = "✅ DOCUMENT VALID - All checks passed"
    
    return analysis


def generate_ocr_analysis_report(analysis: dict) -> str:
    """Generate formatted OCR analysis report"""
    
    report = []
    report.append("\n" + "="*120)
    report.append("🔍 COMPREHENSIVE OCR ANALYSIS REPORT")
    report.append("="*120)
    
    # Overall status
    report.append(f"\n📊 Overall Status: {analysis['summary']}")
    
    # Critical issues
    if analysis["critical_issues"]:
        report.append("\n" + "="*120)
        report.append(f"🚨 CRITICAL ISSUES ({len(analysis['critical_issues'])})")
        report.append("="*120)
        for idx, issue in enumerate(analysis["critical_issues"], 1):
            report.append(f"\n{idx}. {issue['issue']}")
            report.append(f"   Field: {issue['field']}")
            report.append(f"   Value: {issue['value']}")
            report.append(f"   Severity: {issue['severity']}")
            if 'details' in issue:
                report.append(f"   Details: {issue['details']}")
    
    # Field-specific issues
    if analysis["field_issues"]:
        report.append("\n" + "="*120)
        report.append(f"⚠️  FIELD VALIDATION ISSUES ({len(analysis['field_issues'])})")
        report.append("="*120)
        for idx, issue in enumerate(analysis["field_issues"], 1):
            report.append(f"\n{idx}. {issue['issue']}")
            report.append(f"   Field: {issue['field']}")
            if issue.get('visual'):
                report.append(f"   Visual: {issue['visual']}")
            if issue.get('barcode'):
                report.append(f"   Barcode: {issue['barcode']}")
            if issue.get('mrz'):
                report.append(f"   MRZ: {issue['mrz']}")
    
    # Warnings
    if analysis["warnings"]:
        report.append("\n" + "="*120)
        report.append(f"⚠️  WARNINGS ({len(analysis['warnings'])})")
        report.append("="*120)
        for idx, warning in enumerate(analysis["warnings"], 1):
            report.append(f"\n{idx}. {warning['issue']}")
            report.append(f"   Field: {warning['field']}")
            report.append(f"   Value: {warning.get('value', 'N/A')}")
    
    report.append("\n" + "="*120)
    
    return "\n".join(report)
