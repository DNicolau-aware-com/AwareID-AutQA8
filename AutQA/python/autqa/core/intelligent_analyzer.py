"""
Intelligent Test Result Analyzer and Reporter
Automatically extracts transaction data, validates expectations, and raises flags
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests we support"""
    ENROLLMENT = "enrollment"
    REENROLLMENT = "reenrollment"
    AUTHENTICATION = "authentication"
    VERIFICATION = "verification"
    AGE_VERIFICATION = "age_verification"
    LIVENESS = "liveness"
    DOCUMENT_OCR = "document_ocr"


class TransactionStatus(Enum):
    """Transaction status types"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    DEVICE_REGISTERED = "Device registered"
    AGE_ESTIMATION_FAILED = "AGE ESTIMATION FAILED"
    LIVENESS_FAILED = "LIVENESS FAILED"


class AnomalyType(Enum):
    """Types of anomalies to flag"""
    SECURITY_BYPASS = "🚨 SECURITY BYPASS"
    UNEXPECTED_SUCCESS = "⚠️  UNEXPECTED SUCCESS"
    UNEXPECTED_FAILURE = "⚠️  UNEXPECTED FAILURE"
    PERFORMANCE_ISSUE = "⏰ PERFORMANCE ISSUE"
    DATA_INCONSISTENCY = "❌ DATA INCONSISTENCY"
    MISSING_VALIDATION = "🔥 MISSING VALIDATION"
    AGE_VERIFICATION_BYPASS = "🚨 AGE VERIFICATION NOT ENFORCED"
    LIVENESS_BYPASS = "🚨 LIVENESS CHECK BYPASSED"


class Transaction:
    """Represents a single transaction in the flow"""
    
    def __init__(
        self,
        step_name: str,
        transaction_id: Optional[str] = None,
        status: TransactionStatus = TransactionStatus.SUCCESS,
        timestamp: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        data: Optional[Dict] = None
    ):
        self.step_name = step_name
        self.transaction_id = transaction_id or "N/A"
        self.status = status
        self.timestamp = timestamp or datetime.now()
        self.duration_ms = duration_ms
        self.data = data or {}
        self.sub_transactions: List['Transaction'] = []
        self.anomalies: List['Anomaly'] = []
    
    def add_sub_transaction(self, sub_tx: 'Transaction'):
        """Add a sub-transaction (e.g., Analyze Image under Add Face)"""
        self.sub_transactions.append(sub_tx)
    
    def add_anomaly(self, anomaly: 'Anomaly'):
        """Flag an anomaly in this transaction"""
        self.anomalies.append(anomaly)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            "step_name": self.step_name,
            "transaction_id": self.transaction_id,
            "status": self.status.value if isinstance(self.status, TransactionStatus) else str(self.status),
            "timestamp": self.timestamp.strftime("%m/%d/%Y, %I:%M:%S %p"),
            "duration_ms": self.duration_ms,
            "data": self.data,
            "sub_transactions": [st.to_dict() for st in self.sub_transactions],
            "anomalies": [a.to_dict() for a in self.anomalies]
        }


class Anomaly:
    """Represents an anomaly or unexpected behavior"""
    
    def __init__(
        self,
        anomaly_type: AnomalyType,
        severity: str,  # "CRITICAL", "WARNING", "INFO"
        message: str,
        details: Optional[Dict] = None,
        recommendation: Optional[str] = None
    ):
        self.type = anomaly_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.recommendation = recommendation
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.strftime("%m/%d/%Y, %I:%M:%S %p")
        }


class TestReport:
    """Complete test report with intelligent analysis"""
    
    def __init__(
        self,
        test_name: str,
        test_type: TestType,
        expected_outcome: str,
        actual_outcome: str
    ):
        self.test_name = test_name
        self.test_type = test_type
        self.expected_outcome = expected_outcome
        self.actual_outcome = actual_outcome
        self.transactions: List[Transaction] = []
        self.anomalies: List[Anomaly] = []
        self.metadata: Dict = {}
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.test_passed: Optional[bool] = None
    
    def add_transaction(self, transaction: Transaction):
        """Add a transaction to the report"""
        self.transactions.append(transaction)
    
    def add_anomaly(self, anomaly: Anomaly):
        """Add a global anomaly to the report"""
        self.anomalies.append(anomaly)
    
    def finalize(self, passed: bool):
        """Mark test as complete"""
        self.end_time = datetime.now()
        self.test_passed = passed
    
    def get_duration_seconds(self) -> float:
        """Get total test duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            "test_name": self.test_name,
            "test_type": self.test_type.value,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "test_passed": self.test_passed,
            "duration_seconds": self.get_duration_seconds(),
            "start_time": self.start_time.strftime("%m/%d/%Y, %I:%M:%S %p"),
            "end_time": self.end_time.strftime("%m/%d/%Y, %I:%M:%S %p") if self.end_time else None,
            "transactions": [t.to_dict() for t in self.transactions],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "metadata": self.metadata
        }


