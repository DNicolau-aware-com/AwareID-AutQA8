"""
Response analyzer for enrollment and authentication API calls.

Extracts and formats key information from API responses.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ResponseAnalyzer:
    """Analyze and format API response data."""

    @staticmethod
    def analyze_face_liveness_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze face liveness response."""
        liveness_result = response_data.get("livenessResult", None)
        face_liveness = response_data.get("faceLivenessResults", {})
        video_data = face_liveness.get("video", {})
        liveness_detail = video_data.get("liveness_result", {})
        
        decision = liveness_detail.get("decision", "UNKNOWN")
        score_frr = liveness_detail.get("score_frr", "N/A")
        feedback = liveness_detail.get("feedback", [])
        
        is_live = liveness_result is True and decision == "LIVE"
        is_spoof = liveness_result is False or decision != "LIVE"
        
        return {
            "is_live": is_live,
            "is_spoof": is_spoof,
            "liveness_result": liveness_result,
            "decision": decision,
            "score_frr": score_frr,
            "feedback": feedback,
            "verdict": "✅ LIVE PERSON" if is_live else "❌ SPOOF DETECTED",
        }

    @staticmethod
    def analyze_face_match_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze face matching response."""
        match_result = response_data.get("matchResult", None)
        match_score = response_data.get("matchScore", 0)
        
        if match_score >= 80:
            quality = "EXCELLENT"
        elif match_score >= 60:
            quality = "GOOD"
        elif match_score >= 40:
            quality = "FAIR"
        elif match_score >= 25:
            quality = "POOR"
        else:
            quality = "FAILED"
        
        return {
            "match_result": match_result,
            "match_score": match_score,
            "match_quality": quality,
            "verdict": f"{'✅' if match_result else '❌'} Match: {match_score}% ({quality})",
        }

    @staticmethod
    def analyze_document_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document verification response."""
        doc_verified = response_data.get("documentVerificationResult", None)
        ocr_results = response_data.get("ocrResults", {})
        mrz_presence = ocr_results.get("mrzPresence", False)
        rfid_presence = ocr_results.get("rfidPresence", 0)
        
        doc_data = ocr_results.get("documentData", {})
        doc_number = doc_data.get("documentNumber", "N/A")
        expiry_date = doc_data.get("expiryDate", "N/A")
        doc_type = doc_data.get("documentType", "N/A")
        issuing_country = doc_data.get("issuingCountry", "N/A")
        
        is_expired = False
        if expiry_date != "N/A":
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                is_expired = expiry < datetime.now()
            except:
                pass
        
        if doc_verified is True and not is_expired:
            verdict = "✅ VALID DOCUMENT"
        elif doc_verified is True and is_expired:
            verdict = "⚠️ VALID BUT EXPIRED"
        elif doc_verified is False:
            verdict = "❌ INVALID DOCUMENT"
        else:
            verdict = "⚠️ VERIFICATION INCOMPLETE"
        
        return {
            "document_verified": doc_verified,
            "is_expired": is_expired,
            "document_type": doc_type,
            "document_number": doc_number,
            "expiry_date": expiry_date,
            "issuing_country": issuing_country,
            "mrz_present": mrz_presence,
            "rfid_present": rfid_presence > 0,
            "verdict": verdict,
        }

    @staticmethod
    def analyze_authentication_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze complete authentication response."""
        liveness = ResponseAnalyzer.analyze_face_liveness_response(response_data)
        match = ResponseAnalyzer.analyze_face_match_response(response_data)
        
        auth_status = response_data.get("authStatus", None)
        status_map = {0: "FAILED", 1: "PENDING", 2: "COMPLETE"}
        auth_status_name = status_map.get(auth_status, "UNKNOWN")
        
        passed = (
            liveness.get("is_live") and 
            match.get("match_result") and 
            auth_status == 2
        )
        
        return {
            "authentication_passed": passed,
            "auth_status": auth_status_name,
            "liveness": liveness,
            "match": match,
            "overall_verdict": "✅ AUTHENTICATION PASSED" if passed else "❌ AUTHENTICATION FAILED",
        }

    @staticmethod
    def format_analysis(analysis: Dict[str, Any], title: str = "ANALYSIS") -> str:
        """Format analysis results for console output."""
        lines = ["", "=" * 80, f"  {title}", "=" * 80]
        
        for key, value in analysis.items():
            if isinstance(value, dict):
                lines.append(f"\n{key.upper().replace('_', ' ')}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key.replace('_', ' ').title()}: {sub_value}")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def analyze_liveness(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick liveness analysis."""
    return ResponseAnalyzer.analyze_face_liveness_response(response_data)


def analyze_match(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick match analysis."""
    return ResponseAnalyzer.analyze_face_match_response(response_data)


def analyze_document(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick document analysis."""
    return ResponseAnalyzer.analyze_document_response(response_data)


def analyze_authentication(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick authentication analysis."""
    return ResponseAnalyzer.analyze_authentication_response(response_data)


def print_analysis(analysis: Dict[str, Any], title: str = "ANALYSIS"):
    """Print formatted analysis."""
    print(ResponseAnalyzer.format_analysis(analysis, title))
