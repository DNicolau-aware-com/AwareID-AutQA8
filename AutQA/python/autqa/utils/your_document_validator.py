"""
Enhanced Document Validator for AwareID/Regula OCR Responses
Extracts and validates all document fields with proper data display
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def extract_document_ocr_data(doc_response: dict) -> dict:
    """
    Extract all OCR data from AwareID/Regula document response
    
    Args:
        doc_response: Full response from /addDocumentOCR endpoint
        
    Returns:
        Structured dictionary with all extracted fields organized by category
    """
    
    # Get the ocrResults which contains documentsInfo
    ocr_results = doc_response.get("ocrResults", {})
    documents_info = ocr_results.get("documentsInfo", {})
    
    # Extract field types array (this contains all the actual data)
    field_types = documents_info.get("fieldType", [])
    
    # Initialize data structure
    extracted = {
        "personal_info": {},
        "document_info": {},
        "address_info": {},
        "license_info": {},
        "metadata": {},
        "compliance": {},
        "overall_results": {},
        "all_fields": {}
    }
    
    # Extract top-level results
    extracted["overall_results"] = {
        "document_verified": doc_response.get("documentVerificationResult"),
        "icao_verified": doc_response.get("icaoVerificationResult"),
        "match_result": doc_response.get("matchResult"),
        "match_score": doc_response.get("matchScore"),
        "retry_capture": doc_response.get("retryDocumentCapture"),
        "enrollment_status": doc_response.get("enrollmentStatus"),
        "registration_code": doc_response.get("registrationCode"),
        "valid_document": ocr_results.get("validDocument"),
        "rfid_presence": ocr_results.get("rfidPresence"),
        "mrz_presence": ocr_results.get("mrzPresence"),
        "document_name": ocr_results.get("documentName"),
        "document_id": ocr_results.get("documentID"),
        "country_name": ocr_results.get("countryName"),
        "icao_code": ocr_results.get("icaocode"),
    }
    
    # Process each field
    for field in field_types:
        field_name = field.get("name", "unknown")
        field_result = field.get("fieldResult", {})
        
        # Extract values from different sources
        visual = field_result.get("visual", "")
        barcode = field_result.get("barcode", "")
        mrz = field_result.get("mrz", "")
        
        # Use the first available value (prefer visual, then barcode, then mrz)
        value = visual or barcode or mrz
        
        # Store in all_fields for reference
        extracted["all_fields"][field_name] = {
            "visual": visual,
            "barcode": barcode,
            "mrz": mrz,
            "value": value,
            "overall_result": field.get("overallResult"),
        }
        
        # Categorize fields
        
        # Personal Information
        if field_name == "Given names":
            extracted["personal_info"]["given_names"] = value
        elif field_name == "Surname":
            extracted["personal_info"]["surname"] = value
        elif field_name == "Surname And Given Names":
            extracted["personal_info"]["full_name"] = value
        elif field_name == "Date of birth":
            extracted["personal_info"]["date_of_birth"] = value
        elif field_name == "Age":
            extracted["personal_info"]["age"] = value
        elif field_name == "Sex":
            extracted["personal_info"]["sex"] = value
        elif field_name == "Height":
            extracted["personal_info"]["height"] = value
        elif field_name == "Eyes Color":
            extracted["personal_info"]["eyes_color"] = value
        elif field_name == "Weight":
            extracted["personal_info"]["weight"] = value
        
        # Document Information
        elif field_name == "Document #":
            extracted["document_info"]["document_number"] = value
        elif field_name == "DL Class":
            extracted["document_info"]["dl_class"] = value
        elif field_name == "Date of issue":
            extracted["document_info"]["date_of_issue"] = value
        elif field_name == "Date of expiry":
            extracted["document_info"]["date_of_expiry"] = value
        elif field_name == "Months to expire":
            extracted["document_info"]["months_to_expire"] = value
        elif field_name == "Issuing State Code":
            extracted["document_info"]["issuing_state_code"] = value
        elif field_name == "Issuing State":
            extracted["document_info"]["issuing_state"] = value
        elif field_name == "State":
            extracted["document_info"]["state"] = value
        elif field_name == "Jurisdiction Code":
            extracted["document_info"]["jurisdiction_code"] = value
        
        # Address Information
        elif field_name == "Address":
            extracted["address_info"]["full_address"] = value
        elif field_name == "Street":
            extracted["address_info"]["street"] = value
        elif field_name == "City":
            extracted["address_info"]["city"] = value
        elif field_name == "Postal Code":
            extracted["address_info"]["postal_code"] = value
        
        # License-Specific
        elif field_name == "Donor":
            extracted["license_info"]["organ_donor"] = value
        elif field_name == "DL Endorsed":
            extracted["license_info"]["endorsements"] = value
        elif field_name == "DL Restriction Code":
            extracted["license_info"]["restrictions"] = value
        
        # Metadata
        elif field_name == "Record created":
            extracted["metadata"]["record_created"] = value
        elif field_name == "Revision Date":
            extracted["metadata"]["revision_date"] = value
        elif field_name == "Age at issue":
            extracted["metadata"]["age_at_issue"] = value
        elif field_name == "Years since issue":
            extracted["metadata"]["years_since_issue"] = value
        elif field_name == "Inventory Number":
            extracted["metadata"]["inventory_number"] = value
        elif field_name == "Document discriminator":
            extracted["metadata"]["document_discriminator"] = value
        
        # AAMVA Compliance
        elif field_name == "Compliance Type":
            extracted["compliance"]["compliance_type"] = value
        elif field_name == "Family Name Truncation":
            extracted["compliance"]["family_name_truncation"] = value
        elif field_name == "First Name Truncation":
            extracted["compliance"]["first_name_truncation"] = value
        elif field_name == "Middle Name Truncation":
            extracted["compliance"]["middle_name_truncation"] = value
    
    return extracted


def validate_document(extracted_data: dict) -> dict:
    """
    Validate extracted document data
    
    Args:
        extracted_data: Data from extract_document_ocr_data()
        
    Returns:
        Validation results with status and issues
    """
    
    overall_results = extracted_data.get("overall_results", {})
    all_fields = extracted_data.get("all_fields", {})
    document_info = extracted_data.get("document_info", {})
    
    validation_result = {
        "is_valid": True,
        "status": "AUTHENTIC",
        "critical_issues": [],
        "warnings": [],
        "summary": ""
    }
    
    # Check overall verification
    if not overall_results.get("document_verified"):
        validation_result["is_valid"] = False
        validation_result["status"] = "REJECTED"
        validation_result["critical_issues"].append("Document verification failed")
    
    # Check for field mismatches (visual vs barcode)
    mismatches = []
    for field_name, field_data in all_fields.items():
        visual = field_data.get("visual", "")
        barcode = field_data.get("barcode", "")
        
        if visual and barcode and visual != barcode:
            mismatches.append(f"{field_name}: visual='{visual}' vs barcode='{barcode}'")
    
    if mismatches:
        validation_result["is_valid"] = False
        validation_result["status"] = "SUSPICIOUS"
        validation_result["critical_issues"].extend(mismatches)
    
    # Check expiration
    months_to_expire = document_info.get("months_to_expire")
    if months_to_expire:
        try:
            months = int(months_to_expire)
            if months < 0:
                validation_result["is_valid"] = False
                validation_result["status"] = "REJECTED"
                validation_result["critical_issues"].append(f"Document expired {abs(months)} months ago")
            elif months < 6:
                validation_result["warnings"].append(f"Document expires in {months} months")
        except (ValueError, TypeError):
            pass
    
    # Check for too many undefined fields
    undefined_count = sum(1 for field in all_fields.values() if field.get("overall_result") == "UNDEFINED")
    total_fields = len(all_fields)
    
    if total_fields > 0 and undefined_count / total_fields > 0.3:  # More than 30% undefined
        validation_result["warnings"].append(f"{undefined_count}/{total_fields} fields undefined")
    
    # Generate summary
    if validation_result["is_valid"]:
        validation_result["summary"] = "Document is authentic and valid"
    else:
        validation_result["summary"] = f"Document validation failed: {', '.join(validation_result['critical_issues'])}"
    
    return validation_result


def generate_document_report(extracted_data: dict, validation_result: dict) -> str:
    """
    Generate formatted document validation report
    
    Args:
        extracted_data: Data from extract_document_ocr_data()
        validation_result: Results from validate_document()
        
    Returns:
        Formatted report string
    """
    
    personal = extracted_data.get("personal_info", {})
    document = extracted_data.get("document_info", {})
    address = extracted_data.get("address_info", {})
    license = extracted_data.get("license_info", {})
    overall = extracted_data.get("overall_results", {})
    
    report = []
    report.append("\n" + "="*120)
    report.append("📄 DOCUMENT OCR VALIDATION REPORT")
    report.append("="*120)
    
    # Status
    status_icon = "✅" if validation_result["is_valid"] else "❌"
    report.append(f"\n{status_icon} Status: {validation_result['status']}")
    
    # Personal Information
    report.append("\n" + "-"*120)
    report.append("👤 PERSONAL INFORMATION:")
    report.append(f"   Full Name: {personal.get('full_name', 'N/A')}")
    report.append(f"   Given Names: {personal.get('given_names', 'N/A')}")
    report.append(f"   Surname: {personal.get('surname', 'N/A')}")
    report.append(f"   Date of Birth: {personal.get('date_of_birth', 'N/A')}")
    report.append(f"   Age: {personal.get('age', 'N/A')} years")
    report.append(f"   Sex: {personal.get('sex', 'N/A')}")
    report.append(f"   Height: {personal.get('height', 'N/A')}")
    report.append(f"   Eyes: {personal.get('eyes_color', 'N/A')}")
    
    # Document Information
    report.append("\n" + "-"*120)
    report.append("📋 DOCUMENT INFORMATION:")
    doc_name = overall.get('document_name', 'Unknown')
    report.append(f"   Type: {doc_name}")
    report.append(f"   Number: {document.get('document_number', 'N/A')}")
    report.append(f"   Class: {document.get('dl_class', 'N/A')}")
    report.append(f"   State: {document.get('state', 'N/A')} ({document.get('issuing_state', 'N/A')})")
    report.append(f"   Jurisdiction: {document.get('jurisdiction_code', 'N/A')}")
    report.append(f"   Issue Date: {document.get('date_of_issue', 'N/A')}")
    report.append(f"   Expiry Date: {document.get('date_of_expiry', 'N/A')}")
    
    months_to_expire = document.get('months_to_expire', 'N/A')
    if months_to_expire != 'N/A':
        try:
            months = int(months_to_expire)
            if months < 0:
                report.append(f"   ⚠️  EXPIRED: {abs(months)} months ago")
            else:
                report.append(f"   Valid for: {months} months")
        except (ValueError, TypeError):
            report.append(f"   Valid for: {months_to_expire}")
    
    # Address
    report.append("\n" + "-"*120)
    report.append("🏠 ADDRESS:")
    full_address = address.get('full_address', '')
    if full_address and '^' in full_address:
        # Split by ^ separator
        parts = full_address.split('^')
        for part in parts:
            report.append(f"   {part.strip()}")
    else:
        report.append(f"   {address.get('street', 'N/A')}")
        city = address.get('city', '')
        state = document.get('state', '')
        postal = address.get('postal_code', '')
        if city or state or postal:
            report.append(f"   {city}, {state} {postal}")
    
    # License Details
    if license.get('endorsements') or license.get('restrictions') or license.get('organ_donor'):
        report.append("\n" + "-"*120)
        report.append("🪪 LICENSE DETAILS:")
        if license.get('organ_donor'):
            donor_status = "YES" if license.get('organ_donor') == '1' else "NO"
            report.append(f"   Organ Donor: {donor_status}")
        report.append(f"   Endorsements: {license.get('endorsements', 'NONE')}")
        report.append(f"   Restrictions: {license.get('restrictions', 'NONE')}")
    
    # Verification Results
    report.append("\n" + "-"*120)
    report.append("🔒 VERIFICATION:")
    doc_verified = overall.get('document_verified')
    report.append(f"   Document Verified: {'✅ YES' if doc_verified else '❌ NO'}")
    
    icao_verified = overall.get('icao_verified')
    rfid_presence = overall.get('rfid_presence', 0)
    if rfid_presence == 0:
        report.append(f"   ICAO Compliant: ❌ NO (RFID disabled)")
        report.append(f"   RFID Chip: Not present")
    else:
        report.append(f"   ICAO Compliant: {'✅ YES' if icao_verified else '❌ NO'}")
        report.append(f"   RFID Chip: Present")
    
    # Match results (face vs document photo)
    match_result = overall.get('match_result')
    match_score = overall.get('match_score')
    if match_result is not None:
        report.append(f"   Face Match: {'✅ MATCHED' if match_result else '❌ NO MATCH'} (score: {match_score})")
    
    # Critical Issues
    if validation_result["critical_issues"]:
        report.append("\n" + "-"*120)
        report.append("🚨 CRITICAL ISSUES:")
        for issue in validation_result["critical_issues"]:
            report.append(f"   ❌ {issue}")
    
    # Warnings
    if validation_result["warnings"]:
        report.append("\n" + "-"*120)
        report.append("⚠️  WARNINGS:")
        for warning in validation_result["warnings"]:
            report.append(f"   ⚠️  {warning}")
    
    report.append("\n" + "="*120)
    
    return "\n".join(report)