class IntelligentAnalyzer:
    """Analyzes test results and automatically flags anomalies"""
    
    @staticmethod
    def analyze_enrollment(report: TestReport, response_data: Dict) -> TestReport:
        """Analyze enrollment response and extract transactions"""
        
        # Extract enrollment transaction
        enroll_tx = Transaction(
            step_name="Enrollment - Enroll",
            transaction_id=response_data.get("transactionId", "N/A"),
            status=TransactionStatus.SUCCESS if response_data.get("enrollmentToken") else TransactionStatus.FAILED,
            data={
                "username": response_data.get("username"),
                "enrollment_token": response_data.get("enrollmentToken", "")[:20] + "..." if response_data.get("enrollmentToken") else None,
                "required_checks": response_data.get("requiredChecks", [])
            }
        )
        
        report.add_transaction(enroll_tx)
        
        # Check for anomalies
        if not response_data.get("enrollmentToken"):
            report.add_anomaly(Anomaly(
                anomaly_type=AnomalyType.UNEXPECTED_FAILURE,
                severity="CRITICAL",
                message="Enrollment failed to return enrollment token",
                details=response_data,
                recommendation="Check user data validity and server logs"
            ))
        
        return report
    
    @staticmethod
    def analyze_face_enrollment(
        report: TestReport,
        response_data: Dict,
        expected_age_result: Optional[str] = None
    ) -> TestReport:
        """Analyze face enrollment with age verification"""
        
        # Main transaction
        face_tx = Transaction(
            step_name="Enrollment - Add Face",
            transaction_id=response_data.get("transactionId", "N/A"),
            data={"raw_response": response_data}
        )
        
        # Extract age estimation data
        age_check = response_data.get("ageEstimationCheck", {})
        age_from_server = age_check.get("ageFromFaceLivenessServer")
        age_result = age_check.get("result")
        age_config = age_check.get("ageEstimation", {})
        min_age = age_config.get("minAge")
        max_age = age_config.get("maxAge")
        
        # Sub-transaction: Analyze Image
        analyze_tx = Transaction(
            step_name="Analyze Image (Age Detection)",
            status=TransactionStatus.SUCCESS if age_from_server else TransactionStatus.FAILED,
            data={
                "detected_age": age_from_server,
                "min_age": min_age,
                "max_age": max_age,
                "result": age_result,
                "in_range": min_age <= age_from_server <= max_age if age_from_server and min_age and max_age else None
            }
        )
        
        # Check for age verification bypass
        if expected_age_result and age_result != expected_age_result:
            if age_from_server and min_age and max_age:
                age_in_range = min_age <= age_from_server <= max_age
                
                if not age_in_range and age_result != "FAIL":
                    # AGE VERIFICATION BYPASSED!
                    analyze_tx.add_anomaly(Anomaly(
                        anomaly_type=AnomalyType.AGE_VERIFICATION_BYPASS,
                        severity="CRITICAL",
                        message=f"Age verification not enforced: Age {age_from_server} is outside {min_age}-{max_age} but enrollment succeeded",
                        details={
                            "detected_age": age_from_server,
                            "min_age": min_age,
                            "max_age": max_age,
                            "expected_result": expected_age_result,
                            "actual_result": age_result
                        },
                        recommendation="INVESTIGATE IMMEDIATELY - Age verification may be disabled or misconfigured"
                    ))
        
        face_tx.add_sub_transaction(analyze_tx)
        
        # Sub-transaction: Check Liveness
        liveness_data = response_data.get("faceLivenessResults", {}).get("video", {}).get("liveness_result", {})
        liveness_decision = liveness_data.get("decision")
        liveness_score = liveness_data.get("score_frr")
        
        liveness_tx = Transaction(
            step_name="Check Liveness (Spoof Detection)",
            status=TransactionStatus.SUCCESS if liveness_decision == "LIVE" else TransactionStatus.LIVENESS_FAILED,
            data={
                "decision": liveness_decision,
                "score": liveness_score
            }
        )
        
        # Check for liveness bypass
        if liveness_decision != "LIVE" and response_data.get("enrollmentStatus") == 0:
            # LIVENESS BYPASSED!
            liveness_tx.add_anomaly(Anomaly(
                anomaly_type=AnomalyType.LIVENESS_BYPASS,
                severity="CRITICAL",
                message=f"Liveness check bypassed: Decision was '{liveness_decision}' but enrollment succeeded",
                details={
                    "liveness_decision": liveness_decision,
                    "liveness_score": liveness_score,
                    "enrollment_status": response_data.get("enrollmentStatus")
                },
                recommendation="INVESTIGATE IMMEDIATELY - Potential spoof attack allowed through"
            ))
        
        face_tx.add_sub_transaction(liveness_tx)
        
        # Set main transaction status
        if age_result == "FAIL":
            face_tx.status = TransactionStatus.AGE_ESTIMATION_FAILED
        elif liveness_decision != "LIVE":
            face_tx.status = TransactionStatus.LIVENESS_FAILED
        else:
            face_tx.status = TransactionStatus.SUCCESS
        
        report.add_transaction(face_tx)
        
        return report
    
    @staticmethod
    def analyze_document_ocr(report: TestReport, response_data: Dict) -> TestReport:
        """Analyze document OCR response"""
        
        doc_tx = Transaction(
            step_name="Enrollment - Add Document OCR",
            transaction_id=response_data.get("transactionId", "N/A"),
            status=TransactionStatus.SUCCESS if response_data.get("registrationCode") else TransactionStatus.PENDING,
            data={
                "registration_code": response_data.get("registrationCode"),
                "document_verification_result": response_data.get("documentVerificationResult")
            }
        )
        
        report.add_transaction(doc_tx)
        
        return report
    
    @staticmethod
    def analyze_authentication(report: TestReport, response_data: Dict, expected_result: str) -> TestReport:
        """Analyze authentication response"""
        
        auth_result = response_data.get("authenticationResult", "UNKNOWN")
        
        auth_tx = Transaction(
            step_name="Authentication",
            transaction_id=response_data.get("transactionId", "N/A"),
            status=TransactionStatus.SUCCESS if auth_result == "PASS" else TransactionStatus.FAILED,
            data={
                "authentication_result": auth_result,
                "score": response_data.get("score"),
                "username": response_data.get("username")
            }
        )
        
        # Check for unexpected results
        if auth_result != expected_result:
            auth_tx.add_anomaly(Anomaly(
                anomaly_type=AnomalyType.UNEXPECTED_SUCCESS if auth_result == "PASS" else AnomalyType.UNEXPECTED_FAILURE,
                severity="WARNING",
                message=f"Authentication result mismatch: Expected {expected_result}, got {auth_result}",
                details=response_data,
                recommendation="Verify biometric data quality and threshold configurations"
            ))
        
        report.add_transaction(auth_tx)
        
        return report
    
    @staticmethod
    def generate_html_report(report: TestReport) -> str:
        """Generate beautiful HTML report with all details"""
        
        # Build anomaly summary
        critical_anomalies = [a for a in report.anomalies if a.severity == "CRITICAL"]
        warning_anomalies = [a for a in report.anomalies if a.severity == "WARNING"]
        
        # Collect all anomalies from transactions too
        for tx in report.transactions:
            critical_anomalies.extend([a for a in tx.anomalies if a.severity == "CRITICAL"])
            warning_anomalies.extend([a for a in tx.anomalies if a.severity == "WARNING"])
            for sub_tx in tx.sub_transactions:
                critical_anomalies.extend([a for a in sub_tx.anomalies if a.severity == "CRITICAL"])
                warning_anomalies.extend([a for a in sub_tx.anomalies if a.severity == "WARNING"])
        
        html = f"""
        <div class="test-report">
            <h2>🎯 {report.test_name}</h2>
            <div class="test-summary">
                <p><strong>Type:</strong> {report.test_type.value}</p>
                <p><strong>Expected:</strong> {report.expected_outcome}</p>
                <p><strong>Actual:</strong> {report.actual_outcome}</p>
                <p><strong>Result:</strong> <span class="{'pass' if report.test_passed else 'fail'}">
                    {'✅ PASSED' if report.test_passed else '❌ FAILED'}
                </span></p>
                <p><strong>Duration:</strong> {report.get_duration_seconds():.2f}s</p>
            </div>
        """
        
        # Critical anomalies section
        if critical_anomalies:
            html += """
            <div class="critical-anomalies">
                <h3>🚨 CRITICAL ISSUES</h3>
                <ul>
            """
            for anomaly in critical_anomalies:
                html += f"""
                <li class="critical">
                    <strong>{anomaly.type.value}</strong>: {anomaly.message}
                    <br><em>Recommendation: {anomaly.recommendation}</em>
                </li>
                """
            html += "</ul></div>"
        
        # Warning anomalies section
        if warning_anomalies:
            html += """
            <div class="warning-anomalies">
                <h3>⚠️  WARNINGS</h3>
                <ul>
            """
            for anomaly in warning_anomalies:
                html += f"""
                <li class="warning">
                    <strong>{anomaly.type.value}</strong>: {anomaly.message}
                </li>
                """
            html += "</ul></div>"
        
        # Transactions timeline
        html += """
            <div class="transactions">
                <h3>📊 Transaction Flow</h3>
        """
        
        for tx in report.transactions:
            status_class = "success" if tx.status == TransactionStatus.SUCCESS else "failed"
            html += f"""
            <div class="transaction {status_class}">
                <h4>{tx.step_name}</h4>
                <p>ID: {tx.transaction_id}</p>
                <p>Status: {tx.status.value if isinstance(tx.status, TransactionStatus) else tx.status}</p>
                <p>Time: {tx.timestamp.strftime('%m/%d/%Y, %I:%M:%S %p')}</p>
            """
            
            # Sub-transactions
            for sub_tx in tx.sub_transactions:
                sub_status_class = "success" if sub_tx.status == TransactionStatus.SUCCESS else "failed"
                html += f"""
                <div class="sub-transaction {sub_status_class}">
                    <h5>└─ {sub_tx.step_name}</h5>
                    <pre>{json.dumps(sub_tx.data, indent=2)}</pre>
                """
                
                # Sub-transaction anomalies
                for anomaly in sub_tx.anomalies:
                    html += f"""
                    <div class="anomaly {anomaly.severity.lower()}">
                        {anomaly.type.value}: {anomaly.message}
                    </div>
                    """
                
                html += "</div>"
            
            html += "</div>"
        
        html += "</div></div>"
        
        return html


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

