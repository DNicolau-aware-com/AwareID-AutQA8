"""
Document Validation and Data Extraction Guide
Comprehensive analysis of document OCR responses
"""
import pytest
import logging
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentValidationStatus(Enum):
    """Document validation outcomes"""
    GENUINE = "GENUINE"
    FAKE = "FAKE"
    SUSPICIOUS = "SUSPICIOUS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class DocumentValidator:
    """
    Validates document authenticity and extracts all verification data
    """
    
    @staticmethod
    def extract_document_data(doc_response: Dict) -> Dict:
        """
        Extract ALL data from document OCR response
        
        What you need from document response:
        1. Basic OCR data (name, DOB, address, etc.)
        2. Security features validation
        3. Document authenticity checks
        4. Image quality metrics
        5. Verification results
        """
        
        # ==================================================================
        # SECTION 1: BASIC DOCUMENT DATA (OCR Results)
        # ==================================================================
        ocr_data = {
            # Personal Information
            "first_name": doc_response.get("firstName"),
            "last_name": doc_response.get("lastName"),
            "middle_name": doc_response.get("middleName"),
            "full_name": doc_response.get("fullName"),
            "date_of_birth": doc_response.get("dateOfBirth"),
            "age": doc_response.get("age"),
            "gender": doc_response.get("gender"),
            
            # Document Details
            "document_number": doc_response.get("documentNumber"),
            "document_type": doc_response.get("documentType"),  # e.g., "Driver's License", "Passport"
            "issuing_country": doc_response.get("issuingCountry"),
            "issuing_state": doc_response.get("issuingState"),
            "issue_date": doc_response.get("issueDate"),
            "expiry_date": doc_response.get("expiryDate"),
            "is_expired": doc_response.get("isExpired"),
            
            # Address Information
            "address_line1": doc_response.get("addressLine1"),
            "address_line2": doc_response.get("addressLine2"),
            "city": doc_response.get("city"),
            "state": doc_response.get("state"),
            "postal_code": doc_response.get("postalCode"),
            "country": doc_response.get("country"),
        }
        
        # ==================================================================
        # SECTION 2: DOCUMENT VERIFICATION RESULTS
        # ==================================================================
        verification_results = {
            # Overall Results
            "overall_result": doc_response.get("documentVerificationResult"),  # PASS/FAIL
            "overall_score": doc_response.get("overallScore"),
            "confidence_score": doc_response.get("confidenceScore"),
            
            # Specific Checks
            "authenticity_result": doc_response.get("authenticityResult"),
            "validity_result": doc_response.get("validityResult"),
            "security_features_result": doc_response.get("securityFeaturesResult"),
            "data_consistency_result": doc_response.get("dataConsistencyResult"),
        }
        
        # ==================================================================
        # SECTION 3: SECURITY FEATURES VALIDATION
        # ==================================================================
        security_features = {
            # Physical Security Features
            "hologram_present": doc_response.get("hologramPresent"),
            "hologram_valid": doc_response.get("hologramValid"),
            "watermark_present": doc_response.get("watermarkPresent"),
            "watermark_valid": doc_response.get("watermarkValid"),
            "microprint_present": doc_response.get("microprintPresent"),
            "microprint_valid": doc_response.get("microprintValid"),
            "uv_features_present": doc_response.get("uvFeaturesPresent"),
            "uv_features_valid": doc_response.get("uvFeaturesValid"),
            
            # Digital Security
            "barcode_present": doc_response.get("barcodePresent"),
            "barcode_valid": doc_response.get("barcodeValid"),
            "barcode_data_matches_visual": doc_response.get("barcodeDataMatchesVisual"),
            "mrz_present": doc_response.get("mrzPresent"),  # Machine Readable Zone
            "mrz_valid": doc_response.get("mrzValid"),
            "mrz_checksum_valid": doc_response.get("mrzChecksumValid"),
            
            # RFID/Chip (if enabled)
            "rfid_chip_present": doc_response.get("rfidChipPresent"),
            "rfid_chip_readable": doc_response.get("rfidChipReadable"),
            "rfid_data_matches_visual": doc_response.get("rfidDataMatchesVisual"),
            "rfid_signature_valid": doc_response.get("rfidSignatureValid"),
        }
        
        # ==================================================================
        # SECTION 4: IMAGE QUALITY METRICS
        # ==================================================================
        image_quality = {
            "image_quality_score": doc_response.get("imageQualityScore"),
            "is_blurry": doc_response.get("isBlurry"),
            "is_glare": doc_response.get("isGlare"),
            "is_cropped_properly": doc_response.get("isCroppedProperly"),
            "lighting_adequate": doc_response.get("lightingAdequate"),
            "resolution_adequate": doc_response.get("resolutionAdequate"),
            "corners_visible": doc_response.get("cornersVisible"),
        }
        
        # ==================================================================
        # SECTION 5: FRAUD INDICATORS
        # ==================================================================
        fraud_indicators = {
            # Tampering Detection
            "tampering_detected": doc_response.get("tamperingDetected"),
            "photo_replacement_detected": doc_response.get("photoReplacementDetected"),
            "text_alteration_detected": doc_response.get("textAlterationDetected"),
            "laminate_tampering": doc_response.get("laminateTampering"),
            
            # Document Validity
            "is_specimen": doc_response.get("isSpecimen"),  # Test/Sample document
            "is_duplicate": doc_response.get("isDuplicate"),
            "is_revoked": doc_response.get("isRevoked"),
            "is_reported_stolen": doc_response.get("isReportedStolen"),
            
            # Forgery Indicators
            "font_inconsistencies": doc_response.get("fontInconsistencies"),
            "color_inconsistencies": doc_response.get("colorInconsistencies"),
            "layout_inconsistencies": doc_response.get("layoutInconsistencies"),
            "security_feature_mismatches": doc_response.get("securityFeatureMismatches"),
        }
        
        # ==================================================================
        # SECTION 6: FACE MATCHING (Document Photo vs Live Selfie)
        # ==================================================================
        face_match = {
            "face_match_result": doc_response.get("faceMatchResult"),  # PASS/FAIL
            "face_match_score": doc_response.get("faceMatchScore"),
            "face_match_confidence": doc_response.get("faceMatchConfidence"),
            "document_photo_quality": doc_response.get("documentPhotoQuality"),
            "live_selfie_quality": doc_response.get("liveSelfieQuality"),
        }
        
        # ==================================================================
        # SECTION 7: DATA CONSISTENCY CHECKS
        # ==================================================================
        consistency_checks = {
            # Cross-field validation
            "age_matches_dob": doc_response.get("ageMatchesDOB"),
            "name_format_valid": doc_response.get("nameFormatValid"),
            "address_format_valid": doc_response.get("addressFormatValid"),
            "document_number_format_valid": doc_response.get("documentNumberFormatValid"),
            
            # Date validations
            "issue_date_valid": doc_response.get("issueDateValid"),
            "expiry_date_valid": doc_response.get("expiryDateValid"),
            "dates_logical": doc_response.get("datesLogical"),  # Issue < Expiry, etc.
            
            # Geographic validations
            "state_country_match": doc_response.get("stateCountryMatch"),
            "address_state_match": doc_response.get("addressStateMatch"),
        }
        
        # ==================================================================
        # SECTION 8: REGULA/VENDOR SPECIFIC DATA
        # ==================================================================
        vendor_data = {
            "vendor": doc_response.get("vendor", "REGULA"),
            "document_class": doc_response.get("documentClass"),
            "document_subclass": doc_response.get("documentSubclass"),
            "issuing_authority": doc_response.get("issuingAuthority"),
            "template_matched": doc_response.get("templateMatched"),
            "template_confidence": doc_response.get("templateConfidence"),
            
            # Regula-specific scores
            "optical_authenticity": doc_response.get("opticalAuthenticity"),
            "digital_authenticity": doc_response.get("digitalAuthenticity"),
            "physical_authenticity": doc_response.get("physicalAuthenticity"),
        }
        
        # ==================================================================
        # COMBINE ALL DATA
        # ==================================================================
        complete_data = {
            "ocr_data": ocr_data,
            "verification_results": verification_results,
            "security_features": security_features,
            "image_quality": image_quality,
            "fraud_indicators": fraud_indicators,
            "face_match": face_match,
            "consistency_checks": consistency_checks,
            "vendor_data": vendor_data,
            
            # Transaction metadata
            "transaction_id": doc_response.get("transactionId"),
            "timestamp": doc_response.get("timestamp"),
            "processing_time_ms": doc_response.get("processingTimeMs"),
        }
        
        return complete_data
    
    @staticmethod
    def validate_document_authenticity(extracted_data: Dict) -> Dict:
        """
        Validate document authenticity based on extracted data
        Returns validation report with flags
        """
        
        verification = extracted_data.get("verification_results", {})
        security = extracted_data.get("security_features", {})
        fraud = extracted_data.get("fraud_indicators", {})
        quality = extracted_data.get("image_quality", {})
        consistency = extracted_data.get("consistency_checks", {})
        
        # Collect all issues
        critical_issues = []
        warnings = []
        info = []
        
        # ==================================================================
        # CRITICAL ISSUES (Document is FAKE/INVALID)
        # ==================================================================
        
        # Fraud detected
        if fraud.get("tampering_detected"):
            critical_issues.append("🚨 Document tampering detected")
        if fraud.get("photo_replacement_detected"):
            critical_issues.append("🚨 Photo replacement detected")
        if fraud.get("text_alteration_detected"):
            critical_issues.append("🚨 Text alteration detected")
        if fraud.get("is_specimen"):
            critical_issues.append("🚨 Document is a specimen/test document")
        if fraud.get("is_revoked"):
            critical_issues.append("🚨 Document has been revoked")
        if fraud.get("is_reported_stolen"):
            critical_issues.append("🚨 Document reported as stolen")
        
        # Security features failed
        if security.get("hologram_present") and not security.get("hologram_valid"):
            critical_issues.append("🚨 Hologram present but invalid")
        if security.get("watermark_present") and not security.get("watermark_valid"):
            critical_issues.append("🚨 Watermark present but invalid")
        if security.get("mrz_present") and not security.get("mrz_valid"):
            critical_issues.append("🚨 MRZ present but invalid")
        if security.get("barcode_present") and not security.get("barcode_data_matches_visual"):
            critical_issues.append("🚨 Barcode data doesn't match visual data")
        
        # Overall verification failed
        if verification.get("overall_result") == "FAIL":
            critical_issues.append("🚨 Overall document verification FAILED")
        
        # ==================================================================
        # WARNINGS (Suspicious but not conclusive)
        # ==================================================================
        
        # Image quality issues
        if quality.get("is_blurry"):
            warnings.append("⚠️  Image is blurry - may affect accuracy")
        if quality.get("is_glare"):
            warnings.append("⚠️  Glare detected on document")
        if not quality.get("is_cropped_properly"):
            warnings.append("⚠️  Document not cropped properly")
        
        # Missing security features (suspicious)
        if not security.get("hologram_present"):
            warnings.append("⚠️  Hologram not detected (may be required)")
        if not security.get("watermark_present"):
            warnings.append("⚠️  Watermark not detected (may be required)")
        if not security.get("uv_features_present"):
            warnings.append("⚠️  UV features not detected")
        
        # Data inconsistencies
        if not consistency.get("age_matches_dob"):
            warnings.append("⚠️  Age doesn't match date of birth")
        if not consistency.get("dates_logical"):
            warnings.append("⚠️  Document dates are illogical")
        
        # Low confidence
        if verification.get("confidence_score") and verification.get("confidence_score") < 70:
            warnings.append(f"⚠️  Low confidence score: {verification.get('confidence_score')}%")
        
        # Face match issues
        if extracted_data.get("face_match", {}).get("face_match_result") == "FAIL":
            warnings.append("⚠️  Face does not match document photo")
        
        # ==================================================================
        # INFO (Good practices, additional data)
        # ==================================================================
        
        ocr = extracted_data.get("ocr_data", {})
        if ocr.get("is_expired"):
            info.append("ℹ️  Document is expired")
        
        if security.get("rfid_chip_present"):
            if security.get("rfid_chip_readable"):
                info.append("ℹ️  RFID chip present and readable")
            else:
                info.append("ℹ️  RFID chip present but not readable")
        
        # ==================================================================
        # DETERMINE OVERALL STATUS
        # ==================================================================
        
        if critical_issues:
            status = DocumentValidationStatus.FAKE
        elif warnings and len(warnings) >= 3:
            status = DocumentValidationStatus.SUSPICIOUS
        elif verification.get("overall_result") == "PASS":
            status = DocumentValidationStatus.GENUINE
        else:
            status = DocumentValidationStatus.INSUFFICIENT_DATA
        
        return {
            "status": status.value,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "info": info,
            "is_valid": status == DocumentValidationStatus.GENUINE,
            "confidence_score": verification.get("confidence_score"),
            "summary": f"Document is {status.value}: {len(critical_issues)} critical, {len(warnings)} warnings"
        }
    
    @staticmethod
    def generate_validation_report(extracted_data: Dict, validation_result: Dict) -> str:
        """Generate detailed validation report for logging"""
        
        report = []
        report.append("\n" + "="*120)
        report.append("📄 DOCUMENT VALIDATION REPORT")
        report.append("="*120)
        
        # Overall Status
        status = validation_result.get("status")
        if status == "GENUINE":
            report.append(f"\n✅ Status: {status}")
        elif status == "FAKE":
            report.append(f"\n🚨 Status: {status}")
        elif status == "SUSPICIOUS":
            report.append(f"\n⚠️  Status: {status}")
        else:
            report.append(f"\nℹ️  Status: {status}")
        
        report.append(f"Confidence: {validation_result.get('confidence_score', 'N/A')}%")
        
        # Critical Issues
        if validation_result.get("critical_issues"):
            report.append("\n" + "-"*120)
            report.append("🚨 CRITICAL ISSUES:")
            for issue in validation_result.get("critical_issues"):
                report.append(f"   {issue}")
        
        # Warnings
        if validation_result.get("warnings"):
            report.append("\n" + "-"*120)
            report.append("⚠️  WARNINGS:")
            for warning in validation_result.get("warnings"):
                report.append(f"   {warning}")
        
        # Extracted Data Summary
        ocr = extracted_data.get("ocr_data", {})
        report.append("\n" + "-"*120)
        report.append("📋 EXTRACTED DATA:")
        report.append(f"   Name: {ocr.get('full_name') or f'{ocr.get("first_name")} {ocr.get("last_name")}'}")
        report.append(f"   DOB: {ocr.get('date_of_birth')} (Age: {ocr.get('age')})")
        report.append(f"   Document Type: {ocr.get('document_type')}")
        report.append(f"   Document Number: {ocr.get('document_number')}")
        report.append(f"   Issuing State: {ocr.get('issuing_state')}, {ocr.get('issuing_country')}")
        report.append(f"   Issue Date: {ocr.get('issue_date')}")
        report.append(f"   Expiry Date: {ocr.get('expiry_date')} {'(EXPIRED)' if ocr.get('is_expired') else ''}")
        
        # Security Features
        security = extracted_data.get("security_features", {})
        report.append("\n" + "-"*120)
        report.append("🔒 SECURITY FEATURES:")
        report.append(f"   Hologram: {'✅' if security.get('hologram_valid') else '❌' if security.get('hologram_present') else 'Not detected'}")
        report.append(f"   Watermark: {'✅' if security.get('watermark_valid') else '❌' if security.get('watermark_present') else 'Not detected'}")
        report.append(f"   MRZ: {'✅' if security.get('mrz_valid') else '❌' if security.get('mrz_present') else 'Not detected'}")
        report.append(f"   Barcode: {'✅' if security.get('barcode_valid') else '❌' if security.get('barcode_present') else 'Not detected'}")
        report.append(f"   UV Features: {'✅' if security.get('uv_features_valid') else '❌' if security.get('uv_features_present') else 'Not detected'}")
        
        # Face Match
        face = extracted_data.get("face_match", {})
        if face.get("face_match_result"):
            report.append("\n" + "-"*120)
            report.append("👤 FACE MATCH:")
            report.append(f"   Result: {face.get('face_match_result')}")
            report.append(f"   Score: {face.get('face_match_score')}")
            report.append(f"   Confidence: {face.get('face_match_confidence')}")
        
        report.append("\n" + "="*120)
        
        return "\n".join(report)


# ==============================================================================
# EXAMPLE USAGE IN TEST
# ==============================================================================

def example_test_with_validation(api_client, enrollment_token):
    """
    Example of how to use document validation in your tests
    """
    
    # Make document OCR request
    doc_response = api_client.http_client.post(
        "/onboarding/enrollment/addDocumentOCR",
        json={...}  # Your payload
    )
    
    doc_data = doc_response.json()
    
    # Extract all document data
    extracted_data = DocumentValidator.extract_document_data(doc_data)
    
    # Validate authenticity
    validation_result = DocumentValidator.validate_document_authenticity(extracted_data)
    
    # Generate and log report
    report = DocumentValidator.generate_validation_report(extracted_data, validation_result)
    logger.info(report)
    
    # Assert based on validation
    assert validation_result["is_valid"], f"Document validation failed: {validation_result['summary']}"
    
    if validation_result["critical_issues"]:
        pytest.fail(f"Document has critical issues: {validation_result['critical_issues']}")
    
    return extracted_data, validation_result
