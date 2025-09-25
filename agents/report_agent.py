import os
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from weasyprint import HTML, CSS
from .base_agent import BaseAgent, AgentStatus

class ReportGenerationAgent(BaseAgent):
    
    def __init__(self, agent_id: str, websocket_manager=None):
        super().__init__(agent_id, websocket_manager)
        self.report_template = None
        self.output_folder = "reports"
    
    async def execute(self, analysis_results: Dict[str, Any], document_results: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.status = AgentStatus.PROCESSING
            await self.send_update("initialization", "Initializing report generation", 5.0)
            
            os.makedirs(self.output_folder, exist_ok=True)
            
            await self.send_update("template_preparation", "Preparing report template", 15.0)
            self._prepare_template()
            
            await self.send_update("data_compilation", "Compiling analysis data", 25.0)
            report_data = await self._compile_report_data(analysis_results, document_results)
            
            await self.send_update("html_generation", "Generating HTML report", 45.0)
            html_content = await self._generate_html_report(report_data)
            
            await self.send_update("pdf_conversion", "Converting to PDF", 65.0)
            pdf_path = await self._generate_pdf_report(html_content, report_data)
            
            await self.send_update("summary_generation", "Generating executive summary", 80.0)
            executive_summary = await self._generate_executive_summary(report_data)
            
            self.status = AgentStatus.COMPLETED
            self.results = {
                "pdf_report_path": pdf_path,
                "html_content": html_content,
                "executive_summary": executive_summary,
                "report_data": report_data,
                "generation_timestamp": datetime.utcnow().isoformat()
            }
            
            await self.send_update("completion", f"Report generated successfully: {pdf_path}", 100.0)
            
            return self.results
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            await self.send_update("error", error_msg, self.progress, error=error_msg)
            raise
    
    def _prepare_template(self):
        self.report_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Claims Analysis Report</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }
                .header {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                }
                .header h1 {
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }
                .header .subtitle {
                    margin: 10px 0 0 0;
                    font-size: 1.1em;
                    opacity: 0.9;
                }
                .executive-summary {
                    background: #f8f9fa;
                    border-left: 5px solid #007bff;
                    padding: 20px;
                    margin: 20px 0;
                }
                .section {
                    margin: 30px 0;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 20px;
                }
                .section h2 {
                    color: #1e3c72;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 10px;
                }
                .status-badge {
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    color: white;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .status-approve { background-color: #28a745; }
                .status-reject { background-color: #dc3545; }
                .status-review { background-color: #ffc107; color: #333; }
                .risk-high { color: #dc3545; font-weight: bold; }
                .risk-medium { color: #ffc107; font-weight: bold; }
                .risk-low { color: #28a745; font-weight: bold; }
                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                .data-table th, .data-table td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                .data-table th {
                    background-color: #f8f9fa;
                    font-weight: 600;
                }
                .highlight {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .alert {
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 5px;
                }
                .alert-danger {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }
                .alert-warning {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                }
                .alert-success {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 0.9em;
                    color: #666;
                }
                @page {
                    size: A4;
                    margin: 1in;
                }
                .page-break {
                    page-break-before: always;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Claims Analysis Report</h1>
                <div class="subtitle">Comprehensive Reinsurance Claims Assessment</div>
                <div class="subtitle">Generated on {{ report_date }}</div>
            </div>

            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <p><strong>Overall Recommendation:</strong> 
                    <span class="status-badge status-{{ recommendation.lower() }}">{{ recommendation }}</span>
                </p>
                <p><strong>Fraud Risk Level:</strong> 
                    <span class="risk-{{ fraud_risk.lower() }}">{{ fraud_risk }}</span>
                </p>
                <p><strong>Key Findings:</strong></p>
                <ul>
                    {% for finding in key_findings %}
                    <li>{{ finding }}</li>
                    {% endfor %}
                </ul>
            </div>

            <div class="section">
                <h2>Email Analysis</h2>
                <table class="data-table">
                    <tr><th>Sender</th><td>{{ email_data.sender }}</td></tr>
                    <tr><th>Subject</th><td>{{ email_data.subject }}</td></tr>
                    <tr><th>Date Received</th><td>{{ email_data.date }}</td></tr>
                    <tr><th>Document Completeness</th><td>{{ email_analysis.completion_status }}</td></tr>
                    <tr><th>Documents Found</th><td>{{ email_analysis.documents_found|length }}</td></tr>
                </table>
                
                {% if email_analysis.missing_documents %}
                <div class="alert alert-warning">
                    <strong>Missing Documents:</strong>
                    <ul>
                        {% for doc in email_analysis.missing_documents %}
                        <li>{{ doc }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>Document Analysis</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Document</th>
                            <th>Type</th>
                            <th>Confidence</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for doc in documents_found %}
                        <tr>
                            <td>{{ doc.filename }}</td>
                            <td>{{ doc.document_type }}</td>
                            <td>{{ doc.confidence }}</td>
                            <td>✅ Processed</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="page-break section">
                <h2>Fraud Detection Analysis</h2>
                <div class="highlight">
                    <strong>Risk Assessment:</strong> <span class="risk-{{ fraud_risk.lower() }}">{{ fraud_risk }}</span>
                </div>
                <p>{{ fraud_analysis_summary }}</p>
                
                {% if fraud_indicators %}
                <div class="alert alert-danger">
                    <strong>Fraud Indicators Detected:</strong>
                    <ul>
                        {% for indicator in fraud_indicators %}
                        <li>{{ indicator }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>Treaty Exclusions Validation</h2>
                {% if exclusion_violations %}
                <div class="alert alert-danger">
                    <strong>Exclusion Violations Found:</strong>
                    <ul>
                        {% for violation in exclusion_violations %}
                        <li>{{ violation }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <div class="alert alert-success">
                    No treaty exclusions violations detected.
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>Amount Reconciliation</h2>
                {% if reconciliation_issues %}
                <div class="alert alert-warning">
                    <strong>Reconciliation Issues:</strong>
                    <ul>
                        {% for issue in reconciliation_issues %}
                        <li>{{ issue }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <div class="alert alert-success">
                    All amounts reconciled successfully.
                </div>
                {% endif %}
                
                <table class="data-table">
                    <tr><th>Bordereaux Total</th><td>${{ amounts.bordereaux_total }}</td></tr>
                    <tr><th>Statement Total</th><td>${{ amounts.statement_total }}</td></tr>
                    <tr><th>Variance</th><td>${{ amounts.variance }}</td></tr>
                    <tr><th>Variance %</th><td>{{ amounts.variance_percent }}%</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>Date Validation</h2>
                {% if date_validation_errors %}
                <div class="alert alert-warning">
                    <strong>Date Validation Errors:</strong>
                    <ul>
                        {% for error in date_validation_errors %}
                        <li>{{ error }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <div class="alert alert-success">
                    All dates validated successfully.
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>Duplicate Claims Check</h2>
                {% if duplicate_claims %}
                <div class="alert alert-danger">
                    <strong>Duplicate Claims Detected:</strong>
                    <ul>
                        {% for duplicate in duplicate_claims %}
                        <li>{{ duplicate }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <div class="alert alert-success">
                    No duplicate claims detected.
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>Compliance Assessment</h2>
                {% if compliance_issues %}
                <div class="alert alert-warning">
                    <strong>Compliance Issues:</strong>
                    <ul>
                        {% for issue in compliance_issues %}
                        <li>{{ issue }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% else %}
                <div class="alert alert-success">
                    All compliance requirements met.
                </div>
                {% endif %}
            </div>

            <div class="page-break section">
                <h2>Final Recommendation</h2>
                <div class="highlight">
                    <h3>Decision: <span class="status-badge status-{{ recommendation.lower() }}">{{ recommendation }}</span></h3>
                    <p><strong>Rationale:</strong> {{ recommendation_rationale }}</p>
                </div>
                
                {% if next_actions %}
                <h4>Required Actions:</h4>
                <ul>
                    {% for action in next_actions %}
                    <li>{{ action }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
            </div>

            <div class="footer">
                <p>This report was generated by the Automated Claims Processing System</p>
                <p>Report ID: {{ report_id }} | Generated: {{ report_date }}</p>
            </div>
        </body>
        </html>
        """)
    
    async def _compile_report_data(self, analysis_results: Dict[str, Any], document_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "report_id": f"CLM-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "report_date": datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC'),
            "recommendation": analysis_results.get("overall_recommendation", "REVIEW"),
            "fraud_risk": analysis_results.get("fraud_analysis", {}).get("risk_level", "UNKNOWN"),
            "email_data": document_results.get("email_content", {}),
            "email_analysis": document_results.get("email_analysis", {}),
            "documents_found": document_results.get("email_analysis", {}).get("documents_found", []),
            "key_findings": self._extract_key_findings(analysis_results),
            "fraud_analysis_summary": analysis_results.get("fraud_analysis", {}).get("agent_response", "No analysis available"),
            "fraud_indicators": self._extract_fraud_indicators(analysis_results),
            "exclusion_violations": self._extract_exclusion_violations(analysis_results),
            "reconciliation_issues": self._extract_reconciliation_issues(analysis_results),
            "amounts": self._extract_amounts(analysis_results),
            "date_validation_errors": self._extract_date_errors(analysis_results),
            "duplicate_claims": self._extract_duplicate_claims(analysis_results),
            "compliance_issues": self._extract_compliance_issues(analysis_results),
            "recommendation_rationale": self._generate_rationale(analysis_results),
            "next_actions": self._generate_next_actions(analysis_results)
        }
    
    async def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        return self.report_template.render(**report_data)
    
    async def _generate_pdf_report(self, html_content: str, report_data: Dict[str, Any]) -> str:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"claims_analysis_report_{timestamp}.pdf"
        pdf_path = os.path.join(self.output_folder, pdf_filename)
        
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1in;
            }
            .header {
                break-inside: avoid;
            }
            .section {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            .page-break {
                page-break-before: always;
            }
        ''')
        
        HTML(string=html_content).write_pdf(pdf_path, stylesheets=[css])
        return pdf_path
    
    async def _generate_executive_summary(self, report_data: Dict[str, Any]) -> str:
        recommendation = report_data.get("recommendation", "REVIEW")
        fraud_risk = report_data.get("fraud_risk", "UNKNOWN")
        key_findings = report_data.get("key_findings", [])
        
        summary = f"""
EXECUTIVE SUMMARY - CLAIMS ANALYSIS REPORT

Report ID: {report_data.get('report_id', 'N/A')}
Date: {report_data.get('report_date', 'N/A')}

OVERALL RECOMMENDATION: {recommendation}
FRAUD RISK LEVEL: {fraud_risk}

KEY FINDINGS:"""
        
        for i, finding in enumerate(key_findings, 1):
            summary += f"\n{i}. {finding}"
        
        summary += f"\n\nRATIONALE: {report_data.get('recommendation_rationale', 'No rationale provided')}"
        
        next_actions = report_data.get("next_actions", [])
        if next_actions:
            summary += "\n\nREQUIRED ACTIONS:"
            for i, action in enumerate(next_actions, 1):
                summary += f"\n{i}. {action}"
        
        return summary
    
    def _extract_key_findings(self, analysis_results: Dict[str, Any]) -> List[str]:
        findings = []
        
        if analysis_results.get("fraud_analysis", {}).get("risk_level") == "HIGH":
            findings.append("High fraud risk detected - requires immediate review")
        
        if analysis_results.get("exclusion_analysis", {}).get("violations_found"):
            findings.append("Treaty exclusion violations identified")
        
        if analysis_results.get("duplicate_check", {}).get("duplicates_found"):
            findings.append("Duplicate claims detected in system")
        
        if analysis_results.get("reconciliation_results", {}).get("discrepancies_found"):
            findings.append("Amount discrepancies found between documents")
        
        if analysis_results.get("date_validation", {}).get("validation_failures"):
            findings.append("Date validation failures identified")
        
        if analysis_results.get("compliance_results", {}).get("compliance_issues"):
            findings.append("Regulatory compliance issues detected")
        
        if not findings:
            findings.append("All standard validations passed successfully")
        
        return findings
    
    def _extract_fraud_indicators(self, analysis_results: Dict[str, Any]) -> List[str]:
        indicators = []
        fraud_response = analysis_results.get("fraud_analysis", {}).get("agent_response", "").lower()
        
        if "unusual amount" in fraud_response:
            indicators.append("Unusual claim amounts detected")
        if "suspicious documentation" in fraud_response:
            indicators.append("Suspicious documentation patterns")
        if "multiple claims" in fraud_response:
            indicators.append("Multiple claims from same insured")
        if "timing" in fraud_response:
            indicators.append("Suspicious timing of claims")
        
        return indicators
    
    def _extract_exclusion_violations(self, analysis_results: Dict[str, Any]) -> List[str]:
        violations = []
        exclusion_response = analysis_results.get("exclusion_analysis", {}).get("agent_response", "").lower()
        
        if "war" in exclusion_response and "violation" in exclusion_response:
            violations.append("War exclusion violation detected")
        if "nuclear" in exclusion_response and "violation" in exclusion_response:
            violations.append("Nuclear exclusion violation detected")
        if "cyber" in exclusion_response and "violation" in exclusion_response:
            violations.append("Cyber exclusion violation detected")
        
        return violations
    
    def _extract_reconciliation_issues(self, analysis_results: Dict[str, Any]) -> List[str]:
        issues = []
        reconciliation_response = analysis_results.get("reconciliation_results", {}).get("agent_response", "").lower()
        
        if "discrepancy" in reconciliation_response:
            issues.append("Amount discrepancies identified between documents")
        if "variance" in reconciliation_response:
            issues.append("Significant variances in reported amounts")
        
        return issues
    
    def _extract_amounts(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        return {
            "bordereaux_total": "0.00",
            "statement_total": "0.00", 
            "variance": "0.00",
            "variance_percent": "0.0"
        }
    
    def _extract_date_errors(self, analysis_results: Dict[str, Any]) -> List[str]:
        errors = []
        date_response = analysis_results.get("date_validation", {}).get("agent_response", "").lower()
        
        if "outside policy period" in date_response:
            errors.append("Claims with loss dates outside policy periods")
        if "incorrect quarter" in date_response:
            errors.append("Payment dates in incorrect accounting quarter")
        
        return errors
    
    def _extract_duplicate_claims(self, analysis_results: Dict[str, Any]) -> List[str]:
        duplicates = []
        duplicate_response = analysis_results.get("duplicate_check", {}).get("agent_response", "").lower()
        
        if "duplicate claim id" in duplicate_response:
            duplicates.append("Duplicate claim IDs found in database")
        if "same loss date" in duplicate_response:
            duplicates.append("Multiple claims with identical loss dates and insured")
        
        return duplicates
    
    def _extract_compliance_issues(self, analysis_results: Dict[str, Any]) -> List[str]:
        issues = []
        compliance_response = analysis_results.get("compliance_results", {}).get("agent_response", "").lower()
        
        if "documentation" in compliance_response and "incomplete" in compliance_response:
            issues.append("Incomplete documentation standards")
        if "authorization" in compliance_response and "exceeded" in compliance_response:
            issues.append("Authorization limits exceeded")
        
        return issues
    
    def _generate_rationale(self, analysis_results: Dict[str, Any]) -> str:
        recommendation = analysis_results.get("overall_recommendation", "REVIEW")
        
        if recommendation == "APPROVE":
            return "All validation checks passed successfully. No significant issues identified that would prevent claim processing."
        elif recommendation == "REJECT":
            return "Critical issues identified including treaty violations, fraud indicators, or duplicate claims that require claim rejection."
        else:
            return "Multiple validation concerns identified that require supervisory review before processing can proceed."
    
    def _generate_next_actions(self, analysis_results: Dict[str, Any]) -> List[str]:
        actions = []
        recommendation = analysis_results.get("overall_recommendation", "REVIEW")
        
        if recommendation == "REJECT":
            actions.extend([
                "Notify cedant of claim rejection with detailed reasons",
                "Document rejection rationale in claims system",
                "Escalate to senior management for final approval"
            ])
        elif recommendation == "REVIEW":
            actions.extend([
                "Schedule supervisory review meeting",
                "Request additional documentation if needed",
                "Validate disputed amounts with cedant"
            ])
        else:
            actions.extend([
                "Proceed with standard claims processing",
                "Generate payment authorization",
                "Update claims database with processing results"
            ])
        
        return actions