def example_usage():
    """Example of how to use the framework"""
    
    # Create a test report
    report = TestReport(
        test_name="Age Verification 1-16",
        test_type=TestType.AGE_VERIFICATION,
        expected_outcome="FAIL",
        actual_outcome="FAIL"
    )
    
    # Simulate enrollment response
    enroll_response = {
        "transactionId": "abc123",
        "enrollmentToken": "token_xyz",
        "username": "testuser",
        "requiredChecks": ["addFace", "addDocument"]
    }
    
    # Analyze enrollment
    report = IntelligentAnalyzer.analyze_enrollment(report, enroll_response)
    
    # Simulate face response with age verification
    face_response = {
        "transactionId": "def456",
        "ageEstimationCheck": {
            "ageEstimation": {"enabled": True, "minAge": 1, "maxAge": 16},
            "ageFromFaceLivenessServer": 50,
            "result": "FAIL"
        },
        "faceLivenessResults": {
            "video": {
                "liveness_result": {
                    "decision": "LIVE",
                    "score_frr": 0.2162
                }
            }
        }
    }
    
    # Analyze face enrollment
    report = IntelligentAnalyzer.analyze_face_enrollment(
        report,
        face_response,
        expected_age_result="FAIL"
    )
    
    # Finalize report
    report.finalize(passed=True)
    
    # Generate HTML
    html = IntelligentAnalyzer.generate_html_report(report)
    
    # Or export as JSON
    json_report = json.dumps(report.to_dict(), indent=2)
    
    return report, html, json_report